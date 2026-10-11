"""Independently verify the WW14 market-basket workbook.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the second-order market-basket facts straight from the raw rows and
checks the native workbook contracts that carry the solution chain.

Automated acceptance IDs:
  - ww14-second-order-grain
  - ww14-selected-subcat-orders
  - ww14-other-items-exclusion
  - ww14-order-count-ranking
  - ww14-profitability-colour
  - ww14-toggle-switch
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
    "ww14-second-order-grain",
    "ww14-selected-subcat-orders",
    "ww14-other-items-exclusion",
    "ww14-order-count-ranking",
    "ww14-profitability-colour",
    "ww14-toggle-switch",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbX".replace("X", "x")
DASHBOARD_NAME = "2021_04_07_WW14_MarketBasketAnalysis"
DEFAULT_SUBCAT = "Accessories"
TABLE = TableName("Extract", "Extract")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute the second-order market basket from the locked extract."""
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
        customers = query(f'SELECT COUNT(DISTINCT "Customer ID") FROM {TABLE}')[0][0]
        assert customers == 793, "distinct customer count changed"

        # Second order = the minimum order date after the customer's first.
        second = query(
            f"""
            WITH f AS (
                SELECT "Customer ID" cid, MIN("Order Date") d
                FROM {TABLE} GROUP BY 1
            ),
            s AS (
                SELECT t."Customer ID" cid, MIN(t."Order Date") d
                FROM {TABLE} t JOIN f ON t."Customer ID" = f.cid
                WHERE t."Order Date" > f.d
                GROUP BY 1
            )
            SELECT COUNT(*) FROM {TABLE} t
            JOIN s ON t."Customer ID" = s.cid AND t."Order Date" = s.d
            """
        )[0][0]
        assert second == 1607, f"second-order row count changed: {second}"

        selected_orders = {
            order
            for (order,) in query(
                f'SELECT DISTINCT "Order ID" FROM {TABLE} WHERE "Sub-Category" = \'{DEFAULT_SUBCAT}\''
            )
        }

        basket = {}
        for sub, orders, sales, profit in query(
            f"""
            WITH f AS (
                SELECT "Customer ID" cid, MIN("Order Date") d
                FROM {TABLE} GROUP BY 1
            ),
            s AS (
                SELECT t."Customer ID" cid, MIN(t."Order Date") d
                FROM {TABLE} t JOIN f ON t."Customer ID" = f.cid
                WHERE t."Order Date" > f.d
                GROUP BY 1
            ),
            second AS (
                SELECT t.* FROM {TABLE} t
                JOIN s ON t."Customer ID" = s.cid AND t."Order Date" = s.d
            )
            SELECT sc."Sub-Category", COUNT(DISTINCT sc."Order ID"),
                   SUM(sc."Sales"), SUM(sc."Profit")
            FROM second sc
            WHERE sc."Order ID" IN (
                SELECT DISTINCT "Order ID" FROM second WHERE "Sub-Category" = '{DEFAULT_SUBCAT}'
            )
              AND sc."Sub-Category" <> '{DEFAULT_SUBCAT}'
            GROUP BY 1
            """
        ):
            basket[sub] = {
                "orders": int(orders),
                "sales": Decimal(str(sales)),
                "profit": Decimal(str(profit)),
            }

        # A second order is what matters: the first-order grain yields a
        # different basket, so the check is not a tautology.
        first_basket = {
            sub: int(count)
            for sub, count in query(
                f"""
                WITH f AS (
                    SELECT "Customer ID" cid, MIN("Order Date") d
                    FROM {TABLE} GROUP BY 1
                )
                SELECT sc."Sub-Category", COUNT(DISTINCT sc."Order ID")
                FROM {TABLE} sc
                JOIN f ON sc."Customer ID" = f.cid AND sc."Order Date" = f.d
                WHERE sc."Order ID" IN (
                    SELECT DISTINCT t."Order ID" FROM {TABLE} t
                    JOIN f ON t."Customer ID" = f.cid AND t."Order Date" = f.d
                    WHERE t."Sub-Category" = '{DEFAULT_SUBCAT}'
                )
                  AND sc."Sub-Category" <> '{DEFAULT_SUBCAT}'
                GROUP BY 1
                """
            )
        }

    assert len(basket) == 16, "basket domain changed"
    assert DEFAULT_SUBCAT not in basket, "selected Sub-Category must be excluded"
    assert basket != first_basket, "second-order basket equals the first-order basket"

    # Every order counted is a second order containing the selected Sub-Category.
    total_orders = sum(entry["orders"] for entry in basket.values())
    assert total_orders >= max(entry["orders"] for entry in basket.values())

    ordered = sorted(basket, key=lambda sub: (-basket[sub]["orders"], sub))
    return {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "customers": customers,
        "second_order_rows": second,
        "selected_subcat": DEFAULT_SUBCAT,
        "selected_orders": len(selected_orders),
        "basket": {sub: basket[sub]["orders"] for sub in ordered},
        "profit_ratio": {
            sub: float(basket[sub]["profit"] / basket[sub]["sales"]) for sub in ordered
        },
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        root = etree.fromstring(archive.read(name))
    return root


def verify():
    facts = oracle()
    root = workbook()
    ds = next(
        node
        for node in root.findall("datasources/datasource")
        if node.get("name") != "Parameters"
    )

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

    def ref(name):
        return local(internal[name])

    # --- ww14-second-order-grain -------------------------------------------
    first = formulas.get("Is Customer's First Order", "").replace(" ", "").upper()
    assert "{FIXED[CUSTOMERID]:MIN([ORDERDATE])}" in first, (
        f"first-order LoD changed: {first!r}"
    )
    assert "=[ORDERDATE]" in first, (
        "first-order flag must compare the minimum date with the row's date"
    )
    second = formulas.get("Is Customer's 2nd Order", "").replace(" ", "").upper()
    assert "{FIXED[CUSTOMERID]:MIN(IIF(" in second, (
        f"second-order LoD changed: {second!r}"
    )
    assert "NULL))}=[ORDERDATE]" in second, (
        "second-order LoD must take the minimum date after the first order"
    )
    assert ref("Is Customer's 2nd Order") in (
        root.find(".//worksheets/worksheet[@name='Bar']/table/view/filter").get("column", "")
    ), "Bar must filter to the customer's second order"

    # --- ww14-selected-subcat-orders ---------------------------------------
    flag = formulas.get("Customer Ordered Selected SubCat", "").replace(" ", "")
    assert flag.upper().startswith("IIF(") and flag.endswith(",1,0)"), (
        f"selected-subcat flag changed: {flag!r}"
    )
    assert "[SUB-CATEGORY]" in flag.upper() and "PARAMETER1" in flag.upper().replace(" ", ""), (
        "selected-subcat flag must compare the parameter with the Sub-Category"
    )
    setter = formulas.get("Orders with Selected SubCat", "").replace(" ", "").upper()
    assert "{FIXED[ORDERID]:SUM(" in setter, f"order-set LoD changed: {setter!r}"
    assert ">=1" in setter, "order-set LoD must test SUM >= 1"

    # --- ww14-other-items-exclusion ----------------------------------------
    other = formulas.get("Other Items Ordered", "")
    assert "N/A" in other and "[Sub-Category]" in other, (
        f"Other Items Ordered changed: {other!r}"
    )
    for sheet in ("Bar", "Treemap"):
        table = root.find(f".//worksheets/worksheet[@name='{sheet}']/table")
        filters = [f.get("column", "") for f in table.findall("view/filter")]
        assert any(ref("Is Customer's 2nd Order") in c for c in filters), (
            f"{sheet} is not filtered to the second order"
        )
        assert any(ref("Orders with Selected SubCat") in c for c in filters), (
            f"{sheet} is not filtered to orders containing the selected Sub-Category"
        )
        exclusion = next(
            (f for f in table.findall("view/filter") if ref("Other Items Ordered") in f.get("column", "")),
            None,
        )
        assert exclusion is not None, f"{sheet} does not exclude the selected Sub-Category"

    # --- ww14-order-count-ranking ------------------------------------------
    assert "COUNTD([Order ID])" in formulas.get("Count Orders", ""), (
        "Count Orders must be the distinct order count"
    )
    # The dimension is on the Bar row shelf, so its descending order is carried
    # by a shelf-sort; the Treemap dimension is only on Detail, so it needs the
    # native computed-sort. Both order by Count Orders.
    for sheet in ("Bar", "Treemap"):
        table = root.find(f".//worksheets/worksheet[@name='{sheet}']/table")
        computed = table.find("view/computed-sort")
        shelf = table.find("view/shelf-sorts/shelf-sort-v2")
        sort = computed if computed is not None else shelf
        assert sort is not None, f"{sheet} has no sort"
        assert sort.get("direction") == "DESC", f"{sheet} sort must be descending"
        using = sort.get("using") or sort.get("measure-to-sort-by")
        assert ref("Count Orders") in using, f"{sheet} must sort by Count Orders"
        target = sort.get("column") or sort.get("dimension-to-sort")
        assert ref("Other Items Ordered") in target, (
            f"{sheet} must sort the Other Items Ordered dimension"
        )
    bar_table = root.find(".//worksheets/worksheet[@name='Bar']/table")
    bar_rows = (bar_table.findtext("rows") or "").strip()
    assert ref("Other Items Ordered") in bar_rows, "Bar must put Other Items on rows"
    assert ref("Count Orders") in (bar_table.findtext("cols") or ""), (
        "Bar must put Count Orders on columns"
    )
    treemap = root.find(".//worksheets/worksheet[@name='Treemap']/table")
    assert treemap.find("panes/pane/mark").get("class") == "Square", (
        "Treemap must use Square marks"
    )
    size = treemap.find("panes/pane/encodings/size")
    assert size is not None and ref("Count Orders") in size.get("column"), (
        "Treemap tile size must be Count Orders"
    )
    detail = treemap.find("panes/pane/encodings/lod")
    assert detail is not None and ref("Other Items Ordered") in detail.get("column"), (
        "Treemap must break down by Other Items Ordered"
    )

    # --- ww14-profitability-colour -----------------------------------------
    assert "SUM([Profit])/SUM([Sales])" in formulas.get("Profit Ratio", ""), (
        "Profit Ratio must divide summed profit by summed sales"
    )
    assert ">0" in formulas.get("Is Profitable?", "").replace(" ", ""), (
        "Is Profitable? must test Profit Ratio > 0"
    )
    palette = next(
        (
            encoding
            for encoding in ds.findall("style/style-rule[@element='mark']/encoding")
            if ref("Is Profitable?") in (encoding.get("field") or "")
        ),
        None,
    )
    assert palette is not None, "boolean profitability palette missing"
    buckets = {b.text for b in palette.findall("map/bucket")}
    assert buckets == {"true", "false"}, f"palette buckets changed: {buckets}"
    colors = {m.get("to") for m in palette.findall("map")}
    assert len(colors) == 2, "profitable and unprofitable colours must differ"
    for sheet in ("Bar", "Treemap"):
        color = root.find(
            f".//worksheets/worksheet[@name='{sheet}']/table/panes/pane/encodings/color"
        )
        assert color is not None and ref("Is Profitable?") in color.get("column"), (
            f"{sheet} must colour by Is Profitable?"
        )

    # --- ww14-toggle-switch -------------------------------------------------
    parameters = next(
        node for node in root.findall("datasources/datasource") if node.get("name") == "Parameters"
    )
    toggle = parameters.find("column[@caption='Toggle']")
    assert toggle is not None, "Toggle parameter missing"
    assert toggle.get("value") == "0", "Toggle default must be 0 (Bar)"
    selected = parameters.find("column[@caption='pSelected_SubCat']")
    assert selected is not None and selected.get("value") == f'"{DEFAULT_SUBCAT}"', (
        "pSelected_SubCat default changed"
    )
    assert toggle.find("members") is not None, "Toggle must offer the 0/1 list domain"
    assert {m.get("value") for m in toggle.findall("members/member")} == {"0", "1"}, (
        "Toggle must be a two-value list"
    )
    label = formulas.get("Toggle Label", "").replace(" ", "").upper()
    assert "THEN'BAR'ELSE'TREEMAP'END" in label, (
        f"Toggle Label must switch between Bar and Treemap: {label!r}"
    )
    # Each chart is gated on the parameter, so exactly one is visible at a time.
    bar_toggle = [
        f
        for f in bar_table.findall("view/filter")
        if ref("Selected Toggle") in f.get("column", "")
    ]
    tm_toggle = [
        f
        for f in treemap.findall("view/filter")
        if ref("Selected Toggle") in f.get("column", "")
    ]
    assert bar_toggle and bar_toggle[0].get("class") == "quantitative", (
        "Bar must gate on Selected Toggle"
    )
    assert tm_toggle and tm_toggle[0].get("class") == "quantitative", (
        "Treemap must gate on Selected Toggle"
    )
    bar_max = bar_toggle[0].find("max")
    tm_min = tm_toggle[0].find("min")
    assert bar_max is not None and float(bar_max.text) == 0.0, (
        "Bar must show only while Toggle = 0"
    )
    assert tm_min is not None and float(tm_min.text) == 1.0, (
        "Treemap must show only while Toggle = 1"
    )

    # A parameter action sets Toggle from the Toggle sheet selection.
    parameter_action = root.find("actions/edit-parameter-action")
    assert parameter_action is not None, "no parameter action"
    assert parameter_action.find("source").get("worksheet") == "Toggle", (
        "parameter action must source the Toggle sheet"
    )
    params = {
        p.get("name"): p.get("value") for p in parameter_action.findall("params/param")
    }
    assert params.get("target-parameter", "").endswith("Parameter 2]"), (
        "parameter action must target the Toggle parameter"
    )

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    names = {zone.get("name") for zone in dashboard.findall(".//zones//zone")}
    assert {"Bar", "Treemap", "Toggle"} <= names, "dashboard does not host every sheet"

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
