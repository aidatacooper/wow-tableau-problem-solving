"""WW33 Table Formatting — cwtwb SDK Version

Recreates the 2019-08-14 WW33 Tableau workbook completely via cwtwb SDK.
"""
from __future__ import annotations

import json
from pathlib import Path

# ── Path resolution ──────────────────────────────────────────────────
ITERATION_DIR = Path(__file__).resolve().parent
from cwtwb import TableColumn, TWBEditor  # noqa: E402

INPUT_HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD_NAME = "WW33 Table Formatting"

# ── Formatting Constants ─────────────────────────────────────────────
CURRENCY_FMT = 'c"$"#,##0;-"$"#,##0'
INT_FMT = "n#,##0;-#,##0"
PCT_FMT = "p0%"

# ── Internal Field Names ─────────────────────────────────────────────
N_PARAM = "[Parameter 1]"
N_PARAM_REGION = "[Parameter 2]"
N_PROFIT_RATIO = "[Calculation_ProfitRatio]"
N_TOTAL_YC = "[Calculation_TotalSalesYearCat]"
N_PCT_SEL = "[Calculation_PctSelectedRegion]"
N_PCT_OTHER = "[Calculation_PctAllOthers]"
N_HIGHLIGHT = "[Calculation_Highlight]"

N_SUBCAT_B = "[Calculation_LabelSubcatBold]"
N_SUBCAT_N = "[Calculation_LabelSubcatNormal]"
N_SALES_B = "[Calculation_LabelSalesBold]"
N_SALES_N = "[Calculation_LabelSalesNormal]"
N_PROFIT_B = "[Calculation_LabelProfitBold]"
N_PROFIT_N = "[Calculation_LabelProfitNormal]"
N_PR_B = "[Calculation_LabelRatioBold]"
N_PR_N = "[Calculation_LabelRatioNormal]"
N_QTY_B = "[Calculation_LabelQtyBold]"
N_QTY_N = "[Calculation_LabelQtyNormal]"

N_MIN1_SUBCAT = "[Calculation_TableMin1Subcat]"
N_MIN0_SUBCAT = "[Calculation_TableMin0Subcat]"
N_MIN1_A = "[Calculation_TableMin1A]"
N_MIN0_SALES = "[Calculation_TableMin0Sales]"
N_MIN0_PROFIT = "[Calculation_TableMin0Profit]"
N_MIN1_B = "[Calculation_TableMin1B]"
N_MIN0_RATIO = "[Calculation_TableMin0Ratio]"
N_MIN1_C = "[Calculation_TableMin1C]"
N_MIN0_QTY = "[Calculation_TableMin0Qty]"

N_BAR_MIN1 = "[Calculation_BarMin1]"
N_BAR_LABEL = "[Calculation_LabelBar]"

BAR_MARK_SIZE = "1.637182354927063"

