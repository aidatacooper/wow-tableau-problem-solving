"""Build the complete WW04 dynamic moving-average replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent


from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_DIR = ITERATION_DIR / "outputs"
OUTPUT_TWB = OUTPUT_DIR / "2026-02-02-ww04-dynamic-moving-average-replicated-workbook.twb"
OUTPUT_TWBX = OUTPUT_DIR / "replicated-workbook.twbx"
HYPER = ITERATION_DIR / "inputs" / "federated_1yenh2r0raklpz16s6fvu0.hyper"


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_date_options(start_of_week="sunday")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    editor.add_parameter("pTimePortion", datatype="string", default_value="month", domain_type="list", allowed_values=["week", "month", "quarter"], alias="Month", allowed_aliases={"week": "Week", "month": "Month", "quarter": "Quarter"})
    editor.add_parameter("pMoveAvg", datatype="integer", default_value="3", min_value="3", max_value="12", granularity="3")
    editor.add_parameter("pTimeFrame", datatype="integer", default_value="24", min_value="12", max_value="36", granularity="6")
    editor.add_calculated_field("Display Date", "DATE(DATETRUNC([Parameters].[pTimePortion], [Order Date]))", datatype="date", role="dimension", field_type="ordinal")
    editor.add_calculated_field("Moving Average", "WINDOW_AVG(SUM([Sales]), -1*([Parameters].[pMoveAvg]-1), 0)", table_calc="Rows")
    editor.add_calculated_field("Latest Date", "WINDOW_MAX(MAX([Display Date]))", datatype="date", role="measure", field_type="ordinal", table_calc="Rows")
    editor.add_calculated_field("Date to Display", "MIN([Order Date]) > DATEADD([Parameters].[pTimePortion], -1*([Parameters].[pTimeFrame]), [Latest Date])", datatype="boolean", role="measure", field_type="nominal", table_calc="Rows")

    worksheet_name = "Dynamic Moving Average"
    editor.add_worksheet(worksheet_name)
    editor.configure_dual_axis(
        worksheet_name,
        mark_type_1="Line",
        mark_type_2="Line",
        columns=["DAYTRUNC(Display Date)"],
        rows=["SUM(Sales)", "Moving Average"],
        synchronized=True,
        filters=[
            {"column": "Date to Display", "values": [True], "ui_domain": "relevant"}
        ],
        show_labels=False,
        mark_color_1="#D3D3D3",
        mark_color_2="#4e79a7",
    )
    editor.set_worksheet_caption(
        worksheet_name,
        "Sales and trailing moving average by the selected date grain",
    )
    editor.configure_worksheet_style(
        worksheet_name,
        hide_borders=True,
        hide_gridlines=False,
        hide_zeroline=True,
        hide_table_dividers=True,
        axis_style={"per_field": [{"field": "Moving Average", "attr": "display", "scope": "rows", "class": "0", "value": "false"}, {"field": "DAYTRUNC(Display Date)", "attr": "title", "scope": "cols", "class": "0", "title_parameter": "pTimePortion"}]},
    )

    editor.set_worksheet_rich_title(worksheet_name, runs=[
        {"text": "Sales v ", "fontcolor": "#b7b7b7", "fontsize": 14, "fontalignment": "1"},
        {"text": "<[Parameters].[pMoveAvg]> <[Parameters].[pTimePortion]> Moving Average", "fontcolor": "#4e79a7", "fontsize": 14, "fontalignment": "1"},
        {"text": "\nShowing the last <[Parameters].[pTimeFrame]> <[Parameters].[pTimePortion]>s", "fontcolor": "#666666", "fontsize": 14, "fontalignment": "1"},
    ])
    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {"type": "text", "text": "Can you create a dynamic moving average chart?", "font_size": "18", "fixed_size": 58},
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 110,
                "children": [
                    {
                        "type": "paramctrl",
                        "parameter": "pTimePortion", "caption": "Select Date Timeframe",
                        "mode": "compact",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pMoveAvg", "caption": "Moving Average Selector",
                        "mode": "slider",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pTimeFrame", "caption": "Show Last X?",
                        "mode": "slider",
                    },
                ],
            },
            {
                "type": "worksheet",
                "name": worksheet_name,
                "show_title": True,
                "weight": 1,
                "fit": "entire",
            },
            {"type": "text", "text": "CHALLENGE BY: Lorna Brown                  #WOW2026 | WEEK 4                  RECREATED BY: Donna Coles", "font_size": "8", "fixed_size": 45},
            {"type": "text", "text": "https://www.workout-wednesday.com/2026w04tab/", "font_size": "8", "font_color": "#3093bb", "fixed_size": 25},
        ],
    }
    editor.add_dashboard(
        "Dynamic Moving Average Dashboard",
        width=800,
        height=800,
        layout=layout,
        worksheet_names=[worksheet_name],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Run deterministic local and cloud checks as separate evidence steps.
    # Avoid coupling artifact creation to ambient .env credentials.
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for path in (OUTPUT_TWB, OUTPUT_TWBX):
        print(build(path))
