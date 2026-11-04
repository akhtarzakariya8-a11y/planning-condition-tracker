"""The rules. Pure Python — no Streamlit, no API calls — so every rule here can be tested.

The model reads the notice (ct.extract); this module decides what the reading MEANS: what
blocks a start, when the permission lapses, how many discharge applications to make and what
they cost, what to check in the council's own wording, and who to hire.
"""
import difflib
import itertools
import re
from datetime import date, datetime

from ct.extract import FROM_SCAN_KEY

# ----- CATEGORIES -----
CATEGORY_COLOURS = {
    "pre-commencement": "F4CCCC", "pre-occupation": "FCE5CD",
    "ongoing": "CFE2F3", "discharge-required": "D9D2E9", "time-limit": "FFF2CC",
}
CATEGORY_ORDER = ["time-limit", "pre-commencement", "discharge-required", "pre-occupation", "ongoing"]


def sort_by_category(conditions):
    return sorted(
        conditions,
        key=lambda c: (CATEGORY_ORDER.index(c["category"]) if c.get("category") in CATEGORY_ORDER
                       else 99, c.get("condition_number", 0)),
    )


def from_scan(data):
    """True when the notice had no text layer and was read by vision instead."""
    return bool(data.get(FROM_SCAN_KEY))


def n_conditions(n):
    return "1 condition" if n == 1 else f"{n} conditions"


def cond_nums(conditions):
    """Comma-separated condition numbers, e.g. '#3, #4, #5'."""
    return ", ".join(f"#{c['condition_number']}" for c in sorted(
        conditions, key=lambda c: c["condition_number"]))


# ----- DOCUMENT TYPES -----
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

DOC_TYPE_LABEL = {
    "full-grant": "Planning permission", "listed-building-consent": "Listed building consent",
    "discharge-approval": "Discharge of conditions decision", "refusal": "Refusal",
    "appeal-decision": "Appeal decision", "other": "Other document",
}
PERMISSION_TYPE_LABEL = {
    "full": "Full permission", "outline": "Outline permission",
    "reserved-matters": "Reserved matters approval", "variation": "Section 73 variation",
}


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


JURISDICTION_LABEL = {
    "england": "England", "wales": "Wales",
    "scotland": "Scotland", "northern-ireland": "Northern Ireland",
}


def notice_title(data, fallback="This notice"):
    """A short human name for a notice: its reference and site, whatever is known."""
    ref = (data.get("application_reference") or "").strip()
    site = (data.get("site_address") or "").strip()
    if ref and site:
        return f"{ref} — {site}"
    return ref or site or fallback


# ----- GATES (the Safety Gate buckets) -----
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


# ----- DATES -----
_MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december")
_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%Y-%m-%d",
                 "%d %B %y", "%d %b %y", "%d.%m.%y", "%d/%m/%y", "%d-%m-%y")


def parse_date(text):
    """Read a date as councils write them ('10th November 2025', '10.11.2025'...). None if not."""
    if not text:
        return None
    if isinstance(text, date):
        return text
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", str(text).strip(), flags=re.IGNORECASE)
    # Four-digit-year formats first: %y would happily match a two-digit fragment.
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def add_years(d, years):
    try:
        return d.replace(year=d.year + int(years))
    except ValueError:  # 29 Feb edge case
        return d.replace(month=2, day=28, year=d.year + int(years))


def compute_begin_by(decision_date, years):
    """Parse the decision date and add the time-limit years. Returns a date or None."""
    d = parse_date(decision_date)
    if d is None or not years:
        return None
    return add_years(d, years)


def fmt_date(d):
    return d.strftime("%d %B %Y").lstrip("0") if d else "—"


_EXPLICIT_DATE = re.compile(
    rf"\b(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})\s+\d{{4}}|\d{{1,2}}[./]\d{{1,2}}[./]\d{{4}})\b",
    re.IGNORECASE)


