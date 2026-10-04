"""Independent raw-data comparison oracle and hash-bound native/REST checks."""

import csv
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
FOOD = "Food insecurity (includes low and very low food security) Percent of households"
ACCEPTANCE = [
    "all-year-comparison-oracle",
    "native-line-circles-calculations",
    "cloud-state-data-layout",
]
STATES = {
    "default": (2018, 2),
    "first-year": (2018, 0),
    "most-recent": (2018, 1),
    "year-1995-previous": (1995, 2),
    "year-1995-first": (1995, 0),
    "year-2011-first": (2011, 0),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c:
            rows = c.execute_list_query(
                f'SELECT "Year","{FOOD}" FROM "Extract"."Extract"'
            )
    values = dict(rows)
    assert len(rows) == len(values) == 25 and set(values) == set(range(1995, 2020))
    scenarios = []
    for year in sorted(values):
        for mode in range(3):
            comparison_year = (
                min(values) if mode == 0 else max(values) if mode == 1 else year - 1
            )
            comparison = values.get(comparison_year)
            difference = None if comparison is None else values[year] - comparison
            scenarios.append(
                {
                    "year": year,
                    "mode": mode,
                    "selected": values[year],
                    "comparison_year": comparison_year,
                    "comparison": comparison,
                    "difference": difference,
                    "indicator": "N/C"
                    if difference is None or difference == 0
                    else "\u25b2"
                    if difference > 0
                    else "\u25bc",
                    "absolute_difference": None
                    if difference is None or difference == 0
                    else abs(difference),
                }
            )
    assert len(scenarios) == 75
    assert math.isclose(values[2018] - values[2017], -0.73)
    return {
        "raw_rows": 25,
        "values": {str(k): v for k, v in values.items()},
        "scenarios": scenarios,
    }


def numeric(value):
    text = value.strip().replace(",", "").replace("%", "").replace("\u2212", "-")
    return None if text in ("", "Null", "null", "N/A") else float(text)


def expected_measure(measure, year, selected, mode, values):
    comparison_year = 1995 if mode == 0 else 2019 if mode == 1 else selected - 1
    comparison = values.get(comparison_year)
    difference = None if comparison is None else values[selected] - comparison
    lookup = {
        FOOD: values[year],
        "Selected Year %": values[selected] if year == selected else None,
        "Win Max - Selected Year %": values[selected],
        "First Year %": values[1995] if year == 1995 else None,
        "Latest Year %": values[2019] if year == 2019 else None,
        "Previous Year %": values.get(selected - 1) if year == selected - 1 else None,
        "Selected Comparison %": comparison if year == comparison_year else None,
        "Win Max - Selected Comparison %": comparison,
        "Difference": difference,
        "DISPLAY: Difference": None
        if difference is None or difference == 0
        else abs(difference),
    }
    assert measure in lookup, ("Unexpected CSV measure", measure)
    return lookup[measure]


def assert_number(actual, expected, label, raw=None):
    if expected is None:
        assert actual is None, (label, actual, expected)
    else:
        tolerance = 1e-8
        if raw is not None and ("%" in raw or "-viz" in label[0]):
            number_text = raw.strip().rstrip("%").replace(",", "")
            decimals = len(number_text.split(".")[1]) if "." in number_text else 0
            tolerance = 0.5 * 10 ** (-decimals) + 1e-8
        assert actual is not None and abs(actual - expected) <= tolerance, (
            label,
            actual,
            expected,
        )


def cloud_checks(data, artifact):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    manifest = json.loads(path.read_text(encoding="utf8"))
    proof = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf8")
    )
    assert manifest["source_hashes"] == {
        "author": proof["export_sha256"],
        "replica": artifact,
    }
    assert manifest["browser_interaction_executed"] is False
    assert {x["name"] for x in manifest["states"]} == set(STATES)
    checks = []
    values = {int(k): v for k, v in data["values"].items()}
    for state in manifest["states"]:
        selected, mode = STATES[state["name"]]
        assert int(state["parameters"].get("pSelected Year", 2018)) == selected
        assert int(state["parameters"].get("pComparison", 2)) == mode
        assert len(state["data"]) == 4
        for image in state["views"].values():
            assert digest(HERE / image["path"]) == image["sha256"]
        for record in state["data"]:
            assert (
                record["parameters"] == state["parameters"] and record["filters"] == {}
            )
            p = HERE / record["path"]
            assert digest(p) == record["sha256"]
            rows = list(csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()))
            assert rows, ("Empty CSV", record["path"])
            # Tableau exports the Measure Values table in long format, and the line
            # plot in wide format. Assert every value within the actual schema.
            tested = 0
            years = set()
            keys = set()
            for row in rows:
                year_column = next(
                    (
                        k
                        for k in row
                        if k in ("Year", "Year Axis", "Data Year", "ATTR(Year)")
                    ),
                    None,
                )
                assert year_column, ("Missing year column", row)
                year = int(numeric(row[year_column]))
                years.add(year)
                measure_name = row.get("Measure Names", "").split(" along ")[0]
                key = (year, measure_name)
                assert key not in keys, (
                    "Duplicate exported mark/cell",
                    record["path"],
                    key,
                )
                keys.add(key)
                if "Difference Indicator" in row:
                    comparison_year = (
                        1995 if mode == 0 else 2019 if mode == 1 else selected - 1
                    )
                    difference = (
                        None
                        if comparison_year not in values
                        else values[selected] - values[comparison_year]
                    )
                    indicator = (
                        "N/C"
                        if difference is None or difference == 0
                        else "\u25b2"
                        if difference > 0
                        else "\u25bc"
                    )
                    assert row["Difference Indicator"] == indicator, (
                        record["path"],
                        year,
                        row["Difference Indicator"],
                        indicator,
                    )
                if row.get("Measure Names") and "Measure Values" in row:
                    name = row["Measure Names"].split(" along ")[0]
                    expected = expected_measure(name, year, selected, mode, values)
                    assert_number(
                        numeric(row["Measure Values"]),
                        expected,
                        (record["path"], year, name),
                        raw=row["Measure Values"],
                    )
                    tested += 1
                else:
                    for name in (
                        FOOD,
                        "Selected Year %",
                        "Selected Comparison %",
                        "Win Max - Selected Year %",
                        "DISPLAY: Difference",
                    ):
                        if name in row:
                            expected = expected_measure(
                                name, year, selected, mode, values
                            )
                            actual = numeric(row[name])
                            assert_number(
                                actual,
                                expected,
                                (record["path"], year, name),
                                raw=row[name],
                            )
                            tested += 1
            assert years == set(values), (
                "Incomplete exported years",
                record["path"],
                years,
            )
            is_data = "-data" in record["path"]
            expected_names = (
                {
                    FOOD,
                    "Selected Year %",
                    "Win Max - Selected Year %",
                    "First Year %",
                    "Latest Year %",
                    "Previous Year %",
                    "Selected Comparison %",
                    "Win Max - Selected Comparison %",
                    "Difference",
                    "DISPLAY: Difference",
                }
                if is_data
                else {"", "Selected Year %", "Selected Comparison %"}
            )
            assert keys == {
                (year, name) for year in values for name in expected_names
            }, ("Incomplete mark/cell set", record["path"], len(keys))
            assert len(rows) == (250 if is_data else 75)
            assert tested >= 25, ("Insufficient business cells", record["path"], tested)
            checks.append(
                {
                    "state": state["name"],
                    "role": record["role"],
                    "view": record["view"],
                    "rows": len(rows),
                    "years": 25,
                    "verified_cells": tested,
                    "sha256": record["sha256"],
                }
            )
    return checks


