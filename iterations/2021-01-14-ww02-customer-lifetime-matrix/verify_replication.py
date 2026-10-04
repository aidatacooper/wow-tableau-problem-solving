"""Independently verify locked raw cohorts, complete Cloud cells and native XML."""

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "cohort-lifetime-values",
    "single-gap-densification",
    "matrix-native-layout",
]
COHORT = "ACQUISITION QUARTER"
AGE = "QUARTERS SINCE BIRTH"
VALUE = "CUSTOMER LIFETIME VALUE (CLTV)"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quarter(date):
    return date.year * 4 + (date.month - 1) // 3


def oracle():
    path = next((HERE / "inputs").glob("*.hyper"))
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    assert digest(path) == lock["extracted_data"][0]["sha256"]
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(path)) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Order Date","Customer ID","Sales" FROM "Extract"."Extract"'
        )
    assert len(rows) == 9994 and all(d and i and s is not None for d, i, s in rows)
    births = {}
    for date, customer, sales in rows:
        births[customer] = min(births.get(customer, quarter(date)), quarter(date))
    customers = defaultdict(set)
    sales = defaultdict(float)
    line_counts = defaultdict(int)
    for date, customer, amount in rows:
        cohort = births[customer]
        age = quarter(date) - cohort
        assert age >= 0
        customers[cohort].add(customer)
        sales[cohort, age] += amount
        line_counts[cohort, age] += 1
    cells = []
    gaps = []
    for cohort in sorted(customers):
        label = f"Q{cohort % 4 + 1} {cohort // 4}"
        total = 0
        ages = {age for b, age in sales if b == cohort}
        for age in range(max(ages) + 1):
            filled = (cohort, age) not in sales
            if filled:
                assert age - 1 in ages and age + 1 in ages
                gaps.append({"cohort": label, "age": age})
            total += sales.get((cohort, age), 0)
            cells.append(
                {
                    "cohort": label,
                    "age": age,
                    "customers": len(customers[cohort]),
                    "quarter_sales": sales.get((cohort, age)),
                    "running_sales": total,
                    "cltv": total / len(customers[cohort]),
                    "filled_gap": filled,
                    "raw_order_lines": line_counts[cohort, age],
                }
            )
    assert (
        len(births) == 793
        and len(customers) == 16
        and len(sales) == 134
        and len(cells) == 136
    )
    assert gaps == [{"cohort": "Q3 2018", "age": 1}, {"cohort": "Q2 2019", "age": 1}]
    assert math.isclose(min(c["cltv"] for c in cells), 32.3575)
    assert math.isclose(max(c["cltv"] for c in cells), 3353.0410818181813)
    return {
        "raw_rows": len(rows),
        "distinct_customers": len(births),
        "cohorts": len(customers),
        "observed_sales_cells": len(sales),
        "visible_matrix_cells": len(cells),
        "filled_gaps": gaps,
        "cells": cells,
        "trailing_null_cells_excluded": 120,
    }


def parse_cohort(text):
    match = re.fullmatch(r"Q([1-4])\s+(\d{4})", text.strip())
    if match:
        return f"Q{match[1]} {match[2]}"
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        return f"Q{(int(match[2]) - 1) // 3 + 1} {match[1]}"
    raise AssertionError(("Unexpected cohort representation", text))


def number(text):
    return float(text.strip().replace(",", "").replace("$", "").replace("\u2212", "-"))


def verify_cloud(data, artifact):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    manifest = json.loads(path.read_text())
    proof = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert manifest["source_hashes"] == {
        "author": proof["export_sha256"],
        "replica": artifact,
    }
    assert manifest["browser_interaction_executed"] is False
    expected = {(c["cohort"], c["age"]): c for c in data["cells"]}
    results = []
    for state in manifest["states"]:
        assert state["parameters"] == {} and state["filters"] == {}, (
            "This matrix has no original controls; the default full domain is the acceptance state."
        )
        assert state["name"] == "default" and set(state["views"]) == {
            "author",
            "replica",
        }
        for image in state["views"].values():
            assert digest(HERE / image["path"]) == image["sha256"]
        assert len(state["data"]) == 2
        for item in state["data"]:
            assert (
                item["view"] == "Viz"
                and item["parameters"] == {}
                and item["filters"] == {}
            )
            path = HERE / item["path"]
            assert digest(path) == item["sha256"]
            rows = list(
                csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines())
            )
            seen = set()
            for row in rows:
                key = (parse_cohort(row[COHORT]), int(number(row[AGE])))
                assert key in expected and key not in seen, (item["role"], key)
                seen.add(key)
                c = expected[key]
                assert int(number(row["CUSTOMERS"])) == c["customers"]
                actual = number(row[VALUE])
                # Tableau REST CSV commonly serializes the explicitly zero-decimal currency label.
                assert math.isclose(actual, c["cltv"], abs_tol=0.501), (
                    item["role"],
                    key,
                    actual,
                    c["cltv"],
                )
            assert seen == set(expected), (
                item["role"],
                len(seen),
                len(expected),
                sorted(set(expected) - seen),
            )
            results.append(
                {
                    "state": state["name"],
                    "role": item["role"],
                    "view": "Viz",
                    "rows_checked": len(rows),
                    "complete_matrix": True,
                    "filled_gap_cells_checked": 2,
                    "currency_rounding_tolerance": 0.501,
                }
            )
    assert len(results) == 2
    return results


