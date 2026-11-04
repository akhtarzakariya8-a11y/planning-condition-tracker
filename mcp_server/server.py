"""
Planning Condition Tracker — MCP server
=======================================

This file turns the planning tool into an MCP server, so any MCP "host" (Claude Desktop,
Claude Code, Cursor, ChatGPT...) can use it as a set of tools.

  app.py      = the planning tool for a PERSON  (upload a PDF on a web page)
  server.py   = the planning tool for an AI     (the AI calls these functions itself, mid-chat)

Both use the same brain (prompt_v4_production.txt) and the same rules: the ct/ package in
the project folder. Change a rule there once and the web page, the eval and this server all
follow.

What this server offers (the three MCP "server primitives"):

  TOOLS     functions the AI decides to call on its own
              list_notices                which notices are available
              begin_by_date               date maths only, no AI (the simplest possible tool)
              analyse_notice              extract every condition from a notice
              what_blocks_start           the Safety Gate: what stops us starting on site?
              discharge_plan              how many discharge applications, and the fees
              plan_programme              work back from your dates: submit-by / commission-by
              draft_discharge_application write the covering letter + what to submit (paid call)

  RESOURCE  read-only data the user (or app) can attach as context
              notice://{filename} the raw text of a notice

  PROMPT    a ready-made instruction the user picks from a menu
              site_start_briefing

Run it:      .venv/bin/python server.py      (it then sits silently, waiting for a host)
Test it:     .venv/bin/python test_client.py
Inspect it:  npx @modelcontextprotocol/inspector .venv/bin/python server.py
             (opens the MCP Inspector in your browser to call tools by hand; needs Node.js)

GOLDEN RULE FOR STDIO SERVERS: never print() anything. stdout is the "wire" the host and this
server talk over (JSON-RPC messages). A stray print() corrupts it and the connection dies.
Use log() below instead — it writes to stderr, which Claude Desktop saves to its log files.
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import anthropic
import pdfplumber
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError


# ---------------------------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------------------------
# Claude Desktop starts this script from ITS folder, not yours, so every path is worked out
# from where this file lives rather than from "the current folder".
SERVER_DIR = Path(__file__).resolve().parent            # .../summer-project/mcp_server
PROJECT_DIR = SERVER_DIR.parent                         # .../summer-project
CACHE_DIR = SERVER_DIR / ".cache"                       # saved analyses: pay for a notice once

# Only PDFs in this folder are visible to the AI — it can't wander into the rest of your
# computer. Override it with a PLANNING_NOTICES_DIR setting in the host's config if you like.
NOTICES_DIR = Path(os.environ.get("PLANNING_NOTICES_DIR", SERVER_DIR / "notices")).expanduser()

load_dotenv(PROJECT_DIR / ".env")   # reuses ANTHROPIC_API_KEY from the Streamlit app's .env

# The shared rules live in the project's ct/ package. Importing it (rather than app.py, which
# would start the web page) means this server can never drift out of step with the app.
sys.path.insert(0, str(PROJECT_DIR))
from ct import config as ct_config                     # noqa: E402
from ct import drafting as ct_drafting                 # noqa: E402
from ct import extract as ct_extract                   # noqa: E402
from ct import logic                                   # noqa: E402
from ct import programme as ct_programme               # noqa: E402

MODEL = ct_config.MODEL
GATE_DOC_TYPES = logic.GATE_DOC_TYPES
CIL_DOC_TYPES = logic.CIL_DOC_TYPES
CAVEAT = ("Automated flags, not legal advice — whether a condition is a true condition-precedent "
          "can be finely balanced. Confirm with a planning consultant or solicitor before "
          "starting on site.")
CIL_REMINDER = ("Before any material operation on site, check whether the development is "
                "CIL-liable and, if so, submit a CIL Commencement Notice and get written "
                "acknowledgement first. This tool does not read CIL notices.")


def log(message):
    """Print to stderr, never stdout (see the golden rule at the top)."""
    print(f"[planning-mcp] {message}", file=sys.stderr, flush=True)


# This one line creates the server. "instructions" is shown to the AI so it knows when and
# how to use the tools — think of it as the server's job description.
mcp = MCPServer(
    name="planning-condition-tracker",
    instructions=(
        "Tools for reading UK planning permission decision notices. Use list_notices to see "
        "which notices are available, analyse_notice to extract every planning condition, "
        "what_blocks_start to answer 'can we start on site, and what is stopping us?', "
        "discharge_plan for how many discharge applications and what they cost, plan_programme "
        "to work back from the user's dates to submit-by and commission-by deadlines, and "
        "draft_discharge_application to write a first draft of an application. "
        "Everything returned is an automated flag, not legal advice; say so when you use it."
    ),
)


# ---------------------------------------------------------------------------------------------
# HELPERS — the date maths and Safety Gate rules come from ct.logic, shared with app.py.
# ---------------------------------------------------------------------------------------------
strip_fences = ct_extract.strip_fences
compute_begin_by = logic.compute_begin_by
fmt_date = logic.fmt_date
split_by_gate = logic.split_by_gate


# ---------------------------------------------------------------------------------------------
# THE ENGINE — read a PDF, send it to Claude with the production prompt, get JSON back.
# ---------------------------------------------------------------------------------------------
def notice_path(filename, error=ToolError):
    """Turn a filename from the AI into a safe path inside NOTICES_DIR.

    Never trust input blindly — the AI might pass '../../secret.pdf' by mistake (or because
    a document told it to). Only a plain filename of a PDF that exists in the folder is allowed.

    Why raise ToolError rather than a normal error? ToolError means "a failure I expected":
    the AI gets to read the message (including the list of real filenames) and can correct
    itself. Any other exception counts as a crash, and the AI only sees "Error executing tool".
    """
    name = Path(str(filename)).name
    path = NOTICES_DIR / name
    if name != filename or path.suffix.lower() != ".pdf" or not path.is_file():
        available = ", ".join(list_notices()) or "none"
        raise error(f"No notice called '{filename}'. Available notices: {available}")
    return path


def read_pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "".join(page.extract_text() or "" for page in pdf.pages)


def run_extraction(path):
    """Analyse one notice, using the saved copy if this exact file has been analysed before.

    The cache name includes a fingerprint of the prompt, so editing the prompt automatically
    invalidates every saved analysis — an old answer can never outlive the rules that made it.
    """
    import hashlib
    CACHE_DIR.mkdir(exist_ok=True)
    prompt_id = hashlib.sha256(ct_extract.system_prompt().encode("utf-8")).hexdigest()[:8]
    cache_file = CACHE_DIR / f"{path.stem}.{prompt_id}.json"
    if cache_file.exists() and cache_file.stat().st_mtime >= path.stat().st_mtime:
        log(f"cache hit: {path.name}")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    client = ct_extract.get_client()
    if client is None:
        raise ToolError("ANTHROPIC_API_KEY is missing — add it to the project's .env file.")

    log(f"analysing {path.name} with {MODEL} ...")
    try:
        # Exactly the app's pipeline: text (or vision for scans), same retries, same model.
        data = ct_extract.extract(path.read_bytes(), client)
    except ct_extract.ExtractionError as exc:
        raise ToolError(f"Couldn't get a readable analysis of {path.name} after two attempts "
                        f"({exc.kind}).")
    except anthropic.APIError as exc:
        raise ToolError(f"The Anthropic API call failed ({type(exc).__name__}): {exc}")
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log(f"done: {path.name} ({len(data.get('conditions', []))} conditions, "
        f"${data.get(ct_extract.COST_KEY, 0):.3f})")
    return data


# ---------------------------------------------------------------------------------------------
# TOOLS — each @mcp.tool() function becomes a tool the AI can call.
# The function NAME becomes the tool name, the TYPE HINTS become its input schema, and the
# DOCSTRING becomes the description the AI reads to decide when to use it. Write docstrings
# for the AI, not for yourself: they are the tool's sales pitch.
# ---------------------------------------------------------------------------------------------
@mcp.tool()
def list_notices() -> list[str]:
    """List the planning decision-notice PDFs available to analyse.
    Call this first if you don't know the exact filename."""
    if not NOTICES_DIR.is_dir():
        return []
    return sorted(p.name for p in NOTICES_DIR.iterdir()
                  if p.suffix.lower() == ".pdf" and not p.name.startswith("."))


