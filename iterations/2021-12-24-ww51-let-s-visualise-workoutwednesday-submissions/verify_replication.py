"""Verify the WW51 submission tracker from structure and raw Hyper facts."""

from __future__ import annotations

import csv
import hashlib
import datetime as dt
import json
import zipfile
from pathlib import Path

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
HEATMAP = "Heatmap"
TYPE_BAR = "Submission Type Bar"
CHALLENGE_BAR = "Challenges Bar"
DASHBOARD = "2021_12_22_WOW_Submission_Tracker"
EXPECTED_SHEETS = {HEATMAP, TYPE_BAR, CHALLENGE_BAR}


def workbook_root() -> etree._Element:
    with zipfile.ZipFile(OUTPUT) as archive:
        entry = next(name for name in archive.namelist() if name.endswith(".twb"))
        return etree.fromstring(archive.read(entry))


def worksheet(root: etree._Element, name: str) -> etree._Element:
    for sheet in root.iterfind("worksheets/worksheet"):
        if sheet.get("name") == name:
            return sheet
    raise AssertionError(f"missing worksheet {name}")


def formulas(root: etree._Element) -> dict[str, str]:
    return {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.iterfind(".//datasource/column")
        if column.find("calculation") is not None
    }


def oracle() -> dict[str, int]:
    data = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(data)) as connection:
            total = connection.execute_scalar_query(
                'SELECT COUNT(*) FROM "Extract"."Extract"'
            )
            tableau = connection.execute_scalar_query(
                'SELECT COUNT(*) FROM "Extract"."Extract" WHERE "Software" = \'Tableau\''
            )
            days = connection.execute_scalar_query(
                'SELECT COUNT(DISTINCT DATE_TRUNC(\'day\',"Timestamp")) '
                'FROM "Extract"."Extract" WHERE "Software" = \'Tableau\''
            )
    return {"rows": int(total), "tableau_rows": int(tableau), "tableau_days": int(days)}


