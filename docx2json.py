from docx import Document
import json
import re

# Set the Path
doc_path = "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/국어 지식 기반 생성(RAG) 참조 문서.docx"
output_path = (
    "/Users/soeon/Desktop/GCU/25/ISNLP/2025말평/Dataset/GrammarBook_structured.json"
)


# Function to check if a line should be split by comma
def split_by_comma(text):
    if any(
        p in text
        for p in [".", "!", "?", "다", "요", "함", "함.", "한다", "있다", "없다"]
    ):
        return False
    if "/" in text:
        return False
    return text.count(",") >= 3


# Load Document
document = Document(doc_path)
paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

# Initialize variables
entries = []  # List to hold all Entries(Primary Rules)
entry = {}  # Current Entry being processed
subrules = []  # List to hold Subrules
current_subrule = None  # Current Subrule being processed
current_exception = None  # Current Exception being processed
notes = []  # List to hold Notes
in_note = False  # Flag to indicate if we are in a note
prev_line = ""  # Previous line for context
in_auto_example = False  # Flag for auto-example mode

title_pattern = re.compile(r"^<(.+?)\s*-\s*(.+?)(\s*(제.*항|표.*|규정)?)>$")

for line in paragraphs:

    # For Multi(Tens of lines) Auto-example trigger line
    if line.endswith("한다:"):
        prev_line = line
        in_auto_example = True
        continue

    # Auto-example Mode: Handle Lines after '한다:'(which has specific case)
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

    # Rule for Title
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
            entry["category"] = match.group(1).strip()  # (1) Category of the rule
            entry["source"] = match.group(2).strip()  # (2) Source of the rule

            rule_id = match.group(3).strip()
            entry["rule_id"] = rule_id if rule_id else None  # (3) Rule ID if exists

            entry["title"] = (
                match.group(2).strip() + " " + (rule_id if rule_id else "")
            )  # (4) Title of the rule

        else:  # Exceptional case
            entry["category"] = "기타"  # (1) Category of the rule
            entry["source"] = "미지정"  # (2) Source of the rule
            entry["rule_id"] = None  # (3) Rule ID if exists
            entry["title"] = line.strip("<>")  # (4) Title of the rule

    # Subrule Section
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

    # Exception Section
    # '다만', '붙임', '[붙임\d*]', '※' are used to denote exceptions
    elif re.match(r"^(다만|붙임|\[붙임\d*\]|※)", line):
        current_exception = {"description": line.strip(), "examples": []}
        if current_subrule:
            current_subrule["exceptions"].append(current_exception)
        else:
            entry.setdefault("exceptions", []).append(current_exception)

    # Note Section
    elif line.startswith("￭") or line.startswith("*"):
        in_note = True
        note_text = line.strip("￭*").strip()
        if note_text:
            notes.append({"title": note_text, "content": ""})

    # Example with Hyphen
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
            if split_by_comma(ex_line):
                ex_list = [e.strip() for e in ex_line.split(",") if e.strip()]
            else:
                ex_list = [ex_line]

            if current_exception:
                current_exception["examples"].extend(ex_list)
            elif current_subrule:
                current_subrule["examples"].extend(ex_list)
            else:
                entry.setdefault("examples", []).extend(ex_list)

    # Notes Content
    elif in_note and notes:
        notes[-1]["content"] += " " + line.strip()

    # General Description
    elif "description" not in entry:
        entry["description"] = line.strip()
    else:
        entry["description"] += " " + line.strip()

    prev_line = line

# Save last entry if exists
if current_subrule:
    subrules.append(current_subrule)
if subrules:
    entry["subrules"] = subrules
if notes:
    entry["notes"] = notes
if entry:
    entries.append(entry)

# Write to JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"JSON file has been created at: {output_path}")
print(f"Total entries parsed: {len(entries)}")
