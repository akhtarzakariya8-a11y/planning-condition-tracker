"""The HTML panels the page shows. Strings in, strings out — the page decides where they go.

Every colour and type decision comes from theme/tokens.css via the theme helpers.
"""
import html

from ct.logic import (CIL_DOC_TYPES, CIL_TEXT, FLAG_LABEL, GATE_CAVEAT, GATE_DOC_TYPES,
                      JURISDICTION_LABEL, build_discharge_plan, build_specialists, cond_nums,
                      doc_type, fmt_date, from_scan, get_flags, n_conditions,
                      sort_by_category, split_by_gate, start_deadline_message)
from ct.programme import DETERMINATION_WEEKS, fee_rise_saving, submission_groups
from theme.ct_theme import label, note, pill

LAYOUT_CSS = """
<style>
  .block-container { max-width: 1180px; }
  .ct-panel      { padding: var(--ct-s5); margin: 0 0 var(--ct-s5) 0; }
  .ct-panel-hd   { margin-bottom: var(--ct-s3); }
  .ct-line       { padding: 11px 0; border-bottom: 1px solid var(--ct-border-soft); }
  .ct-line:last-of-type { border-bottom: none; }
  .ct-line-txt   { font: 400 var(--ct-body-size)/1.65 var(--ct-font-body); color: var(--ct-body); }
  .ct-nums       { font-variant-numeric: tabular-nums; font-size: 12px; color: var(--ct-faint);
                   margin-top: 5px; letter-spacing: .2px; }
  .ct-kv         { display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; }
  .ct-kv-k       { font: 600 var(--ct-body-size)/1.5 var(--ct-font-body); color: var(--ct-ink);
                   min-width: 236px; }
  .ct-total      { font: var(--ct-h2); color: var(--ct-ink);
                   font-variant-numeric: tabular-nums; margin-top: var(--ct-s4); }
  .ct-expired    { display:flex; gap:10px; align-items:flex-start;
                   padding: 11px 14px; border-radius: var(--ct-r-md);
                   background: var(--ct-overdue-tint); border: 1px solid #e6c9c5;
                   font: 400 13px/1.5 var(--ct-font-body); color: var(--ct-overdue);
                   margin-bottom: var(--ct-s4); }
  .ct-expired b  { font-weight: 700; }
  .ct-warn       { display:flex; gap:10px; align-items:flex-start;
                   padding: 11px 14px; border-radius: var(--ct-r-md);
                   background: var(--ct-action-tint); border: 1px solid #ecd6b0;
                   font: 400 13px/1.5 var(--ct-font-body); color: var(--ct-action-ink);
                   margin-bottom: var(--ct-s4); }
  .ct-step-n     { font: 700 var(--ct-label-size)/1 var(--ct-font-body);
                   letter-spacing: var(--ct-label-track); color: var(--ct-accent); }
  .ct-tbl        { width:100%; border-collapse: collapse; }
  .ct-tbl thead th {
      font:700 10.5px/1 var(--ct-font-body); letter-spacing:.9px; text-transform:uppercase;
      color:var(--ct-faint); text-align:left; padding:13px 18px;
      border-bottom:1px solid var(--ct-border); white-space:nowrap; }
  .ct-tbl tbody td {
      padding: 13px 18px; vertical-align: top;
      border-bottom: 1px solid var(--ct-border-soft);
      font: 600 14px/1.55 var(--ct-font-body); color: var(--ct-ink); }
  .ct-tbl tbody tr:last-child td { border-bottom: none; }
  .ct-tbl tbody tr:hover td { background: var(--ct-surface-hover); }
  .ct-tbl .num   { font-variant-numeric: tabular-nums; font-weight:600; color: var(--ct-faint); }
  .ct-tbl .sec   { font: 400 12.5px/1.5 var(--ct-font-body); color: var(--ct-muted);
                   white-space: nowrap; }
  .ct-tbl.compact tbody td { padding: 10px 14px; font-size: 13px; }
  .ct-tbl.compact thead th { padding: 11px 14px; }
  .ct-quiet      { font: 500 12.5px/1 var(--ct-font-body); color: var(--ct-faint); }
  .ct-src        { margin-top: 9px; }
  .ct-src > summary {
      list-style: none; cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
      font: 600 11.5px/1 var(--ct-font-body); color: var(--ct-accent); }
  .ct-src > summary::-webkit-details-marker { display: none; }
  .ct-src > summary::before { content: "▸"; font-size: 9px; }
  .ct-src[open] > summary::before { content: "▾"; }
  .ct-src > summary:hover { color: var(--ct-accent-hover); text-decoration: underline; }
  .ct-src-ocr    { margin-top: 7px; font: 400 11.5px/1.5 var(--ct-font-body);
                   color: var(--ct-action-ink); }
  .ct-src blockquote {
      margin: 9px 0 0; padding: 10px 14px;
      border-left: 2px solid var(--ct-accent-line); background: var(--ct-surface-alt);
      border-radius: 0 var(--ct-r-sm) var(--ct-r-sm) 0;
      font: 400 13px/1.6 var(--ct-font-body); color: var(--ct-body); font-style: italic; }
  .ct-flagrow    { display:flex; flex-wrap:wrap; gap:9px 12px; align-items:baseline;
                   padding: 11px 0; border-bottom:1px solid var(--ct-border-soft); }
  .ct-flagrow:last-of-type { border-bottom:none; }
  .ct-panel .ct-note { margin-top: var(--ct-s2); }
  .ct-panel .ct-note:first-of-type { margin-top: var(--ct-s5); }
  .ct-sub        { display:grid; grid-template-columns: 150px 1fr; gap: 6px 18px;
                   padding: 14px 0; border-bottom: 1px solid var(--ct-border-soft); }
  .ct-sub:last-of-type { border-bottom: none; }
  .ct-sub-date   { font: 600 15px/1.3 var(--ct-font-display); color: var(--ct-ink);
                   font-variant-numeric: tabular-nums; }
  .ct-sub-k      { font: 700 10.5px/1 var(--ct-font-body); letter-spacing: .9px;
                   text-transform: uppercase; color: var(--ct-faint); margin-bottom: 4px; }
  .ct-letter     { white-space: pre-wrap; font: 400 13px/1.65 var(--ct-font-body);
                   color: var(--ct-body); background: var(--ct-surface-alt);
                   border: 1px solid var(--ct-border); border-radius: var(--ct-r-md);
                   padding: 18px 20px; max-height: 460px; overflow-y: auto; }
  .ct-prog       { height: 6px; border-radius: 3px; background: var(--ct-track); overflow: hidden; }
  .ct-prog > i   { display:block; height: 100%; background: var(--ct-accent); }
  /* Download buttons share the theme's button look (the theme only styles .stButton). */
  .stDownloadButton > button {
    border:1px solid var(--ct-border-strong); background:var(--ct-surface); color:var(--ct-ink);
    border-radius:var(--ct-r-sm); font-size:13px; font-weight:600; box-shadow:none; }
  .stDownloadButton > button:hover { background:var(--ct-fill); color:var(--ct-ink);
    border-color:var(--ct-border-strong); }
  .stDownloadButton > button[kind="primary"] { background:var(--ct-accent); border-color:var(--ct-accent);
    color:var(--ct-bg); }
  .stDownloadButton > button[kind="primary"] p { color:var(--ct-bg); }
  .stDownloadButton > button[kind="primary"]:hover { background:var(--ct-accent-hover);
    border-color:var(--ct-accent-hover); color:var(--ct-bg); }
  @media (max-width: 640px) {
    .ct-sub { grid-template-columns: 1fr; }
    .ct-kv-k { min-width: 0; }
    .ct-tbl thead th, .ct-tbl tbody td { padding: 10px 10px; }
  }
</style>
"""

