"""Independent complaint counts, sample standard deviations and native contracts."""

import csv
import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
STATES = {
    "default": ("Date Submitted", 3, 1),
    "received-3-years-1-std": ("Date Received", 3, 1),
    "submitted-1-year-2-std": ("Date Submitted", 1, 2),
    "received-5-years-3-std": ("Date Received", 5, 3),
}
ACCEPTANCE = [
    "weekly-complaint-counts",
    "year-partitioned-control-limits",
    "native-controls-drilldown",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def monday(value):
    day = dt.date(value.year, value.month, value.day)
    return day - dt.timedelta(days=day.weekday())


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(HERE / "inputs/consumer-complaints.hyper")) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Complaint ID","Date sent to company","Date received" FROM "Extract"."Extract"'
        )
    assert len(rows) == 75513
    assert len({row[0] for row in rows}) == len(rows)
    assert all(all(v is not None for v in row) for row in rows)
    counts = {
        "Date Submitted": Counter(monday(row[1]) for row in rows),
        "Date Received": Counter(monday(row[2]) for row in rows),
    }
    scenarios = {}
    for name, (basis, years, sigma) in STATES.items():
        scenarios[name] = calculate(counts[basis], years, sigma)
    # Cover the entire public parameter domain independently of the four REST states.
    domains = {}
    for basis, basis_counts in counts.items():
        for years in range(1, 6):
            for sigma in range(1, 4):
                value = calculate(basis_counts, years, sigma)
                domains[f"{basis}/{years}/{sigma}"] = {
                    "weekly_marks": len(value["marks"]),
                    "complaints": value["complaints"],
                    "year_limits": value["year_limits"],
                }
    return {
        "raw_rows": len(rows),
        "unique_complaints": len(rows),
        "week_start": "monday",
        "stddev": "sample, ddof=1",
        "strict_limits": True,
        "states": scenarios,
        "all_30_parameter_combinations": domains,
    }


def calculate(counts, years, sigma):
    latest = max(counts).year
    included = {
        day: n for day, n in counts.items() if day >= dt.date(latest - years + 1, 1, 1)
    }
    partitions = defaultdict(list)
    for day, n in included.items():
        partitions[day.year].append(n)
    limits = {}
    for year, values in sorted(partitions.items()):
        avg, spread = mean(values), stdev(values)
        limits[str(year)] = {
            "weekly_marks": len(values),
            "mean": avg,
            "sample_stdev": spread,
            "lower": avg - sigma * spread,
            "upper": avg + sigma * spread,
        }
    global_mean = mean(included.values())
    marks = []
    for day, n in sorted(included.items()):
        lim = limits[str(day.year)]
        week = (
            (day - dt.date(day.year, 1, 1)).days + dt.date(day.year, 1, 1).weekday()
        ) // 7 + 1
        marks.append(
            {
                "date_from": day.isoformat(),
                "date_to": (day + dt.timedelta(days=6)).isoformat(),
                "year": day.year,
                "week": week,
                "count": n,
                "mean": lim["mean"],
                "lower": lim["lower"],
                "upper": lim["upper"],
                "within": lim["lower"] < n < lim["upper"],
                "source_chart_within": global_mean - sigma * lim["sample_stdev"]
                < n
                < global_mean + sigma * lim["sample_stdev"],
            }
        )
    return {
        "latest_year": latest,
        "years": years,
        "sigma": sigma,
        "complaints": sum(included.values()),
        "source_chart_global_mean": global_mean,
        "marks": marks,
        "year_limits": limits,
    }


