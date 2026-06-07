#!/usr/bin/env python3
"""
Convert .odt and .docx files from fwddataset/ into the JSON format used by train.py,
then merge any NEW scenarios into the existing Code/dataset/ JSON files.

Existing scenarios (matched by scenario text) are NOT duplicated.

Usage:
    python convert_fwddataset.py            # dry-run (prints stats only)
    python convert_fwddataset.py --write    # actually write merged JSON files
"""

import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
FWD_DIR = Path(__file__).parent / "fwddataset"
DATASET_DIR = Path(__file__).parent / "Code" / "dataset"

# Maps the fwddataset filename prefix (number) to the existing JSON filename key
FILE_MAP = {
    "1":  "1_personal_identity",
    "2":  "2_social_bias",
    "3":  "3_professional_and_educational",
    "4":  "4_behavioural_and_psychological",
    "5":  "5_situational_and_contexual",
    "6":  "6_intersectional_and_compound",
    "7":  "7_technological_and_media",
    "8":  "8_health_and_wellness",
    "9":  "9_culture_and_regional",
    "10": "10_behavioural_bias_indicators",
    "11": "11_misc",
}


# ─── Document readers ─────────────────────────────────────────────────────────
def read_odt(path: str) -> list[str]:
    """Extract non-empty paragraph texts from an ODT file."""
    with zipfile.ZipFile(path) as z:
        with z.open("content.xml") as f:
            tree = ET.parse(f)
    ns = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    result = []
    for p in tree.findall(".//text:p", ns):
        text = "".join(p.itertext()).strip()
        if text:
            result.append(text)
    return result


def read_docx(path: str) -> list[str]:
    """Extract non-empty paragraph texts from a DOCX file."""
    with zipfile.ZipFile(path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    result = []
    for p in tree.findall(".//w:p", ns):
        texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
        line = "".join(texts).strip()
        if line:
            result.append(line)
    return result


# ─── Dialogue splitter ─────────────────────────────────────────────────────────
# In the ODT/DOCX files dialogues are concatenated like:
#   "Interviewer:How did you ...?Candidate:I felt ..."
# We need to split them into separate strings like:
#   ["Interviewer: How did you ...?", "Candidate: I felt ..."]
_SPEAKER_RE = re.compile(
    r"(?:^|(?<=\S))"               # start-of-string or right after a non-space
    r"(Interviewer|Candidate|Parent|Employee|Manager|Student|Teacher|"
    r"Colleague|Doctor|Patient|Mentor|Mentee|Client|Counsellor|Counselor|"
    r"Recruiter|Applicant|HR|Supervisor|Friend|Neighbour|Neighbor|"
    r"Community Member|Volunteer|Peer|Team Lead|Team Member|"
    r"Facilitator|Participant|Moderator|Panellist|Respondent|"
    r"Customer|Staff|Caregiver|Resident|Vendor|Buyer|Host|Guest|"
    r"Advisor|Adviser|Trainee|Trainer|"
    r"Caller|Dispatcher|Officer|Agent)"
    r"\s*:\s*",
    re.IGNORECASE,
)

def split_dialogues(raw_line: str) -> list[str]:
    """Split a concatenated dialogue line into individual speaker turns."""
    # Find all speaker boundaries
    matches = list(_SPEAKER_RE.finditer(raw_line))
    if not matches:
        return [raw_line]

    parts = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_line)
        speaker = m.group(1)
        text = raw_line[m.end():end].strip()
        parts.append(f"{speaker}: {text}")
    return parts


# ─── Version string normaliser ────────────────────────────────────────────────
def normalise_version(raw: str) -> str:
    """
    Normalise version strings to match the format used in the existing JSON.
    E.g. "Version 3 :Unconscious Bias" -> "Interview Version: Unconscious Bias"
         "Mixed Version 1: Wealth Bias, ..." -> "Version 1: Mixed Bias (Wealth Bias, ...)"
    """
    raw = raw.strip()
    # "Version 3 : Unconscious Bias" variants
    if re.search(r"Unconscious\s+Bias", raw, re.IGNORECASE):
        return "Interview Version: Unconscious Bias"
    # Already looks like an existing version string
    return raw


