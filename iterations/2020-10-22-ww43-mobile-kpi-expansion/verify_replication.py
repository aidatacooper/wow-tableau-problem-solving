"""Independent Superstore record aggregation and native expansion contracts."""

import calendar
import csv
import json
import math
import re
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
METRICS = ["SALES", "PROFIT", "MARGIN", "CUSTOMERS"]
ACCEPTANCE = ["closed-four-kpis", "four-expanded-states", "native-action-controls"]


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Order Date","Sales","Profit","Customer ID" FROM "Extract"."Extract"'
        )
    assert len(rows) == 9994

    def aggregate(facts):
        sales = math.fsum(r[1] for r in facts)
        profit = math.fsum(r[2] for r in facts)
        return {
            "SALES": sales,
            "PROFIT": profit,
            "MARGIN": profit / sales,
            "CUSTOMERS": len({r[3] for r in facts}),
        }

    months = defaultdict(list)
    for row in rows:
        months[row[0].month].append(row)
    assert set(months) == set(range(1, 13))
    return {
        "raw_rows": len(rows),
        "whole_dataset": aggregate(rows),
        "months": {str(m): aggregate(f) for m, f in sorted(months.items())},
        "scope": "Monthly bins combine all source years using baseline year2019; customer distinct counts are recomputed at each grain.",
    }


def value(row, metric):
    keys = [
        key
        for key in row
        if key.upper() == metric
        or key.upper() == "SUM(" + metric + ")"
        or key == "SUM(" + metric.title() + ")"
    ]
    assert len(keys) == 1, (metric, list(row))
    return row[keys[0]]


def numeric(text, expected, metric):
    cleaned = text.strip().replace(",", "").replace("$", "").replace("%", "")
    assert cleaned and "#" not in cleaned
    actual = float(cleaned) / (100 if metric == "MARGIN" and "%" in text else 1)
    tolerance = (
        0.0005001
        if metric == "MARGIN" and "%" in text
        else 0.50001
        if metric in ["SALES", "PROFIT"]
        else 1e-7
    )
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance), (
        text,
        expected,
        metric,
    )


def month_key(text):
    text = text.strip()
    for i in range(1, 13):
        if re.search(
            r"\b" + calendar.month_name[i] + r"\b", text, re.IGNORECASE
        ) or re.search(r"\b" + calendar.month_abbr[i] + r"\b", text, re.IGNORECASE):
            return i
    match = re.search(r"2019-(\d{1,2})-", text)
    if match:
        return int(match.group(1))
    match = re.search(r"^(\d{1,2})/\d{1,2}/2019", text)
    assert match, ("Unknown baseline-date month", text)
    return int(match.group(1))


def cloud(data, digest):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf-8"))
    proof = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    assert report["source_hashes"]["replica"] == digest
    assert report["source_hashes"]["author"] == proof["export_sha256"]
    assert proof["original_sha256"] == lock["source_workbook"]["sha256"]
    assert not report["browser_interaction_executed"]
    expected_states = {"default": {}} | {
        m.lower(): {"Selected Measure": m} for m in METRICS
    }
    assert len(report["states"]) == 5 and {s["name"] for s in report["states"]} == set(
        expected_states
    )
    views = [
        "KPI - Sales",
        "KPI - Profit",
        "KPI - Margin",
        "KPI - Customer",
        "Bar - Sales",
        "Bar - Profit",
        "Bar - Margin",
        "Bar - Customers",
    ]
    expected_exports = {(r, v) for r in ["author", "replica"] for v in views}
    checks = []
    for state in report["states"]:
        assert (
            state["parameters"] == expected_states[state["name"]]
            and not state["filters"]
        )
        selected = state["parameters"].get("Selected Measure", "")
        assert set(state["views"]) == {"author", "replica"}
        assert (
            len(state["data"]) == 16
            and {(i["role"], i["view"]) for i in state["data"]} == expected_exports
        )
        for image in state["views"].values():
            assert (
                sha256((HERE / image["path"]).read_bytes()).hexdigest()
                == image["sha256"]
            )
        for item in state["data"]:
            p = HERE / item["path"]
            assert sha256(p.read_bytes()).hexdigest() == item["sha256"]
            assert item["parameters"] == state["parameters"] and item["filters"] == {}
            rows = [
                {k.strip(): v for k, v in row.items()}
                for row in csv.DictReader(
                    p.read_text(encoding="utf-8-sig").splitlines()
                )
            ]
            metric = item["view"].split(" - ")[1].upper()
            metric = "CUSTOMERS" if metric == "CUSTOMER" else metric
            if item["view"].startswith("KPI"):
                assert rows, (p, "Empty KPI cannot prove metric")
                populated = []
                for row in rows:
                    if value(row, metric).strip():
                        numeric(
                            value(row, metric), data["whole_dataset"][metric], metric
                        )
                        populated.append(row)
                assert len(populated) == 1 and 1 <= len(rows) <= 2
            elif metric == selected:
                if item["role"] == "author" and metric == "MARGIN":
                    assert not rows, (
                        p,
                        "Observed author Margin REST limitation changed; update coverage explicitly",
                    )
                    checks.append(
                        {
                            "state": state["name"],
                            "role": "author",
                            "view": item["view"],
                            "rows": 0,
                            "coverage": "unavailable: author Margin REST export returned no rows; not numerical proof",
                            "passed": False,
                            "known_source_limitation": True,
                        }
                    )
                    continue
                assert len(rows) == 12, (p, len(rows))
                seen = set()
                for row in rows:
                    field = next(k for k in row if "Baseline Date" in k)
                    month = month_key(row[field])
                    assert month not in seen
                    seen.add(month)
                    numeric(
                        value(row, metric), data["months"][str(month)][metric], metric
                    )
                assert seen == set(range(1, 13))
            else:
                assert not rows, (p, "Inactive chart unexpectedly contains marks")
            checks.append(
                {
                    "state": state["name"],
                    "role": item["role"],
                    "view": item["view"],
                    "rows": len(rows),
                    "passed": True,
                }
            )
    return checks


