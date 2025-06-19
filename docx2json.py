from docx import Document
import json
import re

# Set the Path
doc_path = "문서.docx"
output_path = (
    "structured.json"
)


# Helper: split by comma only if it's safe
def should_split_by_comma(text):
    if any(
        p in text
        for p in [".", "!", "?", "다", "요", "함", "함.", "한다", "있다", "없다"]
    ):
        return False
    if "/" in text:
        return False
    return text.count(",") >= 3


# Load document
document = Document(doc_path)
paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

entries = []
entry = {}
subrules = []
current_subrule = None
current_exception = None
notes = []
in_note = False
prev_line = ""
in_auto_example = False

title_pattern = re.compile(r"^<(.+?)\s*-\s*(.+?)(\s*(제.*항|표.*|규정)?)>$")

for line in paragraphs:

    # Auto-example trigger line
    if line.endswith("한다:"):
        prev_line = line
        in_auto_example = True
        continue

    # Auto-example mode: handle lines after '한다:'
    if in_auto_example:
        if line == "" or line.startswith("<") or re.match(r"^\(\d+\)", line):
            in_auto_example = False
        else:
            ex_line = line.strip()
            if ex_line:
                if current_subrule:
                    current_subrule["examples"].append(ex_line)
                else:
                    entry.setdefault("examples", []).append(ex_line)
            continue

    # Rule title
    if line.startswith("<") and line.endswith(">"):
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

    # Subrule section
    elif re.match(r"^\(\d+\)", line):
        if current_subrule:
            subrules.append(current_subrule)
        current_exception = None
        current_subrule = {
            "index": re.match(r"^\((\d+)\)", line).group(0),
            "description": line.split(")", 1)[1].strip(),
            "examples": [],
            "exceptions": [],
        }

    # Exception section
    elif re.match(r"^(다만|붙임|\[붙임\d*\]|※)", line):
        current_exception = {"description": line.strip(), "examples": []}
        if current_subrule:
            current_subrule["exceptions"].append(current_exception)
        else:
            entry.setdefault("exceptions", []).append(current_exception)

    # Notes
    elif line.startswith("￭") or line.startswith("*"):
        in_note = True
        notes.append({"title": line.lstrip("￭*").strip(), "content": ""})

    # Examples with hyphen
    elif line.startswith("-"):
        ex_line = line.lstrip("-").strip()

        if ex_line.startswith(("ㄱ:", "ㄱ.")) and "ㄴ" in ex_line:
            parts = re.split(r"ㄴ[:.]", ex_line)
            g_examples = re.sub(r"^ㄱ[:.]", "", parts[0]).strip()
            n_examples = parts[1].strip() if len(parts) > 1 else ""
            entry["correct_examples"] = [
                e.strip() for e in g_examples.split(",") if e.strip()
            ]
            entry["incorrect_examples"] = [
                e.strip() for e in n_examples.split(",") if e.strip()
            ]
        elif ex_line.startswith(("ㄱ:", "ㄱ.")):
            entry["correct_examples"] = [
                e.strip() for e in ex_line[2:].split(",") if e.strip()
            ]
        elif ex_line.startswith(("ㄴ:", "ㄴ.")):
            entry["incorrect_examples"] = [
                e.strip() for e in ex_line[2:].split(",") if e.strip()
            ]
        else:
            if should_split_by_comma(ex_line):
                ex_list = [e.strip() for e in ex_line.split(",") if e.strip()]
            else:
                ex_list = [ex_line]

            if current_exception:
                current_exception["examples"].extend(ex_list)
            elif current_subrule:
                current_subrule["examples"].extend(ex_list)
            else:
                entry.setdefault("examples", []).extend(ex_list)

    # Notes content
    elif in_note and notes:
        notes[-1]["content"] += " " + line.strip()

    # General description
    elif "description" not in entry:
        entry["description"] = line.strip()
    else:
        entry["description"] += " " + line.strip()

    prev_line = line

# Save last entry
if current_subrule:
    subrules.append(current_subrule)
if subrules:
    entry["subrules"] = subrules
if notes:
    entry["notes"] = notes
if entry:
    entries.append(entry)

# Output JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"JSON file has been created at: {output_path}")
print(f"Total entries parsed: {len(entries)}")