def verify():
    artifact_path = HERE / "outputs/replicated-workbook.twbx"
    artifact = digest(artifact_path)
    with ZipFile(artifact_path) as z:
        x = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    ds = x.find("datasources/datasource")
    fields = {
        c.get("caption", c.get("name").strip("[]")): c for c in ds.findall("column")
    }
    assert len(ds.findall("column/calculation")) == 5
    assert (
        fields[COHORT].get("role") == "dimension"
        and fields[COHORT].get("datatype") == "date"
    )
    formulas = {
        caption: c.find("calculation").get("formula")
        for caption, c in fields.items()
        if c.find("calculation") is not None
    }
    assert (
        formulas[COHORT]
        == "DATE(DATETRUNC('quarter',{FIXED [Customer ID] : MIN([Order Date])}))"
    )
    assert "COUNTD([Customer ID])" in formulas["CUSTOMERS"] and formulas[
        "CUSTOMERS"
    ].startswith("{FIXED ")
    assert "RUNNING_SUM(SUM([Sales])) / SUM(" in formulas["Avg Lifetime Value"]
    assert (
        "ISNULL" in formulas[VALUE]
        and "LOOKUP" in formulas[VALUE]
        and ",-1)" in formulas[VALUE]
        and ",1)" in formulas[VALUE]
    )
    viz = x.find('worksheets/worksheet[@name="Viz"]')
    deps = viz.find("table/view/datasource-dependencies")
    cohort_ci = deps.xpath(
        'column-instance[@column=$field and @derivation="None" and @type="ordinal"]',
        field=fields[COHORT].get("name"),
    )
    assert (
        len(cohort_ci) == 1 and cohort_ci[0].get("name") in viz.find("table/rows").text
    )
    value_ci = deps.xpath(
        "column-instance[@column=$field]", field=fields[VALUE].get("name")
    )
    assert len(value_ci) == 1, (
        "Labels, color, filter and tooltip must share the addressed calculation instance."
    )
    tc = value_ci[0].findall("table-calc")
    assert len(tc) == 2 and all(t.get("ordering-type") == "Field" for t in tc)
    assert fields["Avg Lifetime Value"].get("name") in tc[1].get("field")
    for t in tc:
        assert len(t.findall("order")) == 1 and fields[AGE].get("name")[1:-1] in t.find(
            "order"
        ).get("field")
    pane = viz.find("table/panes/pane")
    assert pane.find("mark").get("class") == "Square"
    assert pane.find("encodings/color").get("column") == pane.find(
        "encodings/text"
    ).get("column")
    assert value_ci[0].get("name") in pane.find("encodings/color").get("column")
    tooltip = "".join(pane.xpath("customized-tooltip/formatted-text/run/text()"))
    assert value_ci[0].get("name") in tooltip and cohort_ci[0].get("name") in tooltip
    assert all(
        text in tooltip
        for text in [
            "TOTAL CUSTOMERS:",
            "QUARTERS SINCE BIRTH:",
            "are worth an average of",
        ]
    )
    f = viz.find("table/view/filter")
    assert (
        value_ci[0].get("name") in f.get("column")
        and f.get("included-values") == "in-range"
    )
    assert math.isclose(float(f.find("min").text), 32.3575) and math.isclose(
        float(f.find("max").text), 3353.0410818181813
    )
    palette = viz.xpath(
        'table/style/style-rule[@element="mark"]/encoding[@type="custom-interpolated"]/color-palette/color/text()'
    )
    assert palette == [
        "#fff7fb",
        "#ece2f0",
        "#d0d1e6",
        "#a6bddb",
        "#67a9cf",
        "#3690c0",
        "#02818a",
        "#016c59",
        "#014636",
    ]
    header_formats = viz.xpath('table/style/style-rule[@element="header"]/format')
    assert any(
        f.get("attr") == "width"
        and f.get("value") == "184"
        and cohort_ci[0].get("name") in f.get("field", "")
        for f in header_formats
    )
    customer_ci = deps.xpath(
        'column-instance[@column=$field and @derivation="None"]',
        field=fields["CUSTOMERS"].get("name"),
    )[0]
    assert any(
        f.get("attr") == "width"
        and f.get("value") == "120"
        and customer_ci.get("name") in f.get("field", "")
        for f in header_formats
    )
    dash = x.find("dashboards/dashboard")
    assert (
        dash.find("size").get("maxwidth") == "1400"
        and dash.find("size").get("maxheight") == "1000"
    )
    assert not x.findall("actions/action") and not ds.findall(
        "column[@param-domain-type]"
    )
    data = oracle()
    checks = verify_cloud(data, artifact)
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "artifact_sha256": artifact,
                "acceptance_ids": ACCEPTANCE,
                "oracle": data,
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS WW02 complete raw cohorts/native nested matrix; Cloud="
        + ("passed" if checks else "pending")
    )
    return artifact


if __name__ == "__main__":
    verify()
