"""Locked-data oracle plus packaged-workbook acceptance checks for 2021 WW10.

The oracle is derived only from the locked Hyper extract and independently
recomputed with SQL. Structural checks read the built TWBX and never open the
author workbook or import the builder.

Run ``--write-oracle`` only to deliberately refresh the fixture.
"""

import argparse
import hashlib
import json
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/replicated-workbook.twbx"
FIXTURE = HERE / "outputs/data-oracle.json"
REPORT = HERE / "outputs/independent-verification.json"
TOTAL_ORDERS = 5009
TOTAL_ROWS = 9994
USER_NS = "{http://www.tableausoftware.com/xml/user}"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_text(value):
    return format(value, "f")


def ratio(numerator, denominator):
    if not denominator:
        return None
    with localcontext() as context:
        context.prec = 40
        return decimal_text(Decimal(numerator) / Decimal(denominator))


def sql_string(value):
    return "'" + value.replace("'", "''") + "'"


def oracle():
    """Recompute every declared expectation from the locked extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = next(
        entry for entry in lock["extracted_data"] if entry["file"].endswith(".hyper")
    )
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "Locked Hyper input hash changed"
    with (
        HyperProcess(
            Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
            parameters={"log_dir": tempfile.gettempdir()},
        ) as process,
        Connection(process.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Order ID", "Customer Name", "Product Name", "Sales", "Quantity" '
            'FROM "Extract"."Extract"'
        )
        assert len(rows) == TOTAL_ROWS, f"Unexpected input row count: {len(rows)}"
        orders = defaultdict(list)
        products = defaultdict(set)
        for order, customer, product, sales, quantity in rows:
            assert all(
                value is not None
                for value in (order, customer, product, sales, quantity)
            )
            orders[order].append((customer, product, Decimal(str(sales)), quantity))
            products[product].add(order)
        assert len(orders) == TOTAL_ORDERS, "Declared total-order expectation changed"

        cooccurrences = Counter()
        for lines in orders.values():
            cooccurrences.update(combinations(sorted({line[1] for line in lines}), 2))
        ranked = sorted(cooccurrences, key=lambda pair: (-cooccurrences[pair], pair))
        pairs = ranked[:3]
        pairs.append(
            next(
                pair
                for pair in combinations(sorted(products), 2)
                if not products[pair[0]] & products[pair[1]]
            )
        )

        fixtures = []
        for first, second in pairs:
            qualifying = sorted(products[first] & products[second])
            sql = (
                'SELECT COUNT(*) FROM (SELECT "Order ID" FROM "Extract"."Extract" '
                'GROUP BY "Order ID" HAVING '
                f'MAX(CASE WHEN "Product Name"={sql_string(first)} THEN 1 ELSE 0 END)=1 AND '
                f'MAX(CASE WHEN "Product Name"={sql_string(second)} THEN 1 ELSE 0 END)=1) q'
            )
            assert connection.execute_scalar_query(sql) == len(qualifying)
            results = []
            for order in qualifying:
                lines = orders[order]
                customers = {line[0] for line in lines}
                assert len(customers) == 1, (order, customers)
                results.append(
                    {
                        "order_id": order,
                        "customer_name": next(iter(customers)),
                        "sales": decimal_text(
                            sum((line[2] for line in lines), Decimal(0))
                        ),
                        "quantity": sum(line[3] for line in lines),
                        "line_count": len(lines),
                        "other_product_line_count": sum(
                            line[1] not in {first, second} for line in lines
                        ),
                    }
                )
            sales = sum((Decimal(order["sales"]) for order in results), Decimal(0))
            quantity = sum(order["quantity"] for order in results)
            fixtures.append(
                {
                    "product1": first,
                    "product2": second,
                    "first_stage_order_count": len(products[first]),
                    "qualifying_order_count": len(qualifying),
                    "orders": results,
                    "sample_orders": results[:3],
                    "bans": {
                        "#ORDERS": len(qualifying),
                        "Total Orders": TOTAL_ORDERS,
                        "% OF TOTAL ORDERS": ratio(len(qualifying), TOTAL_ORDERS),
                        "AVG ORDER AMOUNT": ratio(sales, len(qualifying)),
                        "AVG ORDER QUANTITY": ratio(quantity, len(qualifying)),
                    },
                    "qualifying_order_lines_sales": decimal_text(sales),
                    "qualifying_order_lines_quantity": quantity,
                    "qualifying_order_line_count": sum(
                        order["line_count"] for order in results
                    ),
                }
            )

    # acceptance: order-level-totals -- qualifying orders must span product lines
    # that are not the two selected products, otherwise "all lines" is untested.
    assert all(pair["qualifying_order_count"] >= 2 for pair in fixtures[:3])
    assert all(
        any(order["other_product_line_count"] for order in pair["orders"])
        for pair in fixtures[:3]
    )
    assert fixtures[-1]["qualifying_order_count"] == 0
    total_sales = sum(
        (line[2] for lines in orders.values() for line in lines), Decimal(0)
    )
    total_quantity = sum(line[3] for lines in orders.values() for line in lines)
    return {
        "schema_version": 1,
        "input": item["file"],
        "input_sha256": item["sha256"],
        "raw_row_count": len(rows),
        "total_orders": len(orders),
        "total_sales": decimal_text(total_sales),
        "total_quantity": total_quantity,
        "semantics": "Intersection of order memberships; totals include ALL lines of qualifying orders.",
        "numeric_encoding": (
            "Sales are exact sums of Decimal(str(Hyper Sales)); decimal strings avoid JSON "
            "rounding. Ratios use 40 significant digits; numerator totals and denominators "
            "are included. Empty-result averages are null."
        ),
        "pair_selection": "Three most frequent distinct-product pairs (lexical tie break), then first lexical zero-overlap pair.",
        "pairs": fixtures,
    }


def structural(root, data):
    checks = []

    def check(name, condition, evidence):
        checks.append(
            {
                "check": name,
                "status": "PASS" if condition else "FAIL",
                "evidence": evidence,
            }
        )

    sources = root.findall("datasources/datasource")
    assert len(sources) == 1, "Expected exactly one datasource"
    source = sources[0]
    fields = {
        node.get("caption", node.get("name")): node for node in source.findall("column")
    }
    flags = []
    for stage, name in enumerate(("1st Products", "2nd Product"), start=1):
        groups = source.findall(f'group[@name="[{name}]"]')
        # acceptance: must-include-first-stage, must-include-second-stage
        # The author sets use Tableau's "Use All" condition so the default state
        # keeps every order.
        check(
            f"stage-{stage}-use-all-set",
            len(groups) == 1
            and groups[0].get(f"{USER_NS}ui-builder") == "filter-group"
            and groups[0][0].get("function") == "level-members"
            and groups[0][0].get(f"{USER_NS}ui-enumeration") == "all",
            f"count={len(groups)}; "
            + " ".join(
                etree.tostring(node, encoding="unicode")[:200] for node in groups
            ),
        )
        expected = f"{{FIXED [Order ID]: MAX([{name}])}}"
        columns = [
            node
            for node in source.findall("column")
            if node.find("calculation") is not None
            and node.find("calculation").get("formula") == expected
        ]
        check(
            f"stage-{stage}-boolean-fixed-flag",
            len(columns) == 1 and columns[0].get("datatype") == "boolean",
            expected,
        )
        assert len(columns) == 1, f"Missing or ambiguous flag: {expected}"
        flags.append(columns[0].get("name").strip("[]"))

    # acceptance: must-include-first-stage, must-include-second-stage
    # Native setMembership controls bound to the two PRODUCT sets.
    zones = root.xpath("dashboards/dashboard//zone[@type-v2='setMembership']")
    for stage, name in enumerate(("1st Products", "2nd Product"), start=1):
        controls = [
            node for node in zones if node.get("param", "").endswith(f"[{name}]")
        ]
        check(
            f"stage-{stage}-set-control",
            len(controls) == 1 and controls[0].get("type-v2") == "setMembership",
            repr([dict(node.attrib) for node in controls]),
        )

    for sheet_name in ("Bars", "Order Detail", "BANs"):
        sheet = root.find(f'worksheets/worksheet[@name="{sheet_name}"]')
        assert sheet is not None, f"Missing {sheet_name}"
        filters = sheet.findall("table/view/filter")
        # acceptance: must-include-first-stage, must-include-second-stage
        # Stage 1 is context on Bars/Order Detail so stage 2 evaluates inside the
        # already-qualifying orders. BANs keeps stage 1 out of context so the
        # {FIXED:COUNTD} denominator stays global.
        stage1_context = sheet_name != "BANs"
        for stage, flag in enumerate(flags, start=1):
            matched = [
                node
                for node in filters
                if f"[none:{flag}:nk]" in node.get("column", "")
            ]
            check(
                f"{sheet_name}-stage-{stage}-filter",
                len(matched) == 1
                and matched[0].xpath("groupfilter/@member") == ["true"]
                and (
                    matched[0].get("context") == "true"
                    if stage == 1 and stage1_context
                    else "context" not in matched[0].attrib
                ),
                " ".join(etree.tostring(node, encoding="unicode") for node in matched),
            )
        # acceptance: order-level-totals -- only order-level flags filter the
        # sheet; no line-level product filter is allowed to shrink the totals.
        allowed = {f"[{source.get('name')}].[none:{flag}:nk]" for flag in flags}
        if sheet_name == "Order Detail":
            allowed.add(f"[{source.get('name')}].[Tooltip (Customer Name,Order ID)]")
        check(
            f"{sheet_name}-preserves-all-order-lines",
            all(
                node.get("column") in allowed
                or "Measure Names" in node.get("column", "")
                for node in filters
            )
            and sheet.find("table/view/aggregation").get("value") == "true",
            "filters=" + repr([node.get("column") for node in filters]),
        )

    bars = root.find('worksheets/worksheet[@name="Bars"]')
    tooltip_text = "".join(
        bars.xpath("table/panes/pane/customized-tooltip//run/text()")
    )
    # acceptance: order-level-totals
    check(
        "Bars-order-grain-and-tooltip-sums",
        "[none:Order ID:nk]" in bars.findtext("table/rows", "")
        and all(f"[sum:{field}:qk]" in tooltip_text for field in ("Sales", "Quantity")),
        "rows=" + bars.findtext("table/rows", "") + "; tooltip=" + tooltip_text,
    )
    shelves = bars.findtext("table/rows", "") + " " + bars.findtext("table/cols", "")
    # acceptance: order-level-totals -- Sales and Quantity must be bound on the
    # shelves so the two numeric axes exist.
    check(
        "Bars-numeric-measure-axis",
        "[sum:Sales:qk]" in shelves and "[sum:Quantity:qk]" in shelves,
        "rows/cols=" + shelves,
    )

    def formula(caption):
        return fields[caption].find("calculation").get("formula")

    orders_field = fields["# ORDERS"].get("name")
    total_field = fields["Total Orders"].get("name")
    expected = {
        "# ORDERS": "COUNTD([Order ID])",
        "AVG ORDER AMOUNT": f"SUM([Sales])/{orders_field}",
        "AVG ORDER QUANTITY": f"SUM([Quantity])/{orders_field}",
    }
    for caption, wanted in expected.items():
        # acceptance: bans-metrics
        check(
            caption,
            "".join(formula(caption).split()) == "".join(wanted.split()),
            formula(caption),
        )
    # acceptance: bans-metrics -- the denominator stays the unfiltered order
    # count because stage 1 is not a context filter on BANs.
    check(
        "Total Orders-global-denominator",
        "".join(formula("Total Orders").split()) == "{FIXED:COUNTD([OrderID])}",
        f"formula={formula('Total Orders')}; locked total={TOTAL_ORDERS}",
    )
    check(
        "percentage-single-global-denominator",
        "".join(formula("% OF TOTAL ORDERS").split())
        == f"{orders_field}/SUM({total_field})",
        formula("% OF TOTAL ORDERS"),
    )
    ban_members = root.xpath(
        'worksheets/worksheet[@name="BANs"]/table/view/filter[contains(@column,"Measure Names")]//@member'
    )
    # acceptance: bans-metrics
    check(
        "BANs-four-visible-metrics",
        len(ban_members) == 4
        and all(
            any(
                f"[usr:{fields[caption].get('name').strip('[]')}:qk]" in member
                for member in ban_members
            )
            for caption in (*expected, "% OF TOTAL ORDERS")
        ),
        repr(ban_members),
    )

    runs = bars.xpath("table/panes/pane/customized-tooltip/formatted-text/run/text()")
    tooltip_runs = [run for run in runs if '<Sheet name="Order Detail"' in run]
    # acceptance: order-detail-tooltip
    check(
        "Bars-viz-in-tooltip",
        len(tooltip_runs) == 1
        and all(
            f"[none:{field}:nk]" in tooltip_runs[0]
            for field in ("Order ID", "Customer Name")
        ),
        " ".join(tooltip_runs),
    )
    detail = root.find('worksheets/worksheet[@name="Order Detail"]')
    # acceptance: order-detail-tooltip
    check(
        "Order Detail-product-grain",
        all(
            f"[none:{field}:nk]" in detail.findtext("table/rows", "")
            for field in ("Customer Name", "Order ID", "Product Name")
        ),
        detail.findtext("table/rows", ""),
    )
    # acceptance: order-detail-tooltip -- the source sheet must not appear as a
    # dashboard tile; it is hidden and registered in the viz-in-tooltip manifest.
    detail_window = root.xpath(
        'windows/window[@class="worksheet"][@name="Order Detail"]'
    )
    manifest = root.find("document-format-change-manifest/VizInTooltipHideWorksheet")
    check(
        "Order Detail-hidden-dashboard-viewpoint",
        len(detail_window) == 1
        and detail_window[0].get("hidden") == "true"
        and manifest is not None,
        f"hidden={detail_window[0].get('hidden') if detail_window else None}; "
        f"manifest={'present' if manifest is not None else 'missing'}",
    )
    return checks


def cloud_consistency(data):
    """Compare the captured default-state BANs CSV with the locked-data oracle.

    The REST CSV export returns raw unformatted measure values, so this proves
    the data response; display formatting is reviewed separately in the image.
    """
    path = HERE / "outputs/cloud-replica-bans.csv"
    if not path.is_file():
        return None
    rows = dict(
        line.split(",", 1)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if "," in line
    )

    def number(text):
        return float(text.strip().strip('"').replace(",", "").replace("$", ""))

    observed = {
        "# ORDERS": number(rows["# ORDERS"]),
        "% OF TOTAL ORDERS": number(rows["% OF TOTAL ORDERS"]),
        "AVG ORDER AMOUNT": number(rows["AVG ORDER AMOUNT"]),
        "AVG ORDER QUANTITY": number(rows["AVG ORDER QUANTITY"]),
    }
    total = data["total_orders"]
    expected = {
        "# ORDERS": float(total),
        "% OF TOTAL ORDERS": 1.0,
        "AVG ORDER AMOUNT": float(Decimal(data["total_sales"]) / total),
        "AVG ORDER QUANTITY": data["total_quantity"] / total,
    }
    return {
        "path": path.relative_to(HERE).as_posix(),
        "sha256": digest(path),
        "observed_raw_csv": observed,
        "expected_from_locked_data": expected,
        "display_formatted_png_values": {
            "# ORDERS": "5,009",
            "% OF TOTAL ORDERS": "100.0%",
            "AVG ORDER AMOUNT": "$459",
            "AVG ORDER QUANTITY": "8",
        },
        "consistent": all(
            abs(observed[key] - expected[key]) < 1e-6 for key in expected
        ),
    }


def verify(write_oracle=False):
    data = oracle()
    if write_oracle:
        FIXTURE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print("WROTE data-oracle.json")
        return
    # acceptance: order-level-totals, bans-metrics -- recompute all fixtures.
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == data, (
        "Oracle expectations disagree with locked data"
    )
    assert OUTPUT.exists(), f"Missing output: {OUTPUT}"
    TWBEditor.open_existing(OUTPUT)  # Public API smoke check; XML is parsed below.
    with ZipFile(OUTPUT) as archive:
        names = [name for name in archive.namelist() if name.endswith(".twb")]
        assert len(names) == 1, "Expected one packaged TWB"
        root = etree.fromstring(archive.read(names[0]))
        extracts = [name for name in archive.namelist() if name.endswith(".hyper")]
        assert len(extracts) == 1, "Expected one packaged extract"
        assert (
            hashlib.sha256(archive.read(extracts[0])).hexdigest()
            == data["input_sha256"]
        ), "Packaged extract differs from locked input"

    checks = structural(root, data)
    cloud = cloud_consistency(data)
    if cloud is not None:
        checks.append(
            {
                "check": "cloud-default-state-bans",
                "status": "PASS" if cloud["consistent"] else "FAIL",
                "evidence": json.dumps(cloud, ensure_ascii=False),
            }
        )
    report = {
        "artifact_sha256": digest(OUTPUT),
        "scope": (
            "Independent static XML checks, locked-data oracle and captured "
            "default-state Cloud BANs; no browser interaction executed."
        ),
        "checks": checks,
        "oracle_pair_counts": [
            {
                key: pair[key]
                for key in ("product1", "product2", "qualifying_order_count")
            }
            for pair in data["pairs"]
        ],
        "cloud_default_state": cloud,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for check in checks:
        print(f"{check['status']} {check['check']}: {check['evidence']}")
    failures = [check for check in checks if check["status"] == "FAIL"]
    # acceptance: must-include-first-stage -- set, flag, context and control checks.
    # acceptance: must-include-second-stage -- set, flag and ordinary filter checks.
    # acceptance: order-level-totals -- order grain, sums and numeric axis checks.
    # acceptance: bans-metrics -- counts, averages, denominator and Cloud default checks.
    # acceptance: order-detail-tooltip -- embedded sheet, key filters and hiding.
    assert not failures, "Acceptance failures:\n" + "\n".join(
        f"{check['check']}: {check['evidence']}" for check in failures
    )
    print("PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-oracle", action="store_true")
    verify(parser.parse_args().write_oracle)
