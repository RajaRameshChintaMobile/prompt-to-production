"""
UC-0A — Complaint Classifier
Rule-based classifier enforcing strict taxonomy, severity-driven priority,
cited reasons, and ambiguity flagging per the UC-0A schema.
"""
import argparse
import csv
import re

# Exact allowed category strings — no variations permitted
ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]
#Raja
# Any of these words in the description must trigger Urgent priority
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

# Ordered category rules — more specific / higher-priority patterns listed first.
# Each entry: (category_name, [regex_patterns_on_lowercased_description])
CATEGORY_PATTERNS = [
    ("Noise", [
        r"\bnoise\b", r"\bdrilling\b", r"\bblaring\b", r"\bloud\b",
        r"\bidling\b", r"\bengines?\s+on\b",
    ]),
    ("Heat Hazard", [
        r"\bheat\s*hazard\b", r"\bheatwave\b", r"\bextreme\s+heat\b", r"\bheat\s+wave\b",
    ]),
    ("Heritage Damage", [
        r"\bheritage\b", r"\bmonument\b", r"\bhistoric(al)?\b",
    ]),
    ("Drain Blockage", [
        r"\bdrain\b.*\bblocked\b", r"\bblocked\b.*\bdrain\b",
        r"\bdrain\s+blockage\b", r"\bstormwater\s+drain\b",
        r"\bdrain\s+completely\b",
    ]),
    ("Flooding", [
        r"\bfloods?\b", r"\bflooded\b", r"\bflooding\b",
        r"\bwaterlogg(ed|ing)\b", r"\binundated\b", r"\brainwater\b",
    ]),
    ("Pothole", [
        r"\bpot[\s-]?holes?\b",
    ]),
    ("Streetlight", [
        r"\bstreet[\s-]?light\b", r"\bno\s+light\b", r"\blamp\s+post\b",
        r"\blighting\s+(not|broken|out|faulty)\b",
    ]),
    ("Waste", [
        r"\bgarbage\b", r"\bwaste\b", r"\blitter\b",
        r"\bsolid\s+waste\b", r"\boverflow\b", r"\bnot\s+cleared\b",
    ]),
    ("Road Damage", [
        r"\broad\s+collapse", r"\bcollapsed\b", r"\bcrater\b",
        r"\broad\s+damage\b", r"\broad\s+crack\b",
    ]),
]


def _detect_categories(description: str) -> list:
    """Return list of all matching category names for the description."""
    desc_lower = description.lower()
    matches = []
    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, desc_lower):
                if category not in matches:
                    matches.append(category)
                break
    return matches if matches else ["Other"]


def _detect_priority(description: str) -> str:
    """Return Urgent if any severity keyword is present, else Standard."""
    desc_lower = description.lower()
    for kw in SEVERITY_KEYWORDS:
        # Use startswith-aware substring so 'collapse' matches 'collapsed'
        if re.search(r"\b" + kw, desc_lower):
            return "Urgent"
    return "Standard"


def _make_reason(description: str, category: str, priority: str) -> str:
    """One-sentence reason citing specific words from description."""
    desc_lower = description.lower()
    # Cite severity keyword when Urgent
    if priority == "Urgent":
        for kw in SEVERITY_KEYWORDS:
            if re.search(r"\b" + kw, desc_lower):
                snippet = description[:120].rstrip()
                return (
                    f"Classified as {category} and marked Urgent because "
                    f"description contains '{kw}': \"{snippet}\"."
                )
    # Cite first matching category keyword otherwise
    for cat, patterns in CATEGORY_PATTERNS:
        if cat == category:
            for pattern in patterns:
                m = re.search(pattern, desc_lower)
                if m:
                    snippet = description[:120].rstrip()
                    return (
                        f"Classified as {category} based on keyword "
                        f"'{m.group(0)}' in: \"{snippet}\"."
                    )
    snippet = description[:120].rstrip()
    return f"Classified as {category} from description: \"{snippet}\"."


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Input:  dict with at least keys: complaint_id, description
    Output: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = (row.get("description") or "").strip()
    complaint_id = row.get("complaint_id", "")

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "No description provided — cannot classify.",
            "flag": "NEEDS_REVIEW",
        }

    matched = _detect_categories(description)
    category = matched[0]                        # highest-priority match wins
    ambiguous = len(matched) > 1 or category == "Other"
    priority = _detect_priority(description)
    reason = _make_reason(description, category, priority)
    flag = "NEEDS_REVIEW" if ambiguous else ""

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Never crashes: bad rows are written with category=Other and flag=NEEDS_REVIEW.
    """
    output_fields = ["complaint_id", "category", "priority", "reason", "flag"]
    results = []

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                result = classify_complaint(row)
            except Exception as exc:
                result = {
                    "complaint_id": row.get("complaint_id", ""),
                    "category": "Other",
                    "priority": "Low",
                    "reason": f"Classification error: {exc}",
                    "flag": "NEEDS_REVIEW",
                }
            results.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
