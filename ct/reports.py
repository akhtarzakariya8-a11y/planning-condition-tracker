"""Files people download: the Excel tracker, the PDF summary, the portfolio workbook."""
import io
from datetime import date
from xml.sax.saxutils import escape

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

from ct.logic import (CATEGORY_COLOURS, CIL_DOC_TYPES, CIL_TEXT, FLAG_LABEL, GATE_CAVEAT,
                      GATE_DOC_TYPES, JURISDICTION_LABEL, build_discharge_plan, build_specialists,
                      cond_nums, doc_type, fmt_date, from_scan, gate_label, get_flags,
                      n_conditions, notice_title, sort_by_category, split_by_gate,
                      start_deadline_message, summarise)
from ct.programme import DETERMINATION_WEEKS, fee_rise_saving, submission_groups

NAVY = "1F4E78"
STATUS_LABEL = {
    "not-started": "Not started", "in-progress": "In preparation", "submitted": "Submitted",
    "discharged": "Discharged", "complied": "Complied", "not-applicable": "N/A",
}


# ----- small helpers -----
def _header(ws, labels, fill=NAVY):
    ws.append(labels)
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=fill)


def _widths(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _wrap(ws, cols, min_row=2):
    for row in ws.iter_rows(min_row=min_row):
        for i in cols:
            if i < len(row):
                row[i].alignment = Alignment(wrap_text=True, vertical="top")


class _Lines:
    """A one-column narrative sheet ("Before you start", "Discharge plan")."""

    def __init__(self, ws):
        self.ws = ws

    def head(self, text, fill=NAVY):
        self.ws.append([text])
        cell = self.ws.cell(row=self.ws.max_row, column=1)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=fill)

    def line(self, text="", bold=False, colour=None):
        self.ws.append([text])
        self.ws.cell(row=self.ws.max_row, column=1).font = Font(bold=bold, color=colour)

    def finish(self):
        self.ws.column_dimensions["A"].width = 110
        for row in self.ws.iter_rows(min_row=1):
            row[0].alignment = Alignment(wrap_text=True, vertical="top")


