# CLAUDE.md — AI Planning Condition Tracker

Project context for Claude Code. Read this first every session.

## What this is
A Streamlit web app that reads UK planning permission **decision notices** (PDFs), extracts every planning condition, categorises them, flags which ones legally block starting on site, and outputs a colour-coded Excel tracker + an on-screen table. Live on Streamlit Community Cloud; repo: `akhtarzakariya8-a11y/planning-condition-tracker`.

## The developer
Zak — final-year Quantity Surveying student, **beginner coder who leans on AI to write the code**. Wants concise, direct, honest help. Explain what you're doing in plain terms. Don't assume deep programming knowledge.

## Architecture — two files do everything
- **`prompt_v4_production.txt`** — the system prompt sent to Claude. This is the "brain": all extraction and classification logic lives here, NOT in Python.
- **`app.py`** — Streamlit UI + logic: upload, API call, JSON parsing, the Safety Gate panel, the conditions table, and Excel generation.

`app.py` reads the prompt file at startup: `with open("prompt_v4_production.txt") as f: system_prompt = f.read()`.

## Tech stack
Python · `streamlit` · `anthropic` (model `claude-sonnet-4-5`, `max_tokens=8000`) · `pdfplumber` (digital text) · base64 + Claude vision (OCR fallback for scanned PDFs) · `openpyxl` (Excel) · `python-dotenv`.

## How to run / test / deploy
- Run locally: **`streamlit run app.py`** (never `python3 app.py`).
- API key: local in a `.env` file as `ANTHROPIC_API_KEY=...`; on Streamlit Cloud it's in the app's Secrets. **`.env` must be in `.gitignore` and never committed.**
- Deploy: push to GitHub `main`; Streamlit Cloud auto-rebuilds.

## Build conventions (follow this loop for every feature)
1. **Prompt first** — add/change fields in `prompt_v4_production.txt`.
2. **Validate** — run a real notice through a normal Claude chat and check against a hand-made answer key BEFORE writing code.
3. **Code** — `app.py`: helper → render on screen → add to Excel.
4. **Test** — `streamlit run app.py` on 2–3 real notices.
5. **Ship** — commit + push; confirm live.

Other rules: keep the legal caveats in the Safety Gate; verify any hard-coded fact (e.g. council fees) before shipping; secrets never in code or git.

## Data shape (JSON the prompt returns)
```
{
  "decision": "granted" | "refused",
  "decision_date": "10 November 2025" | null,
  "time_limit_years": 3 | null,
  "conditions": [
    {
      "condition_number": 1,
      "summary": "one-line plain English",
      "category": "time-limit",              // one of: pre-commencement, pre-occupation, ongoing, discharge-required, time-limit
      "deadline": "15 June 2029" | null,
      "responsible_party": "applicant" | null,
      "discharge_required": true | false,     // true only if "submitted to AND approved by" the authority
      "gate": "blocks-any-commencement",      // see gate values below
      "trigger_quote": "No development shall commence until…" | null,
      "gate_ambiguous": true | false
    }
  ]
}
```

### `gate` values (WHEN a condition must be satisfied, from operative wording)
- `blocks-any-commencement` — can't turn a spade at all until discharged (Whitley true condition-precedent).
- `blocks-demolition` — bites before demolition.
- `blocks-piling` — bites before piling.
- `blocks-above-ground` — only blocks above-ground works; demolition/groundworks CAN start.
- `before-occupation`, `before-use`, `ongoing`, `none`.

`gate_ambiguous` = true when the operative wording and the stated Reason disagree (e.g. wording says "above ground works" but the Reason says "development must not commence") — then set `gate` to the stricter trigger.

## Key functions in app.py
`strip_fences`, `sort_by_category`, `gate_label`, `compute_begin_by`, `fmt_date`, `build_safety_gate_html`, `build_excel`, `category_pill`.

## The Safety Gate (v3 — the headline feature)
`build_safety_gate_html(data)` renders a "Before you start on site" panel:
- **Begin-by date** = `compute_begin_by(decision_date, time_limit_years)` (Python date maths, not the model).
- **Hard blockers** = conditions with gate `blocks-any-commencement`/`blocks-demolition`.
- **Before any piling** = `blocks-piling`.
- **Check these (ambiguous)** = `gate_ambiguous == true`.
- **Green "You can break ground before these"** = `blocks-above-ground` (class `gate-go`). This is the key differentiator: it separates "can't start at all" from "only blocks above-ground works."
- **CIL reminder** + **legal caveat** (must stay).

Excel has two sheets: `Conditions` (#, Summary, Category, Deadline, Responsible, Discharge) and `Before you start` (mirrors the panel).

## CURRENT STATE — read carefully
- **v2 is live** (category grouping, approved-plans list, OCR, size guard, positioning).
- **Safety Gate + green "what you can start" section are built** in the latest `app.py`, but the folder may still contain an OLDER copy.
- **Verify first:** search `app.py` for `gate-go`. If it's MISSING, the file is stale — get the current version before making changes.
- **Immediate task:** confirm `app.py` is current, run the Lambeth notice, check: condition 13 flags ambiguous, the green block lists ~8 above-ground conditions, Excel has 2 tabs. Then commit + push.

## Test notices (in the folder)
- **`21_04939_FUL--3474437.pdf`** — Lambeth, 38 conditions, decision 10 Nov 2025. The main test case (has hard blockers, piling, above-ground, and the ambiguous condition 13).
- Others present: various FUL grants, a listed-building consent, a discharge-approval notice, appeals.

## Roadmap (next features, in order)
Full step-by-step + the exact new JSON field for each is in `tool-blueprint-detailed.md`. Summary:
1. **1.2 De-dupe** — `duplicate_of` field; flag near-identical conditions.
2. **2.1 Discharge Application Planner** — `discharge_bundle` field; min applications + fee estimate + deemed-discharge flag. (Verify current discharge fee before hard-coding.)
3. **2.2 Consultant scoping** — `specialist_needed` field; "who to hire" list.
4. **2.3 Sequencing**, **2.4 Auto-drafted submissions** (second "drafting" prompt).
5. **Phase 3** — deadline engine, .ics export, source-clause view, consistency checker, PDF summary, more doc types, batch upload.
6. **Phase 4** — persistence (Supabase), living tracker, portfolio, accounts. Big architecture jump; only when users ask.

## Golden rule
One feature at a time: prompt-first → validate on a real notice → ship small.
