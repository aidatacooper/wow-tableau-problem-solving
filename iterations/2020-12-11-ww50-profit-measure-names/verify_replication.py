"""Verify all source facts, native Measure Values contracts and paired CSVs."""

# Acceptance: raw-fact-oracle, native-artifact-contracts
import csv
import json
import math
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def number(value):
    text = str(value).strip().replace("$", "").replace(",", "").replace("+", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    return float(text)


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Sub-Category", "Sales", "Profit" FROM "Extract"."Extract"'
        )
    assert len(rows) == 9994
    grouped = defaultdict(list)
    for sub, sales, profit in rows:
        grouped[sub].append((sales, profit))
    result = {}
    for sub, records in grouped.items():
        sales = math.fsum(r[0] for r in records)
        profit = math.fsum(r[1] for r in records)
        result[sub] = {
            "Sales": sales,
            "Profit": profit,
            "Cost": sales - profit,
            "Cost (copy)": sales - profit,
            "Is Profitable": profit > 0,
        }
    assert len(result) == 17
    assert {k for k, v in result.items() if not v["Is Profitable"]} == {
        "Bookcases",
        "Supplies",
        "Tables",
    }
    return {
        "facts": len(rows),
        "subcategories": result,
        "descending_profit": sorted(result, key=lambda s: -result[s]["Profit"]),
    }


def native(root):
    assert {s.get("name") for s in root.findall("worksheets/worksheet")} == {
        "Data",
        "Viz",
    }
    viz = root.find("worksheets/worksheet[@name='Viz']")
    assert viz.findtext("table/cols").count("[Multiple Values]") == 2
    calculations = {
        c.get("caption"): c
        for c in root.findall("datasources/datasource/column")
        if c.find("calculation") is not None
    }
    assert (
        calculations["Cost"].find("calculation").get("formula")
        == "SUM([Sales]) - SUM([Profit])"
    )
    assert (
        calculations["Cost (copy)"].find("calculation").get("formula")
        == "SUM([Sales]) - SUM([Profit])"
    )
    assert (
        calculations["Is Profitable"].find("calculation").get("formula")
        == "SUM([Profit])>0"
    )
    assert viz.find("table/view/computed-sort").get("direction") == "DESC"
    assert (
        viz.find("table/view/computed-sort").get("using").endswith(".[sum:Profit:qk]")
    )
    panes = viz.findall("table/panes/pane")
    assert [p.find("mark").get("class") for p in panes] == ["Circle", "Line"]
    for pane, alignment in zip(panes, ("right", "auto")):
        cell = pane.find("style/style-rule[@element='cell']")
        assert cell.find("format[@attr='text-align']").get("value") == alignment
        assert cell.find("format[@attr='vertical-align']").get("value") == "center"
    assert (
        viz.find(
            "table/style/style-rule[@element='label']/format[@attr='text-format']"
        ).get("value")
        == 'c"$"#,##0;-"$"#,##0'
    )
    assert (
        viz.find(
            "table/style/style-rule[@element='axis']/format[@attr='display'][@scope='rows']"
        ).get("value")
        == "false"
    )
    assert (
        root.find("windows/window[@name='Viz']/viewpoint/zoom").get("type")
        == "entire-view"
    )
    assert len(panes[0].findall("encodings/color")) == 2
    assert panes[0].find("encodings/size").get("column").endswith(".[:Measure Names]")
    assert (
        panes[1].find("encodings/path") is None
    )  # Actual author uses implicit native Measure Values lines.
    assert (
        viz.find("table/style/style-rule[@element='axis']/encoding[@fold='true']").get(
            "synchronized"
        )
        == "true"
    )
    compound = [
        x
        for x in root.findall("datasources/datasource/style/style-rule/encoding")
        if x.find("map/multibucket") is not None
    ]
    assert len(compound) == 1
    assert len(compound[0].findall("map")) == 6
    assert {m.get("to") for m in compound[0].findall("map")} == {
        "#004500",
        "#8f2d56",
        "#ffffff",
        "#5c6068",
    }
    assert all(
        len(m.findall("multibucket/bucket")) == 2 for m in compound[0].findall("map")
    )
    size_encoding = viz.find(
        "table/style/style-rule[@element='mark']/encoding[@type='catsize']"
    )
    assert size_encoding is not None
    assert size_encoding.get("field").endswith(".[:Measure Names]")
    assert size_encoding.get("field-type") == "nominal"
    assert float(size_encoding.get("min-size")) == 0.875774
    assert float(size_encoding.get("max-size")) == 1
    assert not root.xpath("datasources/datasource/column[@caption='Measure Names']")
    dash = root.find("dashboards/dashboard/size")
    assert (dash.get("maxwidth"), dash.get("maxheight")) == ("800", "900")
    assert (
        root.find("windows/window[@class='worksheet'][@name='Data']").get("hidden")
        != "true"
    )
    return {
        "passed": True,
        "compound_palette_members": 6,
        "circle_line_panes": 2,
        "native_measure_values_axes": 2,
        "browser_events_executed": False,
    }


