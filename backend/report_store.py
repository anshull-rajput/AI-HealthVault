"""Small local persistence layer for saved medical reports.

The app deliberately keeps reports on the computer running Streamlit.  SQLite
is included with Python, so this remains easy to explain and deploy in a demo.
"""

import json
import re
import shutil
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REPORT_DIR = DATA_DIR / "reports"
DATABASE_PATH = DATA_DIR / "healthvault.db"


def _connection():
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        report_name TEXT NOT NULL,
        report_date TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        saved_path TEXT NOT NULL,
        extracted_text TEXT NOT NULL,
        lab_values TEXT NOT NULL,
        created_at TEXT NOT NULL
        )"""
    )
    return connection


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


def save_report(uploaded_file, report_name, report_date, extracted_text, lab_values):
    report_id = str(uuid.uuid4())
    safe_suffix = Path(uploaded_file.name).suffix.lower() or ".pdf"
    saved_filename = f"{report_id}{safe_suffix}"
    destination = REPORT_DIR / saved_filename
    uploaded_file.seek(0)
    with destination.open("wb") as output:
        shutil.copyfileobj(uploaded_file, output)

    with _connection() as connection:
        connection.execute(
            """INSERT INTO reports
            (id, report_name, report_date, original_filename, saved_path, extracted_text, lab_values, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report_id,
                report_name.strip(),
                report_date.isoformat() if isinstance(report_date, date) else str(report_date),
                uploaded_file.name,
                str(destination),
                extracted_text,
                json.dumps(lab_values),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    return report_id


def list_reports():
    with _connection() as connection:
        rows = connection.execute("SELECT * FROM reports ORDER BY report_date, created_at").fetchall()
    reports = []
    for row in rows:
        report = dict(row)
        report["lab_values"] = json.loads(report["lab_values"])
        reports.append(report)
    return reports


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
