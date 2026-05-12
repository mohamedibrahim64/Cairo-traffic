from pathlib import Path
from pypdf import PdfReader

BASE = Path(r"a:/MyGitHub/Cairo-traffic/project describtion")
FILES = [
    "Project_Provided_Data.pdf",
    "CSE112-Theoretical Project.pdf",
    "CSE112-Practical Project.pdf",
]
OUT = BASE / "requirements_extracted.txt"

with OUT.open("w", encoding="utf-8") as handle:
    for name in FILES:
        handle.write(f"===== {name} =====\n")
        reader = PdfReader(BASE / name)
        for page in reader.pages:
            text = page.extract_text() or ""
            handle.write(text + "\n")
        handle.write("\n")
        print(f"Extracted {name}")