def verify():
    artifact = HERE / "outputs/replicated-workbook.twbx"
    hashed = digest(artifact)
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
    assert lock["source_workbook_used_by_builder"] is False
    for item in lock["extracted_data"]:
        assert digest(HERE / item["file"]) == item["sha256"]
    with ZipFile(artifact) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    ds = next(
        x
        for x in root.findall("datasources/datasource")
        if x.get("name") != "Parameters"
    )
    columns = {
        x.get("caption", x.get("name").strip("[]")): x for x in ds.findall("column")
    }

    def formula(name):
        s = columns[name].find("calculation").get("formula")
        for caption, col in columns.items():
            s = s.replace(col.get("name"), f"[{caption}]")
        return s.replace(
            "[Parameters].[Parameter 1]", "[Parameters].[pComparison]"
        ).replace("[Parameters].[Parameter 2]", "[Parameters].[pSelected Year]")

    assert formula("First Year") == "WINDOW_MIN(MIN([Year]))"
    assert formula("Latest Year") == "WINDOW_MAX(MAX([Year]))"
    assert formula("Win Max - Selected Year %") == "WINDOW_MAX(MIN([Selected Year %]))"
    assert (
        formula("Difference")
        == "[Win Max - Selected Year %]-[Win Max - Selected Comparison %]"
    )
    assert "WINDOW_MAX([First Year %])" in formula("Win Max - Selected Comparison %")
    assert "WINDOW_MAX([Latest Year %])" in formula("Win Max - Selected Comparison %")
    assert "WINDOW_MAX(MAX([Previous Year %]))" in formula(
        "Win Max - Selected Comparison %"
    )
    parameters = root.find('datasources/datasource[@name="Parameters"]')
    pc = parameters.find('column[@caption="pComparison"]')
    py = parameters.find('column[@caption="pSelected Year"]')
    assert pc.get("value") == "2" and py.get("value") == "2018"
    assert [x.get("value") for x in py.findall("members/member")] == [
        str(y) for y in range(1995, 2020)
    ]
    assert [x.get("alias") for x in pc.findall("members/member")] == [
        "First Year",
        "Most Recent Year",
        "Previous Year",
    ]
    data_sheet = root.find('worksheets/worksheet[@name="Data"]')
    data_panes = data_sheet.findall("table/panes/pane")
    assert len(data_panes) == 1 and data_panes[0].find("mark").get("class") == "Text"
    data_texts = data_panes[0].findall("encodings/text")
    assert len(data_texts) == 1 and data_texts[0].get("column").endswith(
        "[Multiple Values]"
    )
    data_members = data_sheet.findall("table/view/filter/groupfilter/groupfilter")
    assert len(data_members) == 10 and all(
        x.get("level") == "[:Measure Names]" for x in data_members
    )
    data_order = data_sheet.findall("table/view/manual-sort/dictionary/bucket")
    assert len(data_order) == 10 and {x.text.strip('"') for x in data_order} == {
        x.get("member").strip('"') for x in data_members
    }
    for name in (
        "Win Max - Selected Year %",
        "First Year %",
        "Latest Year %",
        "Win Max - Selected Comparison %",
        "Difference",
    ):
        instances = data_sheet.xpath(
            "table/view/datasource-dependencies/column-instance[@column=$column]",
            column=columns[name].get("name"),
        )
        assert len(instances) == 1 and instances[0].get("name").endswith(":1]")
        assert all(
            x.get("ordering-type") == "Field" and len(x.findall("order")) == 1
            for x in instances[0].findall("table-calc")
        )
    viz = root.find('worksheets/worksheet[@name="Viz"]')
    panes = viz.findall("table/panes/pane")
    assert [x.find("mark").get("class") for x in panes] == ["Line", "Circle"]
    assert "Multiple Values" in viz.find("table/rows").text
    assert viz.xpath(
        'table/style/style-rule[@element="axis"]/encoding[@synchronized="true" and @fold="true"]'
    )
    assert viz.xpath(
        'table/style/style-rule[@element="axis"]/encoding[@min="1994" and @max="2020"]'
    )
    for name in (
        "Selected Comparison %",
        "DISPLAY: Difference",
        "Difference Indicator",
        "Win Max - Selected Year %",
    ):
        instances = viz.xpath(
            "table/view/datasource-dependencies/column-instance[@column=$column]",
            column=columns[name].get("name"),
        )
        assert len(instances) == 1
        tc = instances[0].findall("table-calc")
        assert tc and all(x.get("ordering-type") == "Field" for x in tc)
        assert all(len(x.findall("order")) == 1 for x in tc)
    assert len(panes[0].findall("customized-tooltip/formatted-text/run")) == 4
    assert len(panes[1].findall("customized-tooltip/formatted-text/run")) == 4
    text = etree.tostring(root, encoding="unicode")
    assert "#f0007b" in text and "#000000" in text
    dash = root.find("dashboards/dashboard")
    size = dash.find("size")
    assert size.get("maxwidth") == "1000" and size.get("maxheight") == "800"
    assert len(dash.xpath('zones//zone[@type-v2="paramctrl"]')) == 2
    assert len(dash.xpath('zones//zone[@name="Title"]')) == 1
    assert not root.findall("actions/action")
    data = oracle()
    checks = cloud_checks(data, hashed)
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf8"
    )
    evidence = {
        "status": "pass",
        "artifact_sha256": hashed,
        "acceptance_ids": ACCEPTANCE,
        "oracle": data,
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf8"
    )
    print(
        "PASS WW01: 75 raw scenarios/native nested calculations; Cloud="
        + ("passed" if checks else "pending")
    )
    return hashed


if __name__ == "__main__":
    verify()
