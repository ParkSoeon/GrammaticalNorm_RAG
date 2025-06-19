from docx import Document
import json
import re

# Load the document
document = Document(
    "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/국어 지식 기반 생성(RAG) 참조 문서.docx"
)
paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

entries = []
entry = {}
current_example_group = None  # 그룹 예시 구분용

# 유연한 규범 제목 패턴
title_pattern = re.compile(r"^<(.+?)\s*-\s*(.+?)(\s*(제.*항|표.*|규정)?)>$")

for line in paragraphs:
    # 규범 제목 감지
    if line.startswith("<") and line.endswith(">"):
        if entry:
            entries.append(entry)
            entry = {}
        current_example_group = None

        match = title_pattern.match(line)
        if match:
            entry["category"] = match.group(1).strip()
            entry["source"] = match.group(2).strip()
            rule_id = match.group(3).strip()
            entry["rule_id"] = rule_id if rule_id else None
        else:
            entry["category"] = "기타"
            entry["source"] = "미지정"
            entry["rule_id"] = None

    # 예시 그룹 제목 감지
    elif re.match(r"^\d+\.\s*['‘\"]?(.*?)['’\"]?\s*의 경우", line):
        group_title = (
            re.match(r"^\d+\.\s*['‘\"]?(.*?)['’\"]?\s*의 경우", line).group(1).strip()
        )
        current_example_group = group_title
        entry.setdefault("examples_grouped", {})[current_example_group] = []

    # 예시 라인
    elif line.startswith("-"):
        ex_line = line.lstrip("-").strip()
        if ex_line.startswith(("ㄱ:", "ㄱ.")):
            entry["correct_examples"] = [ex.strip() for ex in ex_line[2:].split(",")]
        elif ex_line.startswith(("ㄴ:", "ㄴ.")):
            entry["incorrect_examples"] = [ex.strip() for ex in ex_line[2:].split(",")]
        elif current_example_group:
            entry["examples_grouped"][current_example_group].extend(
                [ex.strip() for ex in ex_line.split(",")]
            )
        else:
            entry.setdefault("examples", []).extend(
                [ex.strip() for ex in ex_line.split(",")]
            )

    # 설명 텍스트
    else:
        if "description" not in entry:
            entry["description"] = line.strip()
        else:
            entry["description"] += " " + line.strip()  # 멀티라인 설명 처리

# 마지막 entry 추가
if entry:
    entries.append(entry)

# JSON 저장
output_path = "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/GrammarBook.json"
with open(output_path, "w", encoding="utf-8") as file:
    json.dump(entries, file, ensure_ascii=False, indent=4)

print(f"JSON file has been created at: {output_path}")
print(f"Total rules parsed: {len(entries)}")
