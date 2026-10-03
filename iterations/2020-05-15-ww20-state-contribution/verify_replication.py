"""Independent complete state metrics, distinct customer shares and action contracts."""

import ast
import csv
import json
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
SELECTED = {"Alabama", "Illinois", "Kentucky", "Virginia"}
STATES = {"default": None, "selected-only": SELECTED, "alabama": {"Alabama"}}


def number(raw):
    raw = raw.strip()
    return float(raw.replace(",", "").replace("$", "").replace("%", "")) / (
        100 if "%" in raw else 1
    )


def membership(raw):
    value = raw.strip().lower()
    assert value in ["in", "out", "true", "false", "1", "0"], raw
    return value in ["in", "true", "1"]


def verify():
    # blank-sdk-build; locked-source-data; native-calculations-actions;
    # independent-complete-data-oracle; cloud-rest-comparison; cloud-visual-review
    source = (HERE / "build_replication.py").read_text(encoding="utf-8-sig")
    assert 'TWBEditor("")' in source
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_")
        for n in ast.walk(ast.parse(source))
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
    group = root.xpath('//datasource/group[@caption="Selected States"]')[0]
    assert {
        m.get("member").strip('"')
        for m in group.xpath('.//groupfilter[@function="member"]')
    } == SELECTED
    map_sheet = root.xpath('//worksheet[@name="Map"]')[0]
    assert map_sheet.xpath('./table/panes/pane/mark[@class="Multipolygon"]')
    assert (
        map_sheet.xpath("./table/panes/pane/encodings/geometry")[0]
        .get("column")
        .endswith(".[Geometry (generated)]")
    )
    statecolumns = root.xpath(
        '/workbook/datasources/datasource/column[@name="[State]"]'
    )
    assert statecolumns[0].get("semantic-role") == "[State].[Name]"
    actions = root.xpath("/workbook/actions/edit-group-action")
    assert len(actions) == 2
    for action in actions:
        assert action.find("activation").get("type") == "on-select"
        source_sheet = action.find("source").get("worksheet")
        assert source_sheet in ["Map", "State List"]
        operation = action.find("add-or-remove-marks")
        assert operation is not None and operation.get("value") == (
            "add" if source_sheet == "Map" else "remove"
        )
        params = {p.get("name"): p.get("value") for p in action.findall("params/param")}
        assert params["selection-clear-set-option"] == "do-nothing"
        assert params["target-group"].endswith(".[Selected States]")
    filters = root.xpath("/workbook/actions/action")
    assert (
        len(filters) == 1 and filters[0].find("activation").get("type") == "on-select"
    )
    assert filters[0].find("source").get("worksheet") == "Map"
    assert filters[0].find("activation").get("auto-clear") == "true"
    mapping = unquote(filters[0].find("link").get("expression"))
    assert (
        columns["True"].get("name") in mapping
        and columns["False"].get("name") in mapping
    )
    assert filters[0].xpath('./command/param[@name="target"]')[0].get("value") == "Map"
    assert root.xpath('//worksheet[@name="State List"]/table/view/filter')
    assert not root.xpath(
        '//column-instance[@column="[Selected States]" and @derivation="Attribute"]'
    )
    assert (
        columns["Show Selected State"]
        .find("calculation")
        .get("formula")
        .endswith("[Selected States]")
    )
    assert len(root.xpath('//worksheet[@name="Customers"]/table/panes/pane')) == 2
    for metric in ["Sales", "Orders", "Customers"]:
        heading_base = columns[metric + " Heading"].get("name")
        heading_sheet = root.xpath("//worksheet[@name=$metric]", metric=metric)[0]
        heading_instance = heading_sheet.xpath(
            ".//column-instance[@column=$base]", base=heading_base
        )[0].get("name")
        assert heading_instance in heading_sheet.xpath(
            "string(./layout-options/title/formatted-text/run)"
        )
    for formatted in [
        "Sales Contribution",
        "Orders Contribution",
        "% Customers of Selected States",
    ]:
        assert columns[formatted].get("default-format") == "p0.0%"
    for name in ["Sales Contribution", "Orders Contribution"]:
        assert "WINDOW_SUM" in columns[name].find("calculation").get("formula")
        assert columns[name].find("calculation/table-calc") is not None
        base = columns[name].get("name")
        instances = root.xpath(
            "//worksheet[@name=$sheet]//column-instance[@column=$base]/table-calc",
            sheet=name.split()[0],
            base=base,
        )
        assert instances and all(
            c.get("ordering-type") == "Field"
            and c.get("ordering-field", "").endswith(".[io:Selected States:nk]")
            for c in instances
        )
    assert "COUNTD(IF" in columns["Customers of Selected States"].find(
        "calculation"
    ).get("formula")
    # Layout contracts preserve the original top metrics, wide map and compact
    # removal sidebar; numerical/action tests alone cannot establish readability.
    zones = {
        z.get("name"): z
        for z in root.xpath("/workbook/dashboards/dashboard/zones//zone[@name]")
    }
    assert int(zones["Map"].get("w")) >= 80000
    assert int(zones["Map"].get("y")) == 26375
    for metric in ["Sales", "Orders", "Customers"]:
        assert int(zones[metric].get("y")) < int(zones["Map"].get("y"))
        metric_sheet = root.xpath("//worksheet[@name=$name]", name=metric)[0]
        assert metric_sheet.xpath(
            "table/style/style-rule[@element='axis']/encoding[@range-type='fixed' and @min='0' and @max='1']"
        )
        assert metric_sheet.xpath(
            "table/panes/pane/style/style-rule/format[@attr='size' and @value='0.8']"
        )
    for metric in ["Sales", "Orders"]:
        assert root.xpath(
            "//worksheet[@name=$name]/table/view/computed-sort[@direction='DESC']",
            name=metric,
        )
    customers = root.xpath("//worksheet[@name='Customers']")[0]
    assert customers.xpath(
        "table/style/style-rule[@element='axis']/format[@attr='render-fold-reversed' and @value='true']"
    )
    assert (
        len(
            customers.xpath(
                "table/style/style-rule[@element='axis']/format[@attr='height' and @value='32']"
            )
        )
        == 2
    )
    ratio_base = columns["% Customers of Selected States"].get("name")
    ratio_instance = customers.xpath(
        ".//column-instance[@column=$base]", base=ratio_base
    )[0].get("name")
    assert customers.xpath(
        "table/style/style-rule[@element='axis']/format[@attr='title' and @value='' and @scope='cols' and contains(@field,$instance)]",
        instance=ratio_instance,
    )
    assert customers.xpath(
        "table/style/style-rule[@element='label']/format[@attr='text-format' and @value='p0%' and contains(@field,$instance)]",
        instance=ratio_instance,
    )
    viewpoints = root.xpath(
        "/workbook/windows/window[@class='dashboard']/viewpoints/viewpoint"
    )
    for metric in ["Sales", "Orders", "Customers"]:
        assert any(
            v.get("name") == metric and v.find("zoom").get("type") == "fit-width"
            for v in viewpoints
        )
    list_sheet = root.xpath("//worksheet[@name='State List']")[0]
    assert list_sheet.xpath("table/panes/pane/mark[@class='Bar']")
    assert list_sheet.xpath(
        "table/panes/pane/customized-label/formatted-text/run[@fontcolor='#ffffff']"
    )
    assert root.xpath(
        "/workbook/dashboards/dashboard/zones//zone/zone-style/format[@attr='background-color' and @value='#f5f5f5']"
    )
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(data)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "State","Order ID","Customer ID","Sales" FROM "Extract"."Extract"'
        )
    allstates = {r[0] for r in rows}

    def totals(selected):
        records = [r for r in rows if r[0] in selected]
        return {
            "sales": sum(r[3] for r in records),
            "orders": len({r[1] for r in records}),
            "customers": len({r[2] for r in records}),
        }

    overall = totals(allstates)
    selected = totals(SELECTED)
    customer_share = selected["customers"] / overall["customers"]
    oracle = {}
    for state, restriction in STATES.items():
        active = allstates if restriction is None else restriction
        denominator = totals(active)
        included = totals(active & SELECTED)
        bystate = {s: totals({s}) for s in active}
        oracle[state] = {
            "states": bystate,
            "list": sorted(active & SELECTED),
            "sales_share": included["sales"] / denominator["sales"],
            "orders_share": included["orders"] / denominator["orders"],
            "customer_share": customer_share,
            "selected": included,
            "visible_total": denominator,
        }
    # Independent set-event outcomes supplement native contracts; no browser events.
    outcomes = {
        name: totals(values)
        for name, values in {
            "add-california": SELECTED | {"California"},
            "remove-illinois": SELECTED - {"Illinois"},
            "cleared-selection-keeps-members": SELECTED,
            "empty-set": set(),
        }.items()
    }
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "source_rows": len(rows),
        "overall": overall,
        "initial_selected": selected,
        "states": oracle,
        "independent_set_event_outcomes": outcomes,
        "browser_interaction_executed": False,
        "scope": "Every state Sales/distinct orders/distinct customers, selected list and complete contribution bars. Customer share uses a global distinct numerator and denominator, not summed per-state customer counts. REST states filter State; they do not mutate set membership.",
    }
    cloudpath = HERE / "evidence/cloud-verification.json"
    if cloudpath.exists():
        cloud = json.loads(cloudpath.read_text(encoding="utf-8"))
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert (
            cloud["source_hashes"]["replica"] == digest
            and cloud["source_hashes"]["author"] == provenance["comparison_sha256"]
        )
        assert provenance["original_sha256"] == lock["locked_original_sha256"]
        assert {s["name"] for s in cloud["states"]} == set(STATES)
        checks = []
        for state in cloud["states"]:
            wanted = oracle[state["name"]]
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
                view = capture["view"]
                if view == "Map":
                    found = {}
                    for row in exported:
                        state_name = row["State"]
                        assert state_name in wanted["states"]
                        expected = wanted["states"][state_name]
                        for key, metric in [
                            ("Sales", "sales"),
                            ("# Orders", "orders"),
                            ("# Customers", "customers"),
                        ]:
                            assert key in row and abs(
                                number(row[key]) - expected[metric]
                            ) <= (0.51 if metric == "sales" else 0.001), (
                                path,
                                state_name,
                                key,
                                row,
                            )
                        found[state_name] = row
                    assert set(found) == set(wanted["states"])
                elif view == "State List":
                    assert {r["State"] for r in exported} == set(wanted["list"])
                elif view in ["Sales", "Orders"]:
                    metric = view.lower()
                    seen = {}
                    for row in exported:
                        key = next(
                            (
                                k
                                for k in row
                                if ("In / Out" in k or k == "Selected States")
                                and row[k]
                            ),
                            None,
                        )
                        assert key, (path, "Missing In/Out grouping", row)
                        isin = membership(row[key])
                        valuekey = next(
                            (
                                k
                                for k in row
                                if k
                                in [
                                    view,
                                    view + " Contribution",
                                    "# Orders",
                                    "% of Total " + view,
                                    "% of Total # Orders",
                                ]
                                and row[k]
                            ),
                            None,
                        )
                        assert valuekey, (path, "Missing contribution value", row)
                        expected = (
                            wanted[metric + "_share"]
                            if isin
                            else 1 - wanted[metric + "_share"]
                        )
                        value = number(row[valuekey])
                        assert abs(value - expected) <= 0.00051, (
                            path,
                            isin,
                            value,
                            expected,
                        )
                        seen[isin] = value
                    assert True in seen
                    assert len(seen) == (2 if wanted[metric + "_share"] < 1 else 1)
                elif view == "Customers":
                    sharekeys = [
                        k
                        for k in exported[0]
                        if ("% Customers" in k or "Customer Share" in k)
                    ]
                    assert sharekeys, (path, "Missing customer share")
                    for row in exported:
                        selected_key = next(
                            k
                            for k in row
                            if "Customers of Selected States" in k and "%" not in k
                        )
                        total_key = next(k for k in row if "Total Customers" in k)
                        assert number(row[selected_key]) == selected["customers"], (
                            path,
                            row,
                        )
                        assert number(row[total_key]) == overall["customers"], (
                            path,
                            row,
                        )
                    values = [
                        number(r[k])
                        for r in exported
                        for k in sharekeys
                        if r[k] and r[k] != "Null"
                    ]
                    assert values and all(
                        abs(v - customer_share) <= 0.00051 for v in values
                    ), (path, values, customer_share)
                else:
                    raise AssertionError((path, "Unknown CSV scope", view))
                checks.append(
                    {
                        "path": capture["path"],
                        "status": "pass",
                        "view": view,
                        "rows": len(exported),
                    }
                )
        assert len(checks) == 30
        report["cloud_checks"] = checks
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("PASS", len(rows), "rows;", len(allstates), "states;", selected)


if __name__ == "__main__":
    verify()