def _save(wb):
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ----- EXCEL TRACKER -----
def build_excel(data, programme=None, tracker=None):
    """The colour-coded tracker. `programme` adds a Programme sheet; `tracker` adds status columns.

    tracker: {condition_number(str): {"status", "submitted", "approved", "reference", "notes"}}
    """
    wb = openpyxl.Workbook()

    # ----- Sheet 1: Conditions -----
    ws = wb.active
    ws.title = "Conditions"
    scanned = from_scan(data)
    head = ["#", "Summary", "Category", "Deadline", "Responsible", "Discharge required?",
            "Source clause (read from scan)" if scanned else "Source clause"]
    if tracker is not None:
        head += ["Status", "Submitted", "Approved", "Council ref", "Notes"]
    _header(ws, head)
    for c in sort_by_category(data.get("conditions", [])):
        row = [c["condition_number"], c.get("summary"), c.get("category"),
               c.get("deadline"), c.get("responsible_party"),
               "Yes" if c.get("discharge_required") else "No",
               c.get("source_quote") or ""]
        if tracker is not None:
            t = tracker.get(str(c["condition_number"]), {})
            row += [STATUS_LABEL.get(t.get("status"), "Not started"), t.get("submitted") or "",
                    t.get("approved") or "", t.get("reference") or "", t.get("notes") or ""]
        ws.append(row)
        ws.cell(row=ws.max_row, column=3).fill = PatternFill(
            "solid", fgColor=CATEGORY_COLOURS.get(c.get("category"), "FFFFFF"))
    _widths(ws, {"A": 5, "B": 52, "C": 18, "D": 16, "E": 14, "F": 18, "G": 70,
                 "H": 15, "I": 13, "J": 13, "K": 16, "L": 40})
    for row in ws.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
        # the verbatim clause travels with the export, in the notice's own words
        row[6].alignment = Alignment(wrap_text=True, vertical="top")
        row[6].font = Font(italic=True, color="3C382F")
    ws.freeze_panes = "A2"
    if scanned:
        ws.append([])
        ws.append(["This notice is a scan with no text layer, so the source clauses were read from "
                   "the image rather than copied. Treat them as a transcription and check anything "
                   "you rely on against the original notice."])
        ws.cell(row=ws.max_row, column=1).font = Font(italic=True, color="8A5A14")

    # ----- Things to check (only when the notice actually has problems) -----
    flags = get_flags(data)
    if flags:
        wsf = wb.create_sheet("Things to check")
        _header(wsf, ["Type", "Condition", "Detail"], fill="8A6D20")
        for f in flags:
            cond = f.get("condition")
            wsf.append([FLAG_LABEL.get(f.get("type"), "check"),
                        f"#{cond}" if cond is not None else "—", f["detail"]])
        _widths(wsf, {"A": 17, "B": 11, "C": 78})
        _wrap(wsf, [2])
        wsf.freeze_panes = "A2"
        wsf.append([])
        wsf.append(["Automated flags — the tool may miss some issues or occasionally over-flag. "
                    "Always read against the source notice."])

    # ----- Before you start (only where works can lawfully start) -----
    if doc_type(data) in GATE_DOC_TYPES:
        s = _Lines(wb.create_sheet("Before you start"))
        conditions = data.get("conditions", [])
        blockers, piling, ambiguous, startable = split_by_gate(conditions)
        msg = start_deadline_message(data)
        s.head("BEFORE YOU START ON SITE")
        s.line()
        s.line(msg["text"], bold=True, colour={"expired": "C0392B", "unknown": "B9770E"}.get(msg["kind"]))
        s.line()
        # Summary lines only — counts and condition numbers. Detail lives on the Conditions tab.
        if blockers:
            s.line(f"{n_conditions(len(blockers))} must be discharged before you can lawfully start on "
                   f"site:   {cond_nums(blockers)}", bold=True, colour="C0392B")
        if startable:
            verb = "blocks" if len(startable) == 1 else "block"
            s.line(f"{len(startable)} more only {verb} above-ground works — you can begin demolition "
                   f"and groundworks first:   {cond_nums(startable)}", colour="17663A")
        if piling:
            s.line(f"{n_conditions(len(piling))} to clear before any piling:   {cond_nums(piling)}",
                   colour="B9770E")
        if ambiguous:
            verb = "needs" if len(ambiguous) == 1 else "need"
            s.line(f"{n_conditions(len(ambiguous))} {verb} checking — wording is ambiguous:   "
                   f"{cond_nums(ambiguous)}", colour="B9770E")
        s.line()
        s.line("Full detail is on the Conditions tab.")
        s.line()
        if doc_type(data) in CIL_DOC_TYPES:
            s.line(CIL_TEXT)
            s.line()
        s.line(GATE_CAVEAT)
        s.finish()

    # ----- Discharge plan -----
    plan = build_discharge_plan(data)
    if plan["applies"]:
        s = _Lines(wb.create_sheet("Discharge plan"))
        s.head("DISCHARGE PLAN")
        s.line()
        for text, bold, colour in discharge_plan_lines(plan):
            s.line(text, bold=bold, colour=colour)
        s.finish()

    # ----- Programme (only once the user has given dates) -----
    if programme and programme.get("has_dates"):
        wsp = wb.create_sheet("Programme")
        _header(wsp, ["Submit by", "Commission specialists by", "Needed before", "Conditions",
                      "Specialists", "Council fee", "Status"], fill="2E6E4E")
        for g in submission_groups(programme):
            wsp.append([fmt_date(g["submit_by"]), fmt_date(g["commission_by"]), g["before"],
                        cond_nums(g["discharge"]), ", ".join(g["specialists"]) or "In-house",
                        f"£{g['fee']}" if g["fee"] else "—",
                        {"late": "LATE — submit now", "soon": "Due within 4 weeks",
                         "ok": "On track"}.get(g["status"], "")])
            if g["status"] == "late":
                wsp.cell(row=wsp.max_row, column=7).font = Font(bold=True, color="C0392B")
        _widths(wsp, {"A": 17, "B": 22, "C": 40, "D": 34, "E": 46, "F": 12, "G": 20})
        _wrap(wsp, [2, 3, 4])
        wsp.append([])
        for line in programme_notes(data, programme):
            wsp.append([line])
            wsp.cell(row=wsp.max_row, column=1).font = Font(italic=True, color="6E675C")

    # ----- Specialists -----
    specialists = build_specialists(data)
    if specialists:
        ws4 = wb.create_sheet("Specialists")
        _header(ws4, ["Specialist", "Conditions", "Count"], fill="4B3B7A")
        for name, nums in specialists:
            ws4.append([name, ", ".join(f"#{x}" for x in nums), len(nums)])
        _widths(ws4, {"A": 42, "B": 46, "C": 8})
        _wrap(ws4, [1])
        ws4.freeze_panes = "A2"
        ws4.append([])
        ws4.append(["A guide to resourcing, not a definitive list — some conditions can be handled "
                    "in-house, and one consultant often covers several disciplines. Confirm with your "
                    "team. Not legal or planning advice."])
    return _save(wb)


