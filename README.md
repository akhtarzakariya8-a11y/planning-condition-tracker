# Aftergrant

*From planning permission to start on site.* (Formerly the AI Planning Condition Tracker.)

**Upload a UK planning permission decision notice (PDF) → get every planning condition extracted, categorised, and exported as a structured tracker spreadsheet in seconds.**

🔗 **Live tool:** https://planning-condition-tracker-cbovv39yhnquhj9a7jeefn.streamlit.app

<!-- Add a screenshot here: drag an image into the GitHub editor, or use ![screenshot](screenshot.png) -->

---

## The problem

When a UK council grants planning permission, the approval comes with **planning conditions** — often 20–30 of them, buried in a dense decision-notice PDF. Each condition is a legal requirement, and they fall into types that matter for timing and compliance:

- **Pre-commencement** — must be satisfied *before any work starts*
- **Discharge-required** — details must be formally submitted to and approved by the council
- **Pre-occupation** — must be satisfied before the building is used
- **Ongoing** — must be complied with throughout the development
- **Time-limit** — the statutory deadline to begin work

Developers, quantity surveyors, and planning consultants currently read these by hand and track them manually. Missing a pre-commencement or discharge condition can mean enforcement action, delays, and cost. It's slow, repetitive, and error-prone.

## What this tool does

1. **Reads** the decision-notice PDF (text, or Claude's vision for scanned notices)
2. **Extracts and categorises** every condition — plain-English summary, category, deadline, whether it needs formal discharge, and the council's verbatim wording
3. **Safety Gate** — what legally stops you starting on site, what only blocks above-ground works (so demolition and groundworks can start), what blocks piling, what's ambiguous, and the date the permission lapses (handled correctly for outline and section 73 permissions)
4. **Things to check** — typos, missing drawings, contradictions and duplicated conditions in the council's own notice
5. **Discharge plan** — how many applications to make and the statutory fees (England/Wales, switching automatically when fees rise)
6. **Programme & deadlines** — enter your start, piling, above-ground and occupation dates; it works back to when each discharge application must be submitted and each consultant commissioned, flags anything late, and exports it all to your calendar (.ics)
7. **Auto-drafted submissions** — one click writes the covering letter and a per-condition checklist of what to submit, as a Word document, with placeholders instead of invented facts
8. **Specialists** — which consultants the conditions imply you'll need
9. **Exports** — colour-coded Excel tracker, a printable PDF summary, and a portfolio workbook when you upload several notices at once
10. **Saved projects** — sign in to keep each permission, track every condition's status (submitted, discharged…), and get warned when a deemed-discharge notice may be available

## Why the categorisation is the hard part

Anyone can extract text from a PDF. The value is in the **judgement**: correctly telling apart a condition that must merely be "submitted to" the council (not a discharge condition) from one that must be "submitted to *and approved by*" the council (a discharge condition) — a distinction that materially changes what a developer has to do. That domain logic is encoded in the prompt, built from a quantity-surveying background.

## Tech stack

- **Python**
- **Claude API** (Anthropic) — condition extraction and categorisation
- **pdfplumber** — PDF text extraction
- **openpyxl** — formatted Excel output
- **Streamlit** — web interface, deployed on Streamlit Community Cloud
- **python-docx / reportlab** — Word drafts and PDF summaries
- **Supabase** (Postgres) + Google sign-in — saved projects
- **MCP server** — the same tools inside Claude Desktop / Claude Code (`mcp_server/`)

## How it was built

Built over the summer as a final-year Quantity Surveying student, starting from zero Python. The approach was prompt-first: the extraction logic was developed and validated in the Claude interface across real council decision notices before any code was written, then wrapped in a Python pipeline and deployed as a web app. Every design decision — the category definitions, the discharge logic, the edge-case handling — was tested against real UK planning documents.

**Validated on real decision notices**, including:
- Standard householder approvals (3–6 conditions)
- A 24-condition major scheme (demolition + redevelopment, with contamination, coal-mining, arboricultural, and drainage conditions) — all 24 caught correctly
- Refusals, conditions-discharge approvals, and Planning Inspectorate appeal decisions — handled gracefully

## Run it locally

```bash
git clone https://github.com/akhtarzakariya8-a11y/planning-condition-tracker.git
cd planning-condition-tracker
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
streamlit run app.py
```

Tests and accuracy:

```bash
python3 -m pytest tests/ -q          # the rules — instant, no API calls
python3 eval/run_eval.py --jobs 7    # the model — scored against a hand-made answer key
```

## Scope & limitations (honest notes)

- Designed for **UK planning decision notices**. Discharge approvals, refusals and other documents are recognised and handled as what they are (nothing left to discharge, nothing to start).
- **Scanned PDFs** are read with Claude's vision; quoted wording from a scan is labelled as a transcription.
- Fees are priced for **England and Wales** only. Deemed discharge is an English provision and is only mentioned there.
- Every output — gates, dates, fees, drafts — is a planning aid, **not legal advice**, and should be checked against the source notice and with a planning consultant.

## What's next

- Payments and a free tier
- Email reminders for upcoming submit-by deadlines
- Saved drafts inside projects

---

Built by **Zak Akhtar** — final-year Quantity Surveying student
