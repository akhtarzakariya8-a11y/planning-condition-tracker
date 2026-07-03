# AI Planning Condition Tracker

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

1. **Reads** the decision-notice PDF (text extraction)
2. **Sends** it to the Claude API with a domain-tuned prompt
3. **Extracts and categorises** every condition — number, plain-English summary, category, deadline, responsible party, and whether it needs formal discharge
4. **Outputs** a colour-coded Excel tracker (one row per condition) and an on-screen table

A dense legal document goes in; a structured, categorised tracker comes out — in about 30 seconds.

## Why the categorisation is the hard part

Anyone can extract text from a PDF. The value is in the **judgement**: correctly telling apart a condition that must merely be "submitted to" the council (not a discharge condition) from one that must be "submitted to *and approved by*" the council (a discharge condition) — a distinction that materially changes what a developer has to do. That domain logic is encoded in the prompt, built from a quantity-surveying background.

## Tech stack

- **Python**
- **Claude API** (Anthropic) — condition extraction and categorisation
- **pdfplumber** — PDF text extraction
- **openpyxl** — formatted Excel output
- **Streamlit** — web interface, deployed on Streamlit Community Cloud

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
```

Create a `.env` file with your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

Then run:

```bash
streamlit run app.py
```

## Scope & limitations (honest notes)

- Designed for **UK planning decision notices** specifically. Other document types (discharge approvals, certificates of lawfulness) will correctly return "no conditions."
- Works on **text-based PDFs**. Scanned/image-only PDFs are detected and rejected with a message (OCR support is a planned addition).
- This is a working tool and a proof of concept — not a replacement for professional review. Outputs should be checked against the source document.

## What's next

- OCR support for scanned notices
- Deadline tracking and reminders (turning the extractor into a full condition-management tool)
- Batch processing of multiple notices

---

Built by **Zak Akhtar** — final-year Quantity Surveying student