def time_limit_condition(data):
    for c in data.get("conditions", []):
        if c.get("category") == "time-limit" or (
                c.get("gate") == "none" and "begun" in (c.get("source_quote") or "").lower()):
            return c
    return None


def start_deadline(data):
    """When must development begin? Returns {"date", "basis", "condition"}.

    basis is one of:
      "stated"    the time-limit condition gives a calendar date — used as written
      "computed"  decision date + the time-limit years (the normal full-permission case)
      "outline"   runs from approval of the last reserved matters: not knowable from this notice
      "variation" a s73 permission: runs from the ORIGINAL permission, not this decision
      None        no time limit on this notice

    Getting this wrong is the most expensive mistake the tool can make — a developer who thinks
    they have until 2029 when the permission actually lapses in 2027 loses the permission — so
    anything not computable is reported as not computable rather than guessed.
    """
    tl = time_limit_condition(data)
    num = tl["condition_number"] if tl else None
    quote = (tl or {}).get("source_quote") or ""
    ptype = data.get("permission_type")

    if ptype == "outline" or "reserved matters" in quote.lower():
        return {"date": None, "basis": "outline", "condition": num}

    m = _EXPLICIT_DATE.search(quote)
    if m:
        stated = parse_date(m.group(1))
        if stated:
            return {"date": stated, "basis": "stated", "condition": num}

    if ptype == "variation":
        return {"date": None, "basis": "variation", "condition": num}

    d = compute_begin_by(data.get("decision_date"), data.get("time_limit_years"))
    return {"date": d, "basis": "computed" if d else None, "condition": num}


# ----- DISCHARGE FEES -----
# Statutory fees, charged PER APPLICATION (request), not per condition. The fee line reads
# "Approval of details and/or confirmation that ONE OR MORE conditions have been complied with".
#
# England: £309 / £89 from 1 April 2026 (Planning Portal, Application Fees England). The draft
#   Fees (Amendment and Transitional Provision) Regulations 2026 raise them to £435 / £125 for
#   applications made on or after 8 December 2026 — approved by the Commons on 27 Oct 2026
#   (Planning Portal "Forthcoming Fees for Planning Applications in England"). Each entry below
#   switches on automatically on its date, so the page never shows a stale fee or a "rise" that
#   has already happened.
# Wales: Planning Portal "Application Fees Wales – 1 December 2025" (£242 other, £123 householder).
# Scotland and Northern Ireland run separate systems and are deliberately NOT priced here.
FEE_SCHEDULE = {
    "england": [
        (date(2026, 4, 1), {"other": 309, "householder": 89}),
        (date(2026, 12, 8), {"other": 435, "householder": 125}),
    ],
    "wales": [
        (date(2025, 12, 1), {"other": 242, "householder": 123}),
    ],
}


def fee_scale(juris, on=None):
    """The fee scale in force on a date (default today), or None if we don't price that nation."""
    on = on or date.today()
    rows = [r for r in FEE_SCHEDULE.get(juris, []) if r[0] <= on]
    if not rows:
        rows = FEE_SCHEDULE.get(juris, [])[:1]
    return dict(rows[-1][1], effective=rows[-1][0]) if rows else None


def next_fee_rise(juris, on=None):
    """(date, scale) of the next scheduled change after `on`, or None."""
    on = on or date.today()
    later = [r for r in FEE_SCHEDULE.get(juris, []) if r[0] > on]
    return (later[0][0], later[0][1]) if later else None


def fee_for(data, on=None):
    """Fee per discharge application for this notice on a date. None if free/unpriced/unclear."""
    if doc_type(data) not in FEE_DOC_TYPES:
        return None
    scale = fee_scale(jurisdiction(data), on)
    householder = data.get("is_householder")
    if not scale or householder is None:
        return None
    return scale["householder"] if householder else scale["other"]


# Stage batches. The LAST entry is the catch-all — it also absorbs any unrecognised gate value.
DISCHARGE_BATCHES = [
    ("Before you start (pre-commencement)",
     ("blocks-any-commencement", "blocks-demolition", "blocks-piling", "blocks-above-ground")),
    ("Before occupation", ("before-occupation", "before-use")),
    ("Other / any time", ("ongoing", "none")),
]


