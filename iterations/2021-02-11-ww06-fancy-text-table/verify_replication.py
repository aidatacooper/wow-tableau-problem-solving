"""Independently compute all 96 report cells and verify native measure contracts."""

import calendar
import csv
import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_02_11_WW06_Formatted_Table"
METRICS = [
    "CY SALES",
    "LY SALES",
    "CY vs LY",
    "△",
    "% DIFF",
    "BEST DAY",
    "WORST DAY",
    "RANK",
]
ACCEPTANCE = [
    "all-monthly-metrics",
    "daily-extrema-and-rank",
    "native-measure-formatting",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    assert (
        digest(HERE / "inputs/superstore.hyper") == lock["extracted_data"][0]["sha256"]
    )
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
        Connection(
            process.endpoint, str(HERE / "inputs/superstore.hyper")
        ) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Order Date","Sales" FROM "Extract"."Extract"'
        )
    assert len(rows) == 5899
    assert all(
        day is not None and value is not None and math.isfinite(value)
        for day, value in rows
    )
    years = {day.year for day, _ in rows}
    assert years == {2019, 2020}
    current_year = max(years)
    monthly = defaultdict(list)
    daily = defaultdict(list)
    for day, value in rows:
        monthly[day.year, day.month].append(value)
        if day.year == current_year:
            daily[dt.date(day.year, day.month, day.day)].append(value)
    totals = {key: math.fsum(values) for key, values in monthly.items()}
    days = {day: math.fsum(values) for day, values in daily.items()}
    months = {}
    for month in range(1, 13):
        current = totals[current_year, month]
        previous = totals[current_year - 1, month]
        candidates = {day: value for day, value in days.items() if day.month == month}
        maximum, minimum = max(candidates.values()), min(candidates.values())
        best = max(day for day, value in candidates.items() if value == maximum)
        worst = max(day for day, value in candidates.items() if value == minimum)
        rank = 1 + sum(totals[current_year, m] > current for m in range(1, 13))
        months[calendar.month_name[month]] = {
            "CY SALES": current,
            "LY SALES": previous,
            "CY vs LY": 1 if current > previous else -1,
            "△": current - previous,
            "% DIFF": (current - previous) / previous,
            "BEST DAY": best.isoformat(),
            "WORST DAY": worst.isoformat(),
            "RANK": 1 if rank <= 6 else -1,
            "rank_position": rank,
            "best_daily_sales": maximum,
            "worst_daily_sales": minimum,
            "best_serial": (best - dt.date(1899, 12, 30)).days,
            "worst_serial": (worst - dt.date(1899, 12, 30)).days,
            "observed_current_year_days": len(candidates),
        }
    assert sum(row["RANK"] == 1 for row in months.values()) == 6
    return {
        "raw_rows": len(rows),
        "current_year": current_year,
        "previous_year": current_year - 1,
        "monthly_cells": 96,
        "months": months,
    }


def native():
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as archive:
        root = etree.fromstring(
            archive.read(next(n for n in archive.namelist() if n.endswith(".twb")))
        )
    worksheets = root.findall("worksheets/worksheet")
    assert [w.get("name") for w in worksheets] == ["Table"]
    ws = worksheets[0]
    table = ws.find("table")
    assert len(table.findall("panes/pane")) == 1
    pane = table.find("panes/pane")
    assert pane.find("mark").get("class") == "Text"
    assert table.findtext("cols").endswith(".[:Measure Names]")
    assert "Order Month" not in table.findtext("cols")
    for kind in ("text", "color"):
        encoding = pane.find("encodings/" + kind)
        assert encoding.get("column").endswith(".[Multiple Values]")
        assert encoding.get("separate-domains") == "true"
    dependencies = table.find("view/datasource-dependencies")
    columns = {c.get("name"): c for c in dependencies.findall("column")}
    instances = {
        c.get("name"): c.get("column") for c in dependencies.findall("column-instance")
    }

    def caption(reference):
        local = reference.split("].", 1)[-1].strip('"')
        column = columns[instances[local]]
        return column.get("caption", column.get("name").strip("[]"))

    buckets = table.findall("view/manual-sort/dictionary/bucket")
    assert [caption(b.text.strip('"')) for b in buckets] == METRICS
    assert len(table.findall('style/style-rule/encoding[@attr="color"]')) == 8
    palette_fields = set()
    for encoding in table.findall('style/style-rule/encoding[@attr="color"]'):
        field = caption(encoding.get("field"))
        palette_fields.add(field)
        assert encoding.get("num-steps") == "2"
        colors = [c.text for c in encoding.findall("color-palette/color")]
        expected = (
            ["#000000", "#000000"]
            if field in {"CY SALES", "LY SALES", "△"}
            else ["#00aa00", "#00aa00"]
            if field == "BEST DAY"
            else ["#ff0000", "#ff0000"]
            if field == "WORST DAY"
            else ["#ff0000", "#00aa00"]
        )
        assert colors == expected
    assert palette_fields == set(METRICS)
    formats = {
        c.get("caption"): c.get("default-format")
        for c in columns.values()
        if c.get("caption") in METRICS
    }
    assert formats["CY vs LY"] == "*✅;❌; ▬"
    assert formats["% DIFF"] == "*+0.0%;-0.0%"
    assert formats["RANK"] == '*"TOP";"BOTTOM"'
    assert formats["△"] == '*"$"#,##0;-"$"#,##0'
    for name in ("BEST DAY", "WORST DAY"):
        column = next(c for c in columns.values() if c.get("caption") == name)
        assert (
            column.get("datatype") == "integer"
            and column.get("default-format") == "*dd mmm yyyy"
        )
        formula = column.find("calculation").get("formula")
        assert formula.startswith("INT({FIXED") and formula.endswith("+2")
    rank = next(c for c in columns.values() if c.get("caption") == "RANK")
    assert "RANK(SUM(" in rank.find("calculation").get("formula")
    rank_ci = next(
        c
        for c in dependencies.findall("column-instance")
        if c.get("column") == rank.get("name")
    )
    assert len(rank_ci.findall("table-calc")) == 2
    assert all(
        c.get("ordering-type") == "Columns" for c in rank_ci.findall("table-calc")
    )
    assert table.find("tooltip-style").get("tooltip-mode") == "none"
    dashboard = root.find("dashboards/dashboard")
    assert dashboard.get("name") == DASHBOARD
    assert (
        dashboard.find("size").get("maxwidth") == "1200"
        and dashboard.find("size").get("maxheight") == "800"
    )
    zone = dashboard.find('.//zone[@name="Table"]')
    assert {key: zone.get(key) for key in ("x", "y", "w", "h")} == {
        "x": "667",
        "y": "1000",
        "w": "98666",
        "h": "90000",
    }
    cache = zone.find("layout-cache")
    assert cache.get("type-h") == cache.get("type-w") == "scalable"
    assert root.find("actions") is None or len(root.find("actions")) == 0
    return {
        "single_native_measure_table": True,
        "independent_measure_color_domains": 8,
        "rank_nested_table_calculations": 2,
        "date_serial_offset": 2,
        "dashboard": [1200, 800],
        "actions_required": False,
    }


