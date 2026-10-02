"""Build the complete 2019 WW31 hub-and-spoke replication with cwtwb."""

from pathlib import Path
import csv


ITERATION_DIR = Path(__file__).resolve().parent

from cwtwb.twb_editor import TWBEditor  # noqa: E402


HYPER = ITERATION_DIR / "inputs" / "2019_07_31_PD25_WWPD_MusicData_Output.hyper"
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
                "mark_size_value": "1.0214917659759521",
            },
            {
                "geometry": "Destination",
                "color": "Region",
                "detail": "Venue",
                "tooltip": ["Artist", "Concert", "Venue"],
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
        hide_col_field_labels=True,
        map_style={"map_style": "dark", "washout": 0},
        size_style={"field": "# Concerts", "max_size": "1", "min": "1", "min_size": "0.00251905", "type": "rangesize"},
        label_formats=[{"field": "Artist", "color": "#ffffff"}],
    )


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    editor.add_calculated_field("# Concerts", "COUNTD([ConcertID])", datatype="integer")
    editor.add_calculated_field("Route", "MAKELINE(MAKEPOINT([Hometown Latitude],[Hometown Longitude]), MAKEPOINT([Lat],[Long]))", datatype="spatial", role="measure", field_type="nominal")
    editor.add_calculated_field("Destination", "MAKEPOINT([Lat],[Long])", datatype="spatial", role="measure", field_type="nominal")
    # Group memberships extracted during analysis, not copied XML.
    clauses = []
    with (ITERATION_DIR / "inputs" / "region-members.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            location = row["Location"].replace("'", "''")
            region = row["Region"].replace("'", "''")
            clauses.append(f"WHEN '{location}' THEN '{region}'")
    editor.add_calculated_field("Region", "CASE [Location] " + " ".join(clauses) + " ELSE 'Other' END", datatype="string", role="dimension", field_type="nominal")

    editor.add_calculated_field("Concert Share", "COUNTD([ConcertID]) / TOTAL(COUNTD([ConcertID]))", default_format="p0%", table_calc="Rows")
    editor.add_calculated_field("Monthly Concert Date", "DATETRUNC('month',[Concert Date])", datatype="date", role="dimension", field_type="quantitative")
    editor.add_calculated_field("Cumulative Concerts", "RUNNING_SUM(COUNTD([ConcertID]))", table_calc="Rows")
    editor.add_calculated_field("Last Concert Month", "{FIXED [Artist]:MAX(DATETRUNC('month',[Concert Date]))}", datatype="date", role="dimension", field_type="quantitative")
    editor.add_calculated_field("Trend End Artist", "IF MIN([Monthly Concert Date])=MIN([Last Concert Month]) THEN ATTR([Artist]) END", datatype="string", role="measure", field_type="nominal")
    editor.add_calculated_field("Trend End Concerts", "IF MIN([Monthly Concert Date])=MIN([Last Concert Month]) THEN [Cumulative Concerts] END", datatype="integer", table_calc="Rows")
    editor.set_datasource_color_palette("Region", color_map={"East Asia and Pacific": "#e21d2e", "Europe": "#f5853d", "Middle East": "#aa790b", "North America": "#ebcd00", "South America": "#51a653"})
    for sheet, artist in (
        ("Ben Howard Summary", "Ben Howard"),
        ("Ed Sheeran Summary", "Ed Sheeran"),
    ):
        editor.add_worksheet(sheet)
        editor.configure_chart(
            sheet,
            mark_type="Text",
            columns=["Region"],
            color="Region",
            label="Concert Share",
            label_extra=["# Concerts"],
            tooltip=["Artist", "# Concerts"],
            filters=[{"column": "Artist", "values": [artist]}, {"column": "Region", "values": ["East Asia and Pacific", "Europe", "Middle East", "North America", "South America"]}],
            label_runs=[
                {"field": "Concert Share", "bold": True, "fontsize": "18"},
                {"text": "\u00c6\n"},
                {"field": "# Concerts", "fontsize": "9"},
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
        columns=["DAYTRUNC(Monthly Concert Date)"],
        rows=["Cumulative Concerts"],
        color="Artist",
        color_map={"Ben Howard": "#b3998e", "Ed Sheeran": "#ffffff"},
        label="Trend End Artist",
        label_extra=["Trend End Concerts"],
        label_runs=[{"field": "Trend End Artist", "bold": True}, {"text": "\u00c6\n"}, {"field": "Trend End Concerts", "bold": True}],
        tooltip=["Artist", "# Concerts"],
    )
    editor.configure_worksheet_style(
        "Monthly Concert Trend",
        pane_mark_style={"mark-labels-mode": "line-ends", "mark-labels-line-start": "false", "mark-labels-line-end": "true", "mark-labels-cull": "false"},
        pane_cell_style={"text-align": "right", "vertical-align": "top"},
        pane_datalabel_style={"font-weight": "bold", "color-mode": "match"},
        axis_style={"per_field": [
            {"field": "DAYTRUNC(Monthly Concert Date)", "attr": "display", "scope": "cols", "class": "0", "value": "true"},
            {"field": "DAYTRUNC(Monthly Concert Date)", "attr": "title", "scope": "cols", "class": "0", "value": ""},
            {"field": "Cumulative Concerts", "attr": "display", "scope": "rows", "class": "0", "value": "false"},
            {"attr": "line-visibility", "scope": "cols", "value": "off"},
            {"attr": "tick-color", "scope": "cols", "value": "#00000000"},
        ], "encodings": [{"field": "Cumulative Concerts", "scope": "rows", "class": "0", "range_type": "fixed", "min": 0, "max": 1200}]},
        label_formats=[{"field": "DAYTRUNC(Monthly Concert Date)", "color": "#ffffff", "text-format": "*yyyy"}],
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
        tooltip=["Artist", "Fellow Artist"],
    )
    editor.configure_worksheet_style(
        "Fellow Artist Word Cloud",
        background_color="#2b2b2b",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
    )

    # Independent declarative layout matches the author's 1600 x 900 canvas.
    layout = {"type": "container", "direction": "floating", "style": {"background-color": "#2b2b2b"}, "children": [
        {"type": "text", "text": "Ben Howard & Ed Sheeran\nTour History", "font_size": "24", "font_color": "#ffffff", "absolute": {"x": 30000, "y": 1000, "w": 29000, "h": 12000}},
        {"type": "worksheet", "name": "Ben Howard Summary", "show_title": False, "fit": "entire", "absolute": {"x": 1000, "y": 1000, "w": 28500, "h": 26500}},
        {"type": "worksheet", "name": "Ed Sheeran Summary", "show_title": False, "fit": "entire", "absolute": {"x": 59000, "y": 1000, "w": 40000, "h": 26500}},
        {"type": "worksheet", "name": "Monthly Concert Trend", "show_title": False, "fit": "entire", "absolute": {"x": 30500, "y": 14000, "w": 28500, "h": 16500}},
        {"type": "worksheet", "name": "Routes — North & South America", "show_title": False, "fit": "entire", "absolute": {"x": 1000, "y": 32000, "w": 48500, "h": 30000}},
        {"type": "worksheet", "name": "Routes — Europe", "show_title": False, "fit": "entire", "absolute": {"x": 57000, "y": 32000, "w": 42000, "h": 30000}},
        {"type": "worksheet", "name": "Routes — East Asia & Middle East", "show_title": False, "fit": "entire", "absolute": {"x": 57000, "y": 64000, "w": 42000, "h": 28500}},
        {"type": "worksheet", "name": "Fellow Artist Word Cloud", "show_title": False, "fit": "entire", "absolute": {"x": 1000, "y": 64000, "w": 48500, "h": 28500}},
        {"type": "text", "text": "DESIGNED BY: LORNA EDEN\nRECREATED BY: DONNA COLES", "font_size": "8", "font_color": "#ffffff", "absolute": {"x": 1000, "y": 94000, "w": 25000, "h": 5000}},
        {"type": "text", "text": "#WORKOUTWEDNESDAY | 2019 | WEEK 31", "font_size": "8", "font_color": "#ffffff", "absolute": {"x": 40000, "y": 94000, "w": 45000, "h": 5000}},
    ]}
    editor.add_dashboard(
        DASHBOARD,
        width=1600,
        height=900,
        layout=layout,
        worksheet_names=["Ben Howard Summary", "Ed Sheeran Summary", "Monthly Concert Trend", "Fellow Artist Word Cloud", *MAPS],
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

    for sheet in ["Ben Howard Summary", "Ed Sheeran Summary", "Monthly Concert Trend", "Fellow Artist Word Cloud"]:
        editor.configure_worksheet_style(sheet, background_color="#2b2b2b", hide_col_field_labels=True, hide_row_field_labels=True, hide_axes=sheet != "Monthly Concert Trend", hide_band_color=True, pane_datalabel_style={"color-mode": "match"}, label_formats=[{"field": "Region", "color": "#ffffff"}] if "Summary" in sheet else None)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("2019-08-04-ww31-hub-spoke-map-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
