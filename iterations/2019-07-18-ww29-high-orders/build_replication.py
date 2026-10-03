"""Build the complete 2019 WW29 higher-orders replication with cwtwb."""

from pathlib import Path
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    # Formulas transcribed during analysis; no author workbook at build time.
    calculations = [
        ("Count Orders per Segment", "{FIXED [Segment]: COUNTD([Order ID])}"),
        ("Count Days Per Segment", "{FIXED [Segment]: COUNTD([Order Date])}"),
        (
            "Count Orders per Segment per Month",
            "{FIXED [Segment], MONTH([Order Date]): COUNTD([Order ID])}",
        ),
        (
            "Count Days Per Segment Per Month",
            "{FIXED [Segment], MONTH([Order Date]): COUNTD([Order Date])}",
        ),
        (
            "Overall Avg Orders Per Day Per Segment",
            "SUM([Count Orders per Segment]) / SUM([Count Days Per Segment])",
        ),
        (
            "Avg Orders Per Day Per Segment Per Month",
            "SUM([Count Orders per Segment per Month]) / SUM([Count Days Per Segment Per Month])",
        ),
        (
            "Difference",
            "[Avg Orders Per Day Per Segment Per Month] - [Overall Avg Orders Per Day Per Segment]",
        ),
        ("% Difference", "[Difference] / [Overall Avg Orders Per Day Per Segment]"),
    ]
    for name, formula in calculations:
        editor.add_calculated_field(
            name,
            formula,
            default_format="*+0%;-0%"
            if name == "% Difference"
            else "n#,##0.00;-#,##0.00",
        )
    editor.add_calculated_field(
        "COLOUR:Difference",
        "IF [Difference]>=0 THEN 'green' ELSE 'blue' END",
        datatype="string",
        role="measure",
    )

    editor.add_calculated_field("Gantt Size", "-[Difference]")

    worksheet = "Higher Orders by Month"
    editor.add_worksheet(worksheet)
    editor.configure_chart(
        worksheet,
        mark_type="GanttBar",
        columns=["MONTH(Order Date)"],
        rows=["Segment", "AGG(Avg Orders Per Day Per Segment Per Month)"],
        color="AGG(COLOUR:Difference)",
        size="AGG(Gantt Size)",
        label="AGG(% Difference)",
        detail="AGG(Overall Avg Orders Per Day Per Segment)",
        tooltip=[
            "AGG(Avg Orders Per Day Per Segment Per Month)",
            "AGG(Overall Avg Orders Per Day Per Segment)",
            "AGG(Difference)",
        ],
        color_map={"green": "#d9ba13", "blue": "#1ba3c6"},
    )
    editor.add_reference_line(
        worksheet,
        axis_field="AGG(Avg Orders Per Day Per Segment Per Month)",
        value_field="AGG(Overall Avg Orders Per Day Per Segment)",
        scope="per-pane",
        formula="average",
        label_type="value",
        tooltip="Overall average orders per day = <Value>",
    )
    editor.set_worksheet_caption(
        worksheet,
        "Monthly average orders per day compared with each segment's overall average",
    )
    editor.configure_worksheet_style(
        worksheet,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        pane_cell_style={"vertical-align": "center"},
        pane_datalabel_style={"color-mode": "auto"},
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[
            {"field": "MONTH(Order Date)", "text-format": "iLLL"},
            {
                "field": "AGG(Avg Orders Per Day Per Segment Per Month)",
                "text-format": "n0.0",
            },
        ],
        axis_style={
            "encodings": [
                {
                    "field": "AGG(Avg Orders Per Day Per Segment Per Month)",
                    "scope": "rows",
                    "class": "0",
                    "range_type": "independent",
                    "domain_expand": False,
                }
            ],
            "per_field": [
                {
                    "field": "AGG(Avg Orders Per Day Per Segment Per Month)",
                    "attr": "title",
                    "scope": "rows",
                    "class": "0",
                    "value": "",
                }
            ],
        },
    )

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "runs": [
                    {
                        "text": "WEEK 29: ",
                        "bold": True,
                        "font_size": "14",
                        "font_color": "#1ba3c6",
                        "font_alignment": "1",
                    },
                    {
                        "text": "Which months do we see a higher number of orders?",
                        "font_size": "14",
                        "font_color": "#1ba3c6",
                        "font_alignment": "1",
                    },
                ],
                "font_size": "14",
                "font_color": "#1ba3c6",
                "bold": True,
                "fixed_size": 48,
            },
            {
                "type": "worksheet",
                "name": worksheet,
                "show_title": False,
                "fit": "entire",
                "weight": 1,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 40,
                "children": [
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "DESIGNED BY: @LukeStanke",
                                "font_size": "8",
                                "font_color": "#1ba3c6",
                                "font_alignment": "0",
                            }
                        ],
                        "weight": 1,
                    },
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "#WORKOUTWEDNESDAY | 2019 | WEEK 29\n",
                                "font_size": "8",
                                "font_color": "#1ba3c6",
                                "font_alignment": "1",
                            },
                            {
                                "text": "http://www.workout-wednesday.com/2019-w29/",
                                "font_size": "8",
                                "font_alignment": "1",
                                "hyperlink": "http://www.workout-wednesday.com/2019-w29/",
                            },
                        ],
                        "weight": 2,
                    },
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "RECREATED BY: @donnacoles30",
                                "font_size": "8",
                                "font_color": "#1ba3c6",
                                "font_alignment": "2",
                            }
                        ],
                        "weight": 1,
                    },
                ],
            },
        ],
    }
    editor.add_dashboard(
        "WW29 Higher Orders",
        width=900,
        height=600,
        layout=layout,
        worksheet_names=[worksheet],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2019-07-18-ww29-high-orders-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