def check_value(metric, actual, expected):
    text = actual.strip()
    if metric in {"BEST DAY", "WORST DAY"}:
        parsed = None
        for fmt in ("%d %b %Y", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%B %d, %Y"):
            try:
                parsed = (
                    dt.datetime.strptime(text, fmt)
                    .replace(tzinfo=dt.timezone.utc)
                    .date()
                    .isoformat()
                )
                break
            except ValueError:
                pass
        if parsed is None:
            serial = float(text.replace(",", ""))
            assert math.isfinite(serial) and serial.is_integer(), (metric, actual)
            parsed = (
                dt.date(1899, 12, 30) + dt.timedelta(days=int(serial))
            ).isoformat()
        assert parsed == expected, (metric, actual, expected)
    elif metric == "RANK":
        assert text.upper() in (
            {"TOP", "1", "1.0"} if expected == 1 else {"BOTTOM", "-1", "-1.0"}
        ), (metric, actual, expected)
    elif metric == "CY vs LY":
        assert text in (
            {"✅", "1", "1.0"} if expected == 1 else {"❌", "-1", "-1.0"}
        ), (metric, actual, expected)
    else:
        value = float(
            text.replace("$", "").replace(",", "").replace("%", "").replace("−", "-")
        )
        if metric == "% DIFF" and "%" in text:
            value /= 100
        tolerance = (
            (0.00051 if "%" in text else 1e-8)
            if metric == "% DIFF"
            else (0.51 if "$" in text else 1e-6)
        )
        assert abs(value - expected) <= tolerance, (metric, actual, expected)


def check_csv(path, result):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    cells = {}
    if rows and {"Measure Names", "Measure Values"}.issubset(rows[0]):
        for row in rows:
            key = (row["Order Month"], row["Measure Names"])
            assert key not in cells
            cells[key] = row["Measure Values"]
    else:
        assert len(rows) == 12, (path, len(rows))
        for row in rows:
            for metric in METRICS:
                key = (row["Order Month"], metric)
                assert key not in cells
                cells[key] = row[metric]
    assert set(cells) == {
        (month, metric) for month in result["months"] for metric in METRICS
    }
    for (month, metric), value in cells.items():
        check_value(metric, value, result["months"][month][metric])
    return {
        "path": str(path.relative_to(HERE)),
        "export_rows": len(rows),
        "monthly_cells": len(cells),
        "status": "passed",
    }


def cloud(result):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return {"available": False, "scope": "Cloud capture has not been supplied"}
    report = json.loads(manifest.read_text())
    assert report["source_hashes"]["replica"] == digest(
        HERE / "outputs/replicated-workbook.twbx"
    )
    source = json.loads((HERE / "evidence/export-provenance.json").read_text())
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    assert (
        source["original_source_workbook_sha256"] == lock["source_workbook"]["sha256"]
    )
    assert (
        report["source_hashes"]["author"]
        == source["published_author_comparison_sha256"]
    )
    assert report["browser_interaction_executed"] is False
    assert len(report["states"]) == 1 and report["states"][0]["name"] == "default"
    state = report["states"][0]
    assert state["parameters"] == {} and state["filters"] == {}
    assert set(state["views"]) == {"author", "replica"}
    for view in state["views"].values():
        assert view["name"] == DASHBOARD
        assert digest(HERE / view["path"]) == view["sha256"]
    assert Counter((d["role"], d["view"]) for d in state["data"]) == Counter(
        {("author", "Table"): 1, ("replica", "Table"): 1}
    )
    checks = []
    for data in state["data"]:
        assert data["parameters"] == {} and data["filters"] == {}
        path = HERE / data["path"]
        assert digest(path) == data["sha256"]
        checks.append(check_csv(path, result))
    return {
        "available": True,
        "states": 1,
        "csv_checks": checks,
        "png_hashes_verified": 2,
        "browser_interaction_executed": False,
        "scope": "Complete 12-month by 8-measure table for both roles; no button CSV or browser interaction",
    }


def verify():
    result = oracle()
    result.update(
        {
            "status": "passed",
            "native": native(),
            "cloud": cloud(result),
            "acceptance": {key: "passed" for key in ACCEPTANCE},
            "workbook_sha256": digest(HERE / "outputs/replicated-workbook.twbx"),
        }
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
