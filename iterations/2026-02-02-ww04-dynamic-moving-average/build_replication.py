"""Build the complete WW04 dynamic moving-average replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_DIR = ITERATION_DIR / "outputs"
OUTPUT_TWB = OUTPUT_DIR / "2026-02-02-ww04-dynamic-moving-average-replicated-workbook.twb"
OUTPUT_TWBX = OUTPUT_DIR / "2026-02-02-ww04-dynamic-moving-average-replicated-workbook.twbx"
SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2026_01_27_WW04_Moving_Average"
    / "2026_01_27_WW04_Moving_Average.twbx"
)


def build(output_path: Path) -> Path:
    # Preserve the challenge's datasource, connection, fields, parameters, and
    # packaged Hyper extract; rebuild only the analytical presentation.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()

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
        mark_color_1="#B7B7B7",
        mark_color_2="#E15759",
    )
    editor.set_worksheet_caption(
        worksheet_name,
        "Sales and trailing moving average by the selected date grain",
    )
    editor.configure_worksheet_style(
        worksheet_name,
        hide_borders=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
    )

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 110,
                "children": [
                    {
                        "type": "paramctrl",
                        "parameter": "pTimePortion",
                        "mode": "compact",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pTimeFrame",
                        "mode": "slider",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pMoveAvg",
                        "mode": "slider",
                    },
                ],
            },
            {
                "type": "worksheet",
                "name": worksheet_name,
                "weight": 1,
                "fit": "entire",
            },
        ],
    }
    editor.add_dashboard(
        "Dynamic Moving Average Dashboard",
        width=1000,
        height=700,
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
