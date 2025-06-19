from docx import Document
import json
import re

# 문서 로드
doc_path = "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/국어 지식 기반 생성(RAG) 참조 문서.docx"
document = Document(doc_path)
paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

entries = []
entry = {}
subrules = []
current_subrule = None
current_exception = None
notes = []
in_note = False

# 규범 제목 감지 정규표현식
title_pattern = re.compile(r"^<(.+?)\s*-\s*(.+?)(\s*(제.*항|표.*|규정)?)>$")

for line in paragraphs:
    if line.startswith("<") and line.endswith(">"):
        # entry 저장
        if entry:
            if current_subrule:
                subrules.append(current_subrule)
                current_subrule = None
            if subrules:
                entry["subrules"] = subrules
                subrules = []
            if notes:
                entry["notes"] = notes
                notes = []
            entries.append(entry)
            entry = {}

        current_exception = None
        in_note = False

        match = title_pattern.match(line)
        if match:
            entry["category"] = match.group(1).strip()
            entry["source"] = match.group(2).strip()
            rule_id = match.group(3).strip()
            entry["rule_id"] = rule_id if rule_id else None
            entry["title"] = match.group(2).strip() + " " + (rule_id if rule_id else "")
        else:
            entry["category"] = "기타"
            entry["source"] = "미지정"
            entry["rule_id"] = None
            entry["title"] = line.strip("<>")

    elif re.match(r"^\(\d+\)", line):  # 소규칙 감지
        if current_subrule:
            subrules.append(current_subrule)
        current_subrule = {
            "index": re.match(r"^\((\d+)\)", line).group(0),
            "description": line.split(")", 1)[1].strip(),
            "examples": [],
            "exceptions": [],
        }

    elif (
        line.startswith("다만")
        or line.startswith("[붙임]")
        or line.startswith("※")
        or "않는다." in line
    ):
        current_exception = {"description": line.strip(), "examples": []}
        if current_subrule:
            current_subrule["exceptions"].append(current_exception)

    elif line.startswith("-"):
        ex_line = line.lstrip("-").strip()
        ex_list = [ex.strip() for ex in ex_line.split(",") if ex.strip()]

        if ex_line.startswith(("ㄱ:", "ㄱ.")):
            entry["correct_examples"] = [ex.strip() for ex in ex_line[2:].split(",")]
        elif ex_line.startswith(("ㄴ:", "ㄴ.")):
            entry["incorrect_examples"] = [ex.strip() for ex in ex_line[2:].split(",")]
        elif current_exception:
            current_exception["examples"].extend(ex_list)
        elif current_subrule:
            current_subrule["examples"].extend(ex_list)
        else:
            entry.setdefault("examples", []).extend(ex_list)

    elif line.startswith("￭"):
        in_note = True
        notes.append({"title": line.replace("￭", "").strip(), "content": ""})

    else:
        if in_note and notes:
            notes[-1]["content"] += line.strip()
        elif "description" not in entry:
            entry["description"] = line.strip()
        else:
            entry["description"] += " " + line.strip()

# 마지막 entry 저장
if current_subrule:
    subrules.append(current_subrule)
if subrules:
    entry["subrules"] = subrules
if notes:
    entry["notes"] = notes
if entry:
    entries.append(entry)

# JSON 저장
output_path = (
    "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/GrammarBook_structured.json"
)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"JSON file has been created at: {output_path}")
print(f"Total entries parsed: {len(entries)}")