# Category -> the editorial status set. Colour means status here, so only categories implying
# outstanding work get a pill; time-limit and ongoing need no action and stay quiet.
CATEGORY_PILL = {
    "pre-commencement": "overdue",
    "discharge-required": "action",
    "pre-occupation": "submitted",
}


def category_pill(cat):
    status = CATEGORY_PILL.get(cat)
    return pill(cat, status) if status else f'<span class="ct-quiet">{html.escape(str(cat))}</span>'


def esc(text):
    return html.escape(str(text if text is not None else ""))


def section_label(text, top="var(--ct-s5)"):
    return f'<div style="margin:{top} 0 var(--ct-s3)">{label(text)}</div>'


def source_clause_html(condition, scanned=False):
    """Collapsed disclosure showing the notice's own wording for one condition.

    Renders nothing when there is no quote. On a scanned notice the quote is the model's
    transcription of an image rather than a copy, so it is labelled as such.
    """
    quote = (condition.get("source_quote") or "").strip()
    if not quote:
        return ""
    summary = "Show original clause (read from scan)" if scanned else "Show original clause"
    caveat = ('<div class="ct-src-ocr">This notice is a scan with no text layer, so this wording '
              'was read from the image and may contain transcription errors. Check it against '
              'the original.</div>') if scanned else ""
    return (f'<details class="ct-src"><summary>{summary}</summary>'
            f'<blockquote>{esc(quote)}</blockquote>{caveat}</details>')


