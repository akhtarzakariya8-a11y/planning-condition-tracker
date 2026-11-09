# CLAUDE.md — AI Planning Condition Tracker

Project context for Claude Code. Read this first every session. **Last updated: 4 Nov 2026.**

## What this is
A Streamlit web app that reads UK planning **decision notices** (PDFs), extracts every condition, and turns them into decisions: what stops you starting on site, how many discharge applications to make and what they cost, when each must go in, who to hire, a first draft of each application, and a tracker that stays up to date. Live on Streamlit Community Cloud; repo `akhtarzakariya8-a11y/planning-condition-tracker`. Also exposed to AI assistants as an MCP server (`mcp_server/`).

## The developer
Zak — final-year Quantity Surveying student, **beginner coder who leans on AI to write the code**. Wants concise, direct, honest help in plain terms. Goal: turn this into a paid product (~£50k/yr).

## Architecture
```
prompt_v4_production.txt   the extraction "brain" — all reading/classification rules live here
prompt_drafting.txt        second prompt: drafts one discharge application (letter + checklists)
app.py                     the web page ONLY: layout, buttons, session cache, pages
ct/                        everything else — shared by app.py, eval/ and mcp_server/
  config.py                model, token budgets, prices, batch limits
  extract.py               PDF → text (or vision for scans) → Claude → JSON, retries, cost
  logic.py                 the rules: gates, start deadline, fees (date-aware), discharge plan,
                           flags/duplicates, specialists, summaries, labels
  programme.py             sequencing, deadline engine, .ics calendar export
  drafting.py              drafting call + invented-reference check + Word export
  reports.py               Excel tracker, PDF summary, portfolio workbook
  panels.py                the HTML panels + page CSS
  storage.py               saved projects / living tracker (Supabase, or local file in dev)
mcp_server/server.py       MCP tools for Claude Desktop/Code (imports ct/)
eval/run_eval.py           scores the prompt against eval/answer_key.json (real API calls)
eval/fixtures/*.json       saved real extractions of the test notices (used by tests + dev)
tests/test_core.py         fast tests of the rules — no API calls
supabase/schema.sql        run once in Supabase to create the tables
```
**Rule of thumb:** reading the notice = prompt. Comparing, counting, dates and money = code (deterministic, testable). E.g. duplicates and cross-references between conditions are computed in code, not asked of the model.

## Run / test / deploy
- Run: **`streamlit run app.py`** (never `python3 app.py`).
- Fast tests (free): `python3 -m pytest tests/ -q`
- Model accuracy (costs ~$0.50 for all 7 notices): `python3 eval/run_eval.py --jobs 7` (add `--save eval/fixtures` to refresh fixtures).
- Test the page without API calls: `CT_FIXTURE_DIR=eval/fixtures streamlit run app.py` and upload a test PDF.
- Try saved projects locally: `CT_LOCAL_STORE=1 CT_DEV_USER=you@example.com streamlit run app.py`.
- Secrets: `.env` locally, Streamlit Cloud → Settings → Secrets in production. See `.streamlit/secrets.toml.example`. `.env` and `secrets.toml` are git-ignored — never commit keys.
- Deploy: push to `main`; Streamlit Cloud rebuilds automatically.

## Build conventions (every feature)
1. **Prompt first** if the model must read something new. **Code** if it's maths/comparison.
2. **Validate** on real notices: `eval/run_eval.py`; add the new field to `answer_key.json`.
3. **Code** in `ct/` → panel in `ct/panels.py` → wire into `app.py` → add to Excel/PDF.
4. **Test**: `pytest`, then the page with fixtures, then 2–3 real notices.
5. **Ship**: commit + push; confirm live.

Other rules: keep every legal caveat; **verify any hard-coded fact** (fees, statutory periods) and cite the source in a comment; secrets never in code or git.

## Data shape (extraction JSON)
Top level: `document_type` (full-grant | listed-building-consent | discharge-approval | refusal | appeal-decision | other), `jurisdiction` (england | wales | scotland | northern-ireland | null), `is_householder`, `permission_type` (full | outline | reserved-matters | variation | null), `local_authority`, `application_reference`, `site_address`, `applicant`, `development_description`, `decision`, `decision_date`, `time_limit_years`, `flags[]`, `conditions[]`.
Each condition: `condition_number`, `summary`, `category` (pre-commencement | pre-occupation | ongoing | discharge-required | time-limit), `deadline`, `responsible_party`, `discharge_required` (true only for "submitted to AND approved by"), `gate`, `trigger_quote`, `gate_ambiguous`, `specialist_needed[]`, `source_quote` (verbatim operative wording).
Added locally (never by the model): `_from_scan`, `_usage`, `_cost_usd`.

