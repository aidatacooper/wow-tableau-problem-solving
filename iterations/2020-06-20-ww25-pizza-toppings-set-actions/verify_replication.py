"""Independent complete price oracle and native set/shape/action contracts."""

import csv
import json
import math
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance: ww25-independent-data, ww25-artifact-contracts, ww25-cloud-states.
INITIAL = {
    "Classic",
    "Ground Beef",
    "Jalapeno Peppers",
    'Large 13.5"',
    "No Sauce",
    "Pineapple",
    "Pork Meatballs",
    "Red Peppers",
}


def oracle():
    file = next((HERE / "inputs").glob("*.hyper"))
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(file)) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Type","Product","Vegetarian","Price" FROM "Extract"."Extract"'
        )
    values = [
        {
            "type": kind,
            "product": product,
            "vegetarian": veg == "Yes",
            "price": float(price),
            "selected": product in INITIAL,
        }
        for kind, product, veg, price in rows
    ]
    assert len(values) == 26 and len({x["product"] for x in values}) == 26
    selected = [x for x in values if x["selected"]]
    assert len(selected) == 8
    total = math.fsum(x["price"] for x in selected)
    assert math.isclose(total, 17.54, abs_tol=1e-9)
    by_type = {
        kind: math.fsum(x["price"] for x in selected if x["type"] == kind)
        for kind in ["Size", "Crust", "Sauce", "Toppings"]
    }
    return {
        "rows": 26,
        "products": values,
        "selected_total": total,
        "selected_by_type": by_type,
        "budget_states": {
            str(b): {
                "difference": b - total,
                "under": max(b - total, 0),
                "over": max(total - b, 0),
            }
            for b in [15, 30, 5]
        },
        "scope": "Every raw product price, type and vegetarian flag; all eight initial set members; global selected total and budget difference.",
    }


def number(text):
    return float(text.replace(chr(163), "").replace(",", "").replace("$", "").strip())


