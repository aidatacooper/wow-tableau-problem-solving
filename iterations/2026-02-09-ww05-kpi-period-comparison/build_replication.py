"""Build the WW05 KPI period-comparison replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_DIR = ITERATION_DIR / "outputs"
SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2026_02_04_WW05_KPI_Trend_Monitor_With_Period_Comparison"
    / "2026_02_04_WW05_KPI_Trend_Monitor_With_Period_Comparison.twbx"
)


def build(output_path: Path) -> Path:
    # Preserve the challenge's packaged Hyper datasource and semantic fields.
    # Rebuild the worksheets and dashboard independently on that original data.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()

    period_filter = [
        {
            "column": "Recent | Prior  Mth | Prior Yr",
            "values": ["Recent", "Prior Month", "Prior Year"],
        }
    ]
    editor.add_worksheet("Period Trend")
    editor.configure_dual_axis(
        "Period Trend",
        mark_type_1="Line",
        mark_type_2="Line",
        columns=["X-Axis"],
        rows=["PR - Not Recent", "PR - Recent"],
        color_1="Recent | Prior  Mth | Prior Yr",
        color_2="Recent | Prior  Mth | Prior Yr",
        synchronized=True,
        filters=period_filter,
        show_labels=False,
        color_map_1={
            "Recent": "#1F77B4",
            "Prior Month": "#9E9E9E",
            "Prior Year": "#D0D0D0",
        },
    )
    editor.set_worksheet_caption(
        "Period Trend",
        "Profit ratio aligned by relative day for recent, prior month, and prior year",
    )
    editor.configure_worksheet_style(
        "Period Trend",
        hide_gridlines=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_zeroline=True,
    )

    editor.add_worksheet("KPI Summary")
    editor.configure_chart(
        "KPI Summary",
        mark_type="Text",
        label="PR - Today",
        label_extra=[
            "PR Difference",
            "PR Direction Up",
            "PR Direction Down",
        ],
        label_runs=[
            {"field": "PR - Today", "fontsize": 28, "bold": True},
            {"text": "\n"},
            {"field": "PR Difference", "fontsize": 16},
            {"text": " "},
            {"field": "PR Direction Up", "fontsize": 16},
            {"field": "PR Direction Down", "fontsize": 16},
        ],
    )
    editor.set_worksheet_caption(
        "KPI Summary",
        "Latest profit ratio and change from the previous day",
    )
    editor.configure_worksheet_style(
        "KPI Summary",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        hide_table_dividers=True,
    )

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 220,
                "children": [
                    {"type": "worksheet", "name": "KPI Summary", "weight": 2},
                    {
                        "type": "paramctrl",
                        "parameter": "pToday",
                        "mode": "compact",
                        "weight": 1,
                    },
                ],
            },
            {
                "type": "worksheet",
                "name": "Period Trend",
                "weight": 3,
                "fit": "entire",
            },
        ],
    }
    editor.add_dashboard(
        "KPI Trend Monitor",
        width=900,
        height=700,
        layout=layout,
        worksheet_names=["KPI Summary", "Period Trend"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
