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


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


category_colours = {
    "pre-commencement": "F4CCCC", "pre-occupation": "FCE5CD",
    "ongoing": "CFE2F3", "discharge-required": "D9D2E9", "time-limit": "FFF2CC",
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
            "solid", fgColor=category_colours.get(c["category"], "FFFFFF"))
    for col, w in {"A": 5, "B": 55, "C": 18, "D": 16, "E": 14, "F": 18}.items():
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


st.title("AI Planning Condition Tracker")
st.write("Upload a UK planning permission decision notice (PDF) and get every condition extracted and categorised.")

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

        st.success(f"{data['decision'].upper()} — {len(data['conditions'])} conditions found")

        if len(data["conditions"]) == 0:
            st.info("No conditions found. This may be a refusal or a document without planning conditions.")
        else:
            st.dataframe(data["conditions"])
            excel_bytes = build_excel(data)
            st.download_button("Download Excel tracker", excel_bytes,
                               file_name="tracker.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception:
        st.error("Something went wrong processing this file. Please check it's a valid "
                 "UK planning decision notice PDF and try again.")