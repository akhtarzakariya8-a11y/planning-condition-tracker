"""Roadmap 2.3 + Phase 3: sequencing, the deadline engine, and calendar (.ics) export.

Sequencing answers "what order do I clear these in?". Every condition that gates work is tied
to the milestone it blocks (start on site, piling, above-ground works, occupation). Where one
condition's wording points at another ("in accordance with the details approved under
condition 5"), the referenced condition has to be cleared first — and if that means earlier
than its own milestone, it is pulled forward and the page says why.

The deadline engine works BACKWARDS from the dates the user gives. For every milestone:

    submit the discharge application by = milestone - (statutory 8 weeks + validation buffer)
    commission the specialists by        = submit-by - preparation time

Everything here is plain date maths on the extraction, so it is deterministic and testable.
Like the duplicates check, cross-references are read by code rather than asked of the model.
"""
import re
import uuid
from datetime import date, datetime, timedelta, timezone

from ct.logic import (cond_nums, fee_for, fmt_date, jurisdiction, next_fee_rise, parse_date,
                      specialists_for, start_deadline)

# The statutory period a council has to decide an application to discharge conditions
# (Article 27 DMPO 2015 in England). Other nations are treated the same, as a planning
# assumption, and the page says so.
DETERMINATION_WEEKS = 8
DEFAULT_BUFFER_WEEKS = 2       # registration/validation before the 8-week clock really runs
DEFAULT_PREP_WEEKS = 6         # commissioning + writing the submission
SOON_DAYS = 28                 # "due soon" window

MILESTONES = [
    # key, what the user is asked for, the gates that bite before it
    ("start", "Start on site", ("blocks-any-commencement", "blocks-demolition")),
    ("piling", "Start piling", ("blocks-piling",)),
    ("above_ground", "Start above-ground works", ("blocks-above-ground",)),
    ("occupation", "First occupation / use", ("before-occupation", "before-use")),
]
MILESTONE_KEYS = [m[0] for m in MILESTONES]
MILESTONE_LABEL = {k: label for k, label, _ in MILESTONES}
GATE_TO_MILESTONE = {g: k for k, _, gates in MILESTONES for g in gates}

_REF = re.compile(
    r"\bconditions?\s+(?:nos?\.?\s*)?(\d{1,3}(?:\s*(?:,|and|&|or|to|-|–)\s*\d{1,3})*)",
    re.IGNORECASE)


def referenced_conditions(condition, valid_numbers):
    """Condition numbers this condition's own wording refers to (excluding itself)."""
    text = " ".join(filter(None, [condition.get("source_quote"), condition.get("trigger_quote")]))
    found = set()
    for m in _REF.finditer(text):
        chunk = m.group(1)
        # ranges first: "conditions 5 to 8", "5-8"
        for a, b in re.findall(r"(\d+)\s*(?:to|-|–)\s*(\d+)", chunk):
            a, b = int(a), int(b)
            if 0 < b - a <= 20:
                found.update(range(a, b + 1))
        found.update(int(n) for n in re.findall(r"\d+", chunk))
    me = condition.get("condition_number")
    return sorted(n for n in found if n in valid_numbers and n != me)


def build_sequence(data):
    """Order the work. Returns {"stages": {milestone: [conditions]}, "dependencies", "pulled"}.

    dependencies: list of (needs, needed) — condition `needs` refers to condition `needed`.
    pulled: {condition_number: (own_milestone, new_milestone, because_of)} for conditions that
            must be cleared earlier than their own trigger because a stricter one depends on them.
    """
    conditions = data.get("conditions", [])
    by_num = {c["condition_number"]: c for c in conditions}
    # Only conditions that gate a milestone are "work"; approved-plans and ongoing conditions
    # are referenced all the time ("notwithstanding condition 2") without being a dependency.
    work = {n: GATE_TO_MILESTONE[c.get("gate")] for n, c in by_num.items()
            if c.get("gate") in GATE_TO_MILESTONE}

    deps = []
    for n in work:
        for m in referenced_conditions(by_num[n], set(work)):
            deps.append((n, m))

    order = {k: i for i, k in enumerate(MILESTONE_KEYS)}
    effective = dict(work)
    pulled = {}
    changed = True
    while changed:                       # relax until stable; indices only ever decrease
        changed = False
        for needs, needed in deps:
            if order[effective[needs]] < order[effective[needed]]:
                pulled[needed] = (work[needed], effective[needs], needs)
                effective[needed] = effective[needs]
                changed = True

    stages = {k: [] for k in MILESTONE_KEYS}
    for n, k in effective.items():
        stages[k].append(by_num[n])

    # Within a stage: a condition that others depend on comes first, then by number.
    for k in stages:
        members = {c["condition_number"] for c in stages[k]}
        indeg = {n: 0 for n in members}
        for needs, needed in deps:
            if needs in members and needed in members:
                indeg[needs] += 1
        ordered, ready = [], sorted(n for n in members if indeg[n] == 0)
        remaining = set(members)
        while ready:
            n = ready.pop(0)
            ordered.append(n)
            remaining.discard(n)
            for needs, needed in deps:
                if needed == n and needs in remaining:
                    indeg[needs] -= 1
                    if indeg[needs] == 0:
                        ready.append(needs)
                        ready.sort()
        ordered += sorted(remaining)          # a cycle: fall back to number order
        stages[k] = [by_num[n] for n in ordered]

    return {"stages": stages, "dependencies": deps, "pulled": pulled}