# ── Calculated Fields ─────────────────────────────────────────────────
CALCULATIONS = [
    # caption, formula, datatype, role, field_type, default_format, internal
    ("Profit Ratio", "SUM(IF [Region] = [Parameters].[Selected Region] THEN [Profit] END) / SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END)", "real", "measure", "quantitative", PCT_FMT, N_PROFIT_RATIO),
    ("Total Sales for Year & Category", "{FIXED YEAR([Order Date]), [Sub-Category]: SUM([Sales])}", "real", "measure", "quantitative", "", N_TOTAL_YC),
    ("% Sales for Selected Region", "SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END) / SUM([Sales])", "real", "measure", "quantitative", PCT_FMT, N_PCT_SEL),
    ("% Sales All Others", "SUM(IF [Region] != [Parameters].[Selected Region] THEN [Sales] END) / SUM([Sales])", "real", "measure", "quantitative", PCT_FMT, N_PCT_OTHER),
    ("Highlight", "[% Sales for Selected Region] > ([Parameters].[Highlight Threshold]/100)", "boolean", "measure", "nominal", "", N_HIGHLIGHT),

    ("LABEL:Subcat BOLD", "IF [Highlight] THEN ATTR([Sub-Category]) END", "string", "measure", "nominal", "", N_SUBCAT_B),
    ("LABEL:Subcat Normal", "IF NOT([Highlight]) THEN ATTR([Sub-Category]) END", "string", "measure", "nominal", "", N_SUBCAT_N),
    ("LABEL:Sales BOLD", "IF [Highlight] THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END) END", "real", "measure", "ordinal", CURRENCY_FMT, N_SALES_B),
    ("LABEL:Sales Normal", "IF NOT([Highlight]) THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END) END", "real", "measure", "ordinal", CURRENCY_FMT, N_SALES_N),
    ("LABEL:Profit BOLD", "IF [Highlight] THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Profit] END) END", "real", "measure", "ordinal", CURRENCY_FMT, N_PROFIT_B),
    ("LABEL:Profit Normal", "IF NOT([Highlight]) THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Profit] END) END", "real", "measure", "ordinal", CURRENCY_FMT, N_PROFIT_N),
    ("LABEL:Profit Ratio BOLD", "IF [Highlight] THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Profit] END) / SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END) END", "real", "measure", "ordinal", PCT_FMT, N_PR_B),
    ("LABEL:Profit Ratio Normal", "IF NOT([Highlight]) THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Profit] END) / SUM(IF [Region] = [Parameters].[Selected Region] THEN [Sales] END) END", "real", "measure", "ordinal", PCT_FMT, N_PR_N),
    ("LABEL:Qty BOLD", "IF [Highlight] THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Quantity] END) END", "integer", "measure", "ordinal", INT_FMT, N_QTY_B),
    ("LABEL:Qty Normal", "IF NOT([Highlight]) THEN SUM(IF [Region] = [Parameters].[Selected Region] THEN [Quantity] END) END", "integer", "measure", "ordinal", INT_FMT, N_QTY_N),

    ("MIN(1) Subcat", "MIN(1)", "integer", "measure", "quantitative", "", N_MIN1_SUBCAT),
    ("MIN(0) Subcat", "MIN(0)", "integer", "measure", "quantitative", "", N_MIN0_SUBCAT),
    ("MIN(1) A", "MIN(1)", "integer", "measure", "quantitative", "", N_MIN1_A),
    ("MIN(0) Sales", "MIN(0)", "integer", "measure", "quantitative", "", N_MIN0_SALES),
    ("MIN(0) Profit", "MIN(0)", "integer", "measure", "quantitative", "", N_MIN0_PROFIT),
    ("MIN(1) B", "MIN(1)", "integer", "measure", "quantitative", "", N_MIN1_B),
    ("MIN(0) Ratio", "MIN(0)", "integer", "measure", "quantitative", "", N_MIN0_RATIO),
    ("MIN(1) C", "MIN(1)", "integer", "measure", "quantitative", "", N_MIN1_C),
    ("MIN(0) Qty", "MIN(0)", "integer", "measure", "quantitative", "", N_MIN0_QTY),

    ("MIN(1) Bar", "MIN(1)", "integer", "measure", "quantitative", "", N_BAR_MIN1),
    ("LABEL:Bar", "[Parameters].[Selected Region] + ' vs. All Other Regions'", "string", "dimension", "nominal", "", N_BAR_LABEL),
]

