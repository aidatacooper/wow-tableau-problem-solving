"""Independent polygon vertex, profitability, packaged data and action contracts."""

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
import csv
import json
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def verify():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    raw = HERE / item["file"]
    assert sha256(raw.read_bytes()).hexdigest() == item["sha256"]
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        assert (
            sha256(
                z.read(next(n for n in z.namelist() if n.endswith(".hyper")))
            ).hexdigest()
            == item["sha256"]
        )
        r = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(raw)) as c,
    ):
        table = next(
            t
            for schema in c.catalog.get_schema_names()
            for t in c.catalog.get_table_names(schema)
        )
        records = c.execute_list_query(
            'SELECT "Sub-Category","Table Name","Revenue","Budget","Review" FROM '
            + str(table)
        )
    assert len(records) == 24
    groups = defaultdict(list)
    for cat, copy, revenue, budget, review in records:
        groups[cat, copy].append((revenue, budget, review))
    assert len(groups) == 12 and all(len(v) == 2 for v in groups.values())
    expected = {}
    cats = {}
    for (cat, copy), values in sorted(groups.items()):
        revenue, budget, review = [
            sum(float(v[i]) for v in values) / len(values) for i in range(3)
        ]
        path = {"WW": 1, "WW1": 2, "WW2": 3}[copy]
        x = 0 if path == 1 else 20
        y = review if path == 1 else revenue / 20 if path == 2 else budget / 20
        profit = revenue - budget
        margin = profit / budget
        color = "Non-Profitable" if profit < 0 else "Profitable"
        expected[cat + "|" + copy] = {
            "Review": review,
            "Budget": budget,
            "Revenue": revenue,
            "x": x,
            "y": y,
            "Path": path,
            "Profit": profit,
            "Margin": margin,
            "Colour : Line": color,
        }
        cats[cat] = {
            "Profit": profit,
            "Margin": margin,
            "Review": review,
            "Budget": budget,
            "Revenue": revenue,
        }
    assert (
        cats["Tables"]["Profit"] == -60
        and cats["Chairs"]["Profit"] == 50
        and cats["Labels"]["Margin"] == 29 / 70
    )
    for cat in cats:
        assert (
            len(
                {
                    (v["x"], v["y"])
                    for k, v in expected.items()
                    if k.startswith(cat + "|")
                }
            )
            == 3
        )
    legend_filter = r.find('.//worksheet[@name="Legend"]/table/view/filter')
    assert legend_filter is not None
    assert legend_filter.get("column").endswith("[none:Sub-Category:nk]")
    assert legend_filter.find("groupfilter").get("member") == '"Chairs"'
    action = r.find("actions/edit-group-action")
    assert action is not None
    assert action.find("activation").get("type") == "on-select"
    assert (
        action.find("source").get("worksheet") == "Viz (2)"
        and action.find("source").get("dashboard")
        == "2020_05_27_WW22_Profitability_Polygon v2"
    )
    assert action.find("add-or-remove-marks").get("value") == "add"
    assert r.find("document-format-change-manifest/GroupActionAddRemove") is not None
    assert r.find("document-format-change-manifest/SetMembershipControl") is not None
    assert (
        action.find('params/param[@name="selection-clear-set-option"]').get("value")
        == "exclude-all"
    )
    assert (
        action.find('params/param[@name="target-group"]')
        .get("value")
        .endswith("[Selected Sub-Cats]")
    )
    assert (
        r.find('.//worksheet[@name="Viz (2)"]//mark[@class="Polygon"]') is not None
        and r.find('.//worksheet[@name="Viz (2)"]//mark[@class="Line"]') is not None
    )
    main = r.find('.//worksheet[@name="Viz (2)"]')
    for pane in main.findall("table/panes/pane"):
        assert pane.find("encodings/path") is not None
        assert not any(
            "Table Name" in n.get("column", "") for n in pane.findall("encodings/lod")
        )
    legend2 = r.find('.//worksheet[@name="Legend2"]/table/view/filter')
    assert {n.get("member") for n in legend2.findall("groupfilter/groupfilter")} == {
        '"Labels"',
        '"Tables"',
    }
    formulas = [
        n.get("formula")
        for n in r.findall(".//datasources/datasource/column/calculation")
    ]
    for column in r.findall("datasources/datasource/column"):
        if column.get("caption"):
            formulas = [
                formula.replace(column.get("name"), "[" + column.get("caption") + "]")
                for formula in formulas
            ]
    assert (
        "AVG([Revenue])-AVG([Budget])" in formulas
        and "[Profit]/AVG([Budget])" in formulas
    )
    assert (
        "IF [Selected Sub-Cats] THEN [Sub-Category] ELSE 'Click to Expand' END"
        in formulas
    )
    checks = []
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        report = json.loads(manifest.read_text(encoding="utf-8"))
        assert (
            report["source_hashes"]["replica"]
            == sha256(
                (HERE / "outputs/replicated-workbook.twbx").read_bytes()
            ).hexdigest()
        )
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert report["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert not report["browser_interaction_executed"]
        for state in report["states"]:
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for export in state["data"]:
                path = HERE / export["path"]
                assert sha256(path.read_bytes()).hexdigest() == export["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.DictReader(f))
                selected = state.get("filters", {}).get("Sub-Category")
                required = {
                    k for k in expected if not selected or k.startswith(selected + "|")
                }
                seen = set()
                for row in rows:
                    key = row["Sub-Category"] + "|" + row["Table Name"]
                    v = expected[key]
                    for field in ["Path", "Colour : Line"]:
                        if field in row:
                            assert row[field] == str(v[field])
                    if "Measure Names" in row:
                        metric = row["Measure Names"].split(" along ")[0]
                        metric = (
                            metric.replace("Avg. ", "")
                            .replace("Min. ", "")
                            .replace("AVG(", "")
                            .replace("MIN(", "")
                            .rstrip(")")
                        )
                        if metric in ["Review", "Budget", "Revenue", "x", "y"]:
                            val = float(
                                row["Measure Values"].replace("$", "").replace(",", "")
                            )
                            assert abs(val - v[metric]) < 0.00501
                            seen.add((key, metric))
                    else:
                        for metric in ["Review", "Budget", "Revenue", "x", "y"]:
                            col = next(
                                (
                                    k
                                    for k in row
                                    if k == metric or k == "Avg. " + metric
                                ),
                                None,
                            )
                            if col:
                                assert (
                                    abs(
                                        float(
                                            row[col].replace("$", "").replace(",", "")
                                        )
                                        - v[metric]
                                    )
                                    < 0.00501
                                )
                                seen.add((key, metric))
                assert {
                    (k, m)
                    for k in required
                    for m in ["Review", "Budget", "Revenue", "x", "y"]
                } <= seen, (export, seen)
                checks.append(
                    {
                        "role": export["role"],
                        "state": state["name"],
                        "checked_values": len(seen),
                        "scope": "Every category and union-copy average plus x/y; independent profit and budget-based margin computed for all categories. Set click execution is artifact-only.",
                    }
                )
    result = {
        "status": "passed",
        "acceptance_ids": [
            "ww22-profitability-oracle",
            "ww22-polygon-contract",
            "ww22-expand-action",
            "ww22-cloud-polygons",
        ],
        "raw_rows": len(records),
        "vertices": expected,
        "categories": cats,
        "cloud_checks": checks,
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ["vertices", "categories"]},
            indent=2,
        )
    )
    return result


if __name__ == "__main__":
    verify()
