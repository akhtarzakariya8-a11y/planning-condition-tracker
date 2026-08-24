import streamlit as st
import anthropic
import pdfplumber
import json
import io
import base64
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from dotenv import load_dotenv

from theme.ct_theme import inject_theme, eyebrow, tag, banner, note

load_dotenv()
client = anthropic.Anthropic()

with open("prompt_v4_production.txt") as f:
    system_prompt = f.read()


# ----- PAGE CONFIG + THEME -----
st.set_page_config(
    page_title="AI Planning Condition Tracker",
    page_icon="📋",
    layout="wide",
)
inject_theme()

# Layout only — every colour and type decision comes from theme/tokens.css.
st.markdown("""
<style>
  .block-container { max-width: 1120px; }
  .ct-panel      { padding: var(--ct-s4); margin: 0 0 var(--ct-s4) 0; }
  .ct-panel-hd   { margin-bottom: var(--ct-s3); }
  .ct-line       { padding: 10px 0; border-bottom: 1px solid var(--ct-border-soft); }
  .ct-line:last-of-type { border-bottom: none; }
  .ct-line-txt   { font: 400 var(--ct-body-size)/1.6 var(--ct-font-body); color: var(--ct-body); }
  .ct-nums       { font-family: var(--ct-font-mono); font-size: 11.5px; letter-spacing:.2px;
                   color: var(--ct-faint); margin-top: 4px; font-variant-numeric: tabular-nums; }
  .ct-kv         { display:flex; flex-wrap:wrap; gap:6px 14px; align-items:baseline; }
  .ct-kv-k       { font: 500 var(--ct-body-size)/1.5 var(--ct-font-body); color: var(--ct-ink);
                   min-width: 232px; }
  .ct-total      { font: 600 20px/1.3 var(--ct-font-display); color: var(--ct-ink);
                   font-variant-numeric: tabular-nums; margin-top: var(--ct-s3); }
  .ct-stat       { padding: 18px 20px; }
  .ct-stat-num   { font: 700 31px/1 var(--ct-font-display); color: var(--ct-ink);
                   font-variant-numeric: tabular-nums; margin-top: 8px; }
  .ct-step-n     { font-family: var(--ct-font-mono); font-size: 9.5px; letter-spacing: 1.8px;
                   color: var(--ct-accent); }
  .ct-tbl        { width:100%; border-collapse: collapse; }
  .ct-tbl thead th {
      font-family: var(--ct-font-mono); font-size: 9.5px; letter-spacing: 1.8px;
      text-transform: uppercase; color: var(--ct-fainter); font-weight: 400;
      text-align: left; padding: 12px 18px; border-bottom: 1px solid var(--ct-border);
      white-space: nowrap; }
  .ct-tbl tbody td {
      padding: 16px 18px; vertical-align: top;
      border-bottom: 1px solid var(--ct-border-soft);
      font: 500 14px/1.55 var(--ct-font-body); color: var(--ct-ink); }
  .ct-tbl tbody tr:last-child td { border-bottom: none; }
  .ct-tbl tbody tr:hover td { background: var(--ct-surface-hover); }
  .ct-tbl .num   { font-family: var(--ct-font-mono); font-size: 12px; color: var(--ct-faint);
                   font-variant-numeric: tabular-nums; }
  .ct-tbl .sec   { font: 400 12.5px/1.5 var(--ct-font-body); color: var(--ct-muted);
                   white-space: nowrap; }
  .ct-flagrow    { display:flex; flex-wrap:wrap; gap:8px 12px; align-items:baseline;
                   padding: 10px 0; border-bottom:1px solid var(--ct-border-soft); }
  .ct-flagrow:last-of-type { border-bottom:none; }
  .ct-panel .ct-note { margin-top: var(--ct-s2); }
  .ct-panel .ct-note:first-of-type { margin-top: var(--ct-s4); }
</style>
""", unsafe_allow_html=True)


# ----- HELPERS -----
def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


CATEGORY_COLOURS = {
    "pre-commencement": "F4CCCC", "pre-occupation": "FCE5CD",
    "ongoing": "CFE2F3", "discharge-required": "D9D2E9", "time-limit": "FFF2CC",
}

CATEGORY_ORDER = ["time-limit", "pre-commencement", "discharge-required", "pre-occupation", "ongoing"]


def sort_by_category(conditions):
    return sorted(
        conditions,
        key=lambda c: CATEGORY_ORDER.index(c["category"]) if c["category"] in CATEGORY_ORDER else 99,
    )


def split_by_gate(conditions):
    """Group conditions into the four Safety Gate buckets.

    A condition flagged gate_ambiguous is never listed as startable, even if its
    gate says above-ground only — it belongs in the "check these" bucket instead.
    """
    blockers = [c for c in conditions if c.get("gate") in ("blocks-any-commencement", "blocks-demolition")]
    piling = [c for c in conditions if c.get("gate") == "blocks-piling"]
    ambiguous = [c for c in conditions if c.get("gate_ambiguous")]
    startable = [c for c in conditions
                 if c.get("gate") == "blocks-above-ground" and not c.get("gate_ambiguous")]
    return blockers, piling, ambiguous, startable