def discharge_plan_lines(plan):
    """The discharge plan as (text, bold, colour) lines — shared by Excel and PDF."""
    out = []
    if not plan["total"]:
        return [("No conditions on this notice require formal discharge by the council.", False, None)]
    apps = plan["applications"]
    app_word = f"{apps} application{'' if apps == 1 else 's'}"
    out.append((f"{n_conditions(plan['total'])} {'needs' if plan['total'] == 1 else 'need'} formal "
                f"discharge (submitted to AND approved by the council).", False, None))
    scale = plan["scale"]
    juris_name = JURISDICTION_LABEL.get(plan["jurisdiction"])
    if not plan["fee_payable"]:
        out.append(("There is no council fee for discharging conditions on a listed building consent, "
                    "but you still have to apply.", True, None))
    elif scale is None:
        out.append(("The fee is charged per application, not per condition — so bundle them. This tool "
                    "only holds the England and Wales fee scales, so it cannot price this notice; check "
                    "the figure with the authority.", True, None))
    else:
        out.append((f"The council fee is £{plan['fee'] or scale['other']} per application — not per "
                    f"condition. So bundle them.", True, None))
    out.append(("A sensible way to batch these is by stage:", False, None))
    for stage, members in plan["batches"]:
        out.append((f"   {stage}:   {n_conditions(len(members))} — {cond_nums(members)}", False, None))
    rise = ""
    if plan["next_rise"]:
        rdate, rscale = plan["next_rise"]
        rise = f" Fees rise to £{rscale['other']} / £{rscale['householder']} on {fmt_date(rdate)}."
    if not plan["fee_payable"]:
        out.append((f"≈ {app_word} to submit — no council fee.", True, "17663A"))
    elif scale is None:
        out.append((f"≈ {app_word} to submit.", True, NAVY))
        out.append((f"(No fee shown — this notice is from {juris_name or 'an unclear jurisdiction'}, and "
                    f"this tool holds the England and Wales scales only. The per-application principle "
                    f"still applies, so bundling still saves money.)", False, None))
    elif plan["fee"] is not None:
        scheme = "householder" if plan["householder"] else "non-householder"
        out.append((f"≈ {app_word} × £{plan['fee']} = ~£{plan['cost']:,} in council fees.", True, NAVY))
        out.append((f"(Priced at the {scheme} rate for {juris_name}.{rise})", False, None))
    else:
        out.append((f"≈ {app_word} — about £{apps * scale['other']:,} at the standard rate, or "
                    f"£{apps * scale['householder']:,} if this is a householder scheme.", True, NAVY))
        out.append((f"(Fee category unclear from this notice, so both {juris_name} rates are shown: "
                    f"£{scale['other']} vs £{scale['householder']} per application.{rise})", False, None))
    if plan["deemed_discharge"]:
        out.append(("Deemed discharge: the council has 8 weeks to decide. If it misses that — and the "
                    "condition isn't one of the excluded types — you may be able to serve notice and "
                    "proceed as if the condition were discharged. A useful lever if they go quiet.",
                    False, "17663A"))
    out.append(("Batching is guidance, not a rule — you can combine or split further, and timing depends "
                "on your programme. Fees are the statutory rate and change over time; confirm the "
                "current figure before relying on it. Not legal or planning advice — confirm with your "
                "planning consultant.", False, None))
    return out


