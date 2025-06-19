from docx import Document
import json
import re

# Load the document
document = Document(
    "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/국어 지식 기반 생성(RAG) 참조 문서.docx"
)

# Store the lines in a list
paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

# Parsing the paragraphs into a structured format
entries = []
entry = {}

for line in paragraphs:
    if line.startswith("<") and line.endswith(">"):  # 조항 제목
        if entry:  # Save the previous entry if it exists
            entries.append(entry)
            entry = {}
        title = line.strip("<>")

        match = re.match(r"(.+)\s*-\s*(.+)\s*(제\d+항)", title)

        if match:
            entry["category"] = match.group(1).strip()
            entry["source"] = match.group(2).strip()
            entry["rule_id"] = match.group(3).strip()
    elif line.startswith("-"):  # 예시 목록
        examples = line.lstrip("-").strip().split(",")
        entry["examples"] = [ex.strip() for ex in examples if ex.strip()]
    else:  # 조항 내용
        entry["description"] = line.strip()

# Add the last entry if it exists
if entry:
    entries.append(entry)

output_path = "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/GrammarBook.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(entries, file, ensure_ascii=False, indent=4)
print(f"JSON file has been created at {output_path}")
