"""AI Planning Condition Tracker — the web page.

Run locally with:   streamlit run app.py

Everything that is not the page itself lives in the ct/ package (see ct/__init__.py):
the extraction call, the rules, the programme engine, drafting, the downloads and storage.
This file only decides what to show, in what order, and wires up the buttons.
"""
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

import anthropic
import streamlit as st
from dotenv import load_dotenv

from ct import config, drafting, extract, logic, panels, programme, reports, storage
from theme.ct_theme import C, banner, inject_theme, label, note, pill, tile

load_dotenv()


def secret(name):
    """A setting from the environment (.env locally) or, on Streamlit Cloud, the app's Secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except Exception:
        return None  # no secrets.toml at all: normal when running locally


# The key is resolved up front: a missing key used to surface later as a TypeError that the
# upload handler reported as "check it's a valid PDF" — blaming the user's file for our config.
client = extract.get_client(secret("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="AI Planning Condition Tracker", page_icon="📋", layout="wide")
inject_theme()
st.markdown(panels.LAYOUT_CSS, unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("analyses", {})   # file hash -> {"name", "data"} or {"name", "error", "detail"}
ss.setdefault("drafts", {})     # draft key -> draft dict


# ----- ACCOUNTS + STORAGE (Phase 4) -----
def auth_configured():
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def current_user():
    """The signed-in user's email, lower-case — or None.

    With Google sign-in configured ([auth] in secrets) this is Streamlit's st.user. Without it, a
    developer can set CT_DEV_USER locally to try the saved-projects pages.
    """
    if auth_configured():
        try:
            if st.user.is_logged_in:
                return (st.user.get("email") or "").strip().lower() or None
        except Exception:
            return None
        return None
    dev = os.environ.get("CT_DEV_USER")
    return dev.strip().lower() if dev else None


@st.cache_resource
def get_store():
    return storage.get_store(secret)


store = get_store()
user = current_user()


def log_usage(kind, cost):
    """Record what each action cost. Never let bookkeeping break the page."""
    if not store:
        return
    try:
        store.log_usage(user or "anonymous", kind, cost)
    except Exception:
        pass


def jsonable(obj):
    """Dates -> ISO strings, recursively, so a summary can be stored as JSON."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


# ----- ERRORS -----
def friendly_error(exc):
    """(message, technical detail or None). Says whose problem it is — ours or the file's."""
    # Order matters: AuthenticationError and RateLimitError are subclasses of APIStatusError.
    if isinstance(exc, anthropic.AuthenticationError):
        return ("This app can't reach the AI service — its API key is missing or invalid. "
                "That's a problem with the app, not with your file.", None)
    if isinstance(exc, anthropic.RateLimitError):
        return ("The AI service is busy at the moment. Please wait a few seconds and try again — "
                "there's nothing wrong with your file.", None)
    if isinstance(exc, anthropic.APIStatusError):
        detail = str(getattr(exc, "message", "") or exc).lower()
        if "credit balance" in detail or "billing" in detail or "quota" in detail:
            return ("This app has run out of API credit, so it can't analyse notices right now. "
                    "That's a problem with the app, not with your file.", None)
        return ("The AI service returned an error, so this notice couldn't be analysed. That's a "
                "problem with the service, not with your file — please try again shortly.", None)
    if isinstance(exc, anthropic.APIConnectionError):
        return ("Couldn't reach the AI service — it may be a network problem. "
                "Please try again in a moment.", None)
    if isinstance(exc, extract.ExtractionError):
        if exc.kind == "truncated":
            return ("This notice was large enough to hit the response limit, even on a second "
                    "attempt with more room. Try splitting it into sections, or get in touch.", None)
        return ("Couldn't read the AI's response for this document, twice. It may be an unusual "
                "format — try another decision notice.", None)
    # A friendly message with nothing behind it is undiagnosable once deployed, so the detail
    # is kept (collapsed) for whoever has to chase it.
    return ("Something went wrong processing this file. Please check it's a valid UK planning "
            "decision notice PDF and try again.", f"{type(exc).__name__}: {exc}")


