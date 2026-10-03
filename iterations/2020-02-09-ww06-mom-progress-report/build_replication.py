"""Single-sheet dynamic month-over-month health report."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_02_05_WW06_Month_By_Month_Progress"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    editor.add_parameter(
        "Order Date MY Parameter",
        "date",
        "#2019-11-01#",
        domain_type="list",
        allowed_values=[
            f"#{year}-{month:02d}-01#"
            for year in range(2016, 2020)
            for month in range(1, 13)
        ],
        default_format="*mmmm yyyy",
    )
    for name, formula, datatype, role in [
        ("Order Date MY", "DATE(DATETRUNC('month',[Order Date]))", "date", "dimension"),
        ("Current Month", "[Order Date MY Parameter]", "date", "dimension"),
        (
            "Previous Month",
            "DATE(DATEADD('month',-1,[Current Month]))",
            "date",
            "dimension",
        ),
        ("Sub-Cat UPPER", "UPPER([Sub-Category])", "string", "dimension"),
    ]:
        editor.add_calculated_field(name, formula, datatype=datatype, role=role)
    for prefix, field in [("Sales", "Sales"), ("Qty", "Quantity")]:
        for when in ["Current", "Previous"]:
            editor.add_calculated_field(
                f"{prefix} {when} Month",
                f"IF [Order Date MY]=[{when} Month] THEN [{field}] END",
            )
        editor.add_calculated_field(
            f"% {prefix}",
            f"SUM([{prefix} Current Month])/SUM([{prefix} Previous Month])",
        )
    for when in ["Current", "Previous"]:
        editor.add_calculated_field(
            f"Orders {when} Month",
            f"COUNTD(IF [Order Date MY]=[{when} Month] THEN [Order ID] END)",
        )
    for name in ["Order Date MY", "Current Month", "Previous Month"]:
        editor.set_field_format(name, "*mmmm yyyy")
    for when in ["Current", "Previous"]:
        editor.set_field_format(f"Sales {when} Month", 'c"$"#,##0;-"$"#,##0')
    editor.add_calculated_field(
        "% Orders", "[Orders Current Month]/[Orders Previous Month]"
    )
    for prefix in ["Sales", "Orders", "Qty"]:
        editor.add_calculated_field(
            f"{prefix} Indicator",
            f"IF [% {prefix}] < 1 THEN 0 ELSE 1 END",
            datatype="integer",
            field_type="ordinal",
        )
        editor.set_field_format(f"% {prefix}", "p0%" if prefix == "Sales" else "p0.0%")
    editor.add_calculated_field(
        "Overall Score", "[Sales Indicator]+[Orders Indicator]+[Qty Indicator]"
    )
    editor.add_calculated_field("% Overall Score", "[Overall Score]/3")
    editor.set_field_format("% Overall Score", "p0%")
    editor.add_calculated_field(
        "Overall Indicator", "IF [% Overall Score]<1 THEN '●' END", datatype="string"
    )
    for name, value in [
        ("SALES", "MIN(1)"),
        ("ORDERS", "MIN(1)"),
        ("UNITS", "MIN(1)"),
        ("OVERALL", "MIN(0.5)"),
    ]:
        editor.add_calculated_field(name, value)
    editor.add_worksheet("Viz")
    panes = []
    for axis, prefix in [("SALES", "Sales"), ("ORDERS", "Orders"), ("UNITS", "Qty")]:
        panes.append(
            {
                "axis": axis,
                "mark_type": "Bar",
                "color": f"{prefix} Indicator",
                "color_map": {"1": "#01665e", "0": "#cdcecd"},
                "detail_extra": [
                    f"{prefix} Current Month",
                    f"{prefix} Previous Month",
                    f"% {prefix}",
                    "Current Month",
                    "Previous Month",
                ],
                "mark_sizing_off": True,
                "mark_style": {"size": "1.35", "has-stroke": "false"},
            }
        )
    panes.append(
        {
            "axis": "OVERALL",
            "mark_type": "Text",
            "labels": ["Overall Indicator", "% Overall Score"],
            "detail_extra": [
                "Overall Score",
                "Sales Indicator",
                "Orders Indicator",
                "Qty Indicator",
            ],
            "label_runs": [
                {"field": "Overall Indicator", "fontcolor": "#ff003b"},
                {"text": " "},
                {"field": "% Overall Score", "fontcolor": "#333333"},
            ],
            "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
        }
    )
    editor.configure_layered_chart(
        "Viz",
        columns=["SALES", "ORDERS", "UNITS", "OVERALL"],
        rows=["Sub-Cat UPPER"],
        axis_shelf="columns",
        fold_axes=False,
        panes=panes,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        table_dividers=[
            {
                "scope": "cols",
                "stroke-size": "3",
                "stroke-color": "#ffffff",
                "line-visibility": "on",
            },
            {"scope": "rows", "stroke-size": "0", "line-visibility": "off"},
        ],
        hide_band_color=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_sort_controls=True,
        pane_datalabel_style={"font-family": "Tableau Regular", "font-size": "12"},
        header_formats=[{"field": "Sub-Cat UPPER", "width": "144"}],
        label_formats=[
            {
                "field": "Sub-Cat UPPER",
                "font-family": "Tableau Regular",
                "font-size": "9",
                "font-weight": "bold",
                "color": "#333333",
            }
        ],
        axis_style={
            "encodings": [
                {
                    "field": name,
                    "scope": "cols",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": 0,
                    "max": 1 if name == "OVERALL" else 1.03,
                }
                for i, name in enumerate(["SALES", "ORDERS", "UNITS", "OVERALL"])
            ]
        },
    )
    editor.configure_worksheet_style(
        "Viz",
        panes_style={
            4: {
                "datalabel_style": {
                    "font-family": "Tableau Regular",
                    "font-size": "9",
                    "font-weight": "bold",
                }
            }
        },
    )
    for pane_index, prefix in enumerate(["Sales", "Orders", "Qty"]):
        metric_name = "Units" if prefix == "Qty" else prefix
        editor.configure_custom_tooltip(
            "Viz",
            pane_index=pane_index,
            runs=[
                {"field": "Sub-Cat UPPER", "bold": True},
                {"text": " | "},
                {"field": f"% {prefix}", "bold": True},
                {"text": " of prior month\n"},
                {"field": "Current Month"},
                {"text": f" {metric_name}: "},
                {"field": f"{prefix} Current Month", "bold": True},
                {"text": "\n"},
                {"field": "Previous Month"},
                {"text": f" {metric_name}: "},
                {"field": f"{prefix} Previous Month", "bold": True},
            ],
        )
    editor.configure_custom_tooltip(
        "Viz",
        pane_index=3,
        runs=[
            {"field": "Sub-Cat UPPER", "bold": True},
            {"text": "\n\n"},
            {"field": "% Overall Score"},
            {"text": " on track"},
        ],
    )

    def rect(x, y, w, h):
        return {
            "x": round(x / 600 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 600 * 100000),
            "h": round(h / 800 * 100000),
        }

    def text_zone(text, x, y, w, h, *, size=9, color="#333333", bold=True):
        return {
            "type": "text",
            "runs": [
                {"text": text, "font_size": size, "font_color": color, "bold": bold}
            ],
            "absolute": rect(x, y, w, h),
        }

    zones = [text_zone("MONTH OVER MONTH PROGRESS REPORT", 15, 20, 570, 30, size=15)]
    for caption, x in [
        ("SALES", 159),
        ("ORDERS", 267),
        ("UNITS", 375),
        ("OVERALL", 483),
    ]:
        zones.append(text_zone(caption, x, 60, 102, 28))
    zones.extend(
        [
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "entire",
                "absolute": rect(15, 92, 570, 590),
            },
            {
                "type": "paramctrl",
                "parameter": "Order Date MY Parameter",
                "show_title": False,
                "absolute": rect(210, 696, 180, 26),
            },
            text_zone(
                "DESIGNED BY : ANN JACKSON", 15, 735, 200, 22, size=8, color="#01665e"
            ),
            text_zone("#WOW2020 | WEEK 6", 215, 735, 170, 22, size=8, color="#01665e"),
            text_zone(
                "RECREATED WITH CWTWB", 385, 735, 200, 22, size=8, color="#01665e"
            ),
            text_zone(
                "http://www.workout-wednesday.com/2020w06/",
                80,
                768,
                440,
                23,
                size=8,
                color="#006080",
                bold=False,
            ),
        ]
    )
    editor.add_dashboard(
        DASHBOARD,
        width=600,
        height=800,
        worksheet_names=["Viz"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