# ── Multi-column Table Column Definitions ─────────────────────────────
TABLE_COLUMNS = [
    TableColumn(
        header="Sub-Category",
        bold_field="LABEL:Subcat BOLD",
        normal_field="LABEL:Subcat Normal",
        axis_field="MIN(1) Subcat",
        spacer_field="MIN(0) Subcat",
        instance_kind="nk",
        text_align="left",
        header_font="Tableau Book",
    ),
    TableColumn(
        header="Sales",
        bold_field="LABEL:Sales BOLD",
        normal_field="LABEL:Sales Normal",
        axis_field="MIN(1) A",
        spacer_field="MIN(0) Sales",
        instance_kind="ok",
        text_align="right",
        vertical_align=True,
        header_font="Tableau Book",
    ),
    TableColumn(
        header="Profit",
        bold_field="LABEL:Profit BOLD",
        normal_field="LABEL:Profit Normal",
        axis_field="MIN(1) A",
        spacer_field="MIN(0) Profit",
        instance_kind="ok",
        text_align="right",
        vertical_align=True,
        axis_index="1",
        header_font="Tableau Book",
    ),
    TableColumn(
        header="Profit Ratio",
        bold_field="LABEL:Profit Ratio BOLD",
        normal_field="LABEL:Profit Ratio Normal",
        axis_field="MIN(1) B",
        spacer_field="MIN(0) Ratio",
        instance_kind="ok",
        text_align="right",
        header_font="Tableau Book",
    ),
    TableColumn(
        header="Quantity",
        bold_field="LABEL:Qty BOLD",
        normal_field="LABEL:Qty Normal",
        axis_field="MIN(1) C",
        spacer_field="MIN(0) Qty",
        instance_kind="ok",
        text_align="right",
        header_font="Tableau Book",
    ),
]

# ── Dashboard Layout Tree ─────────────────────────────────────────────
DASHBOARD_LAYOUT = {
    "type": "container", "direction": "floating", "children": [
        {"type": "worksheet", "name": "Title", "absolute": {"x": 889, "y": 1333, "w": 61667, "h": 12000}},
        {"type": "filter", "worksheet": "Table", "field": "Sub-Category", "mode": "checkdropdown", "absolute": {"x": 62556, "y": 1333, "w": 19778, "h": 12000}},
        {"type": "paramctrl", "parameter": "Highlight Threshold", "mode": "type_in", "absolute": {"x": 82334, "y": 1333, "w": 16777, "h": 12000}},
        {"type": "worksheet", "name": "Table", "show_title": False, "fit": "entire", "absolute": {"x": 889, "y": 13333, "w": 58778, "h": 78334}},
        {"type": "worksheet", "name": "Bar", "show_title": False, "fit": "entire", "absolute": {"x": 59667, "y": 13333, "w": 39444, "h": 74584}},
        {"type": "text", "text": "DESIGNED BY:Corey Jones", "font_size": "8", "absolute": {"x": 889, "y": 91667, "w": 20333, "h": 7000}},
        {"type": "text", "runs": [{"text": "#WORKOUTWEDNESDAY | 2019 | WEEK 33\n", "font_size": "8"}, {"text": "http://www.workout-wednesday.com/2019-w33/", "font_size": "8", "font_color": "#3093bb", "hyperlink": "http://www.workout-wednesday.com/2019-w33/"}], "absolute": {"x": 21222, "y": 91667, "w": 56334, "h": 7000}},
        {"type": "text", "text": "RECREATED BY: Donna Coles", "font_size": "8", "absolute": {"x": 77556, "y": 91667, "w": 21555, "h": 7000}},
    ]
}