# ----- ANALYSIS (cached per file, so a click never re-runs a paid call) -----
def analyse_files(files):
    """Analyse every uploaded file not already in this session's cache. Returns entries in order.

    Every widget interaction reruns this whole script. Without the cache, pressing a download
    button or changing a date would send the notice to Claude again — 30 seconds and a fresh bill.
    """
    entries, todo = [], []
    for f in files:
        raw = f.getvalue()
        key = hashlib.sha256(raw).hexdigest()[:16]
        if key not in ss.analyses:
            if len(raw) > config.MAX_PDF_BYTES:
                ss.analyses[key] = {"name": f.name, "error": "This PDF is too large to process (over "
                                    "~24MB). Try a smaller file, or split it into sections."}
            else:
                todo.append((key, f.name, raw))
        entries.append(key)

    if todo:
        n = len(todo)
        msg = ("Reading the decision notice — usually 15–30 seconds..." if n == 1 else
               f"Reading {n} decision notices in parallel — usually under a minute...")
        with st.spinner(msg):
            def work(item):
                key, name, raw = item
                try:
                    # Development only: CT_FIXTURE_DIR points at saved analyses (eval/fixtures), so the
                    # page can be tested end to end without paying for an API call. Unset in production.
                    fixtures = os.environ.get("CT_FIXTURE_DIR")
                    if fixtures:
                        path = os.path.join(fixtures, os.path.splitext(name)[0] + ".json")
                        if os.path.exists(path):
                            import json
                            with open(path, encoding="utf-8") as fh:
                                return key, name, json.load(fh), None
                    return key, name, extract.extract(raw, client), None
                except Exception as exc:  # reported per file below; one bad file can't sink a batch
                    return key, name, None, exc
            with ThreadPoolExecutor(max_workers=min(n, config.BATCH_WORKERS)) as pool:
                results = list(pool.map(work, todo))
        for key, name, data, exc in results:
            if exc is None:
                ss.analyses[key] = {"name": name, "data": data}
                log_usage("analysis", data.get(extract.COST_KEY, 0))
            else:
                message, detail = friendly_error(exc)
                ss.analyses[key] = {"name": name, "error": message, "detail": detail}
    return [(key, ss.analyses[key]) for key in entries]


def show_error(key, entry):
    st.error(f"**{entry['name']}** — {entry['error']}")
    if entry.get("detail"):
        with st.expander("Technical detail"):
            st.code(entry["detail"])
    if st.button("Try this file again", key=f"retry_{key}"):
        ss.analyses.pop(key, None)
        st.rerun()


# ----- PROGRAMME INPUTS -----
PROGRAMME_FIELDS = [
    ("start", "Start on site", "Demolition or first works"),
    ("piling", "Start piling", "Leave blank if none / same as start"),
    ("above_ground", "Above-ground works", "Leave blank if same as start"),
    ("occupation", "First occupation", "Or first use"),
]


def programme_inputs(key, saved=None, on_change=None):
    """Four optional dates + two assumptions. Returns (dates, prep_weeks, buffer_weeks)."""
    saved = saved or {}
    cols = st.columns(4)
    dates = {}
    for col, (field, title, help_text) in zip(cols, PROGRAMME_FIELDS):
        wkey = f"{key}_{field}"
        if wkey not in ss and saved.get(field):
            ss[wkey] = logic.parse_date(saved[field])
        dates[field] = col.date_input(title, value=None, key=wkey, format="DD/MM/YYYY",
                                      help=help_text, on_change=on_change)
    with st.expander("Assumptions"):
        a, b = st.columns(2)
        pkey, bkey = f"{key}_prep", f"{key}_buffer"
        if pkey not in ss:
            ss[pkey] = int(saved.get("prep_weeks") or programme.DEFAULT_PREP_WEEKS)
        if bkey not in ss:
            ss[bkey] = int(saved.get("buffer_weeks") or programme.DEFAULT_BUFFER_WEEKS)
        prep = a.number_input("Weeks to prepare each submission", 1, 52, key=pkey,
                              on_change=on_change)
        buffer = b.number_input("Extra weeks for council validation", 0, 12, key=bkey,
                                on_change=on_change)
        st.caption(f"The council's statutory {programme.DETERMINATION_WEEKS} weeks to decide is "
                   f"always added on top.")
    return dates, int(prep), int(buffer)


