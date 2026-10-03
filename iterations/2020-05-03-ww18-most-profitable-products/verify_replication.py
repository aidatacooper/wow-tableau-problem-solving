"""Independent nested product-margin oracle and native action/addressing contracts."""

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
import ast
import csv
import json
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
STATES = {
    "default": (3, 5, ""),
    "copiers-expanded": (3, 5, "Copiers"),
    "small-top": (1, 2, ""),
    "others-expanded": (3, 5, "All Others"),
}


def number(raw):
    return float(raw.replace(",", "").replace("$", "").replace("%", "").strip())


def verify():
    # blank-sdk-build; locked-source-data; native-calculations-actions;
    # independent-complete-data-oracle; cloud-rest-comparison; cloud-visual-review
    source = (HERE / "build_replication.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    assert 'TWBEditor("")' in source
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_") for n in ast.walk(tree)
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    data = HERE / item["file"]
    assert sha256(data.read_bytes()).hexdigest() == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        assert (
            sha256(
                z.read(next(n for n in z.namelist() if n.endswith(".hyper")))
            ).hexdigest()
            == item["sha256"]
        )
    columns = {
        c.get("caption"): c
        for c in root.xpath("/workbook/datasources/datasource/column[@caption]")
    }
    group = root.xpath('//datasource/group[@caption="Top N SubCats by Profit"]')[0]
    assert group.xpath('./groupfilter[@function="end" and @end="top"]')
    assert "Parameter" in group.find("groupfilter").get("count")
    assert (
        group.xpath('.//groupfilter[@direction="DESC"]')[0].get("expression").upper()
        == "SUM([PROFIT])"
    )
    assert "RANK_UNIQUE" in columns["Margin Rank"].find("calculation").get("formula")
    sheet = root.xpath('//worksheet[@name="Viz"]')[0]
    assert root.xpath(
        '//window[@class="dashboard"]/viewpoints/viewpoint[@name="Viz"]/zoom[@type="fit-width"]'
    )
    aliases = root.xpath(
        '/workbook/datasources/datasource/column[@name="[:Measure Names]"]/aliases/alias'
    )
    assert {a.get("value") for a in aliases} == {" Margin ", " Profit ", " Sales "}
    known = {ci.get("name") for ci in sheet.xpath(".//column-instance")}
    for alias in aliases:
        assert any(name in alias.get("key") for name in known)
    assert sheet.find("table/rows").get("total") == "true"
    assert sheet.find("table/cols").get("total") is None
    assert len(sheet.xpath("./table/subtotals/column")) == 1
    assert not sheet.xpath("./table/view/datasource-dependencies/column[@visual-total]")
    assert not sheet.xpath(
        './table/view/datasource-dependencies/column-instance[contains(@name, "vt_")]'
    )
    assert sheet.xpath(".//text[@column]")
    assert any(
        columns["Show?"].get("name")[1:-1] in f.get("column", "")
        for f in sheet.xpath("./table/view/filter")
    )
    assert len(sheet.xpath("./table/view/filter")) == 2
    # Let the three measure columns share the available pane width, as the source does.
    assert not sheet.xpath(
        './table/style/style-rule[@element="cell"]/format[@attr="width"]'
    )
    for name in [
        "Margin Rank",
        "Sales For Others",
        "Profit For Others",
        "Product Name Group",
        "Grouped Sales",
        "Grouped Profit",
        "Grouped Margin",
        "Show?",
    ]:
        assert columns[name].find("calculation/table-calc") is not None
        instances = sheet.xpath(
            "./table/view/datasource-dependencies/column-instance[@column=$name]",
            name=columns[name].get("name"),
        )
        assert instances and all(ci.find("table-calc") is not None for ci in instances)
        assert all(
            tc.get("ordering-type") == "Field"
            and "Product Name" in tc.get("ordering-field", "")
            for ci in instances
            for tc in ci.findall("table-calc")
        )
    action = root.xpath("/workbook/actions/edit-parameter-action")[0]
    assert action.find("activation").get("type") == "on-select"
    assert action.find("source").get("worksheet") == "Viz"
    assert action.xpath('./params/param[@name="target-parameter"]')[0].get(
        "value"
    ) == "[Parameters]." + columns["Selected SubCat Group"].get("name")
    assert "THEN '' ELSE MIN(" in columns["SubCat Group for Reset"].find(
        "calculation"
    ).get("formula")
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(data)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Sub-Category","Product Name","Sales","Profit" FROM "Extract"."Extract"'
        )
    bycat = defaultdict(lambda: [0.0, 0.0])
    for cat, product, sales, profit in rows:
        bycat[cat][0] += sales
        bycat[cat][1] += profit
    oracle = {}
    for state, (n, p, expanded) in STATES.items():
        top = set(sorted(bycat, key=lambda cat: -bycat[cat][1])[:n])
        groups = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
        for cat, product, sales, profit in rows:
            value = groups[cat if cat in top else "All Others"][product]
            value[0] += sales
            value[1] += profit
        oracle[state] = {
            "top_categories": sorted(top),
            "products_to_show": p,
            "expanded": expanded,
            "groups": {
                g: {
                    name: {"sales": v[0], "profit": v[1], "margin": v[1] / v[0]}
                    for name, v in products.items()
                }
                for g, products in groups.items()
            },
        }
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "source_rows": len(rows),
        "oracle": oracle,
        "scope": "Full nested product groups. Tied margin ranks permit alternative valid top products; others values must conserve complete group totals. Native subtotal contracts and all exported group subtotals/grandtotal records are independently checked against raw aggregate profit/sales. CSV proves total data, while images establish visible placement.",
        "browser_interaction_executed": False,
    }
    cloudpath = HERE / "evidence/cloud-verification.json"
    if cloudpath.exists():
        cloud = json.loads(cloudpath.read_text(encoding="utf-8"))
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert cloud["source_hashes"]["replica"] == digest
        assert cloud["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert provenance["original_sha256"] == lock["locked_original_sha256"]
        assert {s["name"] for s in cloud["states"]} == set(STATES)
        checks = []
        for state in cloud["states"]:
            expected = oracle[state["name"]]
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for capture in state["data"]:
                path = HERE / capture["path"]
                assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as f:
                    exported = list(csv.DictReader(f))
                assert exported, (path, "Empty CSV")
                observed = defaultdict(dict)
                observed_totals = defaultdict(dict)
                for row in exported:
                    groupname = row.get("SubCat Group", "")
                    product = row.get("Product Name Group", "")
                    if (
                        groupname not in expected["groups"]
                        and groupname != "All"
                        or not product
                    ):
                        continue
                    measures = {}
                    for metric in ["Sales", "Profit", "Margin"]:
                        key = next(
                            (
                                k
                                for k in row
                                if k.strip() in ["Grouped " + metric, metric] and row[k]
                            ),
                            None,
                        )
                        if key:
                            measures[metric.lower()] = number(row[key]) / (
                                100 if "%" in row[key] else 1
                            )
                    if not measures and "Measure Names" in row:
                        metric = (
                            row["Measure Names"]
                            .strip()
                            .replace("Grouped ", "")
                            .split(" along ")[0]
                            .lower()
                        )
                        key = next(
                            (
                                k
                                for k in row
                                if k in ["Measure Values", "Value"] and row[k]
                            ),
                            None,
                        )
                        if key:
                            measures[metric] = number(row[key]) / (
                                100 if "%" in row[key] else 1
                            )
                    if measures:
                        if row.get("Product Name") == "All":
                            observed_totals[groupname].update(measures)
                        else:
                            observed[groupname].setdefault(product, {}).update(measures)
                assert set(observed) == set(expected["groups"]), (path, list(observed))
                assert set(observed_totals) == set(expected["groups"]) | {"All"}, (
                    path,
                    list(observed_totals),
                )
                for groupname, measures in observed_totals.items():
                    products = (
                        expected["groups"][groupname]
                        if groupname != "All"
                        else {
                            str(i): value
                            for i, value in enumerate(
                                v
                                for g in expected["groups"].values()
                                for v in g.values()
                            )
                        }
                    )
                    sales = sum(v["sales"] for v in products.values())
                    profit = sum(v["profit"] for v in products.values())
                    wanted_totals = {
                        "sales": sales,
                        "profit": profit,
                        "margin": profit / sales,
                    }
                    assert set(measures) == set(wanted_totals)
                    for metric, value in measures.items():
                        assert abs(value - wanted_totals[metric]) <= (
                            (0.0051 if metric == "margin" else 0.51)
                            if capture["role"] == "replica"
                            else (1e-8 if metric == "margin" else 1e-5)
                        ), (path, groupname, metric, value, wanted_totals[metric])
                for groupname, products in observed.items():
                    full = expected["groups"][groupname]
                    selected = {name for name in products if name != "All Others"}
                    expanded = groupname == expected["expanded"]
                    assert selected <= set(full)
                    assert len(selected) == (
                        len(full)
                        if expanded
                        else min(expected["products_to_show"], len(full))
                    ), (path, groupname, len(selected))
                    if not expanded and selected:
                        cutoff = sorted(
                            (v["margin"] for v in full.values()), reverse=True
                        )[len(selected) - 1]
                        assert all(
                            full[name]["margin"] >= cutoff - 1e-12 for name in selected
                        ), (path, groupname, "Invalid top product")
                    for name, measures in products.items():
                        assert set(measures) == {"sales", "profit", "margin"}, (
                            path,
                            name,
                            measures,
                        )
                        if name == "All Others":
                            remainder = [
                                v for key, v in full.items() if key not in selected
                            ]
                            sales = sum(v["sales"] for v in remainder)
                            profit = sum(v["profit"] for v in remainder)
                            want = {
                                "sales": sales,
                                "profit": profit,
                                "margin": profit / sales,
                            }
                        else:
                            want = full[name]
                        for metric, value in measures.items():
                            tolerance = 0.0051 if metric == "margin" else 0.51
                            assert abs(value - want[metric]) <= tolerance, (
                                path,
                                groupname,
                                name,
                                metric,
                                value,
                                want[metric],
                            )
                    assert ("All Others" in products) == (
                        not expanded and len(full) > len(selected)
                    )
                checks.append(
                    {"path": capture["path"], "status": "pass", "groups": len(observed)}
                )
        assert len(checks) == 8
        report["cloud_checks"] = checks
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        "PASS",
        len(rows),
        "rows;",
        {k: len(v["groups"]) for k, v in oracle.items()},
        "groups",
    )


if __name__ == "__main__":
    verify()