# ----- SAFETY GATE -----
def build_safety_gate_html(data):
    """A short summary panel: counts and condition numbers only.

    Deliberately does NOT repeat condition text — the table below carries the detail.
    """
    if doc_type(data) not in GATE_DOC_TYPES:
        return ""  # nothing to start: a refusal, or conditions already discharged

    conditions = data.get("conditions", [])
    msg = start_deadline_message(data)
    blockers, piling, ambiguous, startable = split_by_gate(conditions)

    if not (msg["kind"] or blockers or piling or ambiguous or startable):
        return ""

    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', label("BEFORE YOU START ON SITE"), '</div>']

    if msg["kind"] == "expired":
        parts.append(f'<div class="ct-expired"><span>⚠</span><span>{msg["html"]}</span></div>')
    elif msg["kind"] == "unknown":
        parts.append(f'<div class="ct-warn"><span>⚠</span><span><b>Start deadline:</b> '
                     f'{msg["html"]}</span></div>')
    elif msg["kind"] == "ok":
        parts.append(f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s4)">{msg["html"]}</div>')

    def line(status, text, conds):
        return (f'<div class="ct-line">{pill(text, status)}'
                f'<div class="ct-nums">{cond_nums(conds)}</div></div>')

    if blockers:
        parts.append(line("overdue",
                          f"{n_conditions(len(blockers))} must be discharged before you can lawfully "
                          f"start on site", blockers))
    if startable:
        verb = "blocks" if len(startable) == 1 else "block"
        parts.append(line("discharged",
                          f"{len(startable)} more only {verb} above-ground works — you can begin "
                          f"demolition and groundworks first", startable))
    if piling:
        parts.append(line("action", f"{n_conditions(len(piling))} to clear before any piling", piling))
    if ambiguous:
        verb = "needs" if len(ambiguous) == 1 else "need"
        parts.append(line("action",
                          f"{n_conditions(len(ambiguous))} {verb} checking — wording is ambiguous",
                          ambiguous))

    parts.append(f'<div style="margin-top:var(--ct-s4)">'
                 f'{label("FULL DETAIL IN THE CONDITIONS TABLE BELOW")}</div>')
    if doc_type(data) in CIL_DOC_TYPES:
        parts.append(note(CIL_TEXT.replace("CIL reminder:", "<b>CIL reminder:</b>")))
    parts.append(note(GATE_CAVEAT))
    parts.append("</div>")
    return "".join(parts)


# ----- THINGS TO CHECK -----
def build_flags_html(data):
    flags = get_flags(data)
    if not flags:
        return ""   # a clean notice shows nothing at all
    n = len(flags)
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', label("THINGS TO CHECK IN THE NOTICE"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s2)">{n} possible '
             f'{"error" if n == 1 else "errors"} in the council\'s own document — worth querying '
             f'before you rely on the wording.</div>']
    for f in flags:
        kind = FLAG_LABEL.get(f.get("type"), "check").upper()
        cond = f.get("condition")
        cond_html = (f'<span class="ct-quiet" style="font-variant-numeric:tabular-nums">#{esc(cond)}'
                     f'</span>') if cond is not None else ""
        parts.append(f'<div class="ct-flagrow">{pill(kind, "action")}{cond_html}'
                     f'<span class="ct-line-txt" style="flex:1;min-width:250px">{esc(f["detail"])}</span>'
                     f'</div>')
    parts.append(note("Automated flags — the tool may miss some issues or occasionally over-flag. "
                      "Always read against the source notice."))
    parts.append("</div>")
    return "".join(parts)