@mcp.tool()
def begin_by_date(decision_date: str, time_limit_years: int = 3) -> str:
    """Work out the date by which development must begin, or the planning permission lapses.
    Give the decision date as written on the notice (e.g. '10 November 2025') and the time
    limit in years from the time-limit condition (usually 3). Pure date maths, no AI."""
    d = compute_begin_by(decision_date, time_limit_years)
    if d is None:
        return f"Couldn't read '{decision_date}' as a date. Try a format like '10 November 2025'."
    status = "This deadline has already passed." if d < date.today() else ""
    return f"Development must begin by {fmt_date(d)}. {status}".strip()


@mcp.tool()
def analyse_notice(filename: str) -> dict:
    """Read one UK planning decision notice and extract every planning condition.

    Returns the document type, decision, decision date, time limit, any flags, and every
    condition with: a plain-English summary, category, deadline, whether it needs formal
    discharge, its 'gate' (what it blocks: any commencement, demolition, piling, above-ground
    works, occupation, use, ongoing), whether that gate is ambiguous, and a verbatim quote of
    the council's wording. The first run on a notice can take a minute or two; repeat runs are
    instant because the result is saved."""
    return run_extraction(notice_path(filename))


@mcp.tool()
def what_blocks_start(filename: str) -> dict:
    """The Safety Gate: can we start on site, and what is stopping us?

    For one decision notice, returns: the date development must begin by; HARD BLOCKERS that
    must be discharged before any work at all (true conditions-precedent); conditions that must
    be cleared before piling; conditions that only block ABOVE-GROUND works (so demolition and
    groundworks can start first); and conditions whose wording is ambiguous and needs checking.
    Always pass on the caveat that this is not legal advice."""
    data = run_extraction(notice_path(filename))
    doc_type = data.get("document_type") or "full-grant"
    if doc_type not in GATE_DOC_TYPES:
        return {"document_type": doc_type,
                "message": "Nothing to start on site: this is not a grant of permission "
                           "(it may be a refusal, or a notice approving conditions already discharged)."}

    conditions = data.get("conditions", [])
    blockers, piling, ambiguous, startable = split_by_gate(conditions)
    deadline = logic.start_deadline_message(data)
    begin_by = deadline["date"]

    # CONSISTENCY CHECK — Python double-checking the AI.
    # A hard blocker whose own trigger wording only mentions above-ground works is a blocker
    # because its Reason (or another part of the condition) says nothing may start first.
    # The extraction should flag that as ambiguous, but doesn't always, so make sure it does.
    for c in blockers:
        trigger = (c.get("trigger_quote") or "").lower()
        if re.search(r"above[\s-]ground", trigger) and c not in ambiguous:
            ambiguous.append(c)

    def brief(group):
        return [{"condition": c.get("condition_number"), "summary": c.get("summary"),
                 "trigger": c.get("trigger_quote")}
                for c in sorted(group, key=lambda c: c.get("condition_number") or 0)]

    result = {
        "document_type": doc_type,
        "decision": data.get("decision"),
        "decision_date": data.get("decision_date"),
        "begin_by": fmt_date(begin_by) if begin_by else None,
        "begin_by_explained": deadline["text"],
        "permission_expired": bool(begin_by and begin_by < date.today()),
        "total_conditions": len(conditions),
        "hard_blockers": brief(blockers),
        "before_piling": brief(piling),
        "can_break_ground_before_these": brief(startable),
        "check_ambiguous_wording": brief(ambiguous),
        "caveat": CAVEAT,
    }
    # Explain the overlap, so the AI reading this doesn't second-guess the classification.
    if any(c in blockers for c in ambiguous):
        result["why_some_blockers_are_also_ambiguous"] = (
            "Conditions listed both as hard blockers and under check_ambiguous_wording have "
            "trigger wording that mentions above-ground works, but the condition's Reason, or "
            "another part of the condition, requires it to be discharged before any development "
            "starts. The stricter reading is used: treat them as blockers until a planning "
            "consultant confirms otherwise.")
    if doc_type in CIL_DOC_TYPES:
        result["cil_reminder"] = CIL_REMINDER
    return result