def normalized_rows(path, expected, view):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert rows, f"Empty business CSV {path.name}"
    checked = 0
    semantic_cells = set()
    cell_counts = Counter()
    seen = set()
    for row in rows:
        sub = row.get("Sub-Category")
        assert sub in expected, (path.name, sub, list(row))
        seen.add(sub)
        if "Measure Names" in row:
            metric = row["Measure Names"]
            if metric not in expected[sub]:
                continue
            val = row.get("Measure Values", row.get("Multiple Values", ""))
            if val:
                assert abs(number(val) - expected[sub][metric]) <= 0.000001, (
                    path.name,
                    sub,
                    metric,
                    val,
                    expected[sub][metric],
                )
                semantic_cells.add((sub, metric))
                cell_counts[(sub, metric)] += 1
                checked += 1
        for header, sign in (
            ("Label Profit is +ve", True),
            ("Label Profit is -ve", False),
        ):
            if row.get(header):
                assert expected[sub]["Is Profitable"] == sign, (path.name, sub, header)
                assert abs(number(row[header]) - expected[sub]["Profit"]) <= 0.51
        for key, value in row.items():
            metric = key.replace("SUM(", "").replace("AGG(", "").rstrip(")")
            if metric in {"Sales", "Profit", "Cost", "Cost (copy)"} and value:
                assert abs(number(value) - expected[sub][metric]) <= 0.51, (
                    path.name,
                    sub,
                    metric,
                    value,
                    expected[sub][metric],
                )
                checked += 1
        if "Is Profitable" in row and row["Is Profitable"]:
            assert row["Is Profitable"].lower() in ("true", "false")
            assert (row["Is Profitable"].lower() == "true") == expected[sub][
                "Is Profitable"
            ]
    required_metrics = (
        {"Cost", "Sales", "Profit"}
        if view == "Data"
        else {"Cost", "Sales", "Cost (copy)"}
    )
    assert semantic_cells == {
        (sub, metric) for sub in expected for metric in required_metrics
    }, (path.name, semantic_cells)
    assert seen == set(expected), (path.name, seen, set(expected))
    repetitions = 1 if view == "Data" else 2
    assert len(rows) == len(expected) * 3 * repetitions, (path.name, len(rows))
    assert all(count == repetitions for count in cell_counts.values()), (
        path.name,
        cell_counts,
    )
    assert checked >= len(expected) * (3 if view == "Data" else 2), (path.name, checked)
    return {
        "rows": len(rows),
        "subcategories": len(seen),
        "metric_checks": checked,
        "complete_business_cells": len(semantic_cells),
        "native_pane_repetitions": repetitions,
        "formatted_currency_tolerance": 0.51,
        "primary_measure_values_tolerance": 0.000001,
    }


def cloud_checks(raw):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return {"status": "pending_cloud_capture", "passed": False}
    capture = json.loads(manifest.read_text(encoding="utf-8"))
    assert capture["source_hashes"]["replica"] == digest(
        HERE / "outputs/replicated-workbook.twbx"
    )
    assert {s["name"] for s in capture["states"]} == {
        "negative",
        "partition-a",
        "partition-b",
        "default",
        "furniture",
    }
    summaries = []
    for state in capture["states"]:
        assert {(r["role"], r["view"]) for r in state["data"]} == {
            (role, view) for role in ("author", "replica") for view in ["Data", "Viz"]
        }

        chosen = state.get("filters", {}).get("Sub-Category")
        names = set(chosen.split(",")) if chosen else set(raw["subcategories"])
        expected = {s: raw["subcategories"][s] for s in names}
        for record in state["data"]:
            path = HERE / record["path"]
            assert digest(path) == record["sha256"]
            limited = (
                state["name"] == "default"
                and record["role"] == "author"
                and record["view"] == "Viz"
            )
            observed_expected = (
                {"Copiers": expected["Copiers"]} if limited else expected
            )
            summary = normalized_rows(path, observed_expected, record["view"])
            if limited:
                summary["coverage_limitation"] = {
                    "passed": False,
                    "observed_subcategories": ["Copiers"],
                    "intended_subcategories": 17,
                    "scope": "Default author Viz CSV is limited to one selected subcategory; not proof of all 17. Complementary partition-a and partition-b REST filter exports jointly verify all 17 separately.",
                }
            summaries.append(
                {
                    "state": state["name"],
                    "role": record["role"],
                    "view": record["view"],
                    **summary,
                }
            )
        for record in state["views"].values():
            assert digest(HERE / record["path"]) == record["sha256"]
    assert len(capture["states"]) == 5 and len(summaries) == 20
    partition_names = [
        set(s["filters"]["Sub-Category"].split(","))
        for s in capture["states"]
        if s["name"] in {"partition-a", "partition-b"}
    ]
    assert len(partition_names) == 2
    assert not partition_names[0] & partition_names[1]
    assert set.union(*partition_names) == set(raw["subcategories"])
    return {
        "passed": True,
        "status": "verified",
        "exports": summaries,
        "source_viz_partition_coverage": {
            "passed": True,
            "subcategories": 17,
            "business_cells": 51,
            "states": ["partition-a", "partition-b"],
        },
        "scope": "Full Data business CSVs and all requested filtered Viz groups; complementary partitions verify all 17 author Viz groups. Default author Viz remains limited to Copiers. No hover execution.",
    }


def verify():
    raw = oracle()
    workbook = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(workbook) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    report = {
        "artifact_sha256": digest(workbook),
        "raw_oracle": raw,
        "native_contracts": native(root),
        "cloud": cloud_checks(raw),
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("Raw/native PASS; Cloud", report["cloud"]["status"])
    return report


if __name__ == "__main__":
    verify()
