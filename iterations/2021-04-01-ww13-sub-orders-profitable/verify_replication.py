"""Independently verify the WW13 modified-mekko "profitable sub-orders" chart.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the order-grain profitability facts straight from the raw rows and
checks the native workbook contracts that carry the mekko solution chain.

Automated acceptance IDs:
  - ww13-order-grain-profitability
  - ww13-profitable-percentage
  - ww13-width-by-sales-share
  - ww13-stacked-height
  - ww13-sort-order
"""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww13-order-grain-profitability",
    "ww13-profitable-percentage",
    "ww13-width-by-sales-share",
    "ww13-stacked-height",
    "ww13-sort-order",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_03_31_WW13_Percentage_Sub_Orders_Profitable"
TABLE = TableName("Extract", "Extract")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute the order-grain profitability facts from the locked extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"

    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        query = lambda sql: connection.execute_list_query(sql)
        rows = query(f"SELECT COUNT(*) FROM {TABLE}")[0][0]
        assert rows == 9994, f"row count changed: {rows}"

        # Order-level, Sub-Category-level profitability: an order counts as
        # profitable for a Sub-Category when the SUM of that Sub-Category's
        # profit on the order is positive.
        profit = {
            (order, sub): Decimal(str(value))
            for order, sub, value in query(
                f'SELECT "Order ID", "Sub-Category", SUM("Profit") '
                f"FROM {TABLE} GROUP BY 1,2"
            )
        }
        orders = {order for order, _ in profit}
        assert len(orders) == 5009, "distinct order count changed"

        sales = {
            sub: Decimal(str(value))
            for sub, value in query(
                f'SELECT "Sub-Category", SUM("Sales") FROM {TABLE} GROUP BY 1'
            )
        }
        total_sales = sum(sales.values())

        per_sub = {}
        for (order, sub), value in profit.items():
            entry = per_sub.setdefault(sub, {"orders": 0, "profitable": 0, "sales": Decimal(0)})
            entry["orders"] += 1
            if value > 0:
                entry["profitable"] += 1
        for sub in per_sub:
            per_sub[sub]["sales"] = sales[sub]
            per_sub[sub]["profitable_pct"] = Decimal(per_sub[sub]["profitable"]) / Decimal(
                per_sub[sub]["orders"]
            )
            per_sub[sub]["sales_share"] = sales[sub] / total_sales

        # The order grain is what matters: averaging per raw row would give a
        # different percentage for most Sub-Categories.
        raw_profitable = {
            sub: Decimal(str(value))
            for sub, value in query(
                f'SELECT "Sub-Category", '
                f'SUM(CASE WHEN "Profit" > 0 THEN 1 ELSE 0 END)*1.0/COUNT(*) '
                f"FROM {TABLE} GROUP BY 1"
            )
        }

    assert len(per_sub) == 17, "Sub-Category domain changed"

    assert any(
        abs(per_sub[sub]["profitable_pct"] - raw_profitable[sub]) > Decimal("0.01")
        for sub in per_sub
    ), "order-grain profitability collapsed to the raw row grain"

    # Author order: the Sort key rounds the profitable percentage to two
    # decimals, then breaks ties on sales (both rendered as strings).
    def sort_key(sub):
        return (
            -round(per_sub[sub]["profitable_pct"], 2),
            -per_sub[sub]["sales"],
        )

    ordered = sorted(per_sub, key=sort_key)
    cumulative = Decimal(0)
    cumulative_by_sub = {}
    for sub in ordered:
        cumulative += per_sub[sub]["sales_share"]
        cumulative_by_sub[sub] = cumulative

    return {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "orders": len(orders),
        "subcategories": len(per_sub),
        "profitable_pct": {
            sub: float(per_sub[sub]["profitable_pct"]) for sub in ordered
        },
        "sales_share": {sub: float(per_sub[sub]["sales_share"]) for sub in ordered},
        "cumulative": {sub: float(value) for sub, value in cumulative_by_sub.items()},
        "order": ordered,
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        root = etree.fromstring(archive.read(name))
    return root


def datasource(root):
    return next(
        node
        for node in root.findall("datasources/datasource")
        if node.get("name") != "Parameters"
    )


def verify():
    facts = oracle()
    root = workbook()
    ds = datasource(root)

    formulas = {}
    internal = {}
    for column in ds.findall("column"):
        caption = column.get("caption") or column.get("name", "").strip("[]")
        internal[caption] = column.get("name")
        calculation = column.find("calculation")
        if calculation is not None:
            formulas[caption] = calculation.get("formula") or ""

    def local(name):
        return str(name).strip("[]")

    # --- ww13-order-grain-profitability ------------------------------------
    # The profitability flag is a FIXED LoD at the Order ID + Sub-Category
    # grain, testing the SUM of profit, not each product row.
    flag = formulas.get("Order Is Profitable", "")
    compact = flag.replace(" ", "").upper()
    assert "{FIXED[ORDERID],[SUB-CATEGORY]:SUM([PROFIT])}" in compact, (
        f"order-grain profitability LoD changed: {flag!r}"
    )
    assert "}>0" in compact and "IIF" in compact, (
        "profitability flag must test SUM(Profit) > 0"
    )
    assert "COUNTD([Order ID])" in formulas.get("Count Orders", ""), (
        "order count must be the distinct order count"
    )

    # --- ww13-profitable-percentage ----------------------------------------
    assert formulas.get("Profitable Orders", "").startswith("SUM("), (
        "Profitable Orders must sum the profitability flag"
    )
    assert "/" in formulas.get("Profitable Orders", ""), (
        "Profitable Orders must divide by the order count"
    )
    non_profitable = formulas.get("Non Profitable Orders", "")
    assert non_profitable.startswith("1 -") and local(internal["Profitable Orders"]) in non_profitable, (
        f"Non Profitable Orders must be 1 - Profitable Orders, got {non_profitable!r}"
    )
    assert "p0%" in etree.tostring(ds).decode(), "percentage format missing"

    # --- ww13-width-by-sales-share -----------------------------------------
    assert "TOTAL(SUM([Sales]))" in formulas.get("% of Total Sales", ""), (
        "% of Total Sales must divide by the table total"
    )
    assert "RUNNING_SUM(" in formulas.get("% Total Sales Cumulative", ""), (
        "% Total Sales Cumulative must be a running sum"
    )

    viz = root.find(".//worksheets/worksheet[@name='Viz']")
    assert viz is not None, "missing Viz worksheet"
    table = viz.find("table")
    rows = (table.findtext("rows") or "").strip()
    cols = (table.findtext("cols") or "").strip()
    assert local(internal["Profitable Orders"]) in rows, "Profitable Orders missing from rows"
    assert local(internal["Non Profitable Orders"]) in rows, (
        "Non Profitable Orders missing from rows"
    )
    assert local(internal["% Total Sales Cumulative"]) in cols, (
        "cumulative sales share must position the bars on the column axis"
    )
    assert local(internal["Sub-Category"]) not in rows and local(internal["Sub-Category"]) not in cols, (
        "Sub-Category must not sit on a shelf; the bars are positioned by the "
        "cumulative sales axis"
    )

    panes = table.findall("panes/pane")
    assert len(panes) == 2, f"expected two panes, found {len(panes)}"
    for pane in panes:
        assert pane.find("mark").get("class") == "Bar", "both panes must be bar marks"
        size = pane.find("encodings/size")
        assert size is not None, "each bar pane needs a size encoding"
        assert local(internal["% of Total Sales"]) in size.get("column"), (
            "bar width must be driven by % of Total Sales"
        )
        detail = pane.find("encodings/lod")
        assert detail is not None and local(internal["Sub-Category"]) in detail.get("column"), (
            "Sub-Category must be on the detail encoding"
        )
        color = pane.find("encodings/color")
        assert color is not None and ":Measure Names" in color.get("column"), (
            "colour must come from Measure Names"
        )

    # --- ww13-stacked-height ------------------------------------------------
    # The upper pane plots Profitable Orders on a normal axis; the lower pane
    # plots Non Profitable Orders on a reversed axis so the two heights stack
    # around the zero line.
    pane_axes = {pane.get("y-axis-name"): pane for pane in panes}
    assert any(
        local(internal["Profitable Orders"]) in (axis or "") for axis in pane_axes
    ), "upper pane must plot Profitable Orders"
    lower = next(
        (
            pane
            for pane in panes
            if local(internal["Non Profitable Orders"]) in (pane.get("y-axis-name") or "")
        ),
        None,
    )
    assert lower is not None, "lower pane must plot Non Profitable Orders"
    axis_rule = table.find("style/style-rule[@element='axis']")
    reverse = [
        encoding
        for encoding in axis_rule.findall("encoding")
        if encoding.get("reverse") == "true"
    ]
    assert any(
        local(internal["Non Profitable Orders"]) in (encoding.get("field") or "")
        for encoding in reverse
    ), "Non Profitable Orders axis must be reversed"

    # A constant zero reference line separates the two halves.
    reference = table.find(".//reference-line")
    assert reference is not None, "constant zero reference line missing"
    assert reference.get("formula") == "constant", "reference line must be a constant"

    # --- ww13-sort-order ----------------------------------------------------
    # Bars are sorted by the string Sort key descending; the key itself
    # combines the profitable percentage and the sales magnitude.
    sort_formula = formulas.get("Sort", "")
    assert local(internal["Profitable Orders"]) in sort_formula, (
        f"Sort key must use the profitable percentage: {sort_formula!r}"
    )
    assert "SUM([Sales])" in sort_formula, (
        f"Sort key must tie-break on sales: {sort_formula!r}"
    )
    assert 'STR(ROUND(' in sort_formula and '"-"' in sort_formula, (
        "Sort key must stringify both rounded parts so 800 sorts after 8000"
    )
    computed = table.find("view/computed-sort")
    assert computed is not None, "computed sort missing"
    assert computed.get("direction") == "DESC", "sort must be descending"
    assert local(internal["Sub-Category"]) in computed.get("column"), (
        "computed sort must address Sub-Category"
    )

    # The author filters to the three Segments; the export scope keeps them all.
    segment_filter = next(
        (
            f
            for f in table.findall("view/filter")
            if "Segment" in f.get("column", "")
        ),
        None,
    )
    assert segment_filter is not None, "Segment filter missing"

    # The dashboard hosts the single sheet.
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    assert any(
        zone.get("name") == "Viz" for zone in dashboard.findall(".//zones//zone")
    ), "dashboard does not host Viz"

    evidence = {
        "scope": "Locked-extract oracle plus native workbook contracts.",
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result["facts"], indent=2))
    print("PASS")