def compute_begin_by(decision_date, years):
    """Parse the decision date and add the time-limit years. Returns a date or None."""
    if not decision_date or not years:
        return None
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", str(decision_date).strip(), flags=re.IGNORECASE)
    d = None
    # Four-digit-year formats first: %y would happily match a two-digit fragment.
    for fmt in ("%d %B %Y", "%d %b %Y", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%Y-%m-%d",
                "%d %B %y", "%d %b %y", "%d.%m.%y", "%d/%m/%y", "%d-%m-%y"):
        try:
            d = datetime.strptime(s, fmt).date()
            break
        except ValueError:
            d = None
    if d is None:
        return None
    try:
        return d.replace(year=d.year + int(years))
    except ValueError:  # 29 Feb edge case
        return d.replace(month=2, day=28, year=d.year + int(years))


def fmt_date(d):
    return d.strftime("%d %B %Y").lstrip("0")


def cond_nums(conditions):
    """Comma-separated condition numbers, e.g. '#3, #4, #5'."""
    return ", ".join(f"#{c['condition_number']}" for c in sorted(
        conditions, key=lambda c: c["condition_number"]))


def n_conditions(n):
    return "1 condition" if n == 1 else f"{n} conditions"


def build_safety_gate_html(data):
    """A short summary panel: counts and condition numbers only.

    Deliberately does NOT repeat condition text — the table below carries the detail.
    """
    if doc_type(data) not in GATE_DOC_TYPES:
        return ""  # nothing to start: a refusal, or conditions already discharged

    conditions = data.get("conditions", [])
    begin_by = compute_begin_by(data.get("decision_date"), data.get("time_limit_years"))

    blockers, piling, ambiguous, startable = split_by_gate(conditions)

    if not (begin_by or blockers or piling or ambiguous or startable):
        return ""

    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', eyebrow("BEFORE YOU START ON SITE"), '</div>']

    if begin_by and begin_by < datetime.now().date():
        parts.append(banner(
            f"This start deadline has already passed — development had to begin by "
            f"{fmt_date(begin_by)}. Unless a material operation lawfully started on site before then, "
            f"this permission has expired and cannot be implemented.", "block"))
    elif begin_by:
        parts.append(
            f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">Development must begin by '
            f'<span class="ct-num" style="color:var(--ct-ink);font-weight:500">{fmt_date(begin_by)}</span> '
            f'or the permission lapses. <span style="color:var(--ct-faint)">(computed from the decision '
            f'date — confirm against the notice)</span></div>'
        )

    def line(pill_cls, text, conditions):
        return (f'<div class="ct-line">'
                f'<span class="ct-pill {pill_cls}">{text}</span>'
                f'<div class="ct-nums">{cond_nums(conditions)}</div></div>')

    if blockers:
        parts.append(line("ct-pill--block",
                          f"{n_conditions(len(blockers))} must be discharged before you can lawfully "
                          f"start on site", blockers))
    if startable:
        verb = "blocks" if len(startable) == 1 else "block"
        parts.append(line("ct-pill--cleared",
                          f"{len(startable)} more only {verb} above-ground works — you can begin "
                          f"demolition and groundworks first", startable))
    if piling:
        parts.append(line("ct-pill--check",
                          f"{n_conditions(len(piling))} to clear before any piling", piling))
    if ambiguous:
        verb = "needs" if len(ambiguous) == 1 else "need"
        parts.append(line("ct-pill--check",
                          f"{n_conditions(len(ambiguous))} {verb} checking — wording is ambiguous",
                          ambiguous))

    parts.append('<div class="ct-nums" style="margin-top:var(--ct-s3)">FULL DETAIL IN THE '
                 'CONDITIONS TABLE BELOW</div>')

    if doc_type(data) in CIL_DOC_TYPES:
        parts.append(note(
            "<b>CIL reminder:</b> before any material operation on site, check whether the development "
            "is CIL-liable and, if so, submit a CIL Commencement Notice to the council and get written "
            "acknowledgement first. Starting before this can mean losing CIL relief and incurring "
            "surcharges. This tool does not read CIL notices."))
    parts.append(note(
        "Automated flags, not legal advice — whether a condition is a true condition-precedent can be "
        "finely balanced. Confirm with your planning consultant or solicitor before starting on site."))
    parts.append("</div>")
    return "".join(parts)


# ----- DISCHARGE FEES -----
# England statutory fees, charged PER APPLICATION (request), not per condition. The fee line reads
# "Approval of details and/or confirmation that ONE OR MORE conditions have been complied with".
# Source: Planning Portal, Application Fees England, 1 April 2026 schedule.
FEE_OTHER = 309         # any other development, per request
FEE_HOUSEHOLDER = 89    # householder, per request
FEE_OTHER_LATER = 435
FEE_HOUSEHOLDER_LATER = 125
FEE_RISE_DATE = "8 December 2026"