def native(root):
    ds = next(
        d
        for d in root.findall("datasources/datasource")
        if d.get("name") != "Parameters"
    )
    fields = {
        c.get("caption", c.get("name", "").strip("[]")): c for c in ds.findall("column")
    }

    def calc(name):
        formula = fields[name].find("calculation").get("formula")
        for caption, column in fields.items():
            formula = formula.replace(column.get("name"), "[" + caption + "]")
        return formula

    assert "DATETRUNC('week'" in calc("Date to Plot")
    assert "[Date sent to company]" in calc(
        "Date to Plot"
    ) and "[Date received]" in calc("Date to Plot")
    assert calc("Number of Complaints") == "COUNT([Complaint ID])"
    assert calc("Avg Complaints Per Year") == "WINDOW_AVG([Number of Complaints])"
    assert "WINDOW_STDEV([Number of Complaints])" in calc("Upper Limit")
    assert "WINDOW_STDEV([Number of Complaints])" in calc("Lower Limit")
    assert (
        calc("Within STD Limits?")
        == "[Number of Complaints]<[Upper Limit] AND [Number of Complaints]>[Lower Limit]"
    )
    assert ds.find("date-options").get("start-of-week") == "monday"
    chart = root.find("worksheets/worksheet[@name='Chart']")
    panes = chart.findall("table/panes/pane")
    assert [p.find("mark").get("class") for p in panes] == ["Line", "Circle"]
    assert (
        len(
            chart.findall(
                "table/style/style-rule[@element='axis']/encoding[@synchronized='true']"
            )
        )
        >= 1
    )
    assert "/" in chart.findtext("table/cols") and "+" in chart.findtext("table/rows")
    lines = panes[0].findall("reference-line")
    assert (
        len(lines) == 2
        and lines[0].get("paired-id") == lines[1].get("id")
        and lines[1].get("paired-id") == lines[0].get("id")
    )
    assert [l.get("formula") for l in lines] == ["min", "max"]
    assert all(l.get("value") is None for l in lines)
    deps = chart.find(
        f"table/view/datasource-dependencies[@datasource='{ds.get('name')}']"
    )
    for line, name in zip(lines, ["Lower Limit", "Upper Limit"]):
        ci = line.get("value-column").split("].", 1)[1]
        instance = deps.find(f"column-instance[@name='{ci}']")
        assert instance is not None and instance.get("column") == fields[name].get(
            "name"
        )
        tcs = instance.findall("table-calc")
        assert tcs and all(
            fields["Week Number"].get("name") in tc.get("ordering-field", "")
            for tc in tcs
        )
        assert all(tc.get("ordering-type") == "Field" for tc in tcs)
    within_ci = deps.find(
        f"column-instance[@column='{fields['Within STD Limits?'].get('name')}']"
    )
    contexts = within_ci.findall("table-calc")
    assert contexts[0].get("ordering-type") == "Rows"
    nested_avg = next(
        tc
        for tc in contexts
        if tc.get("field", "").endswith(fields["Avg Complaints Per Year"].get("name"))
    )
    assert (
        nested_avg.get("ordering-type") == "Rows"
        and nested_avg.get("ordering-field") is None
    )
    for caption in ["Upper Limit", "Lower Limit"]:
        nested = next(
            tc
            for tc in contexts
            if tc.get("field", "").endswith(fields[caption].get("name"))
        )
        assert nested.get("ordering-type") == "Field" and fields["Week Number"].get(
            "name"
        ) in nested.get("ordering-field", "")
    band = chart.find("table/style/style-rule[@element='refband']/format")
    assert band.get("value") == "#f5f5f5" and band.get("id") == lines[0].get("id")
    summary = root.find(
        "dashboards/dashboard[@name='2021_01_20_WW03_Control_Chart_Summary']"
    )
    assert (
        summary.find("size").get("maxwidth") == "900"
        and summary.find("size").get("maxheight") == "700"
    )
    button = summary.find("zones/zone/button")
    assert button is not None and button.get("active-visual-state-index") == "1"
    text = button.findtext("toggle-action")
    container_id = text.split("zone-ids=[")[1].split("]")[0]
    panel = next(z for z in summary.findall(".//zone") if z.get("id") == container_id)
    controls = panel.findall(".//zone")
    assert len(controls) == 3 and all(
        z.get("type-v2", z.get("type")) == "paramctrl"
        and z.get("hidden-by-user") == "true"
        for z in controls
    )
    action = root.find("actions/action[@caption='Click to Show Details']")
    assert action.find("activation").get("type") == "on-select"
    assert (
        action.find("source").get("dashboard") == summary.get("name")
        and action.find("source").get("worksheet") == "Chart"
    )
    command = {p.get("name"): p.get("value") for p in action.find("command")}
    assert (
        command["target"] == "2021_01_20_WW03_Control_Chart_Detail"
        and command["on-empty"] == "none"
    )
    assert all(
        fields[name].get("name") in unquote(action.find("link").get("expression"))
        for name in ["Year", "Week Number", "Dummy"]
    )
    detail = root.find("worksheets/worksheet[@name='Detail']")
    initial = next(
        f
        for f in detail.findall("table/view/filter")
        if "Action (" in f.get("column", "")
    )
    assert "NO_SELECTION" in etree.tostring(initial).decode()
    initial_members = {
        g.get("level"): g.get("member")
        for g in initial.findall("groupfilter/groupfilter")
    }
    assert initial.find("groupfilter").get("function") == "crossjoin"
    assert initial.find("groupfilter").get(
        "{http://www.tableausoftware.com/xml/user}ui-action-filter"
    ) == action.get("name")
    assert initial_members == {
        fields["Year"].get("name"): "0",
        fields["Week Number"].get("name"): "0",
        fields["Dummy"].get("name"): '"NO_SELECTION"',
    }
    title = detail.findtext("layout-options/title/formatted-text/run")
    assert (
        "[Parameters].[Parameter 1]" in title
        and fields["Date to Plot"].get("name").strip("[]") in title
    )
    date_ci = detail.find(
        f"table/view/datasource-dependencies/column-instance[@column='{fields['Date to Plot'].get('name')}']"
    )
    assert date_ci.get("name") in title
    detail_dashboard = root.find(
        "dashboards/dashboard[@name='2021_01_20_WW03_Control_Chart_Detail']"
    )
    detail_sheet = detail_dashboard.find(".//zone[@name='Detail']")
    assert {k: detail_sheet.get(k) for k in ["x", "y", "w", "h"]} == {
        "x": "889",
        "y": "1143",
        "w": "98222",
        "h": "97714",
    }
    back = detail_dashboard.find("zones/zone/button")
    assert {k: back.getparent().get(k) for k in ["x", "y", "w", "h"]} == {
        "x": "87000",
        "y": "1714",
        "w": "12444",
        "h": "3286",
    }
    summary_window = next(
        w
        for w in root.findall("windows/window")
        if w.get("class") == "dashboard" and w.get("name") == summary.get("name")
    )
    assert summary_window.find("simple-id").get("uuid") in back.get("action")
    assert panel.getparent().tag == "zones"
    assert {k: panel.get(k) for k in ["x", "y", "w", "h"]} == {
        "x": "78556",
        "y": "4714",
        "w": "20444",
        "h": "33286",
    }
    assert (
        root.find(
            "dashboards/dashboard[@name='2021_01_20_WW03_Control_Chart_Detail']//button"
        )
        .get("action")
        .startswith("tabdoc:goto-sheet")
    )
    assert (
        root.find("actions/action[@caption='Highlight Dummy']/command").get("command")
        == "tsc:brush"
    )
    assert all(p.find("customized-tooltip") is not None for p in panes)
    return {
        "layers": ["Line", "Circle"],
        "dynamic_reference_band": True,
        "chart_nested_average_scope": "all visible weeks",
        "band_average_scope": "each year",
        "controls_hidden_initially": True,
        "filter_event": "on-select",
        "filter_clear": "none",
        "detail_initial_empty": True,
        "back_navigation": True,
        "browser_interactions_executed": False,
    }