def programme_notes(data, programme):
    groups = submission_groups(programme)
    total = sum(g["fee"] for g in groups if g["fee"])
    notes = [f"{len(groups)} discharge application{'' if len(groups) == 1 else 's'} on this programme"
             + (f", about £{total:,} in council fees at the rates in force on the submit-by dates."
                if total else ".")] if groups else []
    notes += [f"Submit-by dates allow the council's statutory {DETERMINATION_WEEKS} weeks to decide plus "
             f"{programme['buffer_weeks']} weeks for validation; commission-by dates allow "
             f"{programme['prep_weeks']} weeks to prepare each submission."]
    if programme["pulled"]:
        for n, (own, new, because) in sorted(programme["pulled"].items()):
            notes.append(f"Condition #{n} has been brought forward: condition #{because} refers to it, "
                         f"so it must be cleared first.")
    saving = fee_rise_saving(data, programme)
    if saving:
        notes.append(f"Fees rise from £{saving['old']} to £{saving['new']} per application on "
                     f"{fmt_date(saving['rise_date'])}. Any application you get in before then saves "
                     f"£{saving['new'] - saving['old']}.")
    if programme["start_after_lapse"]:
        notes.append(f"WARNING: your planned start is after the permission lapses on "
                     f"{fmt_date(programme['lapse'])}.")
    if not programme["england"]:
        notes.append("The 8-week period is the English statutory period, used here as a planning "
                     "assumption for this notice's nation.")
    notes.append("A planning aid, not legal advice. Confirm your programme with your planning consultant.")
    return notes


# ----- PORTFOLIO (batch upload) -----
def build_portfolio_excel(items):
    """items: [(filename, data)]. One summary row per notice + every condition across all of them."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Portfolio"
    _header(ws, ["File", "Reference", "Site", "Council", "Document", "Decision", "Decision date",
                 "Begin by", "Conditions", "Pre-start blockers", "Need discharge",
                 "Applications", "Fees (£)", "Things to check"])
    for name, data in items:
        s = summarise(data)
        begin = (fmt_date(s["begin_by"]) if s["begin_by"] else
                 {"outline": "From reserved matters", "variation": "From original permission"}.get(
                     s["begin_by_basis"], "—"))
        ws.append([name, data.get("application_reference"), data.get("site_address"), s["council"],
                   s["document"], s["decision"], s["decision_date"], begin, s["conditions"],
                   s["blockers"], s["discharge"], s["applications"], s["fees"], s["flags"]])
        if s["begin_by"] and s["begin_by"] < date.today():
            ws.cell(row=ws.max_row, column=8).font = Font(bold=True, color="C0392B")
    _widths(ws, {"A": 30, "B": 16, "C": 40, "D": 26, "E": 22, "F": 10, "G": 16, "H": 22,
                 "I": 11, "J": 11, "K": 11, "L": 12, "M": 10, "N": 10})
    _wrap(ws, [0, 2, 3])
    ws.freeze_panes = "B2"

    wc = wb.create_sheet("All conditions")
    _header(wc, ["Reference", "#", "Summary", "Category", "Must be cleared", "Discharge?",
                 "Deadline", "Specialists"])
    for name, data in items:
        ref = data.get("application_reference") or name
        for c in sorted(data.get("conditions", []), key=lambda c: c["condition_number"]):
            wc.append([ref, c["condition_number"], c.get("summary"), c.get("category"),
                       gate_label(c), "Yes" if c.get("discharge_required") else "No",
                       c.get("deadline"), ", ".join(c.get("specialist_needed") or [])])
            wc.cell(row=wc.max_row, column=4).fill = PatternFill(
                "solid", fgColor=CATEGORY_COLOURS.get(c.get("category"), "FFFFFF"))
    _widths(wc, {"A": 16, "B": 5, "C": 60, "D": 18, "E": 22, "F": 11, "G": 16, "H": 36})
    _wrap(wc, [2, 7])
    wc.freeze_panes = "C2"
    return _save(wb)


# ----- PDF SUMMARY -----
_PDF_SUBS = {"≈": "approx.", "☐": "[ ]", "→": "->", "✓": "v", "×": "x", " ": " ", " ": " "}


def _p(text):
    """Text safe for reportlab's built-in fonts (cp1252) and its XML-ish markup."""
    s = str(text if text is not None else "")
    for a, b in _PDF_SUBS.items():
        s = s.replace(a, b)
    s = s.encode("cp1252", errors="replace").decode("cp1252")
    return escape(s)