# ─── Main parser ───────────────────────────────────────────────────────────────
def is_type_header(line: str) -> bool:
    """Check if line is a bias type header like '1:Race' or '1: Social Class'."""
    return bool(re.match(r"^\d+[\s.]*:", line)) and not line.lower().startswith("interviewer")

def is_scenario_line(line: str) -> bool:
    return line.lower().startswith("scenario")

def is_version_line(line: str) -> bool:
    return bool(re.match(r"^(Version|Mixed Version|Interview Version)", line, re.IGNORECASE))

def is_dialogue_line(line: str) -> bool:
    """Check if a line contains dialogue (starts with a speaker name)."""
    return bool(re.match(
        r"^(Interviewer|Candidate|Parent|Employee|Manager|Student|Teacher|"
        r"Colleague|Doctor|Patient|Mentor|Mentee|Client|Counsellor|Counselor|"
        r"Recruiter|Applicant|HR|Supervisor|Friend|Neighbour|Neighbor|"
        r"Community Member|Volunteer|Peer|Team Lead|Team Member|"
        r"Facilitator|Participant|Moderator|Panellist|Respondent|"
        r"Customer|Staff|Caregiver|Resident|Vendor|Buyer|Host|Guest|"
        r"Advisor|Adviser|Trainee|Trainer|"
        r"Caller|Dispatcher|Officer|Agent)\s*:",
        line, re.IGNORECASE,
    ))

def clean_scenario(raw: str) -> str:
    """Remove 'Scenario:' prefix and quotes."""
    s = re.sub(r"^Scenario\s*:?\s*", "", raw, flags=re.IGNORECASE).strip()
    s = s.strip('"').strip('"').strip('"').strip("'").strip()
    s = re.sub(r"\s*\.?\s*$", "", s)  # trailing dots
    return s

def clean_bias_type(raw: str) -> str:
    """Extract bias type from header like '1:Race' -> '1: Race'."""
    m = re.match(r"^(\d+)\s*[:.]\s*(.*)", raw)
    if m:
        return f"{m.group(1)}: {m.group(2).strip()}"
    return raw.strip()


def parse_document(lines: list[str]) -> list[dict]:
    """
    Parse a list of text lines (from ODT or DOCX) into the JSON structure:
    [
        {
            "parameters": {
                "bias_type": "1: Race",
                "scenario": "...",
                "conversations": [
                    {"version": "...", "dialogues": ["...", "..."]}
                ]
            }
        },
        ...
    ]
    """
    scenarios = []
    current_bias_type = None
    current_scenario = None
    current_conversations = []
    current_version = None
    current_dialogues = []
    # Extra text lines that appear between type header and scenario (descriptions)
    skip_description = False

    def flush_conversation():
        nonlocal current_version, current_dialogues
        if current_version and current_dialogues:
            current_conversations.append({
                "version": normalise_version(current_version),
                "dialogues": current_dialogues,
            })
        current_version = None
        current_dialogues = []

    def flush_scenario():
        nonlocal current_scenario, current_conversations
        flush_conversation()
        if current_scenario and current_conversations:
            scenarios.append({
                "parameters": {
                    "bias_type": current_bias_type or "Unknown",
                    "scenario": current_scenario,
                    "conversations": current_conversations,
                }
            })
        current_scenario = None
        current_conversations = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Type header
        if is_type_header(line):
            flush_scenario()
            current_bias_type = clean_bias_type(line)
            skip_description = True
            continue

        # Scenario line
        if is_scenario_line(line):
            flush_scenario()
            current_scenario = clean_scenario(line)
            skip_description = False
            continue

        # Version line
        if is_version_line(line):
            flush_conversation()
            current_version = line.strip()
            skip_description = False
            continue

        # Dialogue line
        if is_dialogue_line(line):
            skip_description = False
            # Split concatenated dialogues
            parts = split_dialogues(line)
            current_dialogues.extend(parts)
            continue

        # Description/bullet lines between type header and scenario — skip
        if skip_description:
            continue

    # Flush last items
    flush_scenario()

    return scenarios