def milestone_dates(dates):
    """Fill the gaps the user left. Piling defaults to the start date, above-ground to piling.

    Defaulting EARLIER is the safe direction: an unknown date is treated as "as soon as you
    start", so a deadline is never later than it should be. Occupation has no safe default.
    """
    dates = {k: parse_date(v) if not isinstance(v, date) else v for k, v in (dates or {}).items()}
    start = dates.get("start")
    piling = dates.get("piling") or start
    above = dates.get("above_ground") or piling
    return {"start": start, "piling": piling, "above_ground": above,
            "occupation": dates.get("occupation")}


def build_programme(data, dates=None, prep_weeks=DEFAULT_PREP_WEEKS,
                    buffer_weeks=DEFAULT_BUFFER_WEEKS, today=None):
    """The deadline engine. Works with no dates at all (order only) or with any subset.

    Milestones that fall on the same date share one submission — the same bundling the
    discharge plan recommends, because the fee is charged per application.
    """
    today = today or date.today()
    seq = build_sequence(data)
    md = milestone_dates(dates)
    lead = timedelta(weeks=DETERMINATION_WEEKS + buffer_weeks)
    prep = timedelta(weeks=prep_weeks)

    steps = []
    for key in MILESTONE_KEYS:
        members = seq["stages"][key]
        if not members:
            continue
        discharge = [c for c in members if c.get("discharge_required")]
        other = [c for c in members if not c.get("discharge_required")]
        when = md.get(key)
        submit_by = when - lead if when and discharge else None
        commission_by = submit_by - prep if submit_by else None
        specialists = sorted({s for c in discharge for s in specialists_for(c)})
        status = None
        if submit_by:
            if submit_by < today:
                status = "late"
            elif submit_by <= today + timedelta(days=SOON_DAYS):
                status = "soon"
            else:
                status = "ok"
        steps.append({
            "key": key, "label": MILESTONE_LABEL[key], "date": when,
            "conditions": members, "discharge": discharge, "other": other,
            "submit_by": submit_by, "commission_by": commission_by,
            "specialists": specialists, "status": status,
        })

    # Group steps whose submissions fall on the same day into one application.
    submissions = {}
    for s in steps:
        if s["submit_by"]:
            submissions.setdefault(s["submit_by"], []).append(s["key"])

    sd = start_deadline(data)
    lapse = sd["date"]
    start = md.get("start")
    fee_on_dates = {}
    for d in submissions:
        fee_on_dates[d] = fee_for(data, on=d)

    return {
        "steps": steps,
        "dates": md,
        "has_dates": any(md.values()),
        "dependencies": seq["dependencies"],
        "pulled": seq["pulled"],
        "submissions": submissions,           # {submit_by date: [milestone keys]}
        "fees_by_submission": fee_on_dates,   # fee in force ON the date you'd submit
        "lapse": lapse,
        "lapse_basis": sd["basis"],
        "start_after_lapse": bool(lapse and start and start > lapse),
        "prep_weeks": prep_weeks,
        "buffer_weeks": buffer_weeks,
        "england": jurisdiction(data) == "england",
        "today": today,
    }


def dated_condition_deadlines(data):
    """Conditions whose deadline field is an actual calendar date. [(date, condition)]."""
    out = []
    for c in data.get("conditions", []):
        d = parse_date(c.get("deadline"))
        if d:
            out.append((d, c))
    return sorted(out, key=lambda x: x[0])


def _before_text(steps):
    """'start on site and start piling (1 March 2027)' rather than repeating a shared date."""
    by_date = {}
    for s in steps:
        by_date.setdefault(s["date"], []).append(s["label"].lower())
    return "; ".join(f"{' and '.join(labels)} ({fmt_date(d)})" for d, labels in by_date.items())


