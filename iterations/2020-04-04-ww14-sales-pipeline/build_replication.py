"""Rebuild stage totals, cumulative funnel and closed ratios through public APIs."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_04_01_WW14_Sales_Pipeline_Funnel"
STAGES = ["Prospect", "Lead", "Qualified", "Opportunity", "Negotiations", "Closed"]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/2020_04_01_WW14_sales_funnel_data.hyper"))
    e.add_calculated_field(
        "last_stage order",
        "CASE [last_stage] WHEN 'Prospect' THEN 1 WHEN 'Lead' THEN 2 WHEN 'Qualified' THEN 3 WHEN 'Opportunity' THEN 4 WHEN 'Negotiations' THEN 5 ELSE 6 END",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Running Sum",
        "RUNNING_SUM(SUM([value]))",
        datatype="integer",
        table_calc="Columns",
    )
    e.add_calculated_field(
        "Window Sum",
        "WINDOW_SUM(SUM([value]))",
        datatype="integer",
        table_calc="Columns",
    )
    e.add_calculated_field(
        "Cumulative Value",
        "[Window Sum]-([Running Sum]-SUM([value]))",
        datatype="integer",
        table_calc="Columns",
    )
    e.add_calculated_field(
        "Closed Value",
        "{FIXED:SUM(IF [last_stage order]=6 THEN [value] END)}",
        datatype="integer",
    )
    e.add_calculated_field(
        "% To Close",
        "SUM([Closed Value])/[Cumulative Value]",
        datatype="real",
        table_calc="Columns",
    )
    e.add_calculated_field("Full Bar", "MIN(1)", datatype="integer")
    for f in ["value", "Running Sum", "Window Sum", "Cumulative Value", "Closed Value"]:
        e.set_field_format(f, 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("% To Close", "p0%")
    for name in ["Data", "Current Status", "Overall Funnel", "Percent to Close"]:
        e.add_worksheet(name)
    rows = ["last_stage order", "last_stage"]
    override = {
        "Cumulative Value": [
            {"ordering-type": "Columns"},
            {"field": "Running Sum", "ordering-type": "Columns"},
            {"field": "Window Sum", "ordering-type": "Columns"},
        ],
        "% To Close": [
            {"ordering-type": "Columns"},
            {"field": "Cumulative Value", "ordering-type": "Columns"},
            {"field": "Running Sum", "ordering-type": "Columns"},
            {"field": "Window Sum", "ordering-type": "Columns"},
        ],
    }
    for name, field in [
        ("Current Status", "SUM(value)"),
        ("Overall Funnel", "Cumulative Value"),
    ]:
        e.configure_layered_chart(
            name,
            columns=[field],
            rows=rows,
            axis_shelf="columns",
            panes=[
                {
                    "axis": field,
                    "mark_type": "Bar",
                    "label": field,
                    "mark_sizing_off": True,
                    "mark_style": {
                        "mark-color": "#00646d",
                        "size": "0.7136464",
                        "mark-labels-show": "true",
                    },
                    "label_runs": [{"field": field, "fontsize": 8}],
                }
            ],
            hide_axes=True,
            table_calc_overrides={field: override[field]}
            if field in override
            else None,
        )
    e.configure_dual_axis(
        "Percent to Close",
        columns=["% To Close", "Full Bar"],
        rows=rows,
        dual_axis_shelf="columns",
        mark_type_1="Bar",
        mark_type_2="Bar",
        mark_color_1="#00646d",
        mark_color_2="#7cadb2",
        size_value_1="0.7136464",
        size_value_2="0.7136464",
        label_1="% To Close",
        show_labels=False,
        hide_axes=True,
        mark_sizing_off=True,
        synchronized=True,
        table_calc_overrides={"% To Close": override["% To Close"]},
    )
    for sheet, field, maximum in [
        ("Current Status", "SUM(value)", 1132200),
        ("Overall Funnel", "Cumulative Value", 2711124),
    ]:
        e.configure_worksheet_style(
            sheet,
            axis_style={
                "encodings": [
                    {
                        "field": field,
                        "scope": "cols",
                        "type": "space",
                        "attr": "space",
                        "class": "0",
                        "field-type": "quantitative",
                        "range-type": "fixed",
                        "min": 0,
                        "max": maximum,
                    }
                ]
            },
        )
    e.configure_worksheet_style(
        "Percent to Close",
        panes_style={
            "2": {"mark_style": {"mark-labels-show": "false"}},
            "1": {
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
                "datalabel_style": {
                    "font-size": "8",
                    "color-mode": "user",
                    "color": "#ffffff",
                    "text-align": "left",
                },
            },
        },
        axis_style={
            "render-fold-reversed": "true",
            "per_field": [
                {
                    "field": field,
                    "scope": "cols",
                    "class": str(cls),
                    "attr": "display",
                    "value": "false",
                }
                for field in ["Full Bar", "% To Close"]
                for cls in [0, 1]
            ],
        },
    )
    e.configure_layered_chart(
        "Data",
        rows=rows,
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    "SUM(value)",
                    "Running Sum",
                    "Window Sum",
                    "Cumulative Value",
                    "SUM(Closed Value)",
                    "% To Close",
                ],
                "mark_style": {"mark-labels-show": "true"},
            }
        ],
        table_calc_overrides=override,
    )
    for sheet in ["Data", "Current Status", "Overall Funnel", "Percent to Close"]:
        e.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=(sheet == "Data"),
            hide_col_field_labels=True,
            hide_row_field_labels=True,
            hide_sort_controls=True,
            hide_row_label="last_stage order",
            disable_tooltip=True,
        )
    for sheet in ["Overall Funnel", "Percent to Close"]:
        e.configure_worksheet_style(sheet, hide_row_label="last_stage")
    for sheet in ["Current Status", "Overall Funnel", "Percent to Close"]:
        e.configure_worksheet_style(
            sheet,
            label_formats=[{"field": "last_stage", "font-size": "8"}],
            cell_formats=[{"field": "last_stage", "height": "44"}],
            header_formats=[{"field": "last_stage", "width": "96"}],
            table_dividers=[
                {
                    "scope": "rows",
                    "line-visibility": "on",
                    "line-pattern-only": "solid",
                    "stroke-size": "1",
                    "stroke-color": "#cccccc",
                }
            ],
        )

    def p(x, y, w, h):
        return {
            "x": round(x / 700 * 100000),
            "y": round(y / 400 * 100000),
            "w": round(w / 700 * 100000),
            "h": round(h / 400 * 100000),
        }

    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "WEEK 14: HOW DOES THE SALES PIPELINE LOOK?",
                    "font_color": "#333333",
                    "font_size": 12,
                    "font_alignment": "1",
                }
            ],
            "absolute": p(8, 8, 684, 30),
        }
    ]
    for text, x, w in [
        ("Current Status", 104, 190),
        ("Overall Funnel", 294, 198),
        ("Percent to Close", 492, 198),
    ]:
        zones.append(
            {
                "type": "text",
                "runs": [
                    {"text": text.upper(), "font_color": "#333333", "font_size": 8}
                ],
                "absolute": p(x, 38, w, 30),
            }
        )
    for sheet, x, w in [
        ("Current Status", 8, 286),
        ("Overall Funnel", 294, 198),
        ("Percent to Close", 492, 198),
    ]:
        zones.append(
            {
                "type": "worksheet",
                "name": sheet,
                "fit": "entire",
                "show_title": False,
                "absolute": p(x, 68, w, 264),
            }
        )
    zones += [
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2020 | WEEK 14 | DESIGNED BY LUKE STANKE | RECREATED WITH CWTWB",
                    "font_color": "#00646d",
                    "font_size": 8,
                }
            ],
            "absolute": p(8, 332, 684, 28),
        },
        {
            "type": "text",
            "text": "http://www.workout-wednesday.com/2020w14/",
            "absolute": p(150, 360, 500, 30),
        },
    ]
    e.add_dashboard(
        DASHBOARD,
        width=700,
        height=400,
        worksheet_names=["Current Status", "Overall Funnel", "Percent to Close"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    e.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(exist_ok=True)
    e.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