def verify():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"]:
        assert digest(HERE / item["file"]) == item["sha256"]
    workbook = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(workbook) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    independent = oracle()
    contract = native(root)
    cloud = (
        verify_cloud(independent)
        if (HERE / "evidence/cloud-verification.json").exists()
        else {"available": False, "status": "not_captured"}
    )
    result = {
        "status": "passed",
        "acceptance_ids": ACCEPTANCE,
        "workbook_sha256": digest(workbook),
        "raw_data": independent,
        "native_contracts": contract,
        "cloud": cloud,
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "raw_rows": independent["raw_rows"],
                "states": {
                    k: len(v["marks"]) for k, v in independent["states"].items()
                },
                "cloud": cloud,
            },
            indent=2,
        )
    )
    return result


def verify_cloud(independent):
    manifest = json.loads((HERE / "evidence/cloud-verification.json").read_text())
    assert manifest["source_hashes"]["replica"] == digest(
        HERE / "outputs/replicated-workbook.twbx"
    )
    assert {s["name"] for s in manifest["states"]} == set(STATES)
    assert manifest["browser_interaction_executed"] is False
    export = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert (
        manifest["source_hashes"]["author"]
        == export["published_author_comparison_sha256"]
    )
    checks = []
    for state in manifest["states"]:
        parameters = {
            "Select a Date": "Date Submitted",
            "Latest X Years": "3",
            "STD": "1",
            **state["parameters"],
        }
        assert (
            parameters["Select a Date"],
            int(parameters["Latest X Years"]),
            int(parameters["STD"]),
        ) == STATES[state["name"]]
        assert state["filters"] == {}
        assert set(state["views"]) == {"author", "replica"}
        assert {(item["role"], item["view"]) for item in state["data"]} == {
            (role, sheet)
            for role in ["author", "replica"]
            for sheet in ["Chart", "Data"]
        }
        for image in state["views"].values():
            assert image["name"] == "2021_01_20_WW03_Control_Chart_Summary"
            assert digest(HERE / image["path"]) == image["sha256"]
        for item in state["data"]:
            assert (
                item["parameters"] == state["parameters"]
                and item["filters"] == state["filters"]
            )
            path = HERE / item["path"]
            assert digest(path) == item["sha256"]
            checks.append(check_csv(path, independent["states"][state["name"]], item))
    return {
        "available": True,
        "states": len(manifest["states"]),
        "csv_checks": checks,
        "default_detail": verify_detail(manifest)
        if (HERE / "evidence/cloud-detail-default.json").exists()
        else {"available": False},
        "browser_interactions_executed": False,
    }


