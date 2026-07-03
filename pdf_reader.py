import pdfplumber

with pdfplumber.open("26_01199_FUL--3568317.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text()

print(text)