"""Build the WW50 drill-down dashboard from the extracted Hyper extract.

The builder uses only the public cwtwb API and the packaged extract under
``inputs/``. It never opens or reads the author workbook.
"""

from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path

import cwtwb
from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"

BAR_SHEET = "Bar Chart"
LINE_SHEET = "Line"
DASHBOARD = "2021 Week 50 - Drill Down"

PARAM_CATEGORY = "pSelectedCategory"
PARAM_SUBCAT = "pSelectedSubCat"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    extract = next(INPUTS.glob("*.hyper"))

    editor = TWBEditor("")
    editor.set_hyper_connection(str(extract), table_name="Extract")

    # Two string parameters hold the click path. Empty string means "not
    # selected"; Tableau parameter actions write the clicked values into them.
    editor.add_parameter(
        PARAM_CATEGORY,
        datatype="string",
        default_value="",
        domain_type="any",
    )
    editor.add_parameter(
        PARAM_SUBCAT,
        datatype="string",
        default_value="",
        domain_type="any",
    )

    calculations = [
        (
            "Sub Cat Display",
            'IF [pSelectedCategory]=[Category] THEN [Sub-Category] ELSE "" END',
            "string",
            "dimension",
            "nominal",
        ),
        (
            "FILTER",
            '([pSelectedCategory]="") OR '
            '([pSelectedCategory]=[Category] AND [pSelectedSubCat]="") OR '
            '([pSelectedCategory]=[Category] AND [pSelectedSubCat]=[Sub-Category])',
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Colour:Line",
            "[pSelectedCategory]",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "TOOLTIP:Category",
            'IF [pSelectedCategory]="" THEN "All" ELSE [pSelectedCategory] END',
            "string",
            "dimension",
            "nominal",
        ),
        (
            "TOOLTIP:SubCat",
            'IF [pSelectedSubCat]="" THEN "All" ELSE [pSelectedSubCat] END',
            "string",
            "dimension",
            "nominal",
        ),
    ]
    for name, formula, datatype, role, field_type in calculations:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
        )
    editor.set_field_format("Sales", 'c"£"#,##0;-"£"#,##0')

    # ---- Bar chart: Category -> Sub-Category drill path -------------------
    editor.add_worksheet(BAR_SHEET)
    editor.configure_chart(
        BAR_SHEET,
        mark_type="Bar",
        rows=["Category", "Sub Cat Display"],
        columns=["SUM(Sales)"],
        color="Category",
        label="SUM(Sales)",
        sort_descending="SUM(Sales)",
        sort_field="Sub Cat Display",
        tooltip=["Category", "Sub Cat Display", "SUM(Sales)"],
    )
    editor.configure_worksheet_style(
        BAR_SHEET,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_table_dividers=True,
        pane_datalabel_style={"font-size": "8"},
        header_formats=[
            {"field": "Category", "text-align": "left", "font-size": "8"},
            {"field": "Sub Cat Display", "text-align": "left", "font-size": "8"},
        ],
        color_style={
            "field": "Category",
            "colors": ["#4e79a7", "#f28e2b", "#e15759"],
        },
    )

    # ---- Line chart: monthly sales for the current click path ------------
    editor.add_worksheet(LINE_SHEET)
    editor.configure_chart(
        LINE_SHEET,
        mark_type="Line",
        columns=["MONTHTRUNC(Order Date)"],
        rows=["SUM(Sales)"],
        color="Colour:Line",
        label="SUM(Sales)",
        tooltip=[
            "TOOLTIP:Category",
            "TOOLTIP:SubCat",
            "SUM(Sales)",
            "MONTHTRUNC(Order Date)",
        ],
        filters=[{"column": "FILTER", "values": [True]}],
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        LINE_SHEET,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        pane_mark_style={
            "mark-labels-mode": "range",
            "mark-labels-show": "true",
            "mark-labels-range-min": "true",
            "mark-labels-range-max": "true",
        },
        pane_datalabel_style={"font-size": "8"},
        axis_style={
            "per_field": [
                {
                    "field": "MONTHTRUNC(Order Date)",
                    "attr": "title",
                    "value": "Order Date",
                    "scope": "cols",
                }
            ]
        },
        color_style={
            "field": "Colour:Line",
            "colors": ["#9e9e9e", "#4e79a7", "#f28e2b", "#e15759"],
        },
    )

    # ---- Fixed 500 x 600 dashboard ---------------------------------------
    def box(x: int, y: int, w: int, h: int) -> dict:
        return {
            "x": round(x / 500 * 100000),
            "y": round(y / 600 * 100000),
            "w": round(w / 500 * 100000),
            "h": round(h / 600 * 100000),
        }

    def text_zone(text: str, x: int, y: int, w: int, h: int, **run) -> dict:
        return {
            "type": "text",
            "runs": [{"text": text, **run}],
            "absolute": box(x, y, w, h),
        }

    editor.add_dashboard(
        DASHBOARD,
        width=500,
        height=600,
        worksheet_names=[BAR_SHEET, LINE_SHEET],
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                text_zone(
                    "Sales Drill Down",
                    16,
                    8,
                    468,
                    34,
                    font_size=15,
                    bold=True,
                ),
                {
                    "type": "worksheet",
                    "name": BAR_SHEET,
                    "show_title": False,
                    "fit": "entire",
                    "absolute": box(16, 44, 468, 192),
                },
                {
                    "type": "worksheet",
                    "name": LINE_SHEET,
                    "show_title": False,
                    "fit": "entire",
                    "absolute": box(16, 242, 468, 268),
                },
                text_zone(
                    "CHALLENGE BY LORNA BROWN   |   #WOW2021 WEEK 50",
                    16,
                    516,
                    468,
                    18,
                    font_size=8,
                    font_color="#8175aa",
                    font_alignment="0",
                ),
                text_zone(
                    "RECREATED BY DONNA COLES",
                    16,
                    534,
                    468,
                    18,
                    font_size=8,
                    font_color="#8175aa",
                    font_alignment="1",
                ),
                text_zone(
                    "https://www.workout-wednesday.com/2021tabw50/",
                    16,
                    558,
                    468,
                    18,
                    font_size=8,
                    font_color="#8175aa",
                    font_alignment="1",
                ),
            ],
        },
    )

    # Two parameter actions: clicking a bar writes Category and Sub Cat
    # Display. Clearing the click resets both parameters to the empty string.
    # Selecting another Category therefore resets the Sub-Category in the same
    # gesture, which is the behaviour the challenge calls out as difficult.
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet=BAR_SHEET,
        source_field="Category",
        target_parameter=PARAM_CATEGORY,
        aggregation="attr",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
        caption="Selected Category",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet=BAR_SHEET,
        source_field="Sub Cat Display",
        target_parameter=PARAM_SUBCAT,
        aggregation="attr",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
        caption="Selected Sub Cat",
    )
    editor.set_active_dashboard(DASHBOARD)

    workbook = OUTPUTS / "replicated-workbook.twbx"
    editor.save(workbook)

    report = {
        "version": version("cwtwb"),
        "module": str(Path(cwtwb.__file__).resolve()),
        "module_sha256": sha256(Path(cwtwb.__file__).read_bytes()).hexdigest(),
        "extract_sha256": sha256(extract.read_bytes()).hexdigest(),
        "workbook_sha256": sha256(workbook.read_bytes()).hexdigest(),
        "sheets": [BAR_SHEET, LINE_SHEET],
        "dashboard": DASHBOARD,
        "parameters": [PARAM_CATEGORY, PARAM_SUBCAT],
    }
    (OUTPUTS / "build-provenance.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return workbook


if __name__ == "__main__":
    print(build())
