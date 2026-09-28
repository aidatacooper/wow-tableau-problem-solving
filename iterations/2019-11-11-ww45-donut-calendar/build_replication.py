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
from lxml import etree
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

    # 14. Apply visual styling refinements to editor's in-memory XML tree
    apply_visual_refinements(editor)

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


def apply_visual_refinements(editor: TWBEditor) -> None:
    """Apply visual styling refinements to worksheets."""
    root = editor.root
    ds = editor._datasource
    ds_name = ds.get("name")
    calc_map = {col.get("caption"): col.get("name").strip("[]") for col in ds.findall("column") if col.get("caption")}

    # Fix column-instance in datasource to match calculation name exactly
    for ci in ds.findall("column-instance"):
        col_ref = ci.get("column", "").strip("[]")
        if col_ref == "Has Shipped?" and "Has Shipped?" in calc_map:
            real_name = f"[{calc_map['Has Shipped?']}]"
            ci.set("column", real_name)
            ci.set("name", f"[none:{calc_map['Has Shipped?']}:nk]")
        elif col_ref == "Fully Shipped?" and "Fully Shipped?" in calc_map:
            real_name = f"[{calc_map['Fully Shipped?']}]"
            ci.set("column", real_name)
            ci.set("derivation", "User")
            ci.set("name", f"[usr:{calc_map['Fully Shipped?']}:nk]")

    # ----------------------------------------------------
    # 1. Base sheet styling
    # ----------------------------------------------------
    base_ws = root.find(".//worksheet[@name='Base']")
    base_table = base_ws.find("table")
    b_cols = base_table.find("cols")
    b_cols.set("total", "true")
    b_cols.text = f"([{ds_name}].[none:{calc_map['Baseline Date']}:ok] * [{ds_name}].[usr:{calc_map['MIN(0)']}:qk])"

    # Mark in Base: 灰色占位背景圆环
    b_pane = base_table.find("panes/pane")
    b_mark = b_pane.find("mark")
    b_mark.set("class", "Pie")
    b_style = b_pane.find("style")
    if b_style is None:
        b_style = etree.SubElement(b_pane, "style")
    b_rule = b_style.find("style-rule[@element='mark']")
    if b_rule is None:
        b_rule = etree.SubElement(b_style, "style-rule", element="mark")
    etree.SubElement(b_rule, "format", attr="size", value="1.0214917659759521")
    etree.SubElement(b_rule, "format", attr="mark-labels-cull", value="true")
    etree.SubElement(b_rule, "format", attr="mark-labels-show", value="false")
    etree.SubElement(b_rule, "format", attr="mark-color", value="#e6e6e6")

    # Base table formatting
    t_style = base_table.find("style")
    if t_style is None:
        t_style = etree.SubElement(base_table, "style")

    axis_rule = etree.SubElement(t_style, "style-rule", element="axis")
    etree.SubElement(axis_rule, "format", attr="display", **{"class": "0", "field": f"[{ds_name}].[usr:{calc_map['MIN(0)']}:qk]", "scope": "cols", "value": "false"})
    etree.SubElement(axis_rule, "format", attr="tick-color", value="#00000000")

    hdr_rule = etree.SubElement(t_style, "style-rule", element="header")
    etree.SubElement(hdr_rule, "format", attr="height-header", value="12")
    etree.SubElement(hdr_rule, "format", attr="border-width", **{"data-class": "total", "scope": "cols", "value": "0"})
    etree.SubElement(hdr_rule, "format", attr="border-style", **{"data-class": "total", "scope": "cols", "value": "none"})

    lbl_rule = etree.SubElement(t_style, "style-rule", element="label")
    etree.SubElement(lbl_rule, "format", attr="text-format", field=f"[{ds_name}].[none:{calc_map['Baseline Date']}:ok]", value="*mmm d, 'yy")
    etree.SubElement(lbl_rule, "format", attr="text-orientation", field=f"[{ds_name}].[none:{calc_map['Baseline Date']}:ok]", value="-90")
    etree.SubElement(lbl_rule, "format", attr="color", field=f"[{ds_name}].[none:Region:nk]", value="#ffffff")
    etree.SubElement(lbl_rule, "format", attr="color", field=f"[{ds_name}].[none:{calc_map['Baseline Date']}:ok]", value="#ffffff")

    tbl_rule = etree.SubElement(t_style, "style-rule", element="table")
    etree.SubElement(tbl_rule, "format", attr="background-color", value="#00000000")

    ws_rule = etree.SubElement(t_style, "style-rule", element="worksheet")
    etree.SubElement(ws_rule, "format", attr="display-field-labels", scope="cols", value="false")
    etree.SubElement(ws_rule, "format", attr="display-field-labels", scope="rows", value="false")

    tdiv_rule = etree.SubElement(t_style, "style-rule", element="table-div")
    etree.SubElement(tdiv_rule, "format", attr="div-level", scope="rows", value="1")
    etree.SubElement(tdiv_rule, "format", attr="stroke-size", scope="cols", value="0")
    etree.SubElement(tdiv_rule, "format", attr="line-visibility", scope="cols", value="off")
    etree.SubElement(tdiv_rule, "format", attr="stroke-color", scope="rows", value="#d4d4d4")
    etree.SubElement(tdiv_rule, "format", attr="line-pattern-only", scope="rows", value="dotted")
    etree.SubElement(tdiv_rule, "format", attr="stroke-size", scope="rows", value="0")
    etree.SubElement(tdiv_rule, "format", attr="line-visibility", scope="rows", value="off")

    # ----------------------------------------------------
    # 2. Main sheet styling
    # ----------------------------------------------------
    main_ws = root.find(".//worksheet[@name='Main']")
    main_table = main_ws.find("table")
    m_cols = main_table.find("cols")
    m_cols.set("total", "true")
    marker = " + (["
    if marker in m_cols.text:
        m_cols.text = m_cols.text.replace(marker, " * ([", 1)

    m_style = main_table.find("style")
    m_axis_rule = m_style.find("style-rule[@element='axis']")
    if m_axis_rule is None:
        m_axis_rule = etree.SubElement(m_style, "style-rule", element="axis")
    etree.SubElement(m_axis_rule, "format", attr="display", **{"class": "0", "field": f"[{ds_name}].[usr:{calc_map['MIN(0)']}:qk]", "scope": "cols", "value": "false"})
    etree.SubElement(m_axis_rule, "format", attr="display", **{"class": "1", "field": f"[{ds_name}].[usr:{calc_map['MIN(0)']}:qk]", "scope": "cols", "value": "false"})
    etree.SubElement(m_axis_rule, "format", attr="tick-color", value="#00000000")

    m_hdr_rule = etree.SubElement(m_style, "style-rule", element="header")
    etree.SubElement(m_hdr_rule, "format", attr="height-header", value="12")
    etree.SubElement(m_hdr_rule, "format", attr="border-width", **{"data-class": "total", "scope": "cols", "value": "0"})
    etree.SubElement(m_hdr_rule, "format", attr="border-style", **{"data-class": "total", "scope": "cols", "value": "none"})
    etree.SubElement(m_hdr_rule, "format", attr="total-label", **{"data-class": "total", "field": f"[{ds_name}].[none:Order Date:ok]", "value": "Last 7 days"})
    etree.SubElement(m_hdr_rule, "format", attr="font-weight", **{"data-class": "total", "field": f"[{ds_name}].[none:Order Date:ok]", "value": "bold"})
    etree.SubElement(m_hdr_rule, "format", attr="height", field=f"[{ds_name}].[none:Order Date:ok]", value="92")

    m_lbl_rule = etree.SubElement(m_style, "style-rule", element="label")
    etree.SubElement(m_lbl_rule, "format", attr="text-format", field=f"[{ds_name}].[none:Order Date:ok]", value="*mmm d, 'yy")
    etree.SubElement(m_lbl_rule, "format", attr="text-orientation", field=f"[{ds_name}].[none:Order Date:ok]", value="-90")
    etree.SubElement(m_lbl_rule, "format", attr="color", field=f"[{ds_name}].[none:Order Date:ok]", value="#333333")
    etree.SubElement(m_lbl_rule, "format", attr="color", field=f"[{ds_name}].[none:Region:nk]", value="#333333")

    m_tbl_rule = etree.SubElement(m_style, "style-rule", element="table")
    etree.SubElement(m_tbl_rule, "format", attr="background-color", value="#00000000")

    m_ws_rule = etree.SubElement(m_style, "style-rule", element="worksheet")
    etree.SubElement(m_ws_rule, "format", attr="display-field-labels", scope="cols", value="false")
    etree.SubElement(m_ws_rule, "format", attr="display-field-labels", scope="rows", value="false")

    m_tdiv_rule = etree.SubElement(m_style, "style-rule", element="table-div")
    etree.SubElement(m_tdiv_rule, "format", attr="div-level", scope="rows", value="1")
    etree.SubElement(m_tdiv_rule, "format", attr="stroke-size", scope="cols", value="0")
    etree.SubElement(m_tdiv_rule, "format", attr="line-visibility", scope="cols", value="off")
    etree.SubElement(m_tdiv_rule, "format", attr="stroke-color", scope="rows", value="#d4d4d4")
    etree.SubElement(m_tdiv_rule, "format", attr="line-visibility", scope="rows", value="on")
    etree.SubElement(m_tdiv_rule, "format", attr="line-pattern-only", scope="rows", value="dotted")

    # 标记大小微调与居中标签格式
    for p in main_table.findall("panes/pane"):
        pid = p.get("id")
        p_style = p.find("style")
        if p_style is None:
            p_style = etree.SubElement(p, "style")
        m_rule = p_style.find("style-rule[@element='mark']")
        if m_rule is None:
            m_rule = etree.SubElement(p_style, "style-rule", element="mark")

        if pid == "1":  # Pie 标记
            fmt = m_rule.find("format[@attr='size']")
            if fmt is not None:
                fmt.set("value", "1.1534254550933838")
            else:
                etree.SubElement(m_rule, "format", attr="size", value="1.1534254550933838")
        elif pid == "2":  # Circle 甜甜圈孔
            fmt = m_rule.find("format[@attr='size']")
            if fmt is not None:
                fmt.set("value", "0.82359117269515991")
            else:
                etree.SubElement(m_rule, "format", attr="size", value="0.82359117269515991")
            cell_rule = etree.SubElement(p_style, "style-rule", element="cell")
            etree.SubElement(cell_rule, "format", attr="text-align", value="center")
            etree.SubElement(cell_rule, "format", attr="vertical-align", value="center")
            dl_rule = etree.SubElement(p_style, "style-rule", element="datalabel")
            etree.SubElement(dl_rule, "format", attr="color-mode", value="auto")
            etree.SubElement(dl_rule, "format", attr="font-size", value="6")


if __name__ == "__main__":
    print(build())