@mcp.tool()
def discharge_plan(filename: str) -> dict:
    """How many applications to discharge this notice's conditions, and the council fees.

    Conditions that need formal discharge (submitted to AND approved by the council) are
    bundled by stage, because the statutory fee is charged per application, not per condition.
    Fees are the England/Wales statutory rates in force today (and any scheduled rise);
    Scotland and Northern Ireland are not priced. Free for listed building consent."""
    data = run_extraction(notice_path(filename))
    plan = logic.build_discharge_plan(data)
    if not plan["applies"]:
        return {"document_type": logic.doc_type(data),
                "message": "No outstanding conditions to discharge on this document."}
    rise = plan["next_rise"]
    return {
        "conditions_needing_discharge": plan["total"],
        "applications": [{"stage": stage, "conditions": [c["condition_number"] for c in members]}
                         for stage, members in plan["batches"]],
        "fee_per_application": plan["fee"],
        "total_fees": plan["cost"],
        "fee_rise": ({"on": fmt_date(rise[0]), "other": rise[1]["other"],
                      "householder": rise[1]["householder"]} if rise else None),
        "householder_rate": plan["householder"],
        "jurisdiction": plan["jurisdiction"],
        "deemed_discharge_applies": plan["deemed_discharge"],
        "caveat": "Batching is guidance; fees change — confirm before relying on them. Not legal advice.",
    }