def cloud(data):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return []
    report = json.loads(manifest.read_text())
    assert (
        report["source_hashes"]["replica"]
        == sha256((HERE / "outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    )
    assert len(report["states"]) == 3
    products = {x["product"]: x for x in data["products"]}
    checks = []
    for state in report["states"]:
        for capture in state["data"]:
            file = HERE / capture["path"]
            assert sha256(file.read_bytes()).hexdigest() == capture["sha256"]
            rows = list(
                csv.DictReader(file.read_text(encoding="utf-8-sig").splitlines())
            )
            assert rows, f"Empty CSV does not establish acceptance: {file}"
            if capture["view"] == "Chart":
                expected_kind = state.get("filters", {}).get("Type", "Size")
                expected = {
                    name for name, x in products.items() if x["type"] == expected_kind
                }
                seen = set()
                for row in rows:
                    product = next(
                        (
                            v
                            for k, v in row.items()
                            if k and "Product" in k and v in products
                        ),
                        None,
                    )
                    assert product in expected, (file, row, expected)
                    price = next(
                        v for k, v in row.items() if k and "Price" in k and v.strip()
                    )
                    assert abs(number(price) - products[product]["price"]) < 0.0051
                    seen.add(product)
                assert seen == expected, (file, seen, expected)
                checks.append(
                    {
                        "file": capture["path"],
                        "products": len(seen),
                        "scope": "Every visible product price for the declared Type.",
                    }
                )
            elif capture["view"] == "List of Items":
                seen = {
                    v
                    for row in rows
                    for k, v in row.items()
                    if k and "Product" in k and v in INITIAL
                }
                assert seen == INITIAL, (file, seen)
                checks.append({"file": capture["path"], "selected_products": 8})
            elif capture["view"] == "Total Bar":
                seen = set()
                totals = []
                for row in rows:
                    kind = row.get("Type", "")
                    if kind:
                        value = next(
                            v
                            for k, v in row.items()
                            if k and k in {"Price", "Selected Price"} and v.strip()
                        )
                        assert (
                            abs(number(value) - data["selected_by_type"][kind]) < 0.0051
                        )
                        seen.add(kind)
                    totals += [
                        number(v)
                        for k, v in row.items()
                        if k
                        and k
                        in {"Total Price Selected Products", "Min. Selected Total"}
                        and v.strip()
                    ]
                assert seen == set(data["selected_by_type"]) and totals
                assert all(
                    abs(value - data["selected_total"]) < 0.0051 for value in totals
                )
                checks.append(
                    {
                        "file": capture["path"],
                        "type_subtotals": 4,
                        "global_selected_total": data["selected_total"],
                    }
                )
            elif capture["view"] == "Under Over Budget":
                budget = state.get("parameters", {}).get("Budget", "15")
                expected = data["budget_states"][budget]
                over = [
                    number(v)
                    for row in rows
                    for k, v in row.items()
                    if k in {"Over Budget", "Text Budget Diff Over"} and v.strip()
                ]
                under = [
                    number(v)
                    for row in rows
                    for k, v in row.items()
                    if k in {"Under Budget", "Text Budget Diff Under"} and v.strip()
                ]
                if expected["over"]:
                    assert (
                        over
                        and all(abs(v - expected["over"]) < 0.0051 for v in over)
                        and not under
                    )
                else:
                    assert (
                        under
                        and all(abs(v - expected["under"]) < 0.0051 for v in under)
                        and not over
                    )
                checks.append(
                    {
                        "file": capture["path"],
                        "budget": budget,
                        "difference": expected["difference"],
                    }
                )
            else:
                checks.append(
                    {
                        "file": capture["path"],
                        "rows": len(rows),
                        "scope": "Supporting selector/budget worksheet, not complete price proof.",
                    }
                )
    assert len(checks) == 30
    (HERE / "evidence/cloud-data-comparison.json").write_text(
        json.dumps({"status": "pass", "checks": checks}, indent=2) + "\n"
    )
    return checks


def verify():
    data = oracle()
    output = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    with ZipFile(output) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for item in lock["extracted_data"]:
            assert (
                sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
            )
            assert (
                sha256(
                    z.read(
                        next(
                            n
                            for n in z.namelist()
                            if Path(n).name == Path(item["file"]).name
                        )
                    )
                ).hexdigest()
                == item["sha256"]
            )
    for item in lock["derived_data"]:
        assert sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
    assert len(root.findall("worksheets/worksheet")) == 5
    assert len(root.findall("external/shapes/shape")) == 4
    assert root.xpath(
        'datasources/datasource/style/style-rule/encoding[@attr="shape" and @palette="Custom"]'
    )
    assert root.xpath(
        'worksheets/worksheet[@name="Selector"]/table/panes/pane/encodings/shape'
    )
    group = root.xpath('datasources/datasource/group[@name="[Selected Products]"]')[0]
    members = {
        json.loads(g.get("member"))
        for g in group.findall(".//groupfilter[@function='member']")
    }
    assert members == INITIAL
    actions = root.findall("actions/edit-group-action")
    assert len(actions) == 2 and {
        a.find("add-or-remove-marks").get("value") for a in actions
    } == {"add", "remove"}
    assert all(
        a.find("activation") is None or a.find("activation").get("type") == "on-menu"
        for a in actions
    )
    assert all(
        a.find('params/param[@name="selection-clear-set-option"]').get("value")
        == "do-nothing"
        for a in actions
    )
    assert root.xpath('actions/action/source[@worksheet="Selector"]')
    assert root.xpath('worksheets/worksheet[@name="Total Bar"]//reference-line')
    refstyles = root.xpath(
        'worksheets/worksheet[@name="Total Bar"]//style-rule[@element="refline"]/format'
    )
    assert {f.get("attr"): f.get("value") for f in refstyles}["vertical-align"] == "top"
    assert {f.get("attr"): f.get("value") for f in refstyles}["text-align"] == "right"
    check = root.xpath(
        'datasources/datasource/column[@caption="Selected Product Indicator"]/calculation'
    )[0]
    vegetarian = root.xpath(
        'datasources/datasource/column[@caption="Veg Indicator"]/calculation'
    )[0]
    assert chr(10004) in check.get("formula") and chr(9679) in vegetarian.get("formula")
    action = root.xpath('actions/action[@caption="Filter Chart"]')[0]
    filtering = root.xpath('worksheets/worksheet[@name="Chart"]/table/view/filter')[0]
    initial = filtering.find("groupfilter")
    assert initial.get("member") == '"Size"'
    assert initial.get(
        "{http://www.tableausoftware.com/xml/user}ui-action-filter"
    ) == action.get("name")
    assert "[Action (Type)]" in filtering.get("column")
    assert len(root.xpath('worksheets/worksheet[@name="Chart"]/table/view/filter')) == 1
    assert any(
        "\u00a3" in c.get("default-format", "")
        for c in root.findall("datasources/datasource/column")
    )
    assert root.xpath(
        'worksheets/worksheet[@name="List of Items"]//pane/mark[@class="Bar" or @class="Automatic"]'
    )
    size = root.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "800" and size.get("maxheight") == "500"
    checks = cloud(data)
    result = {
        "case": "ww25",
        "status": "pass",
        "artifact_sha256": sha256(output.read_bytes()).hexdigest(),
        "oracle": data,
        "cloud_status": "passed" if checks else "pending",
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        "PASS WW25 complete product/set/budget oracle and five-sheet contracts; cloud="
        + result["cloud_status"]
    )
    return result


if __name__ == "__main__":
    verify()