# Per-nation fee scales. Wales: Planning Portal "Application Fees Wales – 1 December 2025"
# (£242 any other development, £123 householder; no further rise announced for 2026).
# Scotland and Northern Ireland run separate systems and are deliberately NOT priced here.
FEES = {
    "england": {"other": FEE_OTHER, "householder": FEE_HOUSEHOLDER,
                "later": (FEE_OTHER_LATER, FEE_HOUSEHOLDER_LATER), "later_date": FEE_RISE_DATE},
    "wales": {"other": 242, "householder": 123, "later": None, "later_date": None},
}
JURISDICTION_LABEL = {
    "england": "England", "wales": "Wales",
    "scotland": "Scotland", "northern-ireland": "Northern Ireland",
}

# Which documents impose conditions the applicant still has to discharge. A refusal grants nothing,
# and a discharge-approval notice records conditions that have ALREADY been cleared.
PLAN_DOC_TYPES = ("full-grant", "appeal-decision", "listed-building-consent")
# ...and of those, the ones where a fee is actually payable. Discharging conditions on a listed
# building consent is free: the fee line covers approvals "following grant of planning permission",
# and the schedule lists LBC conditions under concessions.
FEE_DOC_TYPES = ("full-grant", "appeal-decision")
# The Safety Gate only makes sense where something can lawfully be started.
GATE_DOC_TYPES = ("full-grant", "appeal-decision", "listed-building-consent")
# CIL is charged on development granted planning permission, not on listed building consent.
CIL_DOC_TYPES = ("full-grant", "appeal-decision")

# Stage batches. The LAST entry is the catch-all — it also absorbs any unrecognised gate value.
DISCHARGE_BATCHES = [
    ("Before you start (pre-commencement)",
     ("blocks-any-commencement", "blocks-demolition", "blocks-piling", "blocks-above-ground")),
    ("Before occupation", ("before-occupation", "before-use")),
    ("Other / any time", ("ongoing", "none")),
]


def doc_type(data):
    """Document type, defaulting to full-grant when the field is absent."""
    return data.get("document_type") or "full-grant"


def jurisdiction(data):
    """Which nation's fee scale applies.

    An absent key means a legacy extraction from before the field existed — assume England, which
    is what the tool did previously. An explicit null means the model could not tell, and we must
    NOT price it.
    """
    if "jurisdiction" not in data:
        return "england"
    return data.get("jurisdiction") or "unknown"


def build_discharge_plan(data):
    """Batch the discharge-required conditions by stage and price the applications.

    "applies" is False for documents that impose no outstanding obligations — a refusal, or a
    discharge-approval notice where the conditions listed have ALREADY been cleared.
    """
    dt = doc_type(data)
    conditions = [c for c in data.get("conditions", []) if c.get("discharge_required")]
    known = {g for _, gates in DISCHARGE_BATCHES for g in gates}

    batches = []
    for i, (label, gates) in enumerate(DISCHARGE_BATCHES):
        catch_all = i == len(DISCHARGE_BATCHES) - 1
        members = [c for c in conditions
                   if c.get("gate") in gates or (catch_all and c.get("gate") not in known)]
        if members:
            batches.append((label, members))

    householder = data.get("is_householder")
    juris = jurisdiction(data)
    scale = FEES.get(juris)              # None for Scotland, NI, or an unknown jurisdiction
    fee_payable = dt in FEE_DOC_TYPES

    fee = None
    if fee_payable and scale and householder is True:
        fee = scale["householder"]
    elif fee_payable and scale and householder is False:
        fee = scale["other"]

    return {
        "total": len(conditions),
        "batches": batches,
        "applications": len(batches),
        "applies": dt in PLAN_DOC_TYPES,
        "fee_payable": fee_payable,
        "jurisdiction": juris,
        "scale": scale,                  # None when we don't hold that nation's fees
        "fee": fee,                      # None when free, unpriced, or householder status unclear
        "householder": householder,
        "cost": len(batches) * fee if fee else None,
    }