@mcp.tool()
def plan_programme(filename: str, start_on_site: str, start_piling: str = "",
                   above_ground_works: str = "", first_occupation: str = "",
                   prep_weeks: int = 6, validation_buffer_weeks: int = 2) -> dict:
    """Work back from the user's programme dates to the deadlines that matter.

    Give dates like '1 March 2027' or '01/03/2027'. Only start_on_site is required; piling
    and above-ground works default to the start date (the safe assumption), and occupation
    is left unscheduled if not given. Returns, for each discharge application: the date to
    SUBMIT by (milestone minus the council's statutory 8 weeks and a validation buffer), the
    date to COMMISSION the specialists by (minus preparation time), the conditions in it, the
    fee in force on that date, and whether it is already late. Also warns if the planned
    start is after the permission lapses, and if submitting before a fee rise saves money.
    Pure date maths on the extraction — no extra AI cost once the notice is analysed."""
    data = run_extraction(notice_path(filename))
    dates = {"start": start_on_site, "piling": start_piling or None,
             "above_ground": above_ground_works or None, "occupation": first_occupation or None}
    if not logic.parse_date(start_on_site):
        raise ToolError(f"Couldn't read '{start_on_site}' as a date. Try '1 March 2027'.")
    prog = ct_programme.build_programme(data, dates, prep_weeks, validation_buffer_weeks)
    saving = ct_programme.fee_rise_saving(data, prog)
    return {
        "permission_lapses": fmt_date(prog["lapse"]) if prog["lapse"] else None,
        "planned_start_is_after_lapse": prog["start_after_lapse"],
        "applications": [{
            "submit_by": fmt_date(g["submit_by"]),
            "commission_specialists_by": fmt_date(g["commission_by"]),
            "needed_before": g["before"],
            "conditions": [c["condition_number"] for c in g["discharge"]],
            "specialists": g["specialists"],
            "council_fee": g["fee"],
            "status": {"late": "LATE - submit now", "soon": "due within 4 weeks",
                       "ok": "on track"}.get(g["status"]),
        } for g in ct_programme.submission_groups(prog)],
        "comply_without_application": [
            {"before": s["label"], "conditions": [c["condition_number"] for c in s["other"]]}
            for s in prog["steps"] if s["other"]],
        "brought_forward": [{"condition": n, "because_condition": b}
                            for n, (_, _, b) in sorted(prog["pulled"].items())],
        "fee_rise_saving": ({"rise_on": fmt_date(saving["rise_date"]), "from": saving["old"],
                             "to": saving["new"]} if saving else None),
        "assumptions": f"{ct_programme.DETERMINATION_WEEKS} weeks statutory determination + "
                       f"{validation_buffer_weeks} weeks validation; {prep_weeks} weeks to prepare.",
        "caveat": "A planning aid, not legal advice. Confirm the programme with a planning consultant.",
    }


