"""Build 48 grouped monthly bars from the locked, extracted raw sales data."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_06_03_WW23_Excel_Bars"
COLORS = {"2016": "#5557eb", "2017": "#d81159", "2018": "#fbb13c", "2019": "#19626b"}


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Sample - Superstore.hyper"))
    e.add_calculated_field(
        "Date Jitter",
        "CASE YEAR([Order Date]) WHEN 2016 THEN DATEADD('day',-9,DATETRUNC('month',[Order Date])) WHEN 2017 THEN DATEADD('day',-4,DATETRUNC('month',[Order Date])) WHEN 2018 THEN DATEADD('day',1,DATETRUNC('month',[Order Date])) WHEN 2019 THEN DATEADD('day',6,DATETRUNC('month',[Order Date])) END",
        datatype="datetime",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Date Normalised",
        "IF (YEAR([Date Jitter])=2015 OR YEAR([Date Jitter])=2016) AND MONTH([Date Jitter])=12 THEN MAKEDATE(2018,MONTH([Date Jitter]),DAY([Date Jitter])) ELSE MAKEDATE(2019,MONTH([Date Jitter]),DAY([Date Jitter])) END",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field("Tooltip:Sales", "[Sales]", datatype="real")
    e.set_field_format("Sales", 'c"\u00a3"#,##0,K;-"\u00a3"#,##0,K')
    e.set_field_format("Tooltip:Sales", 'c"\u00a3"#,##0;-"\u00a3"#,##0')
    e.add_calculated_field(
        "Plot Date",
        "[Date Normalised]",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.set_field_format("Plot Date", "*yyyy-mm-dd")
    e.set_datasource_color_palette("YEAR(Order Date)", COLORS)
    for sheet in ["Bars", "Dates", "Legend"]:
        e.add_worksheet(sheet)
    e.configure_layered_chart(
        "Bars",
        columns=["EXACTDATE(Date Normalised)"],
        rows=["SUM(Sales)"],
        panes=[
            {
                "mark_type": "Bar",
                "color": "YEAR(Order Date)",
                "detail": "MONTH(Order Date)",
                "tooltip": ["SUM(Tooltip:Sales)", "Plot Date"],
                "mark_sizing": {
                    "custom-mark-size-in-axis-units": 4.0,
                    "mark-alignment": "mark-alignment-left",
                    "mark-sizing-setting": "marks-scaling-on",
                    "use-custom-mark-size": True,
                },
                "mark_style": {"size": "1.5"},
            }
        ],
    )
    e.configure_worksheet_style(
        "Bars",
        hide_gridlines=False,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_sort_controls=True,
        label_formats=[{"field": "EXACTDATE(Date Normalised)", "text-format": "*mmm"}],
        axis_style={
            "stroke-color": "#333333",
            "tick-color": "#333333",
            "per_field": [
                {
                    "field": "EXACTDATE(Date Normalised)",
                    "scope": "cols",
                    "attr": "title",
                    "value": "",
                }
            ],
        },
    )
    e.configure_chart(
        "Dates",
        mark_type="Text",
        rows=[
            "YEAR(Order Date)",
            "MONTH(Order Date)",
            "Date Jitter",
            "Date Normalised",
        ],
        measure_values=["SUM(Sales)"],
    )
    e.configure_chart(
        "Legend",
        mark_type="Circle",
        columns=["YEAR(Order Date)"],
        color="YEAR(Order Date)",
        label="YEAR(Order Date)",
        mark_sizing_off=True,
    )
    e.configure_worksheet_style(
        "Legend",
        hide_axes=True,
        hide_row_label="YEAR(Order Date)",
        hide_col_field_labels=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        pane_mark_style={"size": "0.5157459", "mark-labels-show": "true"},
        pane_datalabel_style={"font-size": "10", "text-align": "right"},
    )

    def p(x, y, w, h):
        return {
            "x": round(x / 900 * 100000),
            "y": round(y / 500 * 100000),
            "w": round(w / 900 * 100000),
            "h": round(h / 500 * 100000),
        }

    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "CAN YOU EXCEL AT BAR CHARTS?",
                    "font_size": 14,
                    "font_alignment": "1",
                }
            ],
            "absolute": p(8, 8, 884, 30),
        },
        {
            "type": "worksheet",
            "name": "Legend",
            "show_title": False,
            "fit": "entire",
            "absolute": p(192, 38, 480, 60),
        },
        {
            "type": "worksheet",
            "name": "Bars",
            "show_title": False,
            "fit": "entire",
            "absolute": p(8, 98, 884, 330),
        },
    ]
    for text, x, w, alignment in [
        ("DESIGNED BY : LUKE STANKE", 8, 292, "0"),
        ("#WOW2020 | WEEK 23", 300, 300, "1"),
        ("RECREATED WITH CWTWB", 600, 292, "2"),
    ]:
        zones.append(
            {
                "type": "text",
                "runs": [
                    {
                        "text": text,
                        "font_size": 8,
                        "font_color": "#d81159",
                        "font_alignment": alignment,
                    }
                ],
                "absolute": p(x, 428, w, 32),
            }
        )
    zones.append(
        {
            "type": "text",
            "runs": [
                {
                    "text": "http://www.workout-wednesday.com/2020w23/",
                    "font_size": 8,
                    "font_alignment": "1",
                    "font_color": "#0000ff",
                }
            ],
            "absolute": p(8, 460, 884, 32),
        }
    )
    e.add_dashboard(
        DASHBOARD,
        width=900,
        height=500,
        worksheet_names=["Bars", "Legend"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    e.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(exist_ok=True)
    e.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
