"""Build the Measure Names lozenge chart from the locked Hyper extract."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_12_09_WW50_Measure_Names_Dot_Plot"


def zone(kind, x, y, w, h, **options):
    if kind == "text":
        options["runs"] = [
            {"text": options.pop("text"), "font_size": options.pop("font_size", 8)}
        ]
    return {"type": kind, "absolute": {"x": x, "y": y, "w": w, "h": h}, **options}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_044agg50zcziw71ecvscg1e946q4.hyper"))
    calculations = {
        "Cost": "SUM([Sales]) - SUM([Profit])",
        "Cost (copy)": "SUM([Sales]) - SUM([Profit])",
        "Is Profitable": "SUM([Profit])>0",
        "Label Profit is +ve": "IF [Is Profitable] THEN SUM([Profit]) END",
        "Label Profit is -ve": "IF NOT([Is Profitable]) THEN SUM([Profit]) END",
        "Row Center": "MIN(0)",
    }
    for name, formula in calculations.items():
        e.add_calculated_field(
            name,
            formula,
            datatype="boolean" if name == "Is Profitable" else "real",
            default_format='c"$"#,##0;-"$"#,##0'
            if name.startswith("Label")
            else 'c"$"#,##0;-"$"#,##0',
        )
    e.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Profit", 'c"$"#,##0;-"$"#,##0')
    for sheet in ("Data", "Viz"):
        e.add_worksheet(sheet)
    e.configure_chart(
        "Data",
        mark_type="Text",
        rows=["Sub-Category"],
        columns=["Measure Names"],
        measure_values=["SUM(Sales)", "AGG(Cost)", "SUM(Profit)"],
        sort_descending="SUM(Profit)",
    )
    measures = ["AGG(Cost)", "SUM(Sales)", "AGG(Cost (copy))"]
    e.configure_layered_chart(
        "Viz",
        columns=["Multiple Values", "Multiple Values"],
        rows=["Sub-Category", "AGG(Row Center)"],
        axis_shelf="columns",
        synchronized=True,
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Circle",
                "measure_values": measures,
                "color": "Measure Names",
                "color_extra": ["AGG(Is Profitable)"],
                "size": "Measure Names",
                "label": "AGG(Label Profit is +ve)",
                "tooltip": ["SUM(Profit)"],
                "mark_sizing_off": True,
                "cell_style": {"text-align": "right", "vertical-align": "center"},
                "mark_style": {
                    "size": "0.55972373485565186",
                    "has-stroke": "false",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "range",
                    "mark-labels-range-field": "Measure Names",
                    "mark-labels-range-min": "true",
                    "mark-labels-range-max": "false",
                    "mark-labels-range-scope": "pane",
                },
            },
            {
                "axis": "Multiple Values",
                "mark_type": "Line",
                "measure_values": measures,
                "color": "AGG(Is Profitable)",
                "color_map": {True: "#b0e498", False: "#f690b5"},
                "label": "AGG(Label Profit is -ve)",
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "6.5326151847839355",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "line-ends",
                    "mark-labels-line-first": "true",
                    "mark-labels-line-last": "false",
                },
            },
        ],
        sort_descending="SUM(Profit)",
        sort_field="Sub-Category",
        sort_mode="computed",
        fold_axes=True,
    )
    mappings = []
    for measure in measures:
        for profitable in (True, False):
            color = (
                ("#004500" if profitable else "#8f2d56")
                if measure == "SUM(Sales)"
                else ("#ffffff" if measure == "AGG(Cost)" else "#5c6068")
            )
            mappings.append({"values": [measure, profitable], "color": color})
    e.set_compound_color_palette(["Measure Names", "AGG(Is Profitable)"], mappings)
    e.configure_worksheet_style(
        "Viz",
        background_color="#f5f5f5",
        hide_row_field_labels=True,
        hide_table_dividers=True,
        axis_style={
            "encodings": [
                {
                    "field": "Multiple Values",
                    "scope": "cols",
                    "class": "0",
                    "attr": "space",
                    "type": "space",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": -21238.05648853755,
                    "max": 399000,
                }
            ],
            "per_field": [
                {
                    "field": "Multiple Values",
                    "scope": "cols",
                    "class": "1",
                    "attr": "title",
                    "value": "Cost & Profit",
                },
                {
                    "field": "AGG(Row Center)",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "Multiple Values",
                    "scope": "cols",
                    "class": "0",
                    "attr": "title",
                    "value": "Cost & Profit",
                },
            ],
            "render-fold-reversed": "true",
        },
        label_formats=[
            {"scope": "rows", "text-align": "right"},
            {"field": "Sub-Category", "font-size": 12},
            {
                "field": "Multiple Values",
                "font-size": 8,
                "text-format": 'c"$"#,##0;-"$"#,##0',
            },
        ],
        size_style={
            "type": "catsize",
            "field": "Measure Names",
            "min_size": 0.875774,
            "max_size": 1,
        },
        header_formats=[{"field": "Sub-Category", "width": 144}],
        gridline_style={
            "cols": {"stroke-color": "#d4d4d4"},
            "rows": {"stroke-color": "#d4d4d4"},
        },
    )
    e.configure_worksheet_style(
        "Viz",
        panes_style={
            1: {"cell_style": {"text-align": "right", "vertical-align": "center"}},
            2: {"cell_style": {"text-align": "auto", "vertical-align": "center"}},
        },
    )
    children = [
        zone(
            "text",
            2500,
            2222,
            95000,
            8778,
            text="Can you highlight profits with measure names?",
            font_size=15,
        ),
        zone(
            "worksheet",
            2500,
            11000,
            95000,
            79667,
            name="Viz",
            show_title=False,
            fit="entire",
        ),
        zone(
            "text",
            2500,
            90667,
            31666,
            3555,
            text="DESIGNED BY : LUKE STANKE",
            font_size=8,
        ),
        zone(
            "text", 34166, 90667, 31668, 3555, text="#WOW2020  |  WEEK 50", font_size=8
        ),
        zone(
            "text", 65834, 90667, 31666, 3555, text="RECREATED WITH CWTWB", font_size=8
        ),
        zone(
            "text",
            2500,
            94222,
            95000,
            3556,
            text="http://www.workout-wednesday.com/2020w50/",
            font_size=8,
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=900,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"background-color": "#f5f5f5"},
            "children": children,
        },
    )
    (HERE / "outputs").mkdir(exist_ok=True)
    output = HERE / "outputs/replicated-workbook.twbx"
    e.set_window_state("Data", hidden=False, zoom_entire_view=True)
    e.set_window_state("Viz", hidden=False, zoom_entire_view=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