@mcp.tool()
def draft_discharge_application(filename: str, conditions: list[int]) -> dict:
    """Write a first draft of ONE application to discharge the given conditions.

    Returns a covering letter addressed to the council and, for each condition: what the
    council must approve, the documents to submit and who prepares them, every matter the
    condition's own wording says the submission must cover, and suggested wording. Anything
    only the applicant knows (names, dates, document references) is a [PLACEHOLDER] — never
    invented. This makes one extra AI call (typically a few pence), so call it only when the
    user asks for a draft. Use discharge_plan or plan_programme first to choose which
    conditions belong together in one application."""
    data = run_extraction(notice_path(filename))
    by_num = {c["condition_number"]: c for c in data.get("conditions", [])}
    unknown = [n for n in conditions if n not in by_num]
    if unknown or not conditions:
        raise ToolError(f"Unknown condition number(s): {unknown or 'none given'}. "
                        f"This notice has conditions {sorted(by_num)}.")
    client = ct_extract.get_client()
    if client is None:
        raise ToolError("ANTHROPIC_API_KEY is missing — add it to the project's .env file.")
    fee_note = ("No fee is payable for applications to discharge conditions on a listed "
                "building consent." if logic.doc_type(data) == "listed-building-consent" else None)
    try:
        draft = ct_drafting.draft_application(
            client, data, [by_num[n] for n in sorted(set(conditions))],
            "Application for approval of details reserved by condition",
            logic.fee_for(data), fee_note)
    except ct_extract.ExtractionError as exc:
        raise ToolError(f"Couldn't get a usable draft after two attempts ({exc.kind}).")
    except anthropic.APIError as exc:
        raise ToolError(f"The Anthropic API call failed ({type(exc).__name__}): {exc}")
    log(f"drafted {filename} {sorted(set(conditions))} (${draft.get('_cost_usd', 0):.3f})")
    draft.pop("_usage", None)
    draft["caveat"] = ("AI draft. Fill every [PLACEHOLDER] and check each statement against the "
                       "condition and the consultants' reports before submitting.")
    return draft


# ---------------------------------------------------------------------------------------------
# RESOURCE — read-only data, addressed by a URI (like a web address). The {filename} part makes
# this a "resource template": one definition covers every notice in the folder.
# ---------------------------------------------------------------------------------------------
@mcp.resource("notice://{filename}", mime_type="text/plain",
              description="The raw text of a planning decision notice, as read from the PDF.")
def notice_text(filename: str) -> str:
    text = read_pdf_text(notice_path(filename, error=ResourceNotFoundError))
    return text or "(This PDF has no text layer — it is a scan. Use analyse_notice instead.)"


# ---------------------------------------------------------------------------------------------
# PROMPT — a reusable instruction the USER picks (in Claude Desktop: the + menu). Tools are
# chosen by the AI; prompts are chosen by the person. That's the key difference.
# ---------------------------------------------------------------------------------------------
@mcp.prompt(title="Site-start briefing")
def site_start_briefing(filename: str) -> str:
    """A one-page 'can we start on site?' briefing for a developer and their QS."""
    return (
        f"Use the planning-condition-tracker tools on the decision notice '{filename}'. "
        "Call what_blocks_start first, then analyse_notice if you need more detail.\n\n"
        "Write a one-page briefing for a developer and their quantity surveyor:\n"
        "1. The date development must begin by.\n"
        "2. What must be discharged before ANY work starts, and who would typically prepare "
        "each submission.\n"
        "3. What can start early (demolition / groundworks) and what only blocks above-ground "
        "works.\n"
        "4. Anything ambiguous to check with the planning consultant.\n"
        "5. A suggested order of work for the first month.\n"
        "Quote condition numbers throughout and end with the not-legal-advice caveat."
    )


if __name__ == "__main__":
    log(f"starting; notices folder = {NOTICES_DIR}")
    mcp.run()   # default transport is stdio: talk to whoever launched us over stdin/stdout