`gate` values: `blocks-any-commencement`, `blocks-demolition`, `blocks-piling`, `blocks-above-ground`, `before-occupation`, `before-use`, `ongoing`, `none`. `gate_ambiguous` = wording and Reason disagree → gate set to the stricter trigger.

## Key facts in code (verify before changing)
- **Fees** (`ct/logic.py FEE_SCHEDULE`): England £309 / £89 householder from 1 Apr 2026, **£435 / £125 from 8 Dec 2026** (switches automatically). Wales £242 / £123. Per application, not per condition. LBC discharge is free. Scotland/NI not priced.
- **Start deadline** (`logic.start_deadline`): computed from decision date for full permissions; a date stated in the time-limit condition wins; **outline / reserved-matters and s73 variations are NOT computed** (they run from other dates).
- **Programme** (`ct/programme.py`): submit-by = milestone − (8 weeks statutory + 2 validation); commission-by = submit-by − 6 weeks prep. Deemed discharge shown for England only.

## Current state (4 Nov 2026)
Built and tested: extraction v4 + notice details, Safety Gate, Consistency Checker + duplicates, Source-Clause View, Discharge Planner, Consultant Scoping, **Sequencing + deadline engine + .ics**, **Auto-drafted submissions (.docx)**, **PDF summary**, **batch upload + portfolio**, **outline/s73 start-deadline safety**, **saved projects + living tracker + sign-in (Phase 4)**, MCP server (7 tools).
Eval: 45/45 on 7 notices. Cost per notice ≈ $0.02–0.20 (Sonnet 4.5); a draft ≈ $0.02–0.13.

**Phase 4 goes live only when these secrets are set** (the sidebar stays hidden until then): `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (after running `supabase/schema.sql`), and an `[auth]` block for Google sign-in.

## Next (in order)
1. Switch on Phase 4 in production (Supabase + Google secrets).
2. **Payments**: Stripe + a free-tier limit using `store.usage_count()`; landing page + pricing.
3. Privacy policy + terms (users upload client documents).
4. Try a newer Sonnet model through `eval/run_eval.py` (accuracy and cost).
5. Persist drafts in saved projects; email reminders for deadlines.

## Test notices (repo root)
`21_04939_FUL--3474437.pdf` Lambeth, 38 conditions (main case: blockers, piling, above-ground, ambiguous #13/#33, a typo, a duplicate) · `24_3095_F…` Greenwich, large · `26_01199_FUL…` householder (1 discharge) · `26_01232_FUL…` · `26_01309_FUL…` refusal · `25_AP_3061…` Southwark LBC · `25_01905_DISC…` Croydon discharge approval.

## Golden rule
One feature at a time: prompt-first (or code-first for maths) → validate on real notices → ship small.

## Team lanes and limits
An agent team works on this repo on a schedule (see `team/RUNBOOK.md`; agents in `.claude/agents/`). The team finishes every ticket end to end; the lane only decides who presses merge. The lane is set by the files a change touches. If any touched path is AMBER, the whole change is AMBER. If unsure, AMBER.

| Lane | What is in it | What the team does |
| --- | --- | --- |
| GREEN: ships itself | `site/`, `theme/`, `tests/`, `README.md` and docs, `team/LESSONS.md`, `team/PLAYBOOK.md`, `team/EVIDENCE.md`, the "Updates" section of `team/MARKET.md`; layout and wording in `app.py`, `ct/panels.py` and `ct/reports.py` that change no rule, number or caveat | Opens the pull request, waits for CI, merges, confirms `main` is green |
| AMBER: built, then parked | `prompt_*.txt`, `ct/logic.py`, `ct/programme.py`, `ct/extract.py`, `ct/drafting.py`, `ct/config.py`, `ct/storage.py`, `supabase/`, `mcp_server/`, `eval/`, `requirements.txt`, `.streamlit/`, `.github/`; sign-in, payments, pricing, user data; privacy policy and terms; any file deletion; any new dependency, plugin or tool | Builds and tests it fully, opens the pull request labelled `needs-zak` with one sentence on what Zak is deciding, then moves on |
| RED: only Zak | Keys and secrets; creating accounts (Supabase, Google sign-in, Stripe, domain, email provider); spending money; sending messages to real people; publishing legal pages; setting prices | Writes the exact step under "Waiting on Zak" in `team/BACKLOG.md` and prepares everything around it |

- While `team/BACKLOG.md` says `autonomy: calibration`, GREEN is treated as AMBER.
- With three `needs-zak` pull requests open, the team works GREEN only.
- Off-limits to agents: `.claude/`, `team/RUNBOOK.md` and this section. Changes to them come as AMBER pull requests.
- The hard limits at the top of `team/RUNBOOK.md` apply to every agent in every run.