def build_discharge_plan_html(data):
    plan = build_discharge_plan(data)
    if not plan["applies"] or not plan["total"]:
        return ""

    apps = plan["applications"]
    app_word = f'{apps} application{"" if apps == 1 else "s"}'
    scale = plan["scale"]
    juris_name = JURISDICTION_LABEL.get(plan["jurisdiction"])
    where = f" is from {juris_name}" if juris_name else "'s nation is unclear"

    if not plan["fee_payable"]:
        fee_lead = ('There is <b>no council fee</b> for discharging conditions on a listed building '
                    'consent, but you still have to apply. A sensible way to batch these is by stage:')
    elif scale is None:
        fee_lead = ('The fee is charged <b>per application</b>, not per condition, so bundle them. This '
                    'tool only holds the England and Wales fee scales, so it cannot price this one — '
                    'check the figure with the authority. A sensible way to batch these is by stage:')
    else:
        fee_lead = (f'The council fee is <b>£{plan["fee"] or scale["other"]} per application</b> — not per '
                    f'condition, so bundle them. A sensible way to batch these is by stage:')

    needs = "needs" if plan["total"] == 1 else "need"
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', eyebrow("DISCHARGE PLAN"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">You have '
             f'<b>{n_conditions(plan["total"])}</b> that {needs} formal discharge (submitted to '
             f'<b>and</b> approved by the council). {fee_lead}</div>']
    for label, members in plan["batches"]:
        parts.append(
            f'<div class="ct-line"><div class="ct-kv">'
            f'<span class="ct-kv-k">{label}</span>'
            f'<span class="ct-pill ct-pill--due">{n_conditions(len(members))}</span>'
            f'<span class="ct-num" style="font-size:11.5px;color:var(--ct-faint)">'
            f'{cond_nums(members)}</span></div></div>'
        )

    if not plan["fee_payable"]:
        parts.append(f'<div class="ct-total">\u2248 {app_word} to submit \u2014 no council fee.</div>')
        parts.append(note("Conditions on a listed building consent carry no application fee. "
                          "Conditions on a linked planning permission do."))
    elif scale is None:
        parts.append(f'<div class="ct-total">\u2248 {app_word} to submit.</div>')
        parts.append(note(
            f"No fee shown — this notice{where}, and this tool only holds the England and Wales fee "
            f"scales. The per-application principle still applies, so bundling still saves money."))
    elif plan["fee"] is not None:
        scheme = "householder" if plan["householder"] else "non-householder"
        rise = ""
        if scale["later"]:
            rise = (f' Fees rise to £{scale["later"][0]} (£{scale["later"][1]} householder) on '
                    f'{scale["later_date"]}.')
        parts.append(f'<div class="ct-total">\u2248 {app_word} \u00d7 £{plan["fee"]} = '
                     f'~£{plan["cost"]:,} in council fees.</div>')
        parts.append(note(f"Priced at the <b>{scheme}</b> rate for {juris_name}.{rise}"))
    else:
        rise = ""
        if scale["later"]:
            rise = f' Fees rise to £{scale["later"][0]} / £{scale["later"][1]} on {scale["later_date"]}.'
        parts.append(f'<div class="ct-total">\u2248 {app_word} \u2014 about '
                     f'£{apps * scale["other"]:,} at the standard rate, or '
                     f'£{apps * scale["householder"]:,} if this is a householder scheme.</div>')
        parts.append(note(
            f"We couldn't tell which fee category this scheme falls into, so both {juris_name} rates "
            f"are shown (£{scale['other']} vs £{scale['householder']} per application).{rise}"))

    parts.append(note(
        "<b>Deemed discharge:</b> the council has 8 weeks to decide. If it misses that — and the "
        "condition isn't one of the excluded types — you may be able to proceed as if the condition "
        "were discharged. A useful lever if they go quiet."))
    parts.append(note(
        "Batching is guidance, not a rule — you can combine or split further, and timing depends on "
        "your programme. Fees are the statutory rate and change over time; confirm the current figure "
        "before relying on it. Not legal or planning advice — confirm with your planning consultant."))
    parts.append("</div>")
    return "".join(parts)


def specialists_for(condition):
    """Disciplines needed for one condition.

    The field is an array — a condition can genuinely need two disciplines at once. Older
    extractions stored a single string or null, so both are still accepted.
    """
    raw = condition.get("specialist_needed")
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    return [s.strip() for s in raw if isinstance(s, str) and s.strip()]


FLAG_LABEL = {
    "typo": "typo", "duplicate": "duplicate", "missing-drawing": "missing drawing",
    "internal-conflict": "conflict", "other": "check",
}


def get_flags(data):
    """Consistency flags raised against the notice itself. Always a list."""
    flags = data.get("flags")
    return [f for f in flags if isinstance(f, dict) and f.get("detail")] if isinstance(flags, list) else []


def build_flags_html(data):
    flags = get_flags(data)
    if not flags:
        return ""   # a clean notice shows nothing at all

    n = len(flags)
    n = len(flags)
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', eyebrow("THINGS TO CHECK IN THE NOTICE"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s2)">{n} possible '
             f'{"error" if n == 1 else "errors"} in the council\'s own document — worth querying '
             f'before you rely on the wording.</div>']
    for f in flags:
        label = FLAG_LABEL.get(f.get("type"), "check").upper()
        cond = f.get("condition")
        cond_html = (f'<span class="ct-num" style="font-size:11.5px;color:var(--ct-faint)">'
                     f'#{cond}</span>') if cond is not None else ""
        parts.append(f'<div class="ct-flagrow">{tag(label)}{cond_html}'
                     f'<span class="ct-line-txt" style="flex:1;min-width:240px">{f["detail"]}</span>'
                     f'</div>')
    parts.append(note("Automated flags — the tool may miss some issues or occasionally over-flag. "
                      "Always read against the source notice."))
    parts.append("</div>")
    return "".join(parts)


