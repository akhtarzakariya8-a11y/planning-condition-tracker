import openpyxl
from openpyxl.styles import Font, PatternFill

# test data — same shape your pipeline produces
data = {
    "decision": "granted",
    "conditions": [
        {"condition_number": 1, "summary": "Begin within 3 years", "category": "time-limit", "deadline": "11 June 2029", "responsible_party": "applicant", "discharge_required": False},
        {"condition_number": 4, "summary": "Arboricultural Method Statement approved before start", "category": "pre-commencement", "deadline": None, "responsible_party": "applicant", "discharge_required": True},
    ]
}

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Conditions"

# header row
headers = ["#", "Summary", "Category", "Deadline", "Responsible", "Discharge required?"]
ws.append(headers)

# one row per condition
for c in data["conditions"]:
    ws.append([
        c["condition_number"],
        c["summary"],
        c["category"],
        c["deadline"],
        c["responsible_party"],
        "Yes" if c["discharge_required"] else "No",
    ])

wb.save("tracker.xlsx")
print("Saved tracker.xlsx")