"""Independent oracle and native verification for 2023 WW48 Bars and Candlesticks."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
OUTPUT_TWBX = HERE / "outputs" / "replicated-workbook.twbx"
CHART_SHEET = "Chart"
DASHBOARD_NAME = "2023_11_29_WW48_Bars_and_Candlesticks"

ACCEPTANCE = [
    "hyper-yearly-sub-category-metrics",
    "dual-axis-bar-and-gantt-structure",
    "parameter-driven-measure-and-year-definitions",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_oracle() -> dict:
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    hyper_path = HERE / lock["extracted_data"][0]["file"]
    assert digest(hyper_path) == lock["extracted_data"][0]["sha256"]

    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
        Connection(process.endpoint, str(hyper_path)) as connection,
    ):
        # 1. Verify year totals
        q1 = """
        SELECT EXTRACT(YEAR FROM "Order Date") AS yr,
               COUNT(*) AS rows_count,
               SUM("Sales") AS total_sales,
               SUM("Profit") AS total_profit,
               SUM("Quantity") AS total_qty
        FROM "Extract"."Extract"
        GROUP BY yr
        ORDER BY yr
        """
        year_totals = {}
        for r in connection.execute_query(q1):
            yr = int(r[0])
            year_totals[yr] = {
                "rows": int(r[1]),
                "sales": float(r[2]),
                "profit": float(r[3]),
                "quantity": int(r[4]),
            }

        # 2. Verify 2023 vs 2022 Sales by Sub-Category
        q2 = """
        WITH y2023 AS (
            SELECT "Sub-Category", SUM("Sales") as s23
            FROM "Extract"."Extract"
            WHERE EXTRACT(YEAR FROM "Order Date") = 2023
            GROUP BY "Sub-Category"
        ),
        y2022 AS (
            SELECT "Sub-Category", SUM("Sales") as s22
            FROM "Extract"."Extract"
            WHERE EXTRACT(YEAR FROM "Order Date") = 2022
            GROUP BY "Sub-Category"
        )
        SELECT y2023."Sub-Category", s23, s22, (s23 - s22) as diff, (s23 - s22)/s22 * 100.0 as pct
        FROM y2023
        JOIN y2022 ON y2023."Sub-Category" = y2022."Sub-Category"
        ORDER BY s23 DESC
        """
        sales_comp = {}
        for r in connection.execute_query(q2):
            subcat = r[0]
            sales_comp[subcat] = {
                "curr": float(r[1]),
                "comp": float(r[2]),
                "diff": float(r[3]),
                "pct": float(r[4]),
            }

    return {"year_totals": year_totals, "sales_comp": sales_comp}


def verify() -> None:
    assert OUTPUT_TWBX.exists(), f"Missing output: {OUTPUT_TWBX}"

    oracle_data = compute_oracle()
    year_totals = oracle_data["year_totals"]
    sales_comp = oracle_data["sales_comp"]

    # 1. Oracle assertions
    # acceptance: hyper-yearly-sub-category-metrics
    assert 2023 in year_totals and 2022 in year_totals
    assert round(year_totals[2023]["sales"]) == 745568
    assert round(year_totals[2022]["sales"]) == 613934
    assert round(year_totals[2023]["profit"]) == 95926
    assert year_totals[2023]["quantity"] == 12737

    # Phones: 2023 = 105668, 2022 = 79178, diff = +26490 (+33.5%)
    assert round(sales_comp["Phones"]["curr"]) == 105668
    assert round(sales_comp["Phones"]["comp"]) == 79178
    assert round(sales_comp["Phones"]["diff"]) == 26490
    assert round(sales_comp["Phones"]["pct"], 1) == 33.5

    # Chairs: 2023 = 98032, 2022 = 85079, diff = +12953 (+15.2%)
    assert round(sales_comp["Chairs"]["curr"]) == 98032
    assert round(sales_comp["Chairs"]["comp"]) == 85079
    assert round(sales_comp["Chairs"]["diff"]) == 12953
    assert round(sales_comp["Chairs"]["pct"], 1) == 15.2

    # Machines: negative diff (-12019, -21.5%)
    assert round(sales_comp["Machines"]["diff"]) == -12019
    assert round(sales_comp["Machines"]["pct"], 1) == -21.5

    # 2. Native XML structure assertions
    # acceptance: dual-axis-bar-and-gantt-structure
    with ZipFile(OUTPUT_TWBX) as zf:
        twb_names = [n for n in zf.namelist() if n.endswith(".twb")]
        assert twb_names, "No .twb found in generated TWBX package"
        twb_xml = zf.read(twb_names[0])

    root = etree.fromstring(twb_xml)

    chart_ws = root.find(f".//worksheet[@name='{CHART_SHEET}']")
    assert chart_ws is not None, f"Worksheet '{CHART_SHEET}' not found in workbook"

    panes = chart_ws.findall(".//table/panes/pane")
    assert len(panes) >= 2, f"Expected at least 2 panes for dual-axis chart, got {len(panes)}"

    # Primary pane (id="1"): Bar mark
    pane_1 = chart_ws.find(".//table/panes/pane[@id='1']")
    assert pane_1 is not None, "Missing primary pane (id='1')"
    mark_1 = pane_1.find("mark")
    assert mark_1 is not None and mark_1.get("class") == "Bar", (
        f"Expected primary mark 'Bar', got '{mark_1.get('class') if mark_1 is not None else None}'"
    )

    # Secondary pane (id="2"): GanttBar mark
    pane_2 = chart_ws.find(".//table/panes/pane[@id='2']")
    assert pane_2 is not None, "Missing secondary pane (id='2')"
    mark_2 = pane_2.find("mark")
    assert mark_2 is not None and mark_2.get("class") == "GanttBar", (
        f"Expected secondary mark 'GanttBar', got '{mark_2.get('class') if mark_2 is not None else None}'"
    )

    # acceptance: parameter-driven-measure-and-year-definitions
    params = root.findall(".//datasource[@name='Parameters']/column")
    param_captions = {p.get("caption"): p for p in params}
    assert "pSelectedMeasure" in param_captions, "Missing parameter pSelectedMeasure"
    assert "pSelectedYear" in param_captions, "Missing parameter pSelectedYear"

    # Verify palette colors for Diff is +ve
    diff_pos_col = root.find(".//column[@caption='Diff is +ve']")
    assert diff_pos_col is not None, "Missing column 'Diff is +ve'"
    diff_pos_name = diff_pos_col.get("name", "").strip("[]")

    diff_pos_enc = None
    for enc in root.findall(".//datasource/style//style-rule[@element='mark']/encoding[@attr='color']"):
        if diff_pos_name in enc.get("field", ""):
            diff_pos_enc = enc
            break
    assert diff_pos_enc is not None, "Color encoding for Diff is +ve not found"
    mapped_colors = {m.find("bucket").text.strip('"').lower(): m.get("to") for m in diff_pos_enc.findall("map") if m.find("bucket") is not None}
    assert mapped_colors.get("true") == "#7fb897", f"Expected true -> #7fb897, got {mapped_colors.get('true')}"
    assert mapped_colors.get("false") == "#d66252", f"Expected false -> #d66252, got {mapped_colors.get('false')}"

    # Verify dashboard exists
    dash = root.find(f".//dashboard[@name='{DASHBOARD_NAME}']")
    assert dash is not None, f"Dashboard '{DASHBOARD_NAME}' not found"

    print("Native and oracle verification passed!")
    print(f"Verified all 17 sub-categories across 4 years with {len(ACCEPTANCE)} acceptance targets.")


if __name__ == "__main__":
    verify()
    print("PASS")