def submission_groups(programme):
    """One entry per discharge application: milestones that share a submit-by date are bundled.

    [{"submit_by", "commission_by", "before", "keys", "discharge", "specialists", "fee",
      "status"}] in date order.
    """
    out = []
    for when, keys in sorted(programme["submissions"].items()):
        steps = [s for s in programme["steps"] if s["key"] in keys]
        discharge = [c for s in steps for c in s["discharge"]]
        if not discharge:
            continue
        out.append({
            "submit_by": when,
            "commission_by": min(s["commission_by"] for s in steps),
            "before": _before_text(steps),
            "keys": keys,
            "discharge": discharge,
            "specialists": sorted({x for s in steps for x in s["specialists"]}),
            "fee": programme["fees_by_submission"].get(when),
            "status": steps[0]["status"],
        })
    return out


def fee_rise_saving(data, programme):
    """If a submission falls just after a scheduled fee rise, how much is saved by going early.

    Returns {"rise_date", "old", "new", "affected"} or None.
    """
    rise = next_fee_rise(jurisdiction(data), programme["today"])
    if not rise:
        return None
    rise_date, new_scale = rise
    old, new = fee_for(data, programme["today"]), fee_for(data, rise_date)
    if not old or not new or new <= old:
        return None
    affected = [g for g in submission_groups(programme) if g["submit_by"] >= rise_date]
    if not affected:
        return None
    return {"rise_date": rise_date, "old": old, "new": new, "affected": len(affected)}


# ----- CALENDAR (.ics) -----
def _ics_escape(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line):
    """RFC 5545: lines over 75 octets are folded with CRLF + a space."""
    out, raw = [], line.encode("utf-8")
    while len(raw) > 75:
        cut = 75
        while (raw[cut] & 0xC0) == 0x80:      # don't split a multi-byte character
            cut -= 1
        out.append(raw[:cut].decode("utf-8"))
        raw = b" " + raw[cut:]
    out.append(raw.decode("utf-8"))
    return "\r\n".join(out)


def _event(when, summary, description, alarm_days=None):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@condition-tracker",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{when.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(when + timedelta(days=1)).strftime('%Y%m%d')}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"DESCRIPTION:{_ics_escape(description)}",
        "TRANSP:TRANSPARENT",
    ]
    if alarm_days:
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_escape(summary)}",
                  f"TRIGGER:-P{int(alarm_days)}D", "END:VALARM"]
    lines.append("END:VEVENT")
    return [_fold(l) for l in lines]


def calendar_events(data, programme):
    """Everything worth a calendar entry, as (date, summary, description, alarm_days)."""
    ref = data.get("application_reference") or data.get("site_address") or "Planning permission"
    events = []
    if programme["lapse"]:
        events.append((programme["lapse"], f"{ref}: permission lapses unless work has begun",
                       "Development must have lawfully begun by this date (a material operation, "
                       "with every pre-commencement condition discharged first). Automated date — "
                       "confirm against the notice.", 56))
    for sub in submission_groups(programme):
        fee = sub["fee"]
        fee_txt = f" Council fee on this date: £{fee} per application." if fee else ""
        events.append((
            sub["submit_by"],
            f"{ref}: submit discharge application — {cond_nums(sub['discharge'])}",
            f"Needed before: {sub['before']}. Allows {DETERMINATION_WEEKS} weeks for the council "
            f"to decide plus {programme['buffer_weeks']} weeks for validation.{fee_txt}", 7))
        if sub["specialists"]:
            events.append((
                sub["commission_by"],
                f"{ref}: commission {', '.join(sub['specialists'])}",
                f"So the submission for {cond_nums(sub['discharge'])} is ready by "
                f"{fmt_date(sub['submit_by'])} ({programme['prep_weeks']} weeks to prepare).", 7))
    for d, c in dated_condition_deadlines(data):
        events.append((d, f"{ref}: condition {c['condition_number']} deadline",
                       c.get("summary") or "", 14))
    return sorted(events, key=lambda e: e[0])


def build_ics(data, programme):
    """A calendar file Outlook, Google Calendar and Apple Calendar can all import."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Condition Tracker//Planning//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             _fold(f"X-WR-CALNAME:{_ics_escape('Planning conditions — ' + (data.get('application_reference') or 'project'))}")]
    for when, summary, desc, alarm in calendar_events(data, programme):
        lines += _event(when, summary, desc, alarm)
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")