def verify() -> None:
    if not OUTPUT.is_file():
        raise AssertionError(f"missing output {OUTPUT}")
    TWBEditor.open_existing(OUTPUT)
    root = workbook_root()
    available = {sheet.get("name") for sheet in root.iterfind("worksheets/worksheet")}
    # acceptance: workbook-structure
    if not EXPECTED_SHEETS.issubset(available):
        raise AssertionError(f"missing worksheets: {EXPECTED_SHEETS - available}")

    calc = formulas(root)
    expected_formulas = {
        "Week Submitted": "DATEPART('week',[Timestamp])",
        "Weekday Submitted": "LEFT(DATENAME('weekday',[Timestamp]),3)",
        "Submissions": "COUNT([Timestamp])",
        "Challenge Submitted": "STR([Challenge Year])+'w'+STR([Challenge Week])",
    }
    # acceptance: derived-fields
    for caption, formula in expected_formulas.items():
        if calc.get(caption, "").replace(" ", "") != formula.replace(" ", ""):
            raise AssertionError(f"{caption} formula mismatch: {calc.get(caption)!r}")
    if "RANK_PERCENTILE" not in calc.get("Percentile of Submissions", ""):
        raise AssertionError("Percentile of Submissions must be a rank percentile")
    same_week_formula = calc.get("Same Week Submission", "")
    if (
        "Same Week Submission" not in same_week_formula
        or "Other Submission" not in same_week_formula
    ):
        raise AssertionError("same-week calculation must emit both labels")

    heatmap = worksheet(root, HEATMAP)
    heatmap_text = etree.tostring(heatmap, encoding="unicode")
    for required in ("Week Submitted", "Weekday Submitted", "Percentile of Submissions"):
        if required not in heatmap_text:
            raise AssertionError(f"{HEATMAP} missing {required}")

    # acceptance: software-filter
    for sheet_name in EXPECTED_SHEETS:
        text = etree.tostring(worksheet(root, sheet_name), encoding="unicode")
        if "Software" not in text or "Tableau" not in text:
            raise AssertionError(f"{sheet_name} is missing the Tableau software filter")

    # acceptance: selection-action
    actions = [
        action for action in root.iterfind("actions/action")
        if "selected day" in action.get("caption", "").casefold()
    ]
    if len(actions) != 1:
        raise AssertionError("missing heatmap-to-bars filter action")
    action = actions[0]
    source = action.find("source")
    command = action.find("command")
    params = {p.get("name"): p.get("value") for p in command.findall("param")}
    if source.get("worksheet") != HEATMAP or source.get("dashboard") != DASHBOARD:
        raise AssertionError("selection action must originate in this dashboard's Heatmap")
    if command.get("command") != "tsc:tsl-filter" or params != {
        "exclude": HEATMAP, "special-fields": "all", "target": DASHBOARD, "on-empty": "none"
    }:
        raise AssertionError("action must filter both bars and clear to no members")
    for name in (TYPE_BAR, CHALLENGE_BAR):
        filters = worksheet(root, name).findall("table/view/filter")
        selected = [
            f for f in filters
            if f.find(".//groupfilter[@function='empty-level']") is not None
        ]
        if len(selected) != 1 or len(selected[0].findall(".//groupfilter[@function='empty-level']")) != 3:
            raise AssertionError(f"{name} must start with an empty three-level day selection")

    dashboard = next(
        dashboard
        for dashboard in root.iterfind("dashboards/dashboard")
        if dashboard.get("name") == DASHBOARD
    )
    # acceptance: dashboard-layout
    size = dashboard.find("size")
    if (size.get("minwidth"), size.get("minheight")) != ("1100", "890"):
        raise AssertionError(f"dashboard size mismatch: {size.attrib}")
    if size.get("sizing-mode") != "fixed":
        raise AssertionError("dashboard must be fixed size")

    # acceptance: raw-data-oracle
    facts = oracle()
    if facts != {"rows": 8627, "tableau_rows": 6963, "tableau_days": 1291}:
        raise AssertionError(f"unexpected Hyper facts: {facts}")
    csv_path = HERE / "outputs" / "cloud-replica-heatmap.csv"
    if csv_path.exists():
        data = next((HERE / "inputs").glob("*.hyper"))
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
            with Connection(hyper.endpoint, str(data)) as connection:
                raw = connection.execute_list_query(
                    'SELECT CAST("Timestamp" AS DATE), COUNT(*) FROM "Extract"."Extract" '
                    'WHERE "Software" = \'Tableau\' GROUP BY 1'
                )
        expected = {str(day): int(count) for day, count in raw}
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            exported = {
                dt.datetime.strptime(row["Day of Timestamp"], "%B %d, %Y").date().isoformat():
                int(row["Submissions"].replace(",", ""))
                for row in csv.DictReader(handle)
            }
        if expected != exported:
            raise AssertionError("Cloud heatmap daily submission counts differ from Hyper")
    with zipfile.ZipFile(OUTPUT) as archive:
        data = next((HERE / "inputs").glob("*.hyper"))
        member = next(n for n in archive.namelist() if n.endswith(".hyper"))
        if hashlib.sha256(archive.read(member)).digest() != hashlib.sha256(data.read_bytes()).digest():
            raise AssertionError("Packaged Hyper differs from the independently queried input")
    evidence = HERE / "evidence" / "cloud-verification.json"
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    if payload.get("status") != "captured_requires_independent_review":
        raise AssertionError("unexpected Cloud evidence status")
    for filename in (
        "cloud-author.png",
        "cloud-replica.png",
        "cloud-author-dashboard.csv",
        "cloud-replica-dashboard.csv",
    ):
        if not (HERE / "outputs" / filename).is_file():
            raise AssertionError(f"missing Cloud artifact {filename}")
    for filename in ("cloud-author-dashboard.csv", "cloud-replica-dashboard.csv"):
        with (HERE / "outputs" / filename).open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
            if any(cell.strip() for row in rows for cell in row):
                raise AssertionError(f"{filename} should be empty for a dashboard crosstab")

    print(
        "PASS: 8627 rows, 6963 Tableau rows, 1291 Tableau days; "
        "3 worksheets, 1 dashboard action, fixed 1100x890 dashboard"
    )


if __name__ == "__main__":
    verify()