# ─── Merge logic ───────────────────────────────────────────────────────────────
def normalise_for_comparison(text: str) -> str:
    """Normalise a scenario string for deduplication comparison."""
    # Remove all kinds of quotes
    s = text
    for ch in '"\'""\u201c\u201d\u2018\u2019\u00ab\u00bb':
        s = s.replace(ch, "")
    # Remove trailing punctuation and whitespace
    s = re.sub(r"[\s.,;:!?•]+$", "", s)
    s = re.sub(r"^[\s.,;:!?•]+", "", s)
    # Collapse whitespace and lowercase
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def merge_scenarios(existing: list[dict], new: list[dict]) -> tuple[list[dict], int]:
    """
    Merge new scenarios into existing list, avoiding duplicates.
    Returns (merged_list, count_of_new_scenarios_added).
    """
    existing_scenarios = set()
    for item in existing:
        key = normalise_for_comparison(item["parameters"]["scenario"])
        existing_scenarios.add(key)

    added = 0
    for item in new:
        key = normalise_for_comparison(item["parameters"]["scenario"])
        if key not in existing_scenarios:
            existing.append(item)
            existing_scenarios.add(key)
            added += 1

    return existing, added


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    write_mode = "--write" in sys.argv

    if not FWD_DIR.exists():
        print(f"ERROR: {FWD_DIR} does not exist.")
        sys.exit(1)
    if not DATASET_DIR.exists():
        print(f"ERROR: {DATASET_DIR} does not exist.")
        sys.exit(1)

    print("=" * 60)
    print("  fwddataset → JSON Converter & Merger")
    print("=" * 60)
    if not write_mode:
        print("  (DRY RUN — pass --write to save changes)\n")
    else:
        print("  (WRITE MODE — changes will be saved)\n")

    total_new = 0
    total_existing = 0

    for filename in sorted(os.listdir(FWD_DIR)):
        filepath = FWD_DIR / filename
        ext = filepath.suffix.lower()

        if ext == ".odt":
            lines = read_odt(str(filepath))
        elif ext == ".docx" and filename != "Bias Taxonomy.docx":
            lines = read_docx(str(filepath))
        else:
            continue

        # Determine which JSON file this maps to
        file_num = re.match(r"^(\d+)", filename)
        if not file_num:
            print(f"  SKIP: {filename} (no number prefix)")
            continue
        num = file_num.group(1)
        if num not in FILE_MAP:
            print(f"  SKIP: {filename} (no mapping for number {num})")
            continue

        json_key = FILE_MAP[num]
        json_filename = f"bias_data_for_type_{json_key}.json"
        json_path = DATASET_DIR / json_filename

        # Parse the document
        new_scenarios = parse_document(lines)

        # Load existing JSON
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        old_count = len(existing)

        # Merge
        merged, added = merge_scenarios(existing, new_scenarios)

        total_new += added
        total_existing += old_count

        # Count conversations
        new_convs = sum(len(s["parameters"]["conversations"]) for s in new_scenarios)

        status = f"+{added} new" if added > 0 else "no new"
        print(f"  {filename}")
        print(f"    → Parsed: {len(new_scenarios)} scenarios, {new_convs} conversations")
        print(f"    → Existing: {old_count} scenarios")
        print(f"    → Result: {len(merged)} scenarios ({status})")

        if write_mode and added > 0:
            # Backup existing
            backup_path = json_path.with_suffix(".json.bak")
            if json_path.exists():
                import shutil
                shutil.copy2(json_path, backup_path)
                print(f"    → Backup: {backup_path.name}")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=4, ensure_ascii=False)
            print(f"    → Saved: {json_filename}")
        print()

    print("=" * 60)
    print(f"  Summary: {total_new} new scenarios to add to {total_existing} existing")
    if not write_mode and total_new > 0:
        print("  Run with --write to save changes.")
    elif write_mode and total_new > 0:
        print("  ✅ All changes saved!")
    else:
        print("  ✅ Dataset is already up to date.")
    print("=" * 60)


if __name__ == "__main__":
    main()
