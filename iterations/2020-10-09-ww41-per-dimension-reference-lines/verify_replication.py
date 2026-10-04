"""Independent raw-record oracle and native contracts for selectable references."""

import csv
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
MEASURES = ["Sales Per Order", "Profit Ratio", "Items Per Order"]
COLORS = {"Technology": "#00a2b3", "Furniture": "#8fb202", "Office Supplies": "#cf3e53"}


def rounding(value, places):
    return float(
        Decimal(str(value)).quantize(Decimal(10) ** (-places), rounding=ROUND_HALF_UP)
    )


def metric(rows, measure):
    sales = math.fsum(r[3] for r in rows)
    orders = len({r[2] for r in rows})
    if measure == "Sales Per Order":
        return rounding(sales / orders, 0)
    if measure == "Profit Ratio":
        return rounding(math.fsum(r[5] for r in rows) / sales * 100, 1)
    return rounding(sum(r[4] for r in rows) / orders, 2)


def oracle():
    path = next((HERE / "inputs").glob("*.hyper"))
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(path)) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Order Date","Category","Order ID","Sales","Quantity","Profit" FROM "Extract"."Extract"'
        )
    assert len(rows) == 9994
    groups = defaultdict(list)
    categories = defaultdict(list)
    for row in rows:
        d = row[0]
        q = date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)
        groups[(q.isoformat(), row[1])].append(row)
        categories[row[1]].append(row)
    assert len(groups) == 48 and set(categories) == set(COLORS)
    result = {}
    for measure in MEASURES:
        cells = [
            {"quarter": q, "category": cat, "value": metric(facts, measure)}
            for (q, cat), facts in sorted(groups.items())
        ]
        refs = {
            cat: math.fsum(cell["value"] for cell in cells if cell["category"] == cat)
            / 16
            for cat in categories
        }
        cards = {cat: metric(facts, measure) for cat, facts in categories.items()}
        ranks = {
            cat: i + 1
            for i, (cat, v) in enumerate(sorted(cards.items(), key=lambda x: -x[1]))
        }
        result[measure] = {
            "quarters": cells,
            "references": refs,
            "cards": cards,
            "ranks": ranks,
        }
    return {
        "raw_rows": len(rows),
        "states": result,
        "scope": "All 9994 source order lines; 48 quarter/category aggregates per measure. Line references average 16 rounded quarter values equally; ranking cards use independently rounded full-category aggregates because the original card query has no quarter dimension.",
    }


def numeric(value, expected):
    text = value.strip().replace(",", "").replace("$", "").replace("%", "")
    assert text and "#" not in text
    actual = float(text)
    assert math.isclose(actual, expected, abs_tol=5e-7), (value, expected)