# ----- DRAFTING (on demand — each draft is a paid call) -----
def drafting_section(key, data, prog):
    plan = logic.build_discharge_plan(data)
    if not plan["applies"] or not plan["total"]:
        return
    if prog["has_dates"]:
        groups = [(g["submit_by"].isoformat(), f"Submit by {logic.fmt_date(g['submit_by'])}",
                   g["discharge"], g["fee"]) for g in programme.submission_groups(prog)]
    else:
        groups = [(stage, stage, members, plan["fee"]) for stage, members in plan["batches"]]
    if not groups:
        return
    fee_note = ("No fee is payable for applications to discharge conditions on a listed building "
                "consent." if logic.doc_type(data) == "listed-building-consent" else None)

    st.markdown(panels.section_label("DRAFT THE DISCHARGE APPLICATIONS"), unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ct-line-txt">One click writes the covering letter and, for each '
                    'condition, what to submit, who prepares it and what it must cover — taken '
                    'from the council\'s own wording. Anything only you know is left as a '
                    '<b>[PLACEHOLDER]</b>.</div>', unsafe_allow_html=True)
        for gid, title, members, fee in groups:
            nums = ",".join(str(c["condition_number"]) for c in members)
            dkey = f"{key}|{gid}|{nums}"
            left, right = st.columns([4, 1])
            left.markdown(f'<div class="ct-line"><div class="ct-kv"><span class="ct-kv-k">'
                          f'{panels.esc(title)}</span>{pill(logic.n_conditions(len(members)), "submitted")}'
                          f'<span class="ct-nums" style="margin-top:0">{logic.cond_nums(members)}</span>'
                          f'</div></div>', unsafe_allow_html=True)
            if dkey not in ss.drafts:
                if right.button("Draft application", key=f"draft_{dkey}", width="stretch"):
                    if client is None:
                        st.error("This app isn't configured with an API key, so it can't draft.")
                    else:
                        with st.spinner(f"Drafting the application for {logic.n_conditions(len(members))}"
                                        f" — usually 20–60 seconds..."):
                            try:
                                d = drafting.draft_application(client, data, members, title, fee, fee_note)
                                ss.drafts[dkey] = d
                                log_usage("draft", d.get("_cost_usd", 0))
                                st.rerun()
                            except Exception as exc:
                                st.error(friendly_error(exc)[0])
            draft = ss.drafts.get(dkey)
            if draft:
                checks = draft.get("_checks") or {}
                with st.expander(f"Draft ready — {title}", expanded=True):
                    if checks.get("missing"):
                        st.warning("The draft skipped condition(s) "
                                   + ", ".join(f"#{n}" for n in checks["missing"])
                                   + " — add them by hand or draft again.")
                    if checks.get("unverified_references"):
                        st.warning("Check these references — they are not in the notice: "
                                   + ", ".join(checks["unverified_references"]))
                    if draft.get("subject"):
                        st.markdown(f"**{draft['subject']}**")
                    st.markdown(f'<div class="ct-letter">{panels.esc(drafting.letter_text(draft))}</div>',
                                unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 1])
                    c1.download_button(
                        "Download as Word  ↓", drafting.build_docx(data, draft),
                        file_name=f"discharge-application-{gid[:20].replace(' ', '-')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"docx_{dkey}", on_click="ignore", type="primary")
                    if c2.button("Draft again", key=f"redraft_{dkey}"):
                        ss.drafts.pop(dkey, None)
                        st.rerun()
                    st.caption("The Word file adds a checklist per condition: documents, who "
                               "prepares them, and every matter the condition says to cover. "
                               "A draft — check it and fill every placeholder before you submit.")


# ----- ONE NOTICE -----
def render_notice(key, name, data, project=None):
    """Everything for one analysed notice. With `project`, programme dates are saved as you type."""
    conditions = data.get("conditions", [])
    decision = (data.get("decision") or "").upper()
    tracker = project["tracker"] if project else None

    title = logic.notice_title(data, name)
    if project is None:
        st.markdown(f'<div class="ct-quiet" style="margin:var(--ct-s5) 0 var(--ct-s2)">'
                    f'{panels.esc(title)}</div>', unsafe_allow_html=True)

    if not conditions:
        st.info(f"**{decision}** — no planning conditions found. This may be a refusal or a "
                f"document without conditions.")
        return

    total = len(conditions)
    discharge = sum(1 for c in conditions if c.get("discharge_required"))
    precom = sum(1 for c in conditions if c.get("category") == "pre-commencement")
    st.markdown(banner(f"{decision} — {total} planning conditions extracted from this notice",
                       f"{discharge} need discharge"), unsafe_allow_html=True)
    st.markdown('<div style="height:var(--ct-s4)"></div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    for col, value, text, dot, danger in [
        (s1, total, "Total conditions", C["submitted"], False),
        (s2, precom, "Pre-commencement", C["overdue"], True),
        (s3, discharge, "Need discharge", C["action"], False),
    ]:
        col.markdown(tile(text, value, dot=dot, danger=danger), unsafe_allow_html=True)
    st.write("")

    for html in (panels.build_safety_gate_html(data), panels.build_flags_html(data)):
        if html:
            st.markdown(html, unsafe_allow_html=True)

    st.markdown(panels.section_label("EXTRACTED CONDITIONS"), unsafe_allow_html=True)
    st.markdown(panels.build_conditions_table_html(data, tracker), unsafe_allow_html=True)
    st.markdown(note(
        "This notice is a scan with no text layer, so the original clauses were read from the image "
        "rather than copied — treat them as a transcription and check anything you rely on against "
        "the source notice." if logic.from_scan(data) else
        "Original clauses are shown for verification. If a quote ever looks off, the source notice "
        "is always the final word."), unsafe_allow_html=True)

    plan_html = panels.build_discharge_plan_html(data)
    if plan_html:
        st.markdown('<div style="height:var(--ct-s5)"></div>', unsafe_allow_html=True)
        st.markdown(plan_html, unsafe_allow_html=True)

    # ----- programme: order of work + deadlines -----
    prog = programme.build_programme(data)
    if prog["steps"]:
        st.markdown(panels.section_label("YOUR PROGRAMME"), unsafe_allow_html=True)
        st.markdown('<div class="ct-line-txt" style="margin-bottom:var(--ct-s3)">Add your planned '
                    'dates and the tool works back to when each discharge application must go in, '
                    'and when to commission each consultant.</div>', unsafe_allow_html=True)

        def save_programme():
            if not project:
                return
            pd = {f: ss.get(f"{key}_{f}") for f, _, _ in PROGRAMME_FIELDS}
            pd = {k: v.isoformat() for k, v in pd.items() if v}
            pd["prep_weeks"] = ss.get(f"{key}_prep")
            pd["buffer_weeks"] = ss.get(f"{key}_buffer")
            try:
                store.update_project(user, project["id"], programme=pd)
            except Exception:
                st.toast("Couldn't save your dates just now.")

        dates, prep, buffer = programme_inputs(key, project["programme"] if project else None,
                                               on_change=save_programme if project else None)
        prog = programme.build_programme(data, dates, prep, buffer)
        st.markdown(panels.build_programme_html(data, prog), unsafe_allow_html=True)

    drafting_section(key, data, prog)

    spec_html = panels.build_specialists_html(data)
    if spec_html:
        st.markdown('<div style="height:var(--ct-s4)"></div>', unsafe_allow_html=True)
        st.markdown(spec_html, unsafe_allow_html=True)

    # ----- downloads -----
    st.markdown(panels.section_label("DOWNLOAD"), unsafe_allow_html=True)
    stem = (data.get("application_reference") or "planning").replace("/", "-")
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("Excel tracker  ↓", reports.build_excel(data, prog, tracker),
                       file_name=f"{stem}-condition-tracker.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", key=f"xlsx_{key}", on_click="ignore", width="stretch")
    d2.download_button("PDF summary  ↓", reports.build_pdf(data, prog),
                       file_name=f"{stem}-summary.pdf", mime="application/pdf",
                       key=f"pdf_{key}", on_click="ignore", width="stretch")
    if prog["lapse"] or prog["has_dates"] or programme.dated_condition_deadlines(data):
        d3.download_button("Calendar (.ics)  ↓", programme.build_ics(data, prog),
                           file_name=f"{stem}-deadlines.ics", mime="text/calendar",
                           key=f"ics_{key}", on_click="ignore", width="stretch",
                           help="Imports into Outlook, Google Calendar or Apple Calendar: the "
                                "permission lapse date and, once you add dates, every submit-by "
                                "and commission-by deadline.")
    if project is None:
        save_button(d4, key, name, data)


def save_button(col, key, name, data):
    if not store:
        return
    if not user:
        if auth_configured():
            col.button("Sign in to save", key=f"signin_{key}", on_click=st.login,
                       width="stretch")
        return
    saved = ss.setdefault("saved", {})
    if key in saved:
        col.button("Saved to My projects ✓", key=f"saved_{key}", disabled=True, width="stretch")
        return
    if col.button("Save to My projects", key=f"save_{key}", width="stretch"):
        pd = {f: ss.get(f"{key}_{f}") for f, _, _ in PROGRAMME_FIELDS}
        pd = {k: v.isoformat() for k, v in pd.items() if v}
        try:
            saved[key] = store.create_project(user, logic.notice_title(data, name), data,
                                              jsonable(logic.summarise(data)), pd)
            st.toast("Saved. Open it from My projects to track each condition.")
            st.rerun()
        except Exception as exc:
            st.error(f"Couldn't save this project: {exc}")


# ----- PAGE: ANALYSE -----
def page_analyse():
    st.markdown(
        f'{label("AI PLANNING CONDITION TRACKER")}'
        f'<h1 class="ct-h1" style="margin:10px 0 12px">Planning conditions, tracked in seconds.</h1>'
        f'<p class="ct-body" style="max-width:660px;margin:0">A second pair of eyes on your planning '
        f'conditions. Upload a UK decision notice and get every condition read and categorised, what '
        f'stops you starting on site, when each discharge application must go in — and a first draft '
        f'of each application.</p>',
        unsafe_allow_html=True)

    st.markdown(panels.section_label("HOW IT WORKS", "var(--ct-s6)"), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, num, title, text in [
        (c1, "01", "Upload", "Drop in one decision notice — or a batch of them"),
        (c2, "02", "Analyse", "AI reads &amp; categorises every condition, then plans the order of work"),
        (c3, "03", "Act", "Draft the discharge applications, export the tracker, add the deadlines to your calendar"),
    ]:
        col.markdown(
            f'<div class="ct-card" style="height:100%;padding:18px 20px">'
            f'<div class="ct-step-n">{num}</div>'
            f'<div style="font:600 17px/1.3 var(--ct-font-display);color:var(--ct-ink);'
            f'margin:9px 0 5px">{title}</div>'
            f'<div class="ct-muted">{text}</div></div>', unsafe_allow_html=True)

    st.markdown(panels.section_label("UPLOAD DECISION NOTICES", "var(--ct-s6)"), unsafe_allow_html=True)
    files = st.file_uploader("Choose PDFs", type="pdf", accept_multiple_files=True,
                             label_visibility="collapsed")
    if not files:
        return
    if client is None and not os.environ.get("CT_FIXTURE_DIR"):
        st.error("This app isn't configured with an API key, so it can't analyse notices right now. "
                 "That's a problem with the app, not with your file — the ANTHROPIC_API_KEY secret "
                 "is missing.")
        return
    if len(files) > config.BATCH_MAX_FILES:
        st.warning(f"Up to {config.BATCH_MAX_FILES} notices at a time — analysing the first "
                   f"{config.BATCH_MAX_FILES}.")
        files = files[:config.BATCH_MAX_FILES]

    entries = analyse_files(files)
    good = [(k, e) for k, e in entries if "data" in e]
    for k, e in entries:
        if "error" in e:
            show_error(k, e)
    if not good:
        return

    if len(good) == 1:
        key, e = good[0]
        render_notice(key, e["name"], e["data"])
        return

    # ----- PORTFOLIO (batch upload) -----
    st.markdown(panels.section_label(f"PORTFOLIO — {len(good)} NOTICES"), unsafe_allow_html=True)
    rows = [{"name": logic.notice_title(e["data"], e["name"]), "summary": logic.summarise(e["data"])}
            for _, e in good]
    st.markdown(panels.build_portfolio_html(rows), unsafe_allow_html=True)
    total_blockers = sum(r["summary"]["blockers"] for r in rows)
    total_fees = sum(r["summary"]["fees"] or 0 for r in rows)
    st.markdown(note(f"Across these notices: <b>{total_blockers}</b> conditions block a start on site, "
                     f"and about <b>£{total_fees:,}</b> in discharge fees if each notice's conditions "
                     f"are bundled by stage."), unsafe_allow_html=True)
    st.download_button("Portfolio workbook  ↓",
                       reports.build_portfolio_excel([(e["name"], e["data"]) for _, e in good]),
                       file_name="planning-portfolio.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", on_click="ignore")

    names = {k: logic.notice_title(e["data"], e["name"]) for k, e in good}
    pick = st.selectbox("Open one notice in full", list(names), format_func=names.get)
    e = dict(good)[pick]
    render_notice(pick, e["name"], e["data"])


# ----- PAGE: MY PROJECTS (the living tracker) -----
STATUS_LABELS = {k: v for k, v in reports.STATUS_LABEL.items()}
LABEL_TO_STATUS = {v: k for k, v in STATUS_LABELS.items()}


def next_deadline(project):
    analysis = project.get("analysis")
    if not analysis:
        return None
    prog = programme.build_programme(analysis, project.get("programme") or {},
                                     int((project.get("programme") or {}).get("prep_weeks") or 6),
                                     int((project.get("programme") or {}).get("buffer_weeks") or 2))
    tracker = project.get("tracker") or {}
    for g in programme.submission_groups(prog):
        open_ = [c for c in g["discharge"]
                 if (tracker.get(str(c["condition_number"])) or {}).get("status")
                 not in ("submitted",) + storage.DONE_STATUSES]
        if open_:
            return g["submit_by"]
    return None


def page_projects():
    st.markdown(f'{label("MY PROJECTS")}<h1 class="ct-h1" style="margin:10px 0 12px">'
                f'Every permission, every condition, in one place.</h1>', unsafe_allow_html=True)
    try:
        projects = store.list_projects(user)
    except Exception as exc:
        st.error(f"Couldn't load your projects: {exc}")
        return
    if not projects:
        st.info("No saved projects yet. Analyse a notice, then press **Save to My projects**.")
        return

    # Portfolio overview — the full analysis is only loaded for the project you open.
    today = date.today()
    rows_html = ""
    for p in projects:
        s = p.get("summary") or {}
        tracker = p.get("tracker") or {}
        begin = logic.parse_date(s.get("begin_by"))
        done = sum(1 for t in tracker.values() if (t or {}).get("status") in storage.DONE_STATUSES)
        submitted = sum(1 for t in tracker.values() if (t or {}).get("status") == "submitted")
        begin_html = (f'<span style="color:var(--ct-overdue);font-weight:700">{logic.fmt_date(begin)}'
                      f'</span>' if begin and begin < today else logic.fmt_date(begin) if begin else "—")
        rows_html += (f'<tr><td>{panels.esc(p["name"])}<div class="ct-quiet" style="margin-top:4px">'
                      f'{panels.esc(s.get("council") or "")}</div></td>'
                      f'<td class="sec">{begin_html}</td>'
                      f'<td class="num">{s.get("conditions", "—")}</td>'
                      f'<td class="num">{done}</td><td class="num">{submitted}</td>'
                      f'<td class="sec">{panels.esc(str(p.get("updated_at", ""))[:10])}</td></tr>')
    st.markdown('<div class="ct-card" style="overflow-x:auto"><table class="ct-tbl compact"><thead><tr>'
                '<th>Project</th><th>Begin by</th><th>Conditions</th><th>Done</th><th>With council</th>'
                f'<th>Updated</th></tr></thead><tbody>{rows_html}</tbody></table></div>',
                unsafe_allow_html=True)

    names = {p["id"]: p["name"] for p in projects}
    pid = st.selectbox("Open a project", list(names), format_func=names.get,
                       index=list(names).index(ss.get("open_project")) if ss.get("open_project") in names else 0)
    ss.open_project = pid
    try:
        project = store.get_project(user, pid)
    except Exception as exc:
        st.error(f"Couldn't open this project: {exc}")
        return
    if not project:
        st.warning("That project no longer exists.")
        return
    render_project(project)


def render_project(project):
    data, tracker = project["analysis"], project.get("tracker") or {}
    today = date.today()

    st.markdown(f'<h2 class="ct-h2" style="margin:var(--ct-s5) 0 4px">{panels.esc(project["name"])}</h2>'
                f'<div class="ct-quiet">{panels.esc(data.get("local_authority") or "")} · '
                f'{panels.esc(data.get("development_description") or "")[:180]}</div>',
                unsafe_allow_html=True)

    done, total = storage.tracker_progress(data, tracker)
    blockers = storage.outstanding_blockers(data, tracker)
    england = logic.jurisdiction(data) == "england"
    deemed = storage.deemed_discharge_candidates(data, tracker, today, england)
    parts = ['<div class="ct-card ct-panel" style="margin-top:var(--ct-s4)">',
             '<div class="ct-panel-hd">', label("PROGRESS"), '</div>', panels.progress_html(done, total)]
    if blockers:
        parts.append(f'<div class="ct-line" style="margin-top:var(--ct-s3)">'
                     f'{pill(f"{logic.n_conditions(len(blockers))} still stop you starting on site", "overdue")}'
                     f'<div class="ct-nums">{logic.cond_nums(blockers)}</div></div>')
    elif logic.doc_type(data) in logic.GATE_DOC_TYPES:
        parts.append(f'<div class="ct-line" style="margin-top:var(--ct-s3)">'
                     f'{pill("Every pre-start blocker is discharged", "discharged")}</div>')
    for c, weeks in deemed:
        parts.append(f'<div class="ct-line">{pill("Deemed discharge?", "action")} '
                     f'<span class="ct-line-txt">Condition #{c["condition_number"]} was submitted '
                     f'{weeks} weeks ago with no decision recorded. Unless you agreed a longer period '
                     f'or it is an excluded type, you may be able to serve a deemed discharge notice. '
                     f'Check with your planning consultant first.</span></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

    # ----- the living tracker -----
    st.markdown(panels.section_label("TRACK EACH CONDITION"), unsafe_allow_html=True)
    rows = []
    for c in sorted(data.get("conditions", []), key=lambda c: c["condition_number"]):
        t = tracker.get(str(c["condition_number"])) or {}
        rows.append({
            "#": c["condition_number"], "Condition": c.get("summary"),
            "Must be cleared": logic.gate_label(c),
            "Discharge": "Yes" if c.get("discharge_required") else "—",
            "Status": STATUS_LABELS.get(t.get("status") or "not-started"),
            "Submitted": logic.parse_date(t.get("submitted")),
            "Approved": logic.parse_date(t.get("approved")),
            "Council ref": t.get("reference") or "",
            "Notes": t.get("notes") or "",
        })
    edited = st.data_editor(
        rows, key=f"tracker_{project['id']}", hide_index=True, width="stretch",
        disabled=["#", "Condition", "Must be cleared", "Discharge"],
        column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "Condition": st.column_config.TextColumn(width="large"),
            "Status": st.column_config.SelectboxColumn(options=list(STATUS_LABELS.values()),
                                                       required=True),
            "Submitted": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Approved": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Council ref": st.column_config.TextColumn(help="The discharge application's reference"),
        })
    if st.button("Save tracker", type="primary", key=f"save_tracker_{project['id']}"):
        new = {}
        for r in edited:
            entry = {"status": LABEL_TO_STATUS.get(r.get("Status"), "not-started"),
                     "submitted": r["Submitted"].isoformat() if r.get("Submitted") else None,
                     "approved": r["Approved"].isoformat() if r.get("Approved") else None,
                     "reference": r.get("Council ref") or None, "notes": r.get("Notes") or None}
            if any(v for k, v in entry.items() if k != "status") or entry["status"] != "not-started":
                new[str(r["#"])] = entry
        try:
            store.update_project(user, project["id"], tracker=new)
            st.toast("Tracker saved.")
            st.rerun()
        except Exception as exc:
            st.error(f"Couldn't save: {exc}")

    render_notice(f"project:{project['id']}", project["name"], data, project=project)

    with st.expander("Rename or delete this project"):
        new_name = st.text_input("Project name", value=project["name"], key=f"name_{project['id']}")
        if st.button("Rename", key=f"rename_{project['id']}") and new_name.strip():
            store.update_project(user, project["id"], name=new_name.strip())
            st.rerun()
        sure = st.checkbox("I want to delete this project permanently", key=f"sure_{project['id']}")
        if st.button("Delete project", key=f"delete_{project['id']}", disabled=not sure):
            store.delete_project(user, project["id"])
            ss.pop("open_project", None)
            st.rerun()


# ----- NAVIGATION -----
# The sidebar only appears once saved projects are switched on (a store is configured), so the
# public page looks exactly as it did until then.
page = "analyse"
if store:
    with st.sidebar:
        st.markdown(f'{label("CONDITION TRACKER")}', unsafe_allow_html=True)
        if user:
            choice = st.radio("Go to", ["Analyse notices", "My projects"], key="nav",
                              label_visibility="collapsed")
            page = "projects" if choice == "My projects" else "analyse"
            st.caption(f"Signed in as {user}")
            try:
                month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0,
                                                                 microsecond=0).isoformat()
                used = store.usage_count(user, "analysis", month_start)
                st.caption(f"{used} notice{'' if used == 1 else 's'} analysed this month")
            except Exception:
                pass
            if auth_configured():
                st.button("Sign out", on_click=st.logout)
        elif auth_configured():
            st.caption("Sign in to save projects, track each condition's discharge and keep "
                       "your deadlines in one place.")
            st.button("Sign in with Google", on_click=st.login, type="primary")

if page == "projects" and store and user:
    page_projects()
else:
    page_analyse()

# ----- FOOTER -----
st.markdown(
    '<hr style="margin:var(--ct-s6) 0 var(--ct-s4)">'
    + note('Built by Zak Akhtar · <a href="https://github.com/akhtarzakariya8-a11y/planning-condition-tracker">GitHub</a>')
    + note("A tool for UK planning decision notices. Always check outputs against the source "
           "document. Drafts and dates are planning aids, not legal advice."),
    unsafe_allow_html=True,
)