def build_discharge_plan(data, on=None):
    """Batch the discharge-required conditions by stage and price the applications.

    "applies" is False for documents that impose no outstanding obligations — a refusal, or a
    discharge-approval notice where the conditions listed have ALREADY been cleared.
    """
    dt = doc_type(data)
    conditions = [c for c in data.get("conditions", []) if c.get("discharge_required")]
    known = {g for _, gates in DISCHARGE_BATCHES for g in gates}

    batches = []
    for i, (stage, gates) in enumerate(DISCHARGE_BATCHES):
        catch_all = i == len(DISCHARGE_BATCHES) - 1
        members = [c for c in conditions
                   if c.get("gate") in gates or (catch_all and c.get("gate") not in known)]
        if members:
            batches.append((stage, members))

    householder = data.get("is_householder")
    juris = jurisdiction(data)
    scale = fee_scale(juris, on)           # None for Scotland, NI, or an unknown jurisdiction
    fee_payable = dt in FEE_DOC_TYPES
    fee = fee_for(data, on) if fee_payable else None
    rise = next_fee_rise(juris, on) if fee_payable else None

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
        "next_rise": rise,               # (date, scale) or None
        # Deemed discharge (s74A TCPA 1990 / DMPO 2015) exists in England only.
        "deemed_discharge": juris == "england" and fee_payable,
    }


# ----- SPECIALISTS -----
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


# ----- CONSISTENCY FLAGS -----
FLAG_LABEL = {
    "typo": "typo", "duplicate": "duplicate", "missing-drawing": "missing drawing",
    "internal-conflict": "conflict", "other": "check",
}

# Two conditions are duplicates when their verbatim wording is this similar. On the Lambeth
# notice the real duplicate pair scores 0.944 and the next-closest pair 0.786, so the gap is
# wide; the tree conditions that the model kept mislabelling score 0.464.
DUPLICATE_SIMILARITY = 0.90
DUPLICATE_MIN_CHARS = 60


def _norm_quote(text):
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", (text or "").lower())).strip()


def detect_duplicates(conditions):
    """Find conditions whose operative wording is near-identical.

    Computed here rather than asked of the model. "Are these two conditions the same" is a
    comparison, and the model kept rationalising related-but-different conditions into duplicates
    — flagging three distinct tree conditions as one repeated. Comparison is what code is good at:
    this is deterministic, explainable, and cannot drift between runs.
    """
    quoted = [(c["condition_number"], _norm_quote(c.get("source_quote")))
              for c in conditions if (c.get("source_quote") or "").strip()]
    found = []
    for (a, qa), (b, qb) in itertools.combinations(quoted, 2):
        # very short clauses match each other by coincidence
        if len(qa) < DUPLICATE_MIN_CHARS or len(qb) < DUPLICATE_MIN_CHARS:
            continue
        ratio = difflib.SequenceMatcher(None, qa, qb).ratio()
        if ratio >= DUPLICATE_SIMILARITY:
            found.append({
                "type": "duplicate",
                "condition": a,
                "detail": (f"Conditions {a} and {b} are near-identical — their operative wording is "
                           f"{round(ratio * 100)}% the same. They can usually be discharged in one "
                           f"submission."),
            })
    return found


def get_flags(data):
    """Consistency flags raised against the notice itself. Always a list.

    The model reports typos, missing drawings and internal conflicts; duplicates are computed
    from the verbatim quotes instead.
    """
    flags = data.get("flags")
    model_flags = ([f for f in flags if isinstance(f, dict) and f.get("detail")]
                   if isinstance(flags, list) else [])
    model_flags = [f for f in model_flags if f.get("type") != "duplicate"]
    return model_flags + detect_duplicates(data.get("conditions", []))


