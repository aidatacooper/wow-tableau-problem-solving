"""Build the complete 2019 WW29 higher-orders replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2019_07_17_WW29_HighOrders"
    / "2019_07_17_WW29_HighOrders.twbx"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"


def build(output_path: Path) -> Path:
    # Preserve the challenge's original datasource, calculations, connection,
    # and bundled Hyper extract. Rebuild all worksheets and dashboards.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()

    worksheet = "Higher Orders by Month"
    editor.add_worksheet(worksheet)
    editor.configure_chart(
        worksheet,
        mark_type="GanttBar",
        columns=["MONTH(Order Date)"],
        rows=["Segment", "AGG(Avg Orders Per Day Per Segment Per Month)"],
        color="AGG(COLOUR:Difference)",
        size="AGG(Difference)",
        label="AGG(% Difference)",
        detail="AGG(Overall Avg Orders Per Day Per Segment)",
        tooltip=[
            "AGG(Avg Orders Per Day Per Segment Per Month)",
            "AGG(Overall Avg Orders Per Day Per Segment)",
            "AGG(Difference)",
        ],
        color_map={"green": "#4E9F3D", "blue": "#2D7DD2"},
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
    )

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "text": "Which months have the higher number of orders?",
                "font_size": "20",
                "bold": True,
                "fixed_size": 70,
            },
            {
                "type": "worksheet",
                "name": worksheet,
                "fit": "entire",
                "weight": 1,
            },
            {
                "type": "text",
                "text": "#WorkoutWednesday | 2019 | Week 29",
                "font_size": "9",
                "fixed_size": 40,
            },
        ],
    }
    editor.add_dashboard(
        "WW29 Higher Orders",
        width=1100,
        height=720,
        layout=layout,
        worksheet_names=[worksheet],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