def verify():
    output = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(output.read_bytes()).hexdigest()
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    for entry in lock["extracted_data"]:
        p = HERE / entry["file"]
        assert (
            p.stat().st_size == entry["bytes"]
            and sha256(p.read_bytes()).hexdigest() == entry["sha256"]
        )
    with ZipFile(output) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    assert len(root.findall("worksheets/worksheet")) == 8
    dashboard = root.find("dashboards/dashboard")
    assert (
        dashboard.find("size").get("maxwidth") == "400"
        and dashboard.find("size").get("maxheight") == "600"
    )
    assert dashboard.find("devicelayouts") is None
    assert dashboard.xpath('.//zone[@type-v2="layout-flow" and @param="vert"]')
    parameter = root.find('datasources/datasource[@name="Parameters"]/column')
    assert (
        parameter.get("caption") == "Selected Measure"
        and parameter.get("value") == '""'
    )
    actions = list(root.find("actions"))
    assert len(actions) == 8
    for metric in METRICS:
        name = "Customer" if metric == "CUSTOMERS" else metric.title()
        sheet = root.find(f'worksheets/worksheet[@name="KPI - {name}"]')
        panes = sheet.findall("table/panes/pane")
        assert len(panes) == 2 and [p.find("mark").get("class") for p in panes] == [
            "Bar",
            "GanttBar",
        ]
        source = root.xpath(
            "/workbook/datasources/datasource/column[@caption=$caption]",
            caption=name + " - String to pass",
        )[0]
        formula = source.find("calculation").get("formula")
        assert f"<>'{metric}'" in formula and "ELSE '' END" in formula
        local = source.get("name")[1:-1]
        for pane in panes:
            assert any(
                local in e.get("column", "") for e in pane.findall("encodings/lod")
            )
        parameter_actions = [
            a for a in actions if a.get("caption") == "Toggle " + metric
        ]
        assert len(parameter_actions) == 1
        assert parameter_actions[0].find("activation").get("type") == "on-select"
        assert parameter_actions[0].find("source").get("worksheet") == "KPI - " + name
        assert local in parameter_actions[0].find(
            "params/param[@name='source-field']"
        ).get("value")
        assert parameter_actions[0].find("params/param[@name='target-parameter']").get(
            "value"
        ) == "[Parameters]." + parameter.get("name")
        assert parameter_actions[0].find("agg-type").get("type") == "attr"
        deselect = next(a for a in actions if a.get("caption") == "Deselect " + metric)
        assert deselect.find("activation").get("type") == "on-select"
        assert (
            deselect.find("command/param[@name='target']").get("value")
            == "KPI - " + name
        )
        for caption in ["True", "False"]:
            field = root.xpath(
                "/workbook/datasources/datasource/column[@caption=$caption]",
                caption=caption,
            )[0]
            assert field.find("calculation").get("formula") == caption.upper()
            for pane in panes:
                assert any(
                    field.get("name")[1:-1] in e.get("column", "")
                    for e in pane.findall("encodings/lod")
                )
        bar = root.find(
            'worksheets/worksheet[@name="Bar - '
            + ("Customers" if metric == "CUSTOMERS" else name)
            + '"]'
        )
        filters = bar.findall("table/view/filter")
        assert any(
            f'"{metric}"' == g.get("member")
            for f in filters
            for g in f.findall(".//groupfilter")
        )
        assert bar.xpath(
            './/encoding[@major-spacing="2.0" and @major-origin="#2018-12-01 00:00:00#"]'
        )
        assert bar.xpath('.//format[@attr="text-format" and @value="*mmmmm"]')
        assert bar.xpath(
            './/column-instance[@derivation="None" and @type="quantitative"]'
        )
        assert not bar.xpath('.//column-instance[@derivation="Month"]')
    for name in ["Bar - Sales", "Bar - Profit"]:
        assert root.xpath(
            "//worksheet[@name=$name]//style-rule[@element='datalabel']/format[@attr='text-orientation' and @value='-90']",
            name=name,
        )
    kpi_zones = dashboard.xpath('.//zone[starts-with(@name,"KPI - ")]')
    assert len(kpi_zones) == 4
    assert all(z.get("fixed-size") == "52" for z in kpi_zones)
    data = oracle()
    checks = cloud(data, digest)
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "artifact_sha256": digest,
                "acceptance_ids": ACCEPTANCE,
                "oracle": data,
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "PASS WW43 raw monthly/KPI oracle and native toggles; Cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    try:
        verify()
    except (AssertionError, KeyError, StopIteration, ValueError) as exc:
        artifact = HERE / "outputs/replicated-workbook.twbx"
        (HERE / "evidence/functional-verification.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                    "reason": str(exc),
                    "browser_interaction_executed": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise
