"""Build 2023 Week 48 Bars and Candlesticks replication workbook.

Replication built 100% via cwtwb public API from an empty workbook TWBEditor("").
Author: Donna Coles / Challenge by Shunta Nakajima
"""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"
HYPER_FILE = INPUTS / "Orders (Sample - Superstore).hyper"
OUTPUT_TWBX = OUTPUTS / "replicated-workbook.twbx"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER_FILE), table_name="Extract")

    # 1. Parameters
    editor.add_parameter(
        name="pSelectedMeasure",
        datatype="string",
        default_value="Sales",
    )
    editor.add_parameter(
        name="pSelectedYear",
        datatype="integer",
        default_value="2022",
    )

    # 2. Calculated Fields
    # Current Year (2023)
    editor.add_calculated_field(
        "Current Year",
        "{FIXED: MAX(YEAR([Order Date]))}",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # Measures for current and comparison year based on selected measure parameter
    editor.add_calculated_field(
        "Measure to Display - Curr Year",
        (
            "IF YEAR([Order Date]) = [Current Year] THEN\n"
            "  CASE [Parameters].[pSelectedMeasure]\n"
            "    WHEN 'Sales' THEN [Sales]\n"
            "    WHEN 'Profit' THEN [Profit]\n"
            "    WHEN 'Quantity' THEN [Quantity]\n"
            "  END\n"
            "END"
        ),
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    editor.add_calculated_field(
        "Measure to Display - Comp Year",
        (
            "IF YEAR([Order Date]) = [Parameters].[pSelectedYear] THEN\n"
            "  CASE [Parameters].[pSelectedMeasure]\n"
            "    WHEN 'Sales' THEN [Sales]\n"
            "    WHEN 'Profit' THEN [Profit]\n"
            "    WHEN 'Quantity' THEN [Quantity]\n"
            "  END\n"
            "END"
        ),
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    # Difference: Curr Year - Comp Year
    editor.add_calculated_field(
        "Difference",
        "SUM([Measure to Display - Curr Year]) - SUM([Measure to Display - Comp Year])",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    # % Difference
    editor.add_calculated_field(
        "% Difference",
        (
            "IF (SUM([Measure to Display - Curr Year]) >= 0 AND SUM([Measure to Display - Comp Year]) >= 0) "
            "OR (SUM([Measure to Display - Curr Year]) < 0 AND SUM([Measure to Display - Comp Year]) < 0) THEN\n"
            "  (SUM([Measure to Display - Curr Year]) - SUM([Measure to Display - Comp Year])) / ABS(SUM([Measure to Display - Comp Year]))\n"
            "ELSE\n"
            "  0\n"
            "END"
        ),
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    # Diff is +ve
    editor.add_calculated_field(
        "Diff is +ve",
        "[Difference] >= 0",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # Candlestick Label: combination of difference and % diff
    editor.add_calculated_field(
        "Candlestick Label",
        "[Difference]",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    # Year selector alias & helpers
    editor.add_calculated_field(
        "Comparison Year",
        "IIF(YEAR([Order Date]) <> [Current Year], YEAR([Order Date]), NULL)",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Is Selected Year",
        "[Comparison Year] = [Parameters].[pSelectedYear]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # Measure selector alias & helpers
    editor.add_calculated_field(
        "Measure Selector Alias",
        (
            "CASE [Segment]\n"
            "  WHEN 'Consumer' THEN 'Sales'\n"
            "  WHEN 'Corporate' THEN 'Profit'\n"
            "  ELSE 'Quantity'\n"
            "END"
        ),
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Is Measure Selected",
        "[Measure Selector Alias] = [Parameters].[pSelectedMeasure]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # Dummy MIN(1)
    editor.add_calculated_field(
        "One",
        "MIN(1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # Set default number formats
    editor.set_field_format("Difference", "+#,##0;-#,##0")
    editor.set_field_format("% Difference", "+0.0%;-0.0%")
    editor.set_field_format("Measure to Display - Curr Year", "#,##0")
    editor.set_field_format("Measure to Display - Comp Year", "#,##0")

    # Set datasource color palettes
    # 1. Diff is +ve: True -> #7fb897 (green), False -> #d66252 (red)
    editor.set_datasource_color_palette(
        "Diff is +ve",
        {
            "true": "#7fb897",
            "false": "#d66252",
        },
    )

    # 2. Measure Names (for dual-axis / bar comparisons)
    editor.set_datasource_color_palette(
        "Measure Names",
        {
            "Measure to Display - Curr Year": "#8075ae",
            "Measure to Display - Comp Year": "#d3d3d3",
        },
        is_measure_names=True,
    )

    # 3. Worksheets
    # 3.1 Primary Chart: Dual Axis (Bar + GanttBar)
    chart_sheet = "Chart"
    editor.add_worksheet(chart_sheet)
    editor.configure_dual_axis(
        chart_sheet,
        mark_type_1="Bar",
        mark_type_2="GanttBar",
        dual_axis_shelf="columns",
        columns=["Measure to Display - Curr Year", "Measure to Display - Comp Year"],
        rows=["[Sub-Category]"],
        color_1="Measure Names",
        color_2="Diff is +ve",
        size_2="Difference",
        label_2="Difference",
        synchronized=True,
        sort_descending="Measure to Display - Curr Year",
    )
    editor.configure_worksheet_style(
        chart_sheet,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=False,
    )

    # 3.2 Curr Year KPI Card
    curr_year_sheet = "Curr Year"
    editor.add_worksheet(curr_year_sheet)
    editor.configure_chart(
        curr_year_sheet,
        mark_type="Text",
        columns=["One"],
        label="Current Year",
    )
    editor.configure_worksheet_style(
        curr_year_sheet,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
    )

    # 3.3 Year Selector
    year_selector_sheet = "Year Selector"
    editor.add_worksheet(year_selector_sheet)
    editor.configure_chart(
        year_selector_sheet,
        mark_type="Square",
        columns=["[Comparison Year]"],
        color="Is Selected Year",
        label="[Comparison Year]",
        color_map={
            "true": "#858796",
            "false": "#e2e2e2",
        },
    )
    editor.configure_worksheet_style(
        year_selector_sheet,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
    )

    # 3.4 Measure Selector
    measure_selector_sheet = "Measure Selector"
    editor.add_worksheet(measure_selector_sheet)
    editor.configure_chart(
        measure_selector_sheet,
        mark_type="Square",
        columns=["[Measure Selector Alias]"],
        color="Is Measure Selected",
        label="[Measure Selector Alias]",
        color_map={
            "true": "#c5a059",
            "false": "#edd886",
        },
    )
    editor.configure_worksheet_style(
        measure_selector_sheet,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
    )

    # 4. Dashboard: 2023_11_29_WW48_Bars_and_Candlesticks
    dash_layout = {
        "type": "container",
        "direction": "vertical",
        "layout_strategy": "manual",
        "children": [
            # Title
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Can you add candlesticks to bar charts?",
                        "font_bold": "true",
                        "font_color": "#000000",
                        "font_name": "Tableau Bold",
                        "font_size": "16",
                    }
                ],
                "absolute": {"x": 1000, "y": 1500, "w": 98000, "h": 5000},
                "style": {"border-style": "none", "border-width": "0", "margin": "0"},
            },
            # Top Controls Row (Current Year card, Year Selector, Measure Selector)
            {
                "type": "worksheet",
                "name": curr_year_sheet,
                "show_title": True,
                "absolute": {"x": 2000, "y": 8000, "w": 15000, "h": 8000},
            },
            {
                "type": "worksheet",
                "name": year_selector_sheet,
                "show_title": True,
                "absolute": {"x": 20000, "y": 8000, "w": 35000, "h": 8000},
            },
            {
                "type": "worksheet",
                "name": measure_selector_sheet,
                "show_title": True,
                "absolute": {"x": 58000, "y": 8000, "w": 38000, "h": 8000},
            },
            # Main Dual-Axis Chart
            {
                "type": "worksheet",
                "name": chart_sheet,
                "show_title": False,
                "absolute": {"x": 1000, "y": 18000, "w": 98000, "h": 75000},
                "style": {"border-style": "none", "border-width": "0", "margin": "0"},
            },
            # Footer
            {
                "type": "text",
                "runs": [
                    {
                        "text": "CHALLENGE BY : Shunta Nakajima",
                        "font_color": "#000000",
                        "font_name": "Tableau Book",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 1000, "y": 94000, "w": 30000, "h": 4000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "#WOW2023 | WEEK 48\n",
                        "font_alignment": "1",
                        "font_color": "#000000",
                        "font_name": "Tableau Book",
                        "font_size": "8",
                    },
                    {
                        "text": "https://workout-wednesday.com/2023w48tab/",
                        "font_alignment": "1",
                        "font_color": "#1ba3c6",
                        "font_name": "Tableau Book",
                        "font_size": "8",
                        "hyperlink": 'tabdoc:load-url url="https://workout-wednesday.com/2023w48tab/"',
                    },
                ],
                "absolute": {"x": 35000, "y": 93500, "w": 30000, "h": 5000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "RECREATED BY : Donna Coles",
                        "font_alignment": "2",
                        "font_color": "#000000",
                        "font_name": "Tableau Book",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 68000, "y": 94000, "w": 30000, "h": 4000},
            },
        ],
    }

    dash_name = "2023_11_29_WW48_Bars_and_Candlesticks"
    editor.add_dashboard(
        dash_name,
        width=1000,
        height=680,
        layout=dash_layout,
        worksheet_names=[chart_sheet, curr_year_sheet, year_selector_sheet, measure_selector_sheet],
    )

    editor.save(OUTPUT_TWBX)
    return OUTPUT_TWBX


if __name__ == "__main__":
    print(build())