def build() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor = TWBEditor("")
    editor.set_hyper_connection(str(INPUT_HYPER), table_name="Extract")

    # Add parameters
    editor.add_parameter(
        "Highlight Threshold",
        datatype="integer",
        default_value="30",
        domain_type="any",
        internal_name=N_PARAM,
    )
    editor.add_parameter(
        "Selected Region",
        datatype="string",
        default_value="East",
        domain_type="list",
        allowed_values=["Central", "East", "South", "West"],
        internal_name=N_PARAM_REGION,
    )

    # Add calculated fields
    for caption, formula, datatype, role, ftype, fmt, internal in CALCULATIONS:
        editor.add_calculated_field(
            caption,
            formula,
            datatype=datatype,
            role=role,
            field_type=ftype,
            default_format=fmt,
            internal_name=internal,
        )

    editor.set_datasource_color_palette(
        "Highlight",
        color_map={"true": "#d3d3d3", "false": "#ffffff"},
    )

    # Create worksheets
    for name in ("Title", "Table", "Bar"):
        editor.add_worksheet(name)
        editor.set_worksheet_hidden(name, hidden=True)

    # 1. Title Worksheet
    editor.set_worksheet_rich_title(
        "Title",
        runs=[
            {
                "text": "2018 <[Parameters].[Selected Region]> Sales",
                "bold": True,
                "fontcolor": "#666666",
                "fontsize": 14,
            },
            {
                "text": " | sub-categories greater than <[Parameters].[Highlight Threshold]>% highlighted",
                "fontcolor": "#666666",
                "fontsize": 9,
            },
        ],
    )

    # 2. Table Worksheet
    editor.configure_multi_column_table(
        "Table",
        row_field="Sub-Category",
        color_field="Highlight",
        columns=TABLE_COLUMNS,
    )

    # 3. Bar Worksheet
    editor.configure_dual_axis(
        "Bar",
        mark_type_1="Bar",
        mark_type_2="Bar",
        columns=["LABEL:Bar", "% Sales for Selected Region", "MIN(1) Bar"],
        rows=["Sub-Category"],
        dual_axis_shelf="cols",
        mark_color_1="#5c6068",
        mark_color_2="#ffffff",
        fold_axis=True,
        label_1="% Sales for Selected Region",
        label_2="% Sales All Others",
        hide_axes=False,
        hide_zeroline=True,
        mark_sizing_off=True,
        size_value_1=BAR_MARK_SIZE,
        size_value_2=BAR_MARK_SIZE,
    )
    editor.configure_worksheet_style(
        "Bar",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        axis_style={"title": "", "tick-color": "#00000000", "render-fold-reversed": "true", "encodings": [
            {"field": "% Sales for Selected Region", "class": "0", "scope": "cols", "range_type": "fixed", "min": -0.07, "max": 1.02, "major_show": False, "minor_show": False},
            {"field": "MIN(1) Bar", "class": "0", "scope": "cols", "fold": True, "synchronized": True},
        ], "per_field": [
            {"field": "% Sales for Selected Region", "attr": "display", "class": "0", "scope": "cols", "value": "false"},
            {"field": "MIN(1) Bar", "attr": "display", "class": "0", "scope": "cols", "value": "false"},
        ]},
        pane_mark_style={"has_stroke": "true", "stroke_color": "#666666"},
        panes_style={"1": {"cell_style": {"text_align": "left"}, "mark_style": {"has_stroke": "true", "stroke_color": "#666666"}}, "2": {"cell_style": {"text_align": "right"}, "mark_style": {"has_stroke": "true", "stroke_color": "#666666"}}},
        cell_formats=[{"field": "Sub-Category", "height": 38}],
        header_formats=[{"height_header": 44}],
        label_formats=[
            {"field": ":Measure Names", "display": False},
            {"field": "Sub-Category", "display": False},
        ],
    )

    # 4. Shared Workbook Filters
    editor.add_shared_filter("Sub-Category", all_members=True)
    editor.add_shared_filter("Order Date", year=2018)

    # 5. Dashboard
    editor.add_dashboard(
        DASHBOARD_NAME,
        width=900,
        height=600,
        layout=DASHBOARD_LAYOUT,
        worksheet_names=["Title", "Table", "Bar"],
    )

    twb_path = OUTPUT_DIR / "2019-08-14-ww33-table-formatting-replicated-workbook.twb"
    twbx_path = OUTPUT_DIR / "replicated-workbook.twbx"
    editor.save(twb_path)
    editor.save(twbx_path)

    return {
        "twb": str(twb_path),
        "twbx": str(twbx_path),
        "worksheets": editor.list_worksheets(),
        "dashboards": editor.list_dashboards(),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False))
