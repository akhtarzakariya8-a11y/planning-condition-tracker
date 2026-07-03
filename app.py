import streamlit as st
import anthropic
import pdfplumber
import json
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from dotenv import load_dotenv
 
load_dotenv()
client = anthropic.Anthropic()
 
with open("prompt_v4_production.txt") as f:
    system_prompt = f.read()
 
 
# ----- PAGE CONFIG -----
st.set_page_config(
    page_title="AI Planning Condition Tracker",
    page_icon="📋",
    layout="centered",
)
 
# ----- LIGHT CUSTOM STYLING -----
st.markdown("""
<style>
    .block-container {padding-top: 2.5rem; max-width: 820px;}
    h1 {font-weight: 700; letter-spacing: -0.5px;}
    .subtitle {font-size: 1.05rem; color: #5f6b7a; margin-top: -0.5rem; margin-bottom: 1.5rem;}
    .step-card {background:#f4f8fd; border:1px solid #e2ecf7; border-radius:12px;
                padding:1rem 1.2rem; height:100%;}
    .step-num {color:#1F4E78; font-weight:700; font-size:0.85rem; letter-spacing:1px;}
    .step-text {color:#31415a; font-size:0.92rem; margin-top:2px;}
    .stat-card {background:#1F4E78; color:#fff; border-radius:12px; padding:0.9rem 1rem; text-align:center;}
    .stat-num {font-size:1.7rem; font-weight:700; line-height:1;}
    .stat-label {font-size:0.78rem; opacity:0.85; margin-top:4px;}
    .footer {color:#8a97a8; font-size:0.85rem; text-align:center; margin-top:3rem;
             padding-top:1.2rem; border-top:1px solid #e8edf3;}
    .footer a {color:#1F4E78; text-decoration:none; font-weight:600;}
</style>
""", unsafe_allow_html=True)
 
 
# ----- HELPERS (unchanged pipeline) -----
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
CATEGORY_HEX = {
    "pre-commencement": "#e06666", "pre-occupation": "#e69138",
    "ongoing": "#3d85c6", "discharge-required": "#8e7cc3", "time-limit": "#d6b656",
}
 
 
def build_excel(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Conditions"
    ws.append(["#", "Summary", "Category", "Deadline", "Responsible", "Discharge required?"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for c in data["conditions"]:
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
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
 
 
def category_pill(cat):
    hex_c = CATEGORY_HEX.get(cat, "#888")
    return f'<span style="background:{hex_c}22;color:{hex_c};padding:3px 10px;border-radius:12px;font-size:0.8rem;font-weight:600;white-space:nowrap;">{cat}</span>'
 
 
# ----- HEADER -----
st.markdown("# 📋 AI Planning Condition Tracker")
st.markdown('<p class="subtitle">Upload a UK planning permission decision notice and get every planning condition extracted, categorised, and exported as a tracker spreadsheet — in seconds.</p>', unsafe_allow_html=True)
 
# ----- HOW IT WORKS -----
c1, c2, c3 = st.columns(3)
for col, num, text in [
    (c1, "STEP 1", "Upload a decision notice PDF"),
    (c2, "STEP 2", "AI reads & categorises every condition"),
    (c3, "STEP 3", "Download your structured tracker"),
]:
    col.markdown(f'<div class="step-card"><div class="step-num">{num}</div><div class="step-text">{text}</div></div>', unsafe_allow_html=True)
 
st.write("")
st.write("")
 
# ----- UPLOAD -----
uploaded_file = st.file_uploader("Choose a PDF", type="pdf")
 
if uploaded_file is not None:
    try:
        with st.spinner("Reading the decision notice — usually 15–30 seconds..."):
            with pdfplumber.open(uploaded_file) as pdf:
                pdf_text = ""
                for page in pdf.pages:
                    pdf_text += page.extract_text() or ""
 
            if len(pdf_text.strip()) < 100:
                st.error("This PDF appears to be a scanned image with no readable text. "
                         "Please upload a text-based decision notice (OCR support coming soon).")
                st.stop()
 
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": pdf_text}],
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
            # ---- SUMMARY STAT CARDS ----
            total = len(conditions)
            discharge = sum(1 for c in conditions if c["discharge_required"])
            precom = sum(1 for c in conditions if c["category"] == "pre-commencement")
 
            st.success(f"**{decision}** — {total} conditions found")
            s1, s2, s3 = st.columns(3)
            s1.markdown(f'<div class="stat-card"><div class="stat-num">{total}</div><div class="stat-label">Total conditions</div></div>', unsafe_allow_html=True)
            s2.markdown(f'<div class="stat-card"><div class="stat-num">{precom}</div><div class="stat-label">Pre-commencement</div></div>', unsafe_allow_html=True)
            s3.markdown(f'<div class="stat-card"><div class="stat-num">{discharge}</div><div class="stat-label">Need discharge</div></div>', unsafe_allow_html=True)
 
            st.write("")
 
            # ---- COLOUR-CODED TABLE ----
            rows_html = ""
            for c in conditions:
                deadline = c["deadline"] or "—"
                disc = "✅" if c["discharge_required"] else "—"
                rows_html += (
                    f'<tr>'
                    f'<td style="text-align:center;color:#8a97a8;">{c["condition_number"]}</td>'
                    f'<td>{c["summary"]}</td>'
                    f'<td>{category_pill(c["category"])}</td>'
                    f'<td style="font-size:0.85rem;">{deadline}</td>'
                    f'<td style="text-align:center;">{disc}</td>'
                    f'</tr>'
                )
            table_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                '<thead><tr style="background:#1F4E78;color:#fff;text-align:left;">'
                '<th style="padding:8px;">#</th><th style="padding:8px;">Summary</th>'
                '<th style="padding:8px;">Category</th><th style="padding:8px;">Deadline</th>'
                '<th style="padding:8px;text-align:center;">Discharge</th></tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )
            st.markdown('<style>tbody tr{border-bottom:1px solid #eef2f6;} tbody td{padding:8px;vertical-align:top;}</style>' + table_html, unsafe_allow_html=True)
 
            st.write("")
 
            # ---- DOWNLOAD ----
            excel_bytes = build_excel(data)
            st.download_button("⬇️  Download Excel tracker", excel_bytes,
                               file_name="planning_condition_tracker.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               type="primary")
 
    except Exception:
        st.error("Something went wrong processing this file. Please check it's a valid "
                 "UK planning decision notice PDF and try again.")
 
# ----- DEMO VIDEO -----
st.write("")
st.markdown("### 🎥 See it in action")
st.markdown('<p style="color:#5f6b7a;margin-top:-0.5rem;">A quick walkthrough of uploading a decision notice and getting a categorised tracker.</p>', unsafe_allow_html=True)
st.video("https://youtu.be/qOlSIYaaAN0")
 
# ----- FOOTER -----
st.markdown(
    '<div class="footer">Built by Zak Akhtar · '
    '<a href="https://github.com/akhtarzakariya8-a11y/planning-condition-tracker">GitHub</a> · '
    'A tool for UK planning decision notices. Always check outputs against the source document.</div>',
    unsafe_allow_html=True,
)