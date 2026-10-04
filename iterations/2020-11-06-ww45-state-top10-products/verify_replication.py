"""Independent complete fact aggregation and native tooltip/TopN contracts."""

import csv
import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
SEABOARD = [
    "Vermont",
    "New Hampshire",
    "Massachusetts",
    "Connecticut",
    "Rhode Island",
    "New Jersey",
    "Delaware",
    "Maryland",
    "District of Columbia",
]
STATES = {
    "default": None,
    "california": "California",
    "texas": "Texas",
    "new-york": "New York",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def oracle():
    source = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint, str(source)) as connection:
            rows = connection.execute_list_query(
                'SELECT "Order ID", "State", "Product Name", "Sales", "Profit" FROM "Extract"."Extract"'
            )
    assert len(rows) == 9994
    by_state, by_product, by_pair = (
        defaultdict(list),
        defaultdict(list),
        defaultdict(list),
    )
    for order, state, product, sales, profit in rows:
        assert order and state and product
        by_state[state].append((order, sales, profit))
        by_product[product].append((order, sales, profit))
        by_pair[state, product].append((order, sales, profit))

    def aggregate(records):
        return {
            "Orders": len(records),
            "Distinct Orders": len({r[0] for r in records}),
            "Sales": math.fsum(r[1] for r in records),
            "Profit": math.fsum(r[2] for r in records),
        }

    states = {s: aggregate(records) for s, records in by_state.items()}
    products = {p: aggregate(records) for p, records in by_product.items()}
    pairs = {
        s: {p: aggregate(records) for (st, p), records in by_pair.items() if st == s}
        for s in states
    }
    top = lambda mapping: sorted(mapping, key=lambda p: (-mapping[p]["Sales"], p))[:10]
    global_top = top(products)
    state_top = {s: top(mapping) for s, mapping in pairs.items()}
    assert len(states) == 49 and all(
        len(state_top[s]) == min(10, len(pairs[s])) for s in states
    )
    return {
        "facts": len(rows),
        "state_totals": states,
        "products": products,
        "state_products": pairs,
        "global_top10": global_top,
        "state_top10": state_top,
        "orders_semantics": "COUNT(Order ID), matching source cnt instance; distinct counts independently included, not substituted.",
    }


def native(root):
    worksheets = {w.get("name"): w for w in root.findall("worksheets/worksheet")}
    assert set(worksheets) >= {"Map", "Seaboard States", "Top 10 Products"}
    top = worksheets["Top 10 Products"]
    assert top.find("table/panes/pane/mark").get("class") == "Square"
    for tag in ("color", "text"):
        encoding = top.find(f"table/panes/pane/encodings/{tag}")
        assert encoding.get("column").endswith(".[Multiple Values]")
        assert encoding.get("separate-domains") == "true"
    assert top.find("table/rows").get("total") == "true"
    criterion = top.find("table/view/filter/groupfilter[@function='end']")
    assert criterion is not None and criterion.get("count") == "10"
    order = criterion.find("groupfilter")
    assert (
        order.get("direction") == "DESC" and order.get("expression") == "SUM([Sales])"
    )
    colors = top.findall(
        "table/style/style-rule[@element='mark']/encoding[@attr='color']"
    )
    profit = next(c for c in colors if c.get("field").endswith(".[sum:Profit:qk]"))
    assert profit.get("center") == "0" and profit.get("palette") == "red_black_10_0"
    assert len(colors) == 3
    for encoding in colors:
        if encoding is not profit:
            assert encoding.get("num-steps") == "2"
            assert set(encoding.xpath("color-palette/color/text()")) == {"#ffffff"}
    context = top.findall("table/view/filter[@context='true']")
    assert len(context) == 1 and "Tooltip" in context[0].get("column")
    levels = context[0].xpath("groupfilter/groupfilter/@level")
    datasource = root.find("datasources/datasource")
    abbrev = next(
        c for c in datasource.findall("column") if c.get("caption") == "State Abbrev"
    )
    assert set(levels) == {"[State]", abbrev.get("name")}
    target_dependencies = top.find("table/view/datasource-dependencies")
    for member in levels:
        assert any(
            c.get("name") == member for c in target_dependencies.findall("column")
        ), (
            member,
            "Compound tooltip target must declare each member and its recursive calculation dependencies",
        )
        assert any(
            ci.get("column") == member
            for ci in target_dependencies.findall("column-instance")
        ), (member, "Compound tooltip target must have a real member instance")
    assert any(
        c.get("name") == "[State]" for c in target_dependencies.findall("column")
    )
    group_local = context[0].get("column").split("].", 1)[1]
    group = next(g for g in datasource.findall("group") if g.get("name") == group_local)
    assert set(group.xpath("groupfilter/groupfilter/@level")) == set(levels)
    for sheet in ("Map", "Seaboard States"):
        tooltip = "".join(
            worksheets[sheet].xpath(
                "table/panes/pane/customized-tooltip/formatted-text/run/text()"
            )
        )
        assert (
            'Sheet name="Top 10 Products"' in tooltip
            and 'maxwidth="500"' in tooltip
            and 'maxheight="350"' in tooltip
        )
        dependencies = worksheets[sheet].find("table/view/datasource-dependencies")
        for field in ("[State]", abbrev.get("name")):
            instance = next(
                ci
                for ci in dependencies.findall("column-instance")
                if ci.get("column") == field and ci.get("derivation") == "None"
            )
            qualified = f"[{datasource.get('name')}].{instance.get('name')}"
            assert qualified in tooltip, (
                sheet,
                field,
                "Tooltip filter must bind an existing actual worksheet instance",
            )
    map_sheet = worksheets["Map"]
    assert map_sheet.find("table/panes/pane/encodings/geometry") is not None
    assert (
        map_sheet.find("table/panes/pane/encodings/color")
        .get("column")
        .endswith(".[sum:Profit:qk]")
    )
    layers = map_sheet.xpath(
        "table/style/style-rule[@element='map-layer']/format[@attr='enabled']/@value"
    )
    assert len(layers) >= 40 and set(layers) == {"false"}
    dash = root.find("dashboards/dashboard")
    assert (
        dash.find("size").get("maxwidth") == "1000"
        and dash.find("size").get("maxheight") == "800"
    )
    for sheet, rectangle in {
        "Map": (800, 21875, 87000, 69125),
        "Seaboard States": (87800, 35250, 5900, 46750),
    }.items():
        zone = next(
            z
            for z in dash.findall("zones//zone")
            if z.get("name") == sheet and z.get("type-v2") != "color"
        )
        assert tuple(int(zone.get(k)) for k in ("x", "y", "w", "h")) == rectangle
    strip = worksheets["Seaboard States"]
    fixed = strip.find(
        "table/style/style-rule[@element='axis']/encoding[@range-type='fixed']"
    )
    assert fixed is not None and fixed.get("min") == "0" and fixed.get("max") == "1"
    assert fixed.get("field") == strip.find("table/cols").text, (
        "Fixed axis must bind the actual aggregate column instance"
    )
    assert not root.findall("actions/action"), (
        "Source relies on native tooltip filtering, not dashboard click actions."
    )
    return ["ww45-native-contracts"]


def number(text):
    return float(text.replace("$", "").replace(",", "").strip())


def cloud(data, workbook_hash):
    # ww45-cloud-states proves the actual REST scope, not a native hover event.
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return {"status": "pending", "checks": []}
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["source_hashes"]["replica"] == workbook_hash
    provenance = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
    )
    assert report["source_hashes"]["author"] == provenance["export_sha256"]
    assert {s["name"] for s in report["states"]} == set(STATES)
    checks = []
    for state in report["states"]:
        selected = STATES[state["name"]]
        for item in state["views"].values():
            assert digest(HERE / item["path"]) == item["sha256"]
        for item in state["data"]:
            file = HERE / item["path"]
            assert digest(file) == item["sha256"]
            rows = list(
                csv.DictReader(file.read_text(encoding="utf-8-sig").splitlines())
            )
            view = item["view"]
            if view == "Map":
                expected = {selected} if selected else set(data["state_totals"])
                actual = {r["State"]: number(r["Profit"]) for r in rows}
                assert set(actual) == expected, (file, actual, expected)
                for s, value in actual.items():
                    assert math.isclose(
                        value, data["state_totals"][s]["Profit"], abs_tol=0.51
                    )
                checks.append(
                    {
                        "file": item["path"],
                        "marks": len(actual),
                        "scope": "Complete state profit aggregates",
                    }
                )
            elif view == "Seaboard States":
                expected = set(SEABOARD) if not selected else {selected}
                actual = {r["State"] for r in rows}
                assert actual == expected, (file, actual, expected)
                checks.append(
                    {
                        "file": item["path"],
                        "marks": len(actual),
                        "scope": "Default seaboard members; REST State replaces the original member filter in selected states",
                    }
                )
            elif view == "Top 10 Products":
                assert rows, (file, "Empty complete product export")
                expected_pairs = {
                    (s, product): measures
                    for s, products in data["state_products"].items()
                    if selected is None or s == selected
                    for product, measures in products.items()
                    if product in data["global_top10"]
                }
                actual, totals = {}, {}
                for row in rows:
                    metric = row["Measure Names"].strip()
                    assert metric in {"Orders", "Sales", "Profit"}
                    s, product = row["State"], row["Product Name"]
                    value = number(row["Measure Values"])
                    if s == product == "All":
                        assert metric not in totals
                        totals[metric] = value
                    else:
                        key = (s, product, metric)
                        assert key not in actual and (s, product) in expected_pairs, (
                            file,
                            key,
                        )
                        target = expected_pairs[s, product][metric]
                        assert math.isclose(
                            value, target, rel_tol=1e-10, abs_tol=1e-6
                        ), (file, key, value, target)
                        actual[key] = value
                expected_keys = {
                    (s, p, metric)
                    for s, p in expected_pairs
                    for metric in ("Orders", "Sales", "Profit")
                }
                assert set(actual) == expected_keys, (
                    file,
                    "Missing product/metric marks",
                    expected_keys - set(actual),
                )
                assert set(totals) == {"Orders", "Sales", "Profit"}
                for metric in totals:
                    target = math.fsum(
                        measures[metric] for measures in expected_pairs.values()
                    )
                    assert math.isclose(
                        totals[metric], target, rel_tol=1e-10, abs_tol=1e-6
                    ), (file, metric, totals[metric], target)
                local = data["state_top10"].get(selected) if selected else None
                actual_products = sorted({p for s, p in expected_pairs})
                checks.append(
                    {
                        "file": item["path"],
                        "body_groups": len(expected_pairs),
                        "metric_values": len(actual),
                        "grand_totals": totals,
                        "products": actual_products,
                        "local_top10_from_raw": local,
                        "scope": "All global Top10 members with facts in REST State, plus full three-measure grand total; does not execute compound VIT context or prove state-local hover membership",
                    }
                )
            else:
                raise AssertionError((file, view))
    assert len(checks) == 24
    image_manifest = HERE / "evidence/tooltip-worksheet-images.json"
    image_scope = {"status": "pending"}
    if image_manifest.exists():
        extra = json.loads(image_manifest.read_text(encoding="utf-8"))
        assert extra["source_hashes"] == report["source_hashes"]
        parent_path = HERE / extra["parent_capture_path"]
        assert parent_path.resolve().is_relative_to((HERE / "evidence").resolve())
        assert extra["main_capture_manifest_sha256"] == digest(parent_path)
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        assert parent["source_hashes"] == report["source_hashes"]
        assert parent["states"] == report["states"]
        assert len(extra["images"]) == 8
        assert {(i["role"], i["state"]) for i in extra["images"]} == {
            (role, state) for role in ("author", "replica") for state in STATES
        }
        for item in extra["images"]:
            assert digest(HERE / item["path"]) == item["sha256"]
            assert item["view"] == "Top 10 Products"
        image_scope = {"status": "passed", "count": 8, "scope": extra["scope"]}
    return {
        "status": "passed",
        "acceptance_id": "ww45-cloud-states",
        "checks": checks,
        "native_hover_executed": False,
        "standalone_product_images": image_scope,
        "local_top10_evidence": "All49 raw state rankings and native compound context-before-TopN artifact contract; ordinary State REST exports only global member subsets.",
    }


def verify():
    workbook = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    with ZipFile(workbook) as package:
        root = etree.fromstring(
            package.read(next(n for n in package.namelist() if n.endswith(".twb")))
        )
        for entry in lock["extracted_data"]:
            assert digest(HERE / entry["file"]) == entry["sha256"]
            packaged = next(
                n
                for n in package.namelist()
                if Path(n).name == Path(entry["file"]).name
            )
            assert sha256(package.read(packaged)).hexdigest() == entry["sha256"]
    data = oracle()
    checks = native(root)
    digest_value = digest(workbook)
    result = {
        "workbook_sha256": digest_value,
        "acceptance_checks": ["ww45-raw-data", *checks],
        "oracle": data,
        "cloud": cloud(data, digest_value),
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        "PASS WW45 9994 facts / 49 state aggregates / all state-product totals and Top10 rankings / native context VIT; Cloud=",
        result["cloud"]["status"],
    )


if __name__ == "__main__":
    verify()
