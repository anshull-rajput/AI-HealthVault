"""Session-only helpers for report history and lab-value comparison.

This module deliberately does not write PDFs, report text, or report history to
disk. The Streamlit app keeps the returned report records in ``st.session_state``
so a browser session can compare its own reports without exposing them to other
visitors of a deployed app.
"""

import re
import uuid
from datetime import date, datetime


def extract_lab_values(report_text):
    """Return likely lab measurements found in text-based PDF lines.

    This is intentionally a simple, explainable heuristic, not a clinical
    parser. Users can see the extracted values before saving.
    """
    values = []
    ignored_labels = ("date", "age", "patient", "phone", "report", "page", "sample", "lab no")
    pattern = re.compile(
        r"^\s*(?P<label>[A-Za-z][A-Za-z0-9 /()%+_.-]{2,70}?)\s*(?::|\t| +)\s*"
        r"(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-zµ/%^0-9.-]{0,20})",
        re.IGNORECASE,
    )
    seen = set()
    for line in report_text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        label = " ".join(match.group("label").split()).strip(" -:")
        normalized_label = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
        if not normalized_label or any(word in normalized_label for word in ignored_labels):
            continue
        unit = match.group("unit").strip()
        # A bare number in a PDF header is not useful as a lab measurement.
        if not unit and len(label.split()) < 2:
            continue
        key = (normalized_label, match.group("value"), unit.lower())
        if key in seen:
            continue
        seen.add(key)
        values.append(
            {
                "label": label,
                "normalized_label": normalized_label,
                "value": float(match.group("value")),
                "unit": unit or "(unit not found)",
            }
        )
    return values[:100]


def save_report(original_filename, report_name, report_date, lab_values):
    """Create an in-memory history record without retaining the PDF or its text."""
    return {
        "id": str(uuid.uuid4()),
        "report_name": report_name.strip(),
        "report_date": report_date.isoformat() if isinstance(report_date, date) else str(report_date),
        "original_filename": original_filename,
        "lab_values": lab_values,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def list_reports(reports):
    """Return the current session's report records in date order."""
    return sorted(reports, key=lambda report: (report["report_date"], report["created_at"]))


def available_tests(reports):
    return sorted({value["normalized_label"] for report in reports for value in report["lab_values"]})


def compare_test(reports, normalized_label):
    """Build comparison rows, only retaining a consistent measurement unit."""
    rows = []
    for report in reports:
        for value in report["lab_values"]:
            if value["normalized_label"] == normalized_label:
                rows.append(
                    {
                        "Date": report["report_date"],
                        "Report": report["report_name"],
                        "Value": value["value"],
                        "Unit": value["unit"],
                        "Test": value["label"],
                    }
                )
                break
    if not rows:
        return [], None
    primary_unit = rows[0]["Unit"]
    rows = [row for row in rows if row["Unit"] == primary_unit]
    change = rows[-1]["Value"] - rows[0]["Value"] if len(rows) >= 2 else None
    return rows, change