def build_specialists(data):
    """Map each external discipline to the conditions that need it.

    Ordered by how many conditions they cover, so the biggest commissions read first. A condition
    needing two disciplines is listed under both, so the counts sum to more than the number of
    conditions — that is correct, they are separate commissions.
    """
    if doc_type(data) not in PLAN_DOC_TYPES:
        return []
    grouped = {}
    for c in sorted(data.get("conditions", []), key=lambda x: x["condition_number"]):
        for name in specialists_for(c):
            grouped.setdefault(name, []).append(c["condition_number"])
    return sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def build_specialists_html(data):
    specialists = build_specialists(data)
    if not specialists:
        return ""

    n = len(specialists)
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', eyebrow("SPECIALISTS TO COMMISSION"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">You will likely need to '
             f'bring in <b>{n} external specialist{"" if n == 1 else "s"}</b> for this scheme. The '
             f'notice never says so — each discipline below is implied by what its conditions '
             f'actually ask you to produce.</div>']
    for name, nums in specialists:
        joined = ", ".join(f"#{x}" for x in nums)
        parts.append(
            f'<div class="ct-line"><div class="ct-kv">'
            f'<span class="ct-kv-k">{name}</span>'
            f'<span class="ct-pill ct-pill--due">{n_conditions(len(nums))}</span>'
            f'<span class="ct-num" style="font-size:11.5px;color:var(--ct-faint)">{joined}</span>'
            f'</div></div>'
        )
    parts.append(note(
        "A guide to resourcing, not a definitive list — some conditions can be handled in-house, and "
        "one consultant often covers several disciplines. Confirm with your team. Not legal or "
        "planning advice."))
    parts.append("</div>")
    return "".join(parts)


