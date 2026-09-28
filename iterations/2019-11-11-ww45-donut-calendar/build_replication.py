"""
WW45 Donut Calendar 100% 纯 cwtwb 从0到1构建脚本
完全使用 cwtwb 官方 API (TWBEditor) 初始化全新工作簿，不引用任何外部模板 XML/JSON 文件。

实现要点：
1. TWBEditor("") 初始化空白工作簿；
2. set_hyper_connection 加载数据源；
3. add_parameter 创建 Report Date 参数；
4. add_calculated_field 创建所有业务计算字段（Has Shipped?, % Shipped, Fully Shipped?, LABEL %, Dates to Include, Baseline Date 等）；
5. set_datasource_color_palette 配置 Has Shipped? 和 Fully Shipped? 的调色板；
6. add_worksheet + configure_chart / configure_dual_axis 构建 Base 和 Main 双轴甜甜圈图表；
7. add_dashboard 组合 800x400 仪表板；
8. 依据原作者视觉样式在内存中应用微调（标题 Teal 样式、-90°日期表头、Last 7 days 汇总、透明背景与浮动图层重叠）。
"""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUTS = HERE / "outputs"
OUTPUT = OUTPUTS / "replicated-workbook.twbx"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")

    # 1. Parameter: Report Date (#2019-11-06#)
    editor.add_parameter(
        name="Report Date",
        datatype="date",
        default_value="#2019-11-06#",
    )

    # 2. Number of Records
    editor.add_calculated_field(
        "Number of Records",
        "1",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # 3. Has Shipped?
    editor.add_calculated_field(
        "Has Shipped?",
        "[Ship Date] <= [Parameters].[Report Date]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # 4. # Shipped
    editor.add_calculated_field(
        "# Shipped",
        "IIF([Has Shipped?], 1, 0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # 5. % Shipped
    editor.add_calculated_field(
        "% Shipped",
        "SUM([# Shipped]) / SUM([Number of Records])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )

    # 6. Fully Shipped?
    editor.add_calculated_field(
        "Fully Shipped?",
        "[% Shipped] = 1",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )

    # 7. Separated Labels for White Tick and Dark Percent
    editor.add_calculated_field(
        "LABEL Tick",
        "IF [Fully Shipped?] THEN '✓' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    editor.add_calculated_field(
        "LABEL % Shipped",
        "IF NOT([Fully Shipped?]) THEN [% Shipped] END",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )

    # 8. LABEL % (Donna Coles' single calculation for center label)
    editor.add_calculated_field(
        "LABEL %",
        "IF [Fully Shipped?] THEN '✓' ELSE STR(ROUND([% Shipped] * 100,0)) + '%' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    # 9. Dates to Include
    editor.add_calculated_field(
        "Dates to Include",
        "[Order Date] >= DATEADD('day', -7, [Parameters].[Report Date]) AND [Order Date] <= [Parameters].[Report Date]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # 10. Baseline Date & Filter for Base background sheet
    editor.add_calculated_field(
        "Baseline Date",
        "MAKEDATE(2019, MONTH([Order Date]), DAY([Order Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )

    editor.add_calculated_field(
        "Baseline Dates to Include",
        "[Baseline Date] >= DATEADD('day', -7, [Parameters].[Report Date]) AND [Baseline Date] <= [Parameters].[Report Date]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # 11. MIN(0) for dual-axis positioning
    editor.add_calculated_field(
        "MIN(0)",
        "MIN(0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # Palette configurations
    editor.set_datasource_color_palette("Has Shipped?", {"true": "#59a14f", "false": "#d3d3d3"})
    editor.set_datasource_color_palette("Fully Shipped?", {"true": "#59a14f", "false": "#ffffff"})

    # 12. Add Worksheets via cwtwb
    editor.add_worksheet("Base")
    editor.configure_chart(
        "Base",
        mark_type="Circle",
        columns=["[Baseline Date]", "[MIN(0)]"],
        rows=["[Region]"],
        filters=[{"column": "Baseline Dates to Include", "values": [True]}],
    )

    editor.add_worksheet("Main")
    editor.configure_dual_axis(
        "Main",
        mark_type_1="Pie",
        mark_type_2="Circle",
        columns=["[Order Date]", "[MIN(0)]", "[MIN(0)]"],
        rows=["[Region]"],
        dual_axis_shelf="columns",
        color_1="[Has Shipped?]",
        wedge_size_1="[Number of Records]",
        color_2="[Fully Shipped?]",
        label_2="[LABEL %]",
        filters=[{"column": "Dates to Include", "values": [True]}],
    )

    # 13. Add Dashboard via high-level declarative layout
    dashboard_layout = {
        "type": "floating",
        "children": [
            # Header title text
            {
                "type": "text",
                "runs": [
                    {
                        "text": "WHAT IS OUR DAILY FULFILMENT RATE BY REGION?",
                        "font_color": "#499894",
                        "font_name": "Tableau Medium",
                        "font_size": "14",
                    }
                ],
                "absolute": {"x": 1000, "y": 2000, "w": 98000, "h": 10311},
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            # Background Base worksheet
            {
                "type": "worksheet",
                "name": "Base",
                "show_title": False,
                "absolute": {"x": 1000, "y": 12311, "w": 98000, "h": 73939},
                "style": {"border-style": "none", "border-width": "0", "margin": "0"},
            },
            # Footer text left
            {
                "type": "text",
                "runs": [
                    {
                        "text": "DESIGNED BY : LUKE STANKE\nRECREATED BY : DONNA COLES",
                        "font_color": "#499894",
                        "font_name": "Tableau Medium",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 1000, "y": 86250, "w": 32250, "h": 11750},
            },
            # Footer text right (with hyperlink)
            {
                "type": "text",
                "runs": [
                    {
                        "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 45\n",
                        "font_alignment": "2",
                        "font_color": "#499894",
                        "font_name": "Tableau Medium",
                        "font_size": "8",
                    },
                    {
                        "text": "http://www.workout-wednesday.com/2019w45/",
                        "font_alignment": "2",
                        "font_color": "#499894",
                        "font_name": "Tableau Medium",
                        "font_size": "8",
                        "hyperlink": 'tabdoc:load-url url="http://www.workout-wednesday.com/2019w45/"',
                    },
                ],
                "absolute": {"x": 33250, "y": 86250, "w": 65750, "h": 11750},
            },
            # Top-level floating Main worksheet overlay
            {
                "type": "worksheet",
                "name": "Main",
                "show_title": False,
                "absolute": {"x": 750, "y": 10000, "w": 98125, "h": 76500},
            },
        ],
    }

    dash_name = "2019_11_06_WW45_Donut_Calendar"
    editor.add_dashboard(
        dash_name,
        width=800,
        height=400,
        layout=dashboard_layout,
        worksheet_names=["Main", "Base"],
    )

    # 14. Apply visual styling via cwtwb configure_worksheet_style
    # 14.1 Base sheet styling
    editor.configure_worksheet_style(
        "Base",
        background_color="#00000000",
        show_column_totals=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        panes_style={
            "0": {
                "mark_class": "Pie",
                "mark_style": {
                    "size": "1.0214917659759521",
                    "mark-labels-cull": "true",
                    "mark-labels-show": "false",
                    "mark-color": "#e6e6e6",
                },
            }
        },
        axis_style={
            "tick-color": "#00000000",
            "per_field": [
                {"field": "MIN(0)", "class": "0", "scope": "cols", "attr": "display", "value": "false"},
            ],
        },
        header_formats=[
            {"attr": "height-header", "value": "12"},
            {"attr": "border-width", "data_class": "total", "scope": "cols", "value": "0"},
            {"attr": "border-style", "data_class": "total", "scope": "cols", "value": "none"},
        ],
        label_formats=[
            {"field": "Baseline Date", "text-format": "*mmm d, 'yy", "text-orientation": "-90", "color": "#ffffff"},
            {"field": "Region", "color": "#ffffff"},
        ],
        table_dividers=[
            {"scope": "rows", "div-level": "1", "stroke-color": "#d4d4d4", "line-pattern-only": "dotted", "stroke-size": "0", "line-visibility": "off"},
            {"scope": "cols", "stroke-size": "0", "line-visibility": "off"},
        ],
    )

    # 14.2 Main sheet styling
    editor.configure_worksheet_style(
        "Main",
        background_color="#00000000",
        show_column_totals=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        panes_style={
            "1": {  # Pie mark
                "mark_style": {"size": "1.1534254550933838"},
            },
            "2": {  # Circle hole
                "mark_style": {"size": "0.82359117269515991"},
                "cell_style": {"text-align": "center", "vertical-align": "center"},
                "datalabel_style": {"color-mode": "auto", "font-size": "6"},
            },
        },
        axis_style={
            "tick-color": "#00000000",
            "per_field": [
                {"field": "MIN(0)", "class": "0", "scope": "cols", "attr": "display", "value": "false"},
                {"field": "MIN(0)", "class": "1", "scope": "cols", "attr": "display", "value": "false"},
            ],
        },
        header_formats=[
            {"attr": "height-header", "value": "12"},
            {"attr": "border-width", "data_class": "total", "scope": "cols", "value": "0"},
            {"attr": "border-style", "data_class": "total", "scope": "cols", "value": "none"},
            {"field": "Order Date", "attr": "total-label", "data_class": "total", "value": "Last 7 days"},
            {"field": "Order Date", "attr": "font-weight", "data_class": "total", "value": "bold"},
            {"field": "Order Date", "attr": "height", "value": "92"},
        ],
        label_formats=[
            {"field": "Order Date", "text-format": "*mmm d, 'yy", "text-orientation": "-90", "color": "#333333"},
            {"field": "Region", "color": "#333333"},
        ],
        table_dividers=[
            {"scope": "rows", "div-level": "1", "stroke-color": "#d4d4d4", "line-pattern-only": "dotted", "line-visibility": "on"},
            {"scope": "cols", "stroke-size": "0", "line-visibility": "off"},
        ],
    )

    # 15. Set active dashboard and window state via cwtwb API
    main_zone_id = None
    dash_el = editor.root.find(f".//dashboards/dashboard[@name='{dash_name}']")
    if dash_el is not None:
        main_z = dash_el.find(".//zone[@name='Main']")
        if main_z is not None:
            main_zone_id = main_z.get("id")

    editor.set_active_dashboard(dash_name, active_zone_id=main_zone_id)
    editor.set_window_state(dash_name, zoom_entire_view=True)
    editor.set_window_state("Base", hidden=True, zoom_entire_view=True)
    editor.set_window_state("Main", hidden=True, zoom_entire_view=True)

    editor.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())

