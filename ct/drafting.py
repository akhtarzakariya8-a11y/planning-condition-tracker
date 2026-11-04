"""Roadmap 2.4: auto-drafted discharge submissions.

A SECOND prompt (prompt_drafting.txt), run on demand for one discharge application at a time.
It writes the covering letter and, for each condition, what to submit, who prepares it and
what the submission must cover — taken from the condition's own wording.

The prompt is told never to invent facts, and this module checks that it didn't:
  * every condition asked for comes back exactly once (extras dropped, gaps reported);
  * any drawing/document-reference-looking token in the draft that is NOT in the notice is
    reported, so a made-up "Dwg 1234-P-01 Rev C" can't slip into a letter unnoticed.
"""
import io
import json
import re

from ct import config
from ct.extract import call_for_json
from ct.logic import JURISDICTION_LABEL, specialists_for


def drafting_prompt():
    return config.DRAFTING_PROMPT_FILE.read_text(encoding="utf-8")


def build_request(data, conditions, stage, fee=None, fee_note=None):
    """The JSON the drafting prompt receives. Only what the notice actually says."""
    return {
        "notice": {
            "local_authority": data.get("local_authority"),
            "application_reference": data.get("application_reference"),
            "site_address": data.get("site_address"),
            "applicant": data.get("applicant"),
            "development_description": data.get("development_description"),
            "decision_date": data.get("decision_date"),
            "nation": JURISDICTION_LABEL.get(data.get("jurisdiction")),
            "document_type": data.get("document_type"),
        },
        "application": {"stage": stage, "fee": fee, "fee_note": fee_note},
        "conditions": [{
            "condition_number": c["condition_number"],
            "summary": c.get("summary"),
            "source_quote": c.get("source_quote"),
            "specialist_needed": specialists_for(c),
        } for c in sorted(conditions, key=lambda c: c["condition_number"])],
    }


# Things that look like drawing / document references: "1234-P-001", "PL-02 Rev B", "A100".
_REF_TOKEN = re.compile(r"\b(?=[A-Z0-9_./-]*\d)(?=[A-Z0-9_./-]*[A-Z])[A-Z0-9][A-Z0-9_./-]{3,}\b")


def unverified_references(draft, source_text):
    """Reference-like tokens in the draft that appear nowhere in what the model was given."""
    text = json.dumps(draft, ensure_ascii=False)
    text = re.sub(r"\[[^\]]*\]", " ", text)          # placeholders are fine by definition
    source = source_text.upper()
    found = set()
    for tok in _REF_TOKEN.findall(text):
        t = tok.strip("./-")
        if len(t) < 4 or t.upper() in source:
            continue
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}", t):   # dates and years
            continue
        found.add(t)
    return sorted(found)


def draft_application(client, data, conditions, stage, fee=None, fee_note=None):
    """Draft one discharge application. Returns the draft dict plus "_checks" and "_usage"."""
    request = build_request(data, conditions, stage, fee, fee_note)
    draft, usage = call_for_json(
        client, drafting_prompt(), json.dumps(request, ensure_ascii=False, indent=1),
        ((config.DRAFT_MAX_TOKENS, 0.2), (config.DRAFT_MAX_TOKENS * 2, 0.3)))

    wanted = [c["condition_number"] for c in request["conditions"]]
    got = {}
    for item in draft.get("conditions") or []:
        n = item.get("condition_number")
        if n in wanted and n not in got:
            got[n] = item
    draft["conditions"] = [got[n] for n in wanted if n in got]
    draft["_checks"] = {
        "missing": [n for n in wanted if n not in got],
        "unverified_references": unverified_references(
            draft, json.dumps(request, ensure_ascii=False)),
    }
    draft["_usage"] = usage
    draft["_cost_usd"] = round(config.cost_usd(usage), 4)
    draft["_stage"] = stage
    return draft


def letter_text(draft):
    return (draft.get("covering_letter") or "").replace("\\n", "\n").strip()


def build_docx(data, draft):
    """The draft as a Word document the applicant can edit and send."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)

    def para(text, bold=False, italic=False, size=None, colour=None, after=6):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold, run.italic = bold, italic
        if size:
            run.font.size = Pt(size)
        if colour:
            run.font.color.rgb = RGBColor.from_string(colour)
        p.paragraph_format.space_after = Pt(after)
        return p

    doc.add_heading("Discharge of conditions — draft submission", level=0)
    para(f"{data.get('application_reference') or '[APPLICATION REFERENCE]'} · "
         f"{data.get('site_address') or '[SITE ADDRESS]'}", bold=True)
    para(f"Stage: {draft.get('_stage') or ''}", colour="6E675C")
    warn = para("DRAFT generated by AI from the decision notice. Fill in every [PLACEHOLDER], "
                "check each statement against the condition wording and your consultants' "
                "reports, and have it reviewed before submission. Not legal or planning advice.",
                italic=True, size=9, colour="8A5A14", after=12)
    warn.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.add_heading("1. Covering letter", level=1)
    if draft.get("subject"):
        para(draft["subject"], bold=True)
    for block in re.split(r"\n\s*\n", letter_text(draft)):
        para(block.strip())

    doc.add_heading("2. What to submit for each condition", level=1)
    for item in draft.get("conditions", []):
        n = item.get("condition_number")
        src = next((c for c in data.get("conditions", []) if c["condition_number"] == n), {})
        doc.add_heading(f"Condition {n} — {src.get('summary') or ''}".strip(" —"), level=2)
        if src.get("source_quote"):
            para("The condition says:", bold=True, after=2)
            para(src["source_quote"], italic=True, colour="3C382F")
        if item.get("requirement"):
            para("What the council needs", bold=True, after=2)
            para(item["requirement"])
        if item.get("documents"):
            para("Documents to submit", bold=True, after=2)
            for d in item["documents"]:
                who = f" — prepared by {d.get('prepared_by')}" if d.get("prepared_by") else ""
                doc.add_paragraph(f"{d.get('title')}{who}", style="List Bullet")
        if item.get("must_cover"):
            para("Your submission must cover", bold=True, after=2)
            for m in item["must_cover"]:
                doc.add_paragraph(f"☐  {m}")
        if item.get("statement"):
            para("Suggested wording", bold=True, after=2)
            para(item["statement"])

    if draft.get("before_submitting"):
        doc.add_heading("3. Before you submit", level=1)
        for step in draft["before_submitting"]:
            doc.add_paragraph(step, style="List Number")

    checks = draft.get("_checks") or {}
    if checks.get("unverified_references"):
        doc.add_heading("Check these references", level=1)
        para("These look like drawing or document references but do not appear in the decision "
             "notice. Confirm each one is real, or replace it with your own reference: "
             + ", ".join(checks["unverified_references"]), colour="A3352C")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