def build_excel(data):
    wb = openpyxl.Workbook()

    # ----- Sheet 1: Conditions -----
    ws = wb.active
    ws.title = "Conditions"
    ws.append(["#", "Summary", "Category", "Deadline", "Responsible", "Discharge required?"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for c in sort_by_category(data["conditions"]):
        ws.append([c["condition_number"], c["summary"], c["category"],
                   c["deadline"], c["responsible_party"],
                   "Yes" if c["discharge_required"] else "No"])
        ws.cell(row=ws.max_row, column=3).fill = PatternFill(
            "solid", fgColor=CATEGORY_COLOURS.get(c["category"], "FFFFFF"))
    for col, w in {"A": 5, "B": 55, "C": 18, "D": 16, "E": 14, "F": 18}.items():
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"

    # ----- Things to check (only when the notice actually has problems) -----
    flags = get_flags(data)
    if flags:
        wsf = wb.create_sheet("Things to check")
        wsf.append(["Type", "Condition", "Detail"])
        for cell in wsf[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="8A6D20")
        for f in flags:
            cond = f.get("condition")
            wsf.append([FLAG_LABEL.get(f.get("type"), "check"),
                        f"#{cond}" if cond is not None else "—", f["detail"]])
        for col, w in {"A": 17, "B": 11, "C": 78}.items():
            wsf.column_dimensions[col].width = w
        for row in wsf.iter_rows(min_row=2):
            row[2].alignment = Alignment(wrap_text=True, vertical="top")
        wsf.freeze_panes = "A2"
        wsf.append([])
        wsf.append(["Automated flags — the tool may miss some issues or occasionally over-flag. "
                    "Always read against the source notice."])

    # ----- Sheet 2: Before you start -----
    # Only for documents that actually permit works to start.
    if doc_type(data) not in GATE_DOC_TYPES:
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    ws2 = wb.create_sheet("Before you start")
    conditions = data.get("conditions", [])
    begin_by = compute_begin_by(data.get("decision_date"), data.get("time_limit_years"))
    blockers, piling, ambiguous, startable = split_by_gate(conditions)

    def head(text, fill="1F4E78"):
        ws2.append([text])
        cell = ws2.cell(row=ws2.max_row, column=1)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=fill)

    def line(text, bold=False, colour=None):
        ws2.append([text])
        ws2.cell(row=ws2.max_row, column=1).font = Font(bold=bold, color=colour)

    head("BEFORE YOU START ON SITE")
    line("")
    if begin_by and begin_by < datetime.now().date():
        line(f"THIS START DEADLINE HAS ALREADY PASSED — development had to begin by {fmt_date(begin_by)}. "
             f"Unless a material operation lawfully started on site before then, this permission has "
             f"expired and cannot be implemented. (computed from the decision date — confirm against "
             f"the notice)", bold=True, colour="C0392B")
    elif begin_by:
        line(f"Development must begin by:  {fmt_date(begin_by)}   (computed from the decision date — confirm against the notice)", bold=True)
    else:
        line("Development must begin by:  not stated on this notice")
    line("")

    # Summary lines only — counts and condition numbers. Detail lives on the Conditions tab.
    if blockers:
        line(f"{n_conditions(len(blockers))} must be discharged before you can lawfully start on site:   "
             f"{cond_nums(blockers)}", bold=True, colour="C0392B")
    if startable:
        verb = "blocks" if len(startable) == 1 else "block"
        line(f"{len(startable)} more only {verb} above-ground works — you can begin demolition and "
             f"groundworks first:   {cond_nums(startable)}", colour="17663A")
    if piling:
        line(f"{n_conditions(len(piling))} to clear before any piling:   {cond_nums(piling)}", colour="B9770E")
    if ambiguous:
        verb = "needs" if len(ambiguous) == 1 else "need"
        line(f"{n_conditions(len(ambiguous))} {verb} checking — wording is ambiguous:   "
             f"{cond_nums(ambiguous)}", colour="B9770E")
    line("")
    line("Full detail is on the Conditions tab.")
    line("")

    line("CIL reminder: before any material operation on site, check whether the development is CIL-liable and, "
         "if so, submit a CIL Commencement Notice to the council and get written acknowledgement first. Starting "
         "before this can mean losing CIL relief and incurring surcharges. This tool does not read CIL notices.")
    line("")
    line("Automated flags, not legal advice — whether a condition is a true condition-precedent can be finely "
         "balanced. Confirm with your planning consultant or solicitor before starting on site.")
    ws2.column_dimensions["A"].width = 110
    for row in ws2.iter_rows(min_row=1):
        row[0].alignment = Alignment(wrap_text=True, vertical="top")

    # ----- Sheet 3: Discharge plan -----
    plan = build_discharge_plan(data)
    if not plan["applies"]:
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    ws3 = wb.create_sheet("Discharge plan")

    def head3(text, fill="1F4E78"):
        ws3.append([text])
        cell = ws3.cell(row=ws3.max_row, column=1)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=fill)

    def line3(text, bold=False, colour=None):
        ws3.append([text])
        ws3.cell(row=ws3.max_row, column=1).font = Font(bold=bold, color=colour)

    head3("DISCHARGE PLAN")
    line3("")
    if not plan["total"]:
        line3("No conditions on this notice require formal discharge by the council.")
    else:
        apps = plan["applications"]
        app_word = f"{apps} application{'' if apps == 1 else 's'}"
        line3(f"{n_conditions(plan['total'])} {'needs' if plan['total'] == 1 else 'need'} formal discharge "
              f"(submitted to AND approved by the council).")
        line3("")
        scale = plan["scale"]
        juris_name = JURISDICTION_LABEL.get(plan["jurisdiction"])
        if not plan["fee_payable"]:
            line3("There is no council fee for discharging conditions on a listed building consent, "
                  "but you still have to apply.", bold=True)
        elif scale is None:
            line3("The fee is charged per application, not per condition — so bundle them. This tool "
                  "only holds the England and Wales fee scales, so it cannot price this notice; check "
                  "the figure with the authority.", bold=True)
        else:
            line3(f"The council fee is £{plan['fee'] or scale['other']} per application — not per "
                  f"condition. So bundle them.", bold=True)
        line3("A sensible way to batch these is by stage:")
        line3("")
        for label, members in plan["batches"]:
            line3(f"   {label}:   {n_conditions(len(members))} — {cond_nums(members)}")
        line3("")
        rise = ""
        if scale and scale["later"]:
            rise = (f" Fees rise to £{scale['later'][0]} / £{scale['later'][1]} on "
                    f"{scale['later_date']}.")
        if not plan["fee_payable"]:
            line3(f"≈ {app_word} to submit — no council fee.", bold=True, colour="17663A")
            line3("Conditions on a listed building consent carry no application fee. Conditions on a "
                  "linked planning permission do.")
        elif scale is None:
            line3(f"≈ {app_word} to submit.", bold=True, colour="1F4E78")
            line3(f"(No fee shown — this notice is from {juris_name or 'an unclear jurisdiction'}, and "
                  f"this tool holds the England and Wales scales only. The per-application principle "
                  f"still applies, so bundling still saves money.)")
        elif plan["fee"] is not None:
            scheme = "householder" if plan["householder"] else "non-householder"
            line3(f"≈ {app_word} × £{plan['fee']} = ~£{plan['cost']:,} in council fees.",
                  bold=True, colour="1F4E78")
            line3(f"(Priced at the {scheme} rate for {juris_name}.{rise})")
        else:
            line3(f"≈ {app_word} — about £{apps * scale['other']:,} at the standard rate, or "
                  f"£{apps * scale['householder']:,} if this is a householder scheme.",
                  bold=True, colour="1F4E78")
            line3(f"(Fee category unclear from this notice, so both {juris_name} rates are shown: "
                  f"£{scale['other']} vs £{scale['householder']} per application.{rise})")
        line3("")
        line3("Deemed discharge: the council has 8 weeks to decide. If it misses that — and the condition "
              "isn't one of the excluded types — you may be able to proceed as if the condition were "
              "discharged. A useful lever if they go quiet.", colour="17663A")
    line3("")
    line3("Batching is guidance, not a rule — you can combine or split further, and timing depends on your "
          "programme. Fees are the England statutory rate and change over time; confirm the current figure "
          "before relying on it. Not legal or planning advice — confirm with your planning consultant.")
    ws3.column_dimensions["A"].width = 110
    for row in ws3.iter_rows(min_row=1):
        row[0].alignment = Alignment(wrap_text=True, vertical="top")

    # ----- Sheet 4: Specialists -----
    specialists = build_specialists(data)
    if specialists:
        ws4 = wb.create_sheet("Specialists")
        ws4.append(["Specialist", "Conditions", "Count"])
        for cell in ws4[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="4B3B7A")
        for name, nums in specialists:
            ws4.append([name, ", ".join(f"#{x}" for x in nums), len(nums)])
        for col, w in {"A": 42, "B": 46, "C": 8}.items():
            ws4.column_dimensions[col].width = w
        for row in ws4.iter_rows(min_row=2):
            row[1].alignment = Alignment(wrap_text=True, vertical="top")
        ws4.freeze_panes = "A2"
        ws4.append([])
        ws4.append(["A guide to resourcing, not a definitive list — some conditions can be handled "
                    "in-house, and one consultant often covers several disciplines. Confirm with your "
                    "team. Not legal or planning advice."])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# Category -> safety-gate severity. Colour in this theme only ever means severity, so the old