# ----- ONE-LINE SUMMARY (portfolio rows, saved projects) -----
def summarise(data, on=None):
    """The handful of numbers a portfolio row or a saved-project card shows."""
    conditions = data.get("conditions", [])
    blockers, piling, ambiguous, startable = split_by_gate(conditions)
    sd = start_deadline(data)
    plan = build_discharge_plan(data, on)
    return {
        "title": notice_title(data),
        "council": data.get("local_authority"),
        "document": DOC_TYPE_LABEL.get(doc_type(data), doc_type(data)),
        "decision": (data.get("decision") or "").capitalize(),
        "decision_date": data.get("decision_date"),
        "begin_by": sd["date"],
        "begin_by_basis": sd["basis"],
        "conditions": len(conditions),
        "blockers": len(blockers),
        "discharge": plan["total"],
        "applications": plan["applications"] if plan["applies"] else 0,
        "fees": plan["cost"],
        "flags": len(get_flags(data)),
    }


# ----- HUMAN LABELS -----
GATE_LABEL = {
    "blocks-any-commencement": "Before any works", "blocks-demolition": "Before demolition",
    "blocks-piling": "Before piling", "blocks-above-ground": "Before above-ground works",
    "before-occupation": "Before occupation", "before-use": "Before use",
    "ongoing": "Ongoing", "none": "—",
}


def gate_label(condition):
    return GATE_LABEL.get(condition.get("gate"), condition.get("gate") or "—")


def start_deadline_message(data, today=None):
    """What to say about the start deadline, everywhere it is said (page, Excel, PDF).

    Returns {"kind", "date", "text", "html"}; kind is "ok", "expired", "unknown" or None.
    """
    today = today or date.today()
    sd = start_deadline(data)
    ref = f" (see condition #{sd['condition']})" if sd["condition"] else ""
    if sd["basis"] == "outline":
        text = ("This is an outline permission, or its time limit runs from reserved matters, so "
                "the start deadline runs from approval of the LAST reserved matters. It can't be "
                f"worked out from this notice alone{ref}.")
        return {"kind": "unknown", "date": None, "text": text, "html": text}
    if sd["basis"] == "variation":
        text = ("This permission varies an earlier one (section 73). Its start deadline normally "
                "runs from the ORIGINAL permission's date, not from this decision — check the "
                f"original permission{ref}.")
        return {"kind": "unknown", "date": None, "text": text, "html": text}
    d = sd["date"]
    if not d:
        return {"kind": None, "date": None, "text": "Development must begin by: not stated on this notice",
                "html": ""}
    if d < today:
        text = (f"THIS START DEADLINE HAS ALREADY PASSED — development had to begin by {fmt_date(d)}. "
                "Unless a material operation lawfully started on site before then, this permission "
                "has expired and cannot be implemented.")
        html = (f"<b>This start deadline has already passed.</b> Development had to begin by "
                f"<b>{fmt_date(d)}</b>. Unless a material operation lawfully started on site before "
                f"then, this permission has expired and cannot be implemented.")
        return {"kind": "expired", "date": d, "text": text, "html": html}
    how = (f"as stated in condition #{sd['condition']}" if sd["basis"] == "stated"
           else "computed from the decision date — confirm against the notice")
    text = f"Development must begin by {fmt_date(d)} or the permission lapses ({how})."
    html = (f'Development must begin by <b style="font-variant-numeric:tabular-nums">{fmt_date(d)}</b> '
            f'or the permission lapses. <span style="color:var(--ct-faint)">({how})</span>')
    return {"kind": "ok", "date": d, "text": text, "html": html}


CIL_TEXT = ("CIL reminder: before any material operation on site, check whether the development is "
            "CIL-liable and, if so, submit a CIL Commencement Notice to the council and get written "
            "acknowledgement first. Starting before this can mean losing CIL relief and incurring "
            "surcharges. This tool does not read CIL notices.")
GATE_CAVEAT = ("Automated flags, not legal advice — whether a condition is a true condition-precedent "
               "can be finely balanced. Confirm with your planning consultant or solicitor before "
               "starting on site.")
