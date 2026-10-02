"""Build the complete 2019 WW31 hub-and-spoke replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2019_07_31_WW31_WWPD_MusicData"
    / "2019_07_31_WW31_WWPD_MusicData.twbx"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"
DASHBOARD = "2019 WW31 Music Data Hub & Spoke"

MAPS = {
    "Routes — North & South America": ["North America", "South America"],
    "Routes — Europe": ["Europe"],
    "Routes — East Asia & Middle East": [
        "East Asia and Pacific",
        "Middle East",
    ],
}


def configure_hub_spoke(
    editor: TWBEditor,
    worksheet: str,
    regions: list[str],
) -> None:
    editor.add_worksheet(worksheet)
    editor.configure_chart(
        worksheet,
        mark_type="Map",
        geographic_field="Route",
        filters=[{"column": "Region", "values": regions}],
        map_layers=[
            {
                "geometry": "Route",
                "color": "Region",
                "size": "# Concerts",
                "detail": "Venue",
                "tooltip": ["Artist", "Concert", "Venue", "# Concerts"],
                "mark_sizing_off": True,
                "mark_size_value": "1.0214917659759521",
            },
            {
                "geometry": "Destination",
                "color": "Region",
                "detail": "Venue",
                "tooltip": ["Artist", "Concert", "Venue"],
                "mark_sizing_off": True,
                "mark_size_value": "7.7539858818054199",
                "has_stroke": True,
                "stroke_color": "#ffffff",
            },
        ],
        map_partition="Artist",
    )
    editor.configure_worksheet_style(
        worksheet,
        background_color="#2b2b2b",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
    )


def build(output_path: Path) -> Path:
    # Preserve the case-specific MusicData Hyper and all original spatial
    # calculations. Rebuild the complete analytical and interaction layer.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()

    for sheet, artist in (
        ("Ben Howard Summary", "Ben Howard"),
        ("Ed Sheeran Summary", "Ed Sheeran"),
    ):
        editor.add_worksheet(sheet)
        editor.configure_chart(
            sheet,
            mark_type="Text",
            rows=["Region"],
            color="Region",
            label="# Concerts",
            tooltip=["Artist", "# Concerts"],
            filters=[{"column": "Artist", "values": [artist]}],
            label_runs=[
                {"field": "# Concerts", "bold": True, "fontsize": "18"},
                {"text": "\u00c6\n"},
                {"field": "Region", "fontsize": "9"},
            ],
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
        )

    editor.add_worksheet("Monthly Concert Trend")
    editor.configure_chart(
        "Monthly Concert Trend",
        mark_type="Line",
        columns=["MONTH(Concert Date)"],
        rows=["# Concerts"],
        color="Artist",
        label="# Concerts",
        tooltip=["Artist", "# Concerts"],
    )
    editor.configure_worksheet_style(
        "Monthly Concert Trend",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
    )

    for worksheet, regions in MAPS.items():
        configure_hub_spoke(editor, worksheet, regions)

    editor.add_worksheet("Fellow Artist Word Cloud")
    editor.configure_chart(
        "Fellow Artist Word Cloud",
        mark_type="Text",
        color="Region",
        size="COUNT(Fellow Artist)",
        label="Fellow Artist",
        detail="Artist",
        tooltip=["Artist", "Fellow Artist"],
    )
    editor.configure_worksheet_style(
        "Fellow Artist Word Cloud",
        background_color="#ffffff",
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
                "text": "ED SHEERAN & BEN HOWARD — TOUR ROUTES",
                "font_size": "20",
                "bold": True,
                "fixed_size": 58,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "weight": 0.30,
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Ben Howard Summary",
                        "fit": "entire",
                        "weight": 0.28,
                    },
                    {
                        "type": "worksheet",
                        "name": "Monthly Concert Trend",
                        "fit": "entire",
                        "weight": 0.36,
                    },
                    {
                        "type": "worksheet",
                        "name": "Ed Sheeran Summary",
                        "fit": "entire",
                        "weight": 0.36,
                    },
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "weight": 0.31,
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Routes — North & South America",
                        "fit": "entire",
                    },
                    {
                        "type": "worksheet",
                        "name": "Routes — Europe",
                        "fit": "entire",
                    },
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "weight": 0.31,
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Fellow Artist Word Cloud",
                        "fit": "entire",
                    },
                    {
                        "type": "worksheet",
                        "name": "Routes — East Asia & Middle East",
                        "fit": "entire",
                    },
                ],
            },
            {
                "type": "text",
                "text": "#WorkoutWednesday 2019 Week 31",
                "font_size": "9",
                "fixed_size": 34,
            },
        ],
    }
    worksheets = [
        "Ben Howard Summary",
        "Ed Sheeran Summary",
        "Monthly Concert Trend",
        *MAPS,
        "Fellow Artist Word Cloud",
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=1800,
        layout=layout,
        worksheet_names=worksheets,
    )

    for source in ("Ben Howard Summary", "Ed Sheeran Summary"):
        editor.add_dashboard_action(
            dashboard_name=DASHBOARD,
            action_type="filter",
            source_sheet=source,
            target_sheet="Fellow Artist Word Cloud",
            fields=["Artist", "Region"],
            caption=f"Filter word cloud from {source}",
            event_type="on-hover",
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("2019-08-04-ww31-hub-spoke-map-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