# decorative per-category palette is gone.
CATEGORY_PILL = {
    "pre-commencement": "ct-pill--block",
    "discharge-required": "ct-pill--check",
    "pre-occupation": "ct-pill--due",
    "time-limit": "ct-pill--due",
    "ongoing": "ct-pill--ongoing",
}


def category_pill(cat):
    return f'<span class="ct-pill {CATEGORY_PILL.get(cat, "ct-pill--due")}">{cat}</span>'


# ----- HERO -----
st.markdown(
    f'{eyebrow("AI PLANNING CONDITION TRACKER")}'
    f'<h1 class="ct-h1" style="margin:10px 0 12px">Planning conditions, tracked in seconds.</h1>'
    f'<p class="ct-body" style="max-width:640px;margin:0">A second pair of eyes on your planning '
    f'conditions. Upload a UK decision notice and get every condition read, categorised and exported '
    f'as a structured tracker spreadsheet — in seconds.</p>',
    unsafe_allow_html=True,
)

# ----- HOW IT WORKS -----
st.markdown(f'<div style="margin:var(--ct-s6) 0 var(--ct-s3)">{eyebrow("HOW IT WORKS")}</div>',
            unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col, num, title, text in [
    (c1, "01", "Upload", "Drop in a decision notice PDF"),
    (c2, "02", "Analyse", "AI reads &amp; categorises every condition"),
    (c3, "03", "Export", "Download your structured tracker"),
]:
    col.markdown(
        f'<div class="ct-card ct-stat" style="height:100%">'
        f'<div class="ct-step-n">{num}</div>'
        f'<div class="ct-h3" style="margin:10px 0 4px">{title}</div>'
        f'<div class="ct-muted">{text}</div></div>',
        unsafe_allow_html=True,
    )

# ----- UPLOAD -----
st.markdown(f'<div style="margin:var(--ct-s6) 0 var(--ct-s3)">{eyebrow("UPLOAD A DECISION NOTICE")}</div>',
            unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose a PDF", type="pdf", label_visibility="collapsed")

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()

        # Anthropic request limit is ~32MB; base64 inflates ~33%, so cap the raw file
        if len(file_bytes) > 24_000_000:
            st.error("This PDF is too large to process (over ~24MB). "
                     "Try a smaller file, or split it into sections.")
            st.stop()

        with st.spinner("Reading the decision notice — usually 15–30 seconds..."):
            # 1. try fast digital text extraction
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pdf_text = ""
                for page in pdf.pages:
                    pdf_text += page.extract_text() or ""

            if len(pdf_text.strip()) >= 100:
                # digital PDF — send the extracted text (fast, cheap)
                user_content = pdf_text
            else:
                # scanned / image PDF — send the PDF itself so Claude reads it with vision
                pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
                user_content = [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": "Analyse this planning decision notice."},
                ]

            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=8000,
                # Extraction and classification, not creative writing: always take the most likely
                # reading so the same notice gives the same answer twice.
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )

            try:
                data = json.loads(strip_fences(message.content[0].text))
            except json.JSONDecodeError:
                st.error("Couldn't read the AI's response for this document. "
                         "It may be an unusual format — try another decision notice.")
                st.stop()

        conditions = data["conditions"]
        decision = data["decision"].upper()

        if len(conditions) == 0:
            st.info(f"**{decision}** — no planning conditions found. This may be a refusal or a document without conditions.")
        else:
            total = len(conditions)
            discharge = sum(1 for c in conditions if c["discharge_required"])
            precom = sum(1 for c in conditions if c["category"] == "pre-commencement")

            st.markdown(banner(f"{decision} — {total} planning conditions extracted from this "
                               f"notice", "ok"), unsafe_allow_html=True)
            st.markdown('<div style="height:var(--ct-s4)"></div>', unsafe_allow_html=True)

            s1, s2, s3 = st.columns(3)
            for col, value, label in [
                (s1, total, "TOTAL CONDITIONS"),
                (s2, precom, "PRE-COMMENCEMENT"),
                (s3, discharge, "NEED DISCHARGE"),
            ]:
                col.markdown(
                    f'<div class="ct-card ct-stat">{eyebrow(label)}'
                    f'<div class="ct-stat-num">{value}</div></div>',
                    unsafe_allow_html=True,
                )

            st.write("")

            # ----- SAFETY GATE: "Before you start on site" -----
            gate_html = build_safety_gate_html(data)
            if gate_html:
                st.markdown(gate_html, unsafe_allow_html=True)

            # ----- THINGS TO CHECK IN THE NOTICE -----
            flags_html = build_flags_html(data)
            if flags_html:
                st.markdown(flags_html, unsafe_allow_html=True)

            st.markdown(f'<div style="margin:var(--ct-s5) 0 var(--ct-s3)">'
                        f'{eyebrow("EXTRACTED CONDITIONS")}</div>', unsafe_allow_html=True)

            rows_html = ""
            for c in sort_by_category(conditions):
                deadline = c["deadline"] or "—"
                disc = ('<span class="ct-num" style="color:var(--ct-ink)">YES</span>'
                        if c["discharge_required"]
                        else '<span class="ct-num" style="color:var(--ct-fainter)">—</span>')
                rows_html += (
                    f'<tr>'
                    f'<td class="num">{c["condition_number"]}</td>'
                    f'<td>{c["summary"]}</td>'
                    f'<td>{category_pill(c["category"])}</td>'
                    f'<td class="sec">{deadline}</td>'
                    f'<td class="sec" style="text-align:center">{disc}</td>'
                    f'</tr>'
                )
            table_html = (
                '<div class="ct-card" style="overflow:hidden"><table class="ct-tbl">'
                '<thead><tr>'
                '<th style="width:56px">#</th><th>Summary</th>'
                '<th style="width:180px">Category</th><th style="width:130px">Deadline</th>'
                '<th style="width:110px;text-align:center">Discharge</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table></div>'
            )
            st.markdown(table_html, unsafe_allow_html=True)

            # ----- DISCHARGE PLAN -----
            plan_html = build_discharge_plan_html(data)
            if plan_html:
                st.markdown('<div style="height:var(--ct-s5)"></div>', unsafe_allow_html=True)
                st.markdown(plan_html, unsafe_allow_html=True)

            # ----- SPECIALISTS TO COMMISSION -----
            spec_html = build_specialists_html(data)
            if spec_html:
                st.markdown(spec_html, unsafe_allow_html=True)

            st.write("")

            excel_bytes = build_excel(data)
            st.download_button("Download Excel tracker  ↓", excel_bytes,
                               file_name="planning_condition_tracker.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               type="primary")

    # Order matters: AuthenticationError and RateLimitError are subclasses of APIStatusError.
    except anthropic.AuthenticationError:
        st.error("This app can't reach the AI service — its API key is missing or invalid. "
                 "That's a problem with the app, not with your file.")
    except anthropic.RateLimitError:
        st.error("The AI service is busy at the moment. Please wait a few seconds and try again — "
                 "there's nothing wrong with your file.")
    except anthropic.APIStatusError as exc:
        detail = str(getattr(exc, "message", "") or exc).lower()
        if "credit balance" in detail or "billing" in detail or "quota" in detail:
            st.error("This app has run out of API credit, so it can't analyse notices right now. "
                     "That's a problem with the app, not with your file.")
        else:
            st.error("The AI service returned an error, so this notice couldn't be analysed. "
                     "That's a problem with the service, not with your file — please try again shortly.")
    except anthropic.APIConnectionError:
        st.error("Couldn't reach the AI service — it may be a network problem. "
                 "Please try again in a moment.")
    except Exception:
        st.error("Something went wrong processing this file. Please check it's a valid "
                 "UK planning decision notice PDF and try again.")

# ----- FOOTER -----
st.markdown(
    f'<hr style="margin:var(--ct-s6) 0 var(--ct-s4)">'
    f'{note("Built by Zak Akhtar · <a href=\'https://github.com/akhtarzakariya8-a11y/planning-condition-tracker\'>GitHub</a>")}'
    f'{note("A tool for UK planning decision notices. Always check outputs against the source document.")}',
    unsafe_allow_html=True,
)