# ----- CONDITIONS TABLE -----
STATUS_PILL = {
    "not-started": None, "in-progress": ("In preparation", "action"),
    "submitted": ("Submitted", "submitted"), "discharged": ("Discharged", "discharged"),
    "complied": ("Complied", "discharged"), "not-applicable": None,
}


def build_conditions_table_html(data, tracker=None):
    scanned = from_scan(data)
    rows = ""
    for c in sort_by_category(data.get("conditions", [])):
        deadline = esc(c.get("deadline") or "—")
        disc = ('<span class="ct-quiet" style="color:var(--ct-ink)">Yes</span>'
                if c.get("discharge_required") else '<span class="ct-quiet">—</span>')
        status = ""
        if tracker is not None:
            st_ = STATUS_PILL.get((tracker.get(str(c["condition_number"])) or {}).get("status"))
            status = f'<div style="margin-top:7px">{pill(*st_)}</div>' if st_ else ""
        rows += (
            f'<tr><td class="num">{c["condition_number"]}</td>'
            f'<td>{esc(c.get("summary"))}{status}{source_clause_html(c, scanned)}</td>'
            f'<td>{category_pill(c.get("category"))}</td>'
            f'<td class="sec">{deadline}</td>'
            f'<td class="sec" style="text-align:center">{disc}</td></tr>'
        )
    return (
        '<div class="ct-card" style="overflow-x:auto"><table class="ct-tbl">'
        '<thead><tr>'
        '<th style="width:56px">#</th><th>Summary</th>'
        '<th style="width:180px">Category</th><th style="width:130px">Deadline</th>'
        '<th style="width:110px;text-align:center">Discharge</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
    )


# ----- DISCHARGE PLAN -----
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
        fee_lead = (f'The council fee is <b>£{plan["fee"] or scale["other"]} per application</b> — not '
                    f'per condition, so bundle them. A sensible way to batch these is by stage:')

    needs = "needs" if plan["total"] == 1 else "need"
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', label("DISCHARGE PLAN"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">You have '
             f'<b>{n_conditions(plan["total"])}</b> that {needs} formal discharge (submitted to '
             f'<b>and</b> approved by the council). {fee_lead}</div>']
    for stage, members in plan["batches"]:
        parts.append(
            f'<div class="ct-line"><div class="ct-kv">'
            f'<span class="ct-kv-k">{stage}</span>'
            f'{pill(n_conditions(len(members)), "submitted")}'
            f'<span class="ct-nums" style="margin-top:0">{cond_nums(members)}</span></div></div>')

    rise = ""
    if plan["next_rise"]:
        rdate, rscale = plan["next_rise"]
        rise = (f' Fees rise to £{rscale["other"]} (£{rscale["householder"]} householder) on '
                f'{fmt_date(rdate)}.')
    if not plan["fee_payable"]:
        parts.append(f'<div class="ct-total">≈ {app_word} to submit — no council fee.</div>')
        parts.append(note("Conditions on a listed building consent carry no application fee. "
                          "Conditions on a linked planning permission do."))
    elif scale is None:
        parts.append(f'<div class="ct-total">≈ {app_word} to submit.</div>')
        parts.append(note(
            f"No fee shown — this notice{where}, and this tool only holds the England and Wales fee "
            f"scales. The per-application principle still applies, so bundling still saves money."))
    elif plan["fee"] is not None:
        scheme = "householder" if plan["householder"] else "non-householder"
        parts.append(f'<div class="ct-total">≈ {app_word} × £{plan["fee"]} = '
                     f'~£{plan["cost"]:,} in council fees.</div>')
        parts.append(note(f"Priced at the <b>{scheme}</b> rate for {juris_name}.{rise}"))
    else:
        parts.append(f'<div class="ct-total">≈ {app_word} — about '
                     f'£{apps * scale["other"]:,} at the standard rate, or '
                     f'£{apps * scale["householder"]:,} if this is a householder scheme.</div>')
        parts.append(note(
            f"We couldn't tell which fee category this scheme falls into, so both {juris_name} rates "
            f"are shown (£{scale['other']} vs £{scale['householder']} per application).{rise}"))

    if plan["deemed_discharge"]:
        parts.append(note(
            "<b>Deemed discharge:</b> the council has 8 weeks to decide. If it misses that — and the "
            "condition isn't one of the excluded types — you may be able to serve notice and proceed as "
            "if the condition were discharged. A useful lever if they go quiet."))
    parts.append(note(
        "Batching is guidance, not a rule — you can combine or split further, and timing depends on "
        "your programme. Fees are the statutory rate and change over time; confirm the current figure "
        "before relying on it. Not legal or planning advice — confirm with your planning consultant."))
    parts.append("</div>")
    return "".join(parts)