def datevalue(value, role, textual=False):
    if textual:
        return (
            dt.datetime.strptime(value, "%d %B %Y")
            .replace(tzinfo=dt.timezone.utc)
            .date()
            .isoformat()
        )
    pattern = "%m/%d/%Y" if role == "author" else "%d/%m/%Y"
    return (
        dt.datetime.strptime(value, pattern)
        .replace(tzinfo=dt.timezone.utc)
        .date()
        .isoformat()
    )


def numeric(value):
    return float(value.replace(",", ""))


def check_csv(path, expected, item):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert rows, "Unexpectedly empty export: " + str(path)
    role, sheet = item["role"], item["view"]
    marks = {m["date_from"]: m for m in expected["marks"]}
    limits = expected["year_limits"]
    coverage = defaultdict(set)
    count_values = {}
    dense_count_blanks = 0
    checked_values = 0
    seen = Counter()
    for row in rows:
        day = (
            datevalue(row["Date to Plot"], role, textual=True)
            if row.get("Date to Plot")
            else datevalue(row["Date From"], role)
        )
        assert day in marks, (path.name, day)
        year = row["Year"]
        assert year in limits
        mark = marks[day]
        if sheet == "Chart":
            seen[day] += 1
            assert int(year) == mark["year"]
            for field, key in [
                ("Number of Complaints", "count"),
                ("Lower Limit", "lower"),
                ("Upper Limit", "upper"),
            ]:
                assert row[field], (path.name, day, field, "missing")
                assert math.isclose(numeric(row[field]), mark[key], abs_tol=0.011), (
                    path.name,
                    day,
                    field,
                    row[field],
                    mark[key],
                )
                coverage[day].add(key)
                checked_values += 1
            if "Avg Complaints Per Year" in row:
                assert math.isclose(
                    numeric(row["Avg Complaints Per Year"]), mark["mean"], abs_tol=0.011
                )
                checked_values += 1
            assert (
                row["Within STD Limits?"].lower()
                == str(mark["source_chart_within"]).lower()
            )
            assert row["In or Out of Upper or Lower Limits?"] == (
                "In" if mark["source_chart_within"] else "Out"
            )
            assert datevalue(row["Date To"], role) == mark["date_to"]
            assert row["Dummy"] == "DUMMY"
            count_values[day] = numeric(row["Number of Complaints"])
        else:
            assert sheet == "Data"
            measure = row["Measure Names"].split(" along ")[0]
            key = {
                "Number of Complaints": "count",
                "Avg Complaints Per Year": "mean",
                "Lower Limit": "lower",
                "Upper Limit": "upper",
            }[measure]
            seen[(day, year, key)] += 1
            value = row["Measure Values"]
            if key == "count" and not value:
                assert int(year) != mark["year"]
                dense_count_blanks += 1
                continue
            assert value, (path.name, day, measure, "missing")
            reference = mark["count"] if key == "count" else limits[year][key]
            assert math.isclose(numeric(value), reference, abs_tol=0.011), (
                path.name,
                day,
                year,
                measure,
                value,
                reference,
            )
            checked_values += 1
            if int(year) == mark["year"]:
                coverage[day].add(key)
                assert (
                    row["Within STD Limits?"].lower() == str(mark["within"]).lower()
                ), (path.name, day, "classification")
                if key == "count":
                    count_values[day] = numeric(value)
            else:
                assert not row["Within STD Limits?"]
    required = (
        {"count", "lower", "upper"}
        if sheet == "Chart"
        else {"count", "mean", "lower", "upper"}
    )
    if sheet == "Chart":
        assert set(seen) == set(marks) and all(count == 2 for count in seen.values())
    else:
        assert set(seen) == {
            (day, year, key)
            for day in marks
            for year in limits
            for key in ["count", "mean", "lower", "upper"]
        }
        assert all(count == 1 for count in seen.values())
    assert set(coverage) == set(marks), (
        path.name,
        "missing dates",
        set(marks) - set(coverage),
    )
    assert all(keys == required for keys in coverage.values())
    assert set(count_values) == set(marks)
    assert sum(count_values.values()) == expected["complaints"]
    return {
        "file": str(path.relative_to(HERE)),
        "role": role,
        "sheet": sheet,
        "export_rows": len(rows),
        "complete_weekly_marks": len(marks),
        "distinct_complaint_sum": expected["complaints"],
        "numeric_values_checked": checked_values,
        "densified_empty_count_cells": dense_count_blanks,
        "status": "passed",
    }


def verify_detail(main):
    report = json.loads((HERE / "evidence/cloud-detail-default.json").read_text())
    assert report["source_hashes"] == main["source_hashes"]
    assert report["browser_interaction_executed"] is False
    assert set(report["views"]) == {"author", "replica"}
    for image in report["views"].values():
        assert image["name"] == "2021_01_20_WW03_Control_Chart_Detail"
        assert digest(HERE / image["path"]) == image["sha256"]
    records = []
    for role, item in report["data"].items():
        assert item["name"] == "Detail"
        if "path" in item:
            path = HERE / item["path"]
            assert digest(path) == item["sha256"]
            rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
            assert not rows, (
                path.name,
                "default Detail must be empty without selection",
            )
            records.append(
                {
                    "role": role,
                    "bytes": path.stat().st_size,
                    "rows": 0,
                    "status": "passed",
                }
            )
        else:
            assert item.get("error")
            records.append(
                {"role": item["role"], "status": "not_exported", "error": item["error"]}
            )
    assert {item["role"] for item in records} == {"author", "replica"}
    return {
        "available": True,
        "state": "default-no-selection",
        "images_hash_verified": True,
        "data": records,
        "browser_interaction_executed": False,
    }


if __name__ == "__main__":
    verify()