def quarter_key(value):
    text = value.strip()
    match = re.search(r"(20\d\d).*?Q([1-4])", text)
    if not match:
        match = re.search(r"Q([1-4]).*?(20\d\d)", text)
    if match:
        a, b = match.groups()
        year, q = (int(a), int(b)) if len(a) == 4 else (int(b), int(a))
        return date(year, (q - 1) * 3 + 1, 1).isoformat()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y"):
        try:
            d = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).date()
            return d.replace(month=((d.month - 1) // 3) * 3 + 1, day=1).isoformat()
        except ValueError:
            pass
    raise AssertionError(("Unrecognized quarter export", value))


def cloud(data, artifact_hash):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf8"))
    assert report["source_hashes"]["replica"] == artifact_hash
    proof = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf8")
    )
    assert report["source_hashes"]["author"] == proof["export_sha256"]
    expected_states = {
        "default": {},
        "profit-ratio": {"SELECT A MEASURE": "Profit Ratio"},
        "items-per-order": {"SELECT A MEASURE": "Items Per Order"},
    }
    expected_exports = {
        (role, view)
        for role in ("author", "replica")
        for view in ("Line", "Rank1", "Rank2", "Rank3")
    }
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
    assert proof["original_sha256"] == lock["source_workbook"]["sha256"]
    assert report["browser_interaction_executed"] is False
    assert len(report["states"]) == len(expected_states)
    assert {state["name"] for state in report["states"]} == set(expected_states)
    for state in report["states"]:
        assert state["parameters"] == expected_states[state["name"]]
        assert state["filters"] == {}
        assert set(state["views"]) == {"author", "replica"}
        assert len(state["data"]) == len(expected_exports)
        assert {
            (item["role"], item["view"]) for item in state["data"]
        } == expected_exports
        assert len({item["path"] for item in state["data"]}) == len(expected_exports)
    checks = []
    for state in report["states"]:
        measure = state.get("parameters", {}).get("SELECT A MEASURE", "Sales Per Order")
        expected = data["states"][measure]
        for item in state["views"].values():
            assert (
                sha256((HERE / item["path"]).read_bytes()).hexdigest() == item["sha256"]
            )
        for item in state["data"]:
            p = HERE / item["path"]
            assert sha256(p.read_bytes()).hexdigest() == item["sha256"]
            rows = [
                {k.strip(): v for k, v in row.items()}
                for row in csv.DictReader(
                    p.read_text(encoding="utf-8-sig").splitlines()
                )
            ]
            assert rows, (p, "Empty business worksheet CSV is not data proof")
            if item["view"] == "Line":
                seen = set()
                reference_seen = set()
                reference_exported = "Ref Line per Category" in rows[0]
                assert reference_exported, (p, "Full numeric reference CSV is required")
                targets = {
                    (c["quarter"], c["category"]): c["value"]
                    for c in expected["quarters"]
                }
                for row in rows:
                    if item["role"] == "replica":
                        assert row["Metric Label"] == measure, (
                            p,
                            row["Metric Label"],
                            measure,
                        )
                    assert row["$ Label Prefix"] == (
                        "$" if measure == "Sales Per Order" else ""
                    )
                    assert row["% Label Suffix"] == (
                        "%" if measure == "Profit Ratio" else ""
                    )
                    category = row["Category"]
                    quarter = quarter_key(
                        row.get("Quarter of Order Date", row.get("Quarter Date", ""))
                    )
                    key = (quarter, category)
                    assert key in targets
                    if row.get("Display Measure", "").strip():
                        numeric(row["Display Measure"], targets[key])
                        seen.add(key)
                    if row.get("Ref Line per Category", "").strip():
                        numeric(
                            row["Ref Line per Category"],
                            expected["references"][category],
                        )
                        reference_seen.add(key)
                assert seen == set(targets), (p, len(seen))
                if reference_exported:
                    assert reference_seen == set(targets), (
                        "Incomplete exported reference-line coverage",
                        p,
                        len(reference_seen),
                    )
                checks.append(
                    {
                        "path": item["path"],
                        "state": state["name"],
                        "role": item["role"],
                        "quarter_cells": len(seen),
                        "reference_cells": len(reference_seen),
                        "reference_proof": "full CSV quarter/category coverage"
                        if reference_exported
                        else "raw-record oracle and native reference-line contract only; CSV omits this field",
                    }
                )
            else:
                rank = int(item["view"][-1])
                category = next(
                    cat for cat, r in expected["ranks"].items() if r == rank
                )
                assert {r["Category"] for r in rows} == {category}, (p, rows, category)
                for row in rows:
                    key = (
                        "Display Ref Line"
                        if "Display Ref Line" in row
                        else "Display Measure"
                    )
                    numeric(row[key], expected["cards"][category])
                checks.append(
                    {
                        "path": item["path"],
                        "state": state["name"],
                        "role": item["role"],
                        "rank": rank,
                        "category": category,
                    }
                )
    assert len(checks) == 24
    return checks


def verify():
    data = oracle()
    workbook = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(workbook.read_bytes()).hexdigest()
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
    with ZipFile(workbook) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for entry in lock["extracted_data"]:
            p = HERE / entry["file"]
            assert sha256(p.read_bytes()).hexdigest() == entry["sha256"]
            name = next(n for n in z.namelist() if n.endswith(p.name))
            assert sha256(z.read(name)).hexdigest() == entry["sha256"]
    assert not root.xpath(
        "//worksheet/table/view/datasource-dependencies[@datasource!='Parameters']/column[@name='[ParameterMeasure]']"
    )
    assert (
        len(
            root.xpath(
                "//worksheet/table/view/datasource-dependencies[@datasource='Parameters']/column[@name='[ParameterMeasure]']"
            )
        )
        == 4
    )
    range_fields = root.xpath(
        "//worksheet[@name='Line']//format[@attr='mark-labels-range-field']/@value"
    )
    assert range_fields and all(
        v.startswith("[federated.") and ".[usr:" in v for v in range_fields
    )
    assert len(root.xpath("//worksheet[@name='Line']//reference-line")) == 3
    for line in root.xpath("//worksheet[@name='Line']//reference-line"):
        assert line.get("scope") == "per-pane" and line.get("label-type") == "none"
    assert root.xpath(
        "//worksheet[@name='Line']//encoding[@fold='true' and @synchronized='true']"
    )
    assert root.xpath(
        "//worksheet[@name='Line']//column-instance[@derivation='Quarter-Trunc' and @type='quantitative']"
    )
    metric_label = root.xpath(
        "/workbook/datasources/datasource/column[@caption='Metric Label']"
    )[0]
    assert (
        metric_label.find("calculation").get("formula")
        == "[Parameters].[ParameterMeasure]"
    )
    assert metric_label.get("role") == "dimension"
    assert (
        metric_label.get("name")[1:-1]
        in root.xpath("//worksheet[@name='Line']/table/rows/text()")[0]
    )
    assert root.xpath(
        "//worksheet[@name='Line']//format[@attr='text-orientation' and @value='-90']"
    )
    assert not root.xpath(
        "//worksheet[@name='Line']//format[@attr='title' and contains(@value,'ParameterMeasure')]"
    )
    assert len(root.xpath("//dashboard/zones//zone[@type-v2='paramctrl']")) == 1
    assert {s.get("name") for s in root.xpath("//worksheet")} == {
        "Line",
        "Rank1",
        "Rank2",
        "Rank3",
    }
    for i in range(1, 4):
        worksheet = root.xpath("//worksheet[@name=$name]", name=f"Rank{i}")[0]
        panes = worksheet.findall("table/panes/pane")
        assert len(panes) == 1 and panes[0].find("mark").get("class") == "Automatic"
        assert not worksheet.findtext("table/rows") and not worksheet.findtext(
            "table/cols"
        )
        assert panes[0].find("encodings/size") is not None
        assert len(panes[0].findall("encodings/text")) == 4
        f = root.xpath(
            "//worksheet[@name=$name]//filter[@class='quantitative']", name=f"Rank{i}"
        )[0]
        assert f.findtext("min") == f.findtext("max") == str(i)
    checks = cloud(data, digest)
    result = {
        "status": "pass",
        "artifact_sha256": digest,
        "acceptance_ids": [
            "ww41-raw-quarter-oracle",
            "ww41-reference-contracts",
            "ww41-rank-blocks",
            "ww41-cloud-states",
        ],
        "oracle": data,
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf8"
    )
    print(
        "PASS WW41 full raw-record/category oracle and reference contracts; Cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    try:
        verify()
    except AssertionError as exc:
        artifact = HERE / "outputs/replicated-workbook.twbx"
        (HERE / "evidence/functional-verification.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "passed": False,
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
