"""Independent native logical tables preserve sales and monthly-goal grains."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_08_WW28_SalesvGoal_Relationships"
ACTUAL_TABLE = "Orders_62E6C5F2B15645379EECE2780C356F05"
GOAL_TABLE = "Sheet1_2F515896DFF04D7BBA0A3B18B0EE95A7"
COLORS = {
    "ON TRACK": "#59a14f",
    "NO COMPARISON": "#d3d3d3",
    "WAY OFF TRACK": "#e15759",
    "OFF TRACK": "#edc948",
}


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/federated_04hx3ys00s54am1dxildb1.hyper"),
        tables=[
            {"name": "Actual", "table": ACTUAL_TABLE},
            {"name": "Goals", "table": GOAL_TABLE},
        ],
        relationships=[
            {
                "left": "Actual",
                "right": "Goals",
                "keys": [
                    ["Segment", "Segment"],
                    ["Category", "Category"],
                    ["Month of Order Date", "Month of Order Date"],
                ],
            }
        ],
    )
    for parameter, default in [
        ("GREEN (WITHIN X%)", "0.1"),
        ("RED (ABOVE Y%)", "0.25"),
    ]:
        editor.add_parameter(
            parameter, default_value=default, domain_type="any", default_format="p0%"
        )
    for name, source, datatype in [
        ("SEGMENT", "Segment (Goals)", "string"),
        ("CATEGORY", "Category (Goals)", "string"),
        ("SUB-CATEGORY", "Sub-Category", "string"),
        ("MONTH", "Month of Order Date (Goals)", "date"),
    ]:
        editor.add_calculated_field(
            name,
            "[" + source + "]",
            datatype=datatype,
            role="dimension",
            field_type="ordinal" if datatype == "date" else "nominal",
        )
    editor.add_hierarchy("SEGMENT", ["SEGMENT", "CATEGORY", "SUB-CATEGORY"])
    editor.add_calculated_field(
        "Today",
        "#2019-07-01#",
        datatype="date",
        role="dimension",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "In Reporting Period",
        "YEAR([MONTH])<>2016",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "ACTUAL SALES", "IF DATETRUNC('month',[Order Date]) <= [Today] THEN [Sales] END"
    )
    editor.add_calculated_field(
        "# Sub-Cats", "ZN(COUNTD([SUB-CATEGORY]))", datatype="integer"
    )
    formulas = {
        "Max Sub-Cats in Window": "WINDOW_MAX([# Sub-Cats])",
        "At Lowest Level": "[# Sub-Cats]=1 AND [# Sub-Cats]=[Max Sub-Cats in Window]",
        "SALES GOAL": "IF [At Lowest Level] THEN 0 ELSE SUM([Goal]) END",
        "RESULT": "IF [At Lowest Level] THEN NULL ELSE SUM([ACTUAL SALES])-[SALES GOAL] END",
        "ACTUAL vs GOAL": "[RESULT]/SUM([ACTUAL SALES])",
        "Plot Goal": "IF [SALES GOAL]>0 THEN [SALES GOAL] END",
        "Records to Show": "IF [Max Sub-Cats in Window]=0 THEN FALSE ELSEIF [At Lowest Level] THEN ATTR([MONTH])<[Today] ELSEIF [# Sub-Cats]=0 AND [Max Sub-Cats in Window]=1 THEN FALSE ELSE TRUE END",
        "RAG": "IF ABS([ACTUAL vs GOAL])>[RED (ABOVE Y%)] THEN 'WAY OFF TRACK' ELSEIF ABS([ACTUAL vs GOAL])<[GREEN (WITHIN X%)] THEN 'ON TRACK' ELSEIF ATTR([MONTH])>=[Today] THEN 'NO COMPARISON' ELSEIF [SALES GOAL]=0 THEN 'NO COMPARISON' ELSE 'OFF TRACK' END",
    }
    for name, formula in formulas.items():
        datatype = (
            "boolean"
            if name in ["At Lowest Level", "Records to Show"]
            else "string"
            if name == "RAG"
            else "integer"
            if name == "Max Sub-Cats in Window"
            else "real"
        )
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            field_type="nominal"
            if datatype in ["boolean", "string"]
            else "quantitative",
            table_calc="Rows",
        )
    editor.add_calculated_field("One", "1", datatype="integer")
    editor.add_calculated_field(
        "vs Goal",
        "'vs Goal'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Trend Title",
        "'SEGMENT: ' + IF MIN({EXCLUDE [MONTH]: COUNTD([SEGMENT])})=1 THEN ATTR([SEGMENT]) ELSE 'All' END + ' | CATEGORY: ' + IF MIN({EXCLUDE [MONTH]: COUNTD([CATEGORY])})=1 THEN ATTR([CATEGORY]) ELSE 'All' END + ' | SUB-CATEGORY: ' + IF MIN({EXCLUDE [MONTH]: COUNTD([SUB-CATEGORY])})=1 THEN ATTR([SUB-CATEGORY]) ELSE 'All' END",
        datatype="string",
        field_type="nominal",
    )
    editor.set_field_format("MONTH", "*mmmm yyyy")
    editor.set_field_format("Today", "*mmm yyyy")
    for field in ["ACTUAL SALES", "Plot Goal"]:
        editor.set_field_format(field, 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("SALES GOAL", 'c"$"#,##0;-"$"#,##0;"NO GOAL"')
    editor.set_field_format("RESULT", "*↑#,##0;↓#,##0")
    editor.set_field_format("ACTUAL vs GOAL", "p0%")

    def dependencies(name):
        direct = {
            candidate
            for candidate in formulas
            if "[" + candidate + "]" in formulas[name]
        }
        return direct | {
            nested for candidate in direct for nested in dependencies(candidate)
        }

    overrides = {
        name: [{"ordering_type": "Field", "ordering_field": "[MONTH]"}]
        + [
            {"field": nested, "ordering_type": "Field", "ordering_field": "[MONTH]"}
            for nested in formulas
            if nested in dependencies(name)
        ]
        for name in formulas
    }
    common_filter = [{"column": "In Reporting Period", "values": [True]}]
    for sheet, row_fields, measures in [
        ("Table", ["SEGMENT", "[MONTH]"], ["SALES GOAL", "ACTUAL SALES", "RESULT"]),
        (
            "Data",
            ["SEGMENT", "CATEGORY", "SUB-CATEGORY", "[MONTH]", "Records to Show"],
            [
                "ACTUAL SALES",
                "SALES GOAL",
                "RESULT",
                "ACTUAL vs GOAL",
                "# Sub-Cats",
                "Max Sub-Cats in Window",
            ],
        ),
    ]:
        editor.add_worksheet(sheet)
        editor.configure_layered_chart(
            sheet,
            rows=row_fields,
            columns=["Measure Names"],
            panes=[
                {
                    "mark_type": "Text",
                    "label": "Multiple Values",
                    "measure_values": measures,
                    "detail_extra": [
                        "Max Sub-Cats in Window",
                        "At Lowest Level",
                        "Records to Show",
                    ],
                }
            ],
            filters=common_filter
            + (
                [{"column": "Records to Show", "values": [True]}]
                if sheet == "Table"
                else []
            ),
            table_calc_overrides={
                name: specifications
                for name, specifications in overrides.items()
                if name not in {"RAG", "Plot Goal"}
                and (name != "ACTUAL vs GOAL" or sheet == "Data")
            },
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_band_color=True,
            pane_cell_style={"font-size": "8"},
            cell_formats=[{"field": "MONTH", "height": "20"}, {"width": "110"}],
            header_formats=[
                {"field": "SEGMENT", "width": "110"},
                {"field": "MONTH", "width": "135"},
            ],
            table_formats=[
                {"attr": "width", "value": "120"},
                {"attr": "band-size", "scope": "rows", "value": "0"},
            ],
        )
        editor.set_measure_name_aliases(sheet, {field: field for field in measures})
    editor.set_worksheet_rich_title(
        "Table",
        [
            {"text": "MONTHLY SALES vs ", "fontsize": 12, "bold": True},
            {"text": "GOAL", "fontsize": 12, "bold": True, "fontcolor": "#e00071"},
            {"text": " DETAIL\n", "fontsize": 12, "bold": True},
            {"text": "USE [+] TO DRILL, CLICK TO FILTER ABOVE CHART", "fontsize": 8},
        ],
    )
    editor.add_worksheet("Line Graph")
    line_overrides = {
        name: [
            {
                **({"field": spec["field"]} if "field" in spec else {}),
                **(
                    {"ordering_type": "Field", "ordering_field": "EXACTDATE(MONTH)"}
                    if spec.get("field", name) == "Max Sub-Cats in Window"
                    else {"ordering_type": "Rows"}
                ),
            }
            for spec in specifications
        ]
        for name, specifications in overrides.items()
        if name
        in {"Plot Goal", "SALES GOAL", "At Lowest Level", "Max Sub-Cats in Window"}
    }
    editor.configure_layered_chart(
        "Line Graph",
        columns=["EXACTDATE(MONTH)"],
        rows=["Multiple Values"],
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Line",
                "color": "Measure Names",
                "color_map": {"ACTUAL SALES": "#333333", "Plot Goal": "#e00071"},
                "measure_values": ["ACTUAL SALES", "Plot Goal"],
                "detail_extra": [
                    "MIN(Today)",
                    "Trend Title",
                    "Max Sub-Cats in Window",
                    "At Lowest Level",
                    "SALES GOAL",
                ],
            }
        ],
        filters=common_filter,
        table_calc_overrides=line_overrides,
    )
    editor.configure_worksheet_style(
        "Line Graph",
        hide_borders=True,
        hide_gridlines=True,
        hide_col_field_labels=True,
        axis_style={"title": ""},
    )
    editor.set_measure_name_aliases("Line Graph", {"Plot Goal": "GOAL"})
    editor.set_worksheet_rich_title(
        "Line Graph",
        [
            {"text": "MONTHLY SALES vs ", "fontsize": 12, "bold": True},
            {"text": "GOAL", "fontsize": 12, "bold": True, "fontcolor": "#e00071"},
            {"text": " TREND\n", "fontsize": 12, "bold": True},
            {"text": "<Trend Title>", "fontsize": 9},
        ],
    )
    reference = editor.add_reference_line(
        "Line Graph",
        axis_field="EXACTDATE(MONTH)",
        value_field="MIN(Today)",
        formula="min",
        label_type="value",
    )
    editor.configure_reference_line_style(
        "Line Graph",
        reference.split("'")[1],
        {
            "stroke-color": "#000000",
            "line-pattern-only": "dotted",
            "fill-above": "#eeeeee",
        },
    )
    editor.add_worksheet("Barcode")
    editor.configure_layered_chart(
        "Barcode",
        columns=["[MONTH]"],
        rows=["vs Goal", "MIN(One)"],
        panes=[
            {
                "axis": "MIN(One)",
                "mark_type": "Bar",
                "color": "RAG",
                "color_map": COLORS,
                "detail_extra": [
                    "ACTUAL vs GOAL",
                    "RESULT",
                    "SALES GOAL",
                    "At Lowest Level",
                    "Max Sub-Cats in Window",
                ],
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "2.154696226",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                },
            }
        ],
        filters=common_filter,
        table_calc_overrides={
            name: [
                {"field": spec["field"], "ordering_type": "Rows"}
                if "field" in spec
                else {"ordering_type": "Rows"}
                for spec in specifications
            ]
            for name, specifications in overrides.items()
            if name not in {"Plot Goal", "Records to Show"}
        },
    )
    editor.configure_worksheet_style(
        "Barcode",
        hide_axes=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_borders=True,
        label_formats=[{"field": "[MONTH]", "display": "false"}],
        axis_style={
            "encodings": [
                {
                    "field": "MIN(One)",
                    "attr": "space",
                    "type": "space",
                    "scope": "rows",
                    "field-type": "quantitative",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                }
            ]
        },
    )
    editor.add_dashboard(
        DASHBOARD,
        width=800,
        height=900,
        worksheet_names=["Line Graph", "Barcode", "Table"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "horizontal",
                    "fixed_size": 58,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "ARE SALES ON TRACK WITH GOAL?",
                                    "font_size": 15,
                                    "font_alignment": "0",
                                    "font_color": "#000000",
                                    "bold": True,
                                }
                            ],
                            "fixed_size": 490,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "GREEN (WITHIN X%)",
                            "mode": "type_in",
                            "fixed_size": 150,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "RED (ABOVE Y%)",
                            "mode": "type_in",
                            "fixed_size": 150,
                        },
                    ],
                },
                {
                    "type": "empty",
                    "fixed_size": 4,
                    "style": {"background-color": "#000000", "margin": "0"},
                },
                {
                    "type": "worksheet",
                    "name": "Line Graph",
                    "fixed_size": 366,
                    "fit": "entire",
                },
                {
                    "type": "worksheet",
                    "name": "Barcode",
                    "fixed_size": 28,
                    "show_title": False,
                    "fit": "entire",
                },
                {
                    "type": "empty",
                    "fixed_size": 4,
                    "style": {"background-color": "#000000", "margin": "0"},
                },
                {"type": "worksheet", "name": "Table", "fit": "width"},
                {
                    "type": "text",
                    "text": "DESIGNED BY ANN JACKSON | #WOW2020 WEEK 28 | RECREATED WITH CWTWB",
                    "font_size": 8,
                    "font_color": "#d81159",
                    "fixed_size": 32,
                },
                {
                    "type": "text",
                    "text": "https://www.workout-wednesday.com/2020w28/",
                    "font_size": 8,
                    "fixed_size": 30,
                },
            ],
        },
    )
    for field in ["SEGMENT", "CATEGORY", "SUB-CATEGORY"]:
        editor.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet="Table",
            target_sheets=["Line Graph", "Barcode"],
            fields=[field],
            caption="Filter by " + field,
            event_type="on-select",
            clear_behavior="show-all",
        )
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
