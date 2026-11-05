"""WW44: build from extracted Hyper using public cwtwb APIs only."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
MONEY = 'c"$"#,##0;("$"#,##0)'


def build() -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs" / "Orders (Sample - Superstore).hyper"),
        table_name="Extract",
    )
    editor.add_parameter(
        "Period",
        datatype="string",
        default_value="Month",
        domain_type="list",
        allowed_values=["Month", "Quarter", "Year"],
    )
    editor.add_calculated_field(
        "Latest Month",
        "{FIXED : MAX(DATE(DATETRUNC('month', [Order Date])))}",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    for period in ("Month", "Quarter", "Year"):
        unit = period.lower()
        editor.add_calculated_field(
            period,
            f"IF DATETRUNC('{unit}', [Order Date]) = DATETRUNC('{unit}', [Latest Month]) THEN [Profit] END",
            datatype="real",
            default_format=MONEY,
        )
    editor.add_calculated_field(
        "Selected Profit",
        "CASE [Period] WHEN 'Month' THEN [Month] WHEN 'Quarter' THEN [Quarter] ELSE [Year] END",
        datatype="real",
        default_format=MONEY,
    )
    for name, direction in (("Top 5", "DESC"), ("Bottom 5", "ASC")):
        editor.add_set(
            name,
            "Sub-Category",
            basis_field="Selected Profit",
            aggregation="Sum",
            top_n=5,
            direction=direction,
        )
    editor.add_calculated_field(
        "Display Category",
        "IF [Top 5] OR [Bottom 5] THEN [Sub-Category] ELSE 'Everyone Else' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Performance Group",
        "IF [Top 5] THEN 'Top 5' ELSEIF [Bottom 5] THEN 'Bottom 5' ELSE 'Everything Else' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Average Profit",
        "SUM([Selected Profit])/COUNTD([Sub-Category])",
        datatype="real",
        default_format=MONEY,
    )
    editor.add_calculated_field("Zero", "0", datatype="real")
    for side, comparison in (("Left", "<"), ("Right", ">=")):
        editor.add_calculated_field(
            f"{side} Profit",
            f"IF [Average Profit] {comparison} 0 THEN [Average Profit] END",
            datatype="real",
            default_format=MONEY,
        )
        opposite = ">=" if comparison == "<" else "<"
        editor.add_calculated_field(
            f"{side} Category",
            f"IF [Average Profit] {opposite} 0 THEN ATTR([Display Category]) END",
            datatype="string",
            role="measure",
            field_type="nominal",
        )
    editor.add_worksheet("Period KPIs")
    editor.configure_chart(
        "Period KPIs",
        mark_type="Text",
        columns=["Measure Names"],
        measure_values=["SUM(Month)", "SUM(Quarter)", "SUM(Year)"],
        label_runs=[
            {"field": "Multiple Values", "fontsize": 24, "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Period KPIs",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        header_formats=[
            {"field": "Measure Names", "attr": "display", "value": "false"}
        ],
        pane_mark_style={"mark-labels-show": "true"},
    )
    editor.add_worksheet("Profit Performers")
    panes = []
    for side in ("Left", "Right"):
        panes.append(
            {
                "axis": "MIN(Zero)",
                "mark_type": "GanttBar",
                "size": "Average Profit",
                "color": "Performance Group",
                "labels": [f"{side} Profit", f"{side} Category"],
                "label_runs": [
                    {"field": f"{side} Profit", "fontsize": 10},
                    {"field": f"{side} Category", "fontsize": 10},
                ],
                "color_map": {
                    "Top 5": "#499894",
                    "Bottom 5": "#e15759",
                    "Everything Else": "#a0a0a0",
                },
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false", "size": "0.85"},
            }
        )
    editor.configure_layered_chart(
        "Profit Performers",
        columns=["MIN(Zero)", "MIN(Zero)"],
        rows=["Display Category"],
        axis_shelf="cols",
        panes=panes,
        synchronized=True,
        fold_axes=True,
        hide_axes=True,
        sort_field="Display Category",
        sort_descending="Average Profit",
        sort_mode="computed",
    )
    editor.configure_worksheet_style(
        "Profit Performers",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_label="Display Category",
        hide_row_field_labels=True,
        disable_tooltip=True,
        panes_style={
            "1": {
                "datalabel_style": {"text-align": "left", "vertical-align": "center"}
            },
            "2": {
                "datalabel_style": {"text-align": "right", "vertical-align": "center"}
            },
        },
    )
    editor.add_dashboard(
        "WW44 Profit Performers",
        width=700,
        height=800,
        worksheet_names=["Period KPIs", "Profit Performers"],
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "Top and Bottom Profit Performers",
                    "font_size": "20",
                    "bold": True,
                    "fixed_size": 52,
                },
                {
                    "type": "text",
                    "text": "Select Month, Quarter or Year to compare profit performance.",
                    "font_size": "11",
                    "fixed_size": 30,
                },
                {
                    "type": "worksheet",
                    "name": "Period KPIs",
                    "show_title": False,
                    "fit": "entire",
                    "fixed_size": 110,
                },
                {
                    "type": "worksheet",
                    "name": "Profit Performers",
                    "show_title": False,
                    "fit": "entire",
                    "weight": 1,
                },
                {
                    "type": "text",
                    "text": "Everyone Else = average profit per remaining sub-category.\n#WOW2021 W44 | Candra McRae | Rebuilt from Donna Coles' analysis",
                    "font_size": "9",
                    "fixed_size": 42,
                },
            ],
        },
    )
    editor.add_dashboard_action(
        "WW44 Profit Performers",
        action_type="parameter",
        source_sheet="Period KPIs",
        source_field="Measure Names",
        target_parameter="Period",
        event_type="on-select",
        aggregation="attr",
        clear_behavior="keep-current",
        clear_value="s:LROOT:",
        caption="Choose profit period",
    )
    output = HERE / "outputs" / "replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(output)
    return output


if __name__ == "__main__":
    print(build())