# ----- SPECIALISTS -----
def build_specialists_html(data):
    specialists = build_specialists(data)
    if not specialists:
        return ""
    n = len(specialists)
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', label("SPECIALISTS TO COMMISSION"), '</div>',
             f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">You will likely need to '
             f'bring in <b>{n} external specialist{"" if n == 1 else "s"}</b> for this scheme. The '
             f'notice never says so — each discipline below is implied by what its conditions '
             f'actually ask you to produce.</div>']
    for name, nums in specialists:
        joined = ", ".join(f"#{x}" for x in nums)
        parts.append(
            f'<div class="ct-line"><div class="ct-kv">'
            f'<span class="ct-kv-k">{esc(name)}</span>'
            f'{pill(n_conditions(len(nums)), "submitted")}'
            f'<span class="ct-nums" style="margin-top:0">{joined}</span>'
            f'</div></div>')
    parts.append(note(
        "A guide to resourcing, not a definitive list — some conditions can be handled in-house, and "
        "one consultant often covers several disciplines. Confirm with your team. Not legal or "
        "planning advice."))
    parts.append("</div>")
    return "".join(parts)


# ----- PROGRAMME (sequencing + deadlines) -----
STATUS_TEXT = {"late": ("Late — submit now", "overdue"), "soon": ("Due within 4 weeks", "action"),
               "ok": ("On track", "discharged")}