def build_pdf(data, programme=None):
    """A short, printable summary for a site meeting or a client: the decisions, not the data."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    ink, muted, accent = colors.HexColor("#1c1a17"), colors.HexColor("#6e675c"), colors.HexColor("#2e6e4e")
    red, amber, line = colors.HexColor("#a3352c"), colors.HexColor("#8a5a14"), colors.HexColor("#e5dfd0")
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=9, leading=12.5,
                          textColor=ink, alignment=TA_LEFT)
    small = ParagraphStyle("s", parent=body, fontSize=7.8, leading=10.5, textColor=muted)
    h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=16, leading=20)
    h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                        textColor=accent, spaceBefore=10, spaceAfter=4)
    cell = ParagraphStyle("c", parent=body, fontSize=8, leading=10.5)
    cellb = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")

    def table(rows, widths, header=True):
        t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LINEBELOW", (0, 0), (-1, -1), 0.4, line),
                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                 ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1ea"))]
        t.setStyle(TableStyle(style))
        return t

    story = []
    title = notice_title(data, "Planning decision notice")
    story.append(Paragraph("PLANNING CONDITIONS — SUMMARY", small))
    story.append(Paragraph(_p(title), h1))
    meta = " · ".join(_p(x) for x in [data.get("local_authority"),
                                       (data.get("decision") or "").capitalize(),
                                       data.get("decision_date")] if x)
    story.append(Paragraph(meta, small))
    if data.get("development_description"):
        story.append(Spacer(1, 3))
        story.append(Paragraph(_p(data["development_description"]), small))
    story.append(Spacer(1, 8))

    s = summarise(data)
    msg = start_deadline_message(data)
    colour = {"expired": red, "unknown": amber}.get(msg["kind"], ink)
    facts = [
        [Paragraph("Start deadline", cellb), Paragraph(f'<font color="{colour.hexval()}">{_p(msg["text"])}</font>', cell)],
        [Paragraph("Conditions", cellb), Paragraph(f"{s['conditions']} in total — {s['blockers']} must be "
                                                   f"discharged before any work starts; {s['discharge']} need "
                                                   f"formal discharge", cell)],
    ]
    plan = build_discharge_plan(data)
    if plan["applies"] and plan["total"]:
        cost = f" — about £{plan['cost']:,} in council fees" if plan["cost"] else ""
        facts.append([Paragraph("Discharge applications", cellb),
                      Paragraph(f"approx. {plan['applications']} if bundled by stage{cost}", cell)])
    if s["flags"]:
        facts.append([Paragraph("Things to check", cellb),
                      Paragraph(f"{s['flags']} possible error(s) in the council's own notice", cell)])
    story.append(table(facts, [38 * mm, 136 * mm], header=False))

    if doc_type(data) in GATE_DOC_TYPES and data.get("conditions"):
        blockers, piling, ambiguous, startable = split_by_gate(data["conditions"])
        lines = []
        if blockers:
            lines.append((red, f"{n_conditions(len(blockers))} must be discharged before you can lawfully "
                               f"start on site: {cond_nums(blockers)}"))
        if startable:
            lines.append((accent, f"{len(startable)} only block above-ground works — demolition and "
                                  f"groundworks can start first: {cond_nums(startable)}"))
        if piling:
            lines.append((amber, f"{n_conditions(len(piling))} to clear before any piling: {cond_nums(piling)}"))
        if ambiguous:
            verb = "needs" if len(ambiguous) == 1 else "need"
            lines.append((amber, f"{n_conditions(len(ambiguous))} {verb} checking — wording is ambiguous: "
                                 f"{cond_nums(ambiguous)}"))
        if lines:
            story.append(Paragraph("Before you start on site", h2))
            for col, text in lines:
                story.append(Paragraph(f'<font color="{col.hexval()}">■</font>&nbsp; {_p(text)}', body))

    flags = get_flags(data)
    if flags:
        story.append(Paragraph("Things to check in the notice", h2))
        rows = [[Paragraph("Type", cellb), Paragraph("#", cellb), Paragraph("Detail", cellb)]]
        for f in flags:
            rows.append([Paragraph(_p(FLAG_LABEL.get(f.get("type"), "check")), cell),
                         Paragraph(_p(f.get("condition") or "—"), cell), Paragraph(_p(f["detail"]), cell)])
        story.append(table(rows, [24 * mm, 10 * mm, 140 * mm]))

    if programme and programme.get("has_dates"):
        groups = submission_groups(programme)
        if groups:
            story.append(Paragraph("Programme — work back from your dates", h2))
            rows = [[Paragraph(x, cellb) for x in ("Submit by", "Commission by", "Needed before",
                                                   "Conditions", "Fee")]]
            for g in groups:
                late = g["status"] == "late"
                sub = _p(fmt_date(g["submit_by"])) + (' <font color="#a3352c">LATE</font>' if late else "")
                rows.append([Paragraph(sub, cell), Paragraph(_p(fmt_date(g["commission_by"])), cell),
                             Paragraph(_p(g["before"]), cell), Paragraph(_p(cond_nums(g["discharge"])), cell),
                             Paragraph(_p(f"£{g['fee']}" if g["fee"] else "—"), cell)])
            story.append(table(rows, [24 * mm, 24 * mm, 56 * mm, 56 * mm, 14 * mm]))
            for n in programme_notes(data, programme):
                story.append(Paragraph(_p(n), small))

    if plan["applies"] and plan["total"]:
        story.append(Paragraph("Discharge plan", h2))
        for text, bold, colour_hex in discharge_plan_lines(plan):
            t = _p(text)
            story.append(Paragraph(f"<b>{t}</b>" if bold else t, body))

    specialists = build_specialists(data)
    if specialists:
        story.append(Paragraph("Specialists to commission", h2))
        rows = [[Paragraph("Specialist", cellb), Paragraph("Conditions", cellb)]]
        for name, nums in specialists:
            rows.append([Paragraph(_p(name), cell), Paragraph(_p(", ".join(f"#{x}" for x in nums)), cell)])
        story.append(table(rows, [70 * mm, 104 * mm]))

    if data.get("conditions"):
        story.append(Paragraph("All conditions", h2))
        rows = [[Paragraph(x, cellb) for x in ("#", "Summary", "Category", "Must be cleared", "Discharge")]]
        for c in sorted(data["conditions"], key=lambda c: c["condition_number"]):
            rows.append([Paragraph(str(c["condition_number"]), cell), Paragraph(_p(c.get("summary")), cell),
                         Paragraph(_p(c.get("category")), cell), Paragraph(_p(gate_label(c)), cell),
                         Paragraph("Yes" if c.get("discharge_required") else "—", cell)])
        story.append(table(rows, [8 * mm, 100 * mm, 26 * mm, 26 * mm, 14 * mm]))

    story.append(Spacer(1, 10))
    if doc_type(data) in CIL_DOC_TYPES:
        story.append(Paragraph(_p(CIL_TEXT), small))
    story.append(Paragraph(_p(GATE_CAVEAT + " Generated " + fmt_date(date.today()) +
                              " by the AI Planning Condition Tracker — always check against the "
                              "source notice."), small))

    buf = io.BytesIO()

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(muted)
        canvas.drawString(18 * mm, 10 * mm, _p(title)[:110].replace("&amp;", "&"))
        canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc_.page}")
        canvas.restoreState()

    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=18 * mm,
                      title=f"Planning conditions — {title}").build(
        story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