def build_programme_html(data, prog):
    """The order of work, and — once dates are given — when each application must go in."""
    steps = prog["steps"]
    if not steps:
        return ""
    parts = ['<div class="ct-card ct-panel">',
             '<div class="ct-panel-hd">', label("ORDER OF WORK & DEADLINES"), '</div>']

    if prog["start_after_lapse"]:
        parts.append(f'<div class="ct-expired"><span>⚠</span><span><b>Your planned start is after the '
                     f'permission lapses</b> on {fmt_date(prog["lapse"])}. Start a material operation '
                     f'before then, or the permission cannot be implemented.</span></div>')

    if not prog["has_dates"]:
        parts.append('<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">Clear the conditions '
                     'in this order. Add your programme dates above to see when each discharge '
                     'application has to go in.</div>')
        for s in steps:
            disc = (f'{pill(n_conditions(len(s["discharge"])) + " to discharge", "submitted")}'
                    if s["discharge"] else "")
            other = (f'<span class="ct-quiet">+ {len(s["other"])} to comply with</span>'
                     if s["other"] else "")
            parts.append(f'<div class="ct-line"><div class="ct-kv"><span class="ct-kv-k">'
                         f'Before: {s["label"].lower()}</span>{disc}{other}</div>'
                         f'<div class="ct-nums">{cond_nums(s["conditions"])}</div></div>')
    else:
        groups = submission_groups(prog)
        total_fee = sum(g["fee"] for g in groups if g["fee"])
        if groups:
            fee_txt = (f", about <b>£{total_fee:,}</b> in council fees at the rates in force on those "
                       f"dates") if total_fee else ""
            parts.append(f'<div class="ct-line-txt" style="margin-bottom:var(--ct-s2)">Working back from '
                         f'your dates: <b>{len(groups)} discharge application'
                         f'{"" if len(groups) == 1 else "s"}</b>{fee_txt}.</div>')
        for g in groups:
            status_text, status_kind = STATUS_TEXT.get(g["status"], ("", "submitted"))
            who = ", ".join(g["specialists"]) or "In-house (no external specialist)"
            parts.append(
                f'<div class="ct-sub">'
                f'<div><div class="ct-sub-k">Submit by</div>'
                f'<div class="ct-sub-date">{fmt_date(g["submit_by"])}</div>'
                f'<div style="margin-top:8px">{pill(status_text, status_kind)}</div></div>'
                f'<div><div class="ct-line-txt"><b>{n_conditions(len(g["discharge"]))}</b> needed '
                f'before {esc(g["before"])}'
                f'{" — £" + str(g["fee"]) if g["fee"] else ""}</div>'
                f'<div class="ct-nums">{cond_nums(g["discharge"])}</div>'
                f'<div class="ct-line-txt" style="margin-top:8px;font-size:13px">'
                f'Commission by <b>{fmt_date(g["commission_by"])}</b>: {esc(who)}</div></div>'
                f'</div>')
        others = [s for s in steps if s["other"]]
        for s in others:
            when = f" ({fmt_date(s['date'])})" if s["date"] else ""
            parts.append(f'<div class="ct-line"><div class="ct-kv"><span class="ct-kv-k">'
                         f'Comply before {s["label"].lower()}{when}</span>'
                         f'<span class="ct-nums" style="margin-top:0">{cond_nums(s["other"])}</span>'
                         f'</div></div>')
        undated = [s for s in steps if s["discharge"] and not s["date"]]
        if undated:
            parts.append(note("No date given for: " + ", ".join(s["label"].lower() for s in undated)
                              + " — add one to schedule those applications."))

    for n, (own, new, because) in sorted(prog["pulled"].items()):
        parts.append(note(f"<b>Condition #{n} has been brought forward:</b> condition #{because} "
                          f"refers to it, so it has to be cleared first."))
    saving = fee_rise_saving(data, prog) if prog["has_dates"] else None
    if saving:
        parts.append(note(f"<b>Save £{saving['new'] - saving['old']} per application:</b> council fees "
                          f"rise from £{saving['old']} to £{saving['new']} on "
                          f"{fmt_date(saving['rise_date'])}. Anything you can submit before then is "
                          f"cheaper."))
    if prog["has_dates"]:
        assumption = "" if prog["england"] else (" The 8-week period is England's, used here as a "
                                                 "planning assumption for this notice's nation.")
        parts.append(note(f"Submit-by dates allow the council's statutory {DETERMINATION_WEEKS} weeks "
                          f"plus {prog['buffer_weeks']} weeks for validation; commission-by dates allow "
                          f"{prog['prep_weeks']} weeks to prepare each submission.{assumption} A "
                          f"planning aid, not legal advice."))
    parts.append("</div>")
    return "".join(parts)


# ----- PORTFOLIO (batch upload, saved projects) -----
def build_portfolio_html(rows):
    """rows: [{"name", "summary"}] where summary is logic.summarise()."""
    body = ""
    for r in rows:
        s = r["summary"]
        begin = fmt_date(s["begin_by"]) if s["begin_by"] else {
            "outline": "From reserved matters", "variation": "From original permission"}.get(
            s["begin_by_basis"], "—")
        blockers = (pill(str(s["blockers"]), "overdue") if s["blockers"]
                    else '<span class="ct-quiet">0</span>')
        fees = f'£{s["fees"]:,}' if s["fees"] else "—"
        body += (f'<tr><td style="min-width:260px">{esc(r["name"])}<div class="ct-quiet" style="margin-top:4px">'
                 f'{esc(s["council"] or "")}</div></td>'
                 f'<td class="sec">{esc(s["document"])}<br>{esc(s["decision"])}</td>'
                 f'<td class="sec">{esc(begin)}</td>'
                 f'<td class="num">{s["conditions"]}</td><td>{blockers}</td>'
                 f'<td class="num">{s["discharge"]}</td><td class="sec">{fees}</td>'
                 f'<td class="num">{s["flags"] or "—"}</td></tr>')
    return ('<div class="ct-card" style="overflow-x:auto"><table class="ct-tbl compact"><thead><tr>'
            '<th>Notice</th><th>Type</th><th>Begin by</th><th>Conds</th><th>Pre-start</th>'
            '<th>Discharge</th><th>Fees</th><th>Checks</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def progress_html(done, total):
    pct = round(100 * done / total) if total else 0
    return (f'<div class="ct-prog"><i style="width:{pct}%"></i></div>'
            f'<div class="ct-nums">{done} of {total} discharged or complied · {pct}%</div>')
