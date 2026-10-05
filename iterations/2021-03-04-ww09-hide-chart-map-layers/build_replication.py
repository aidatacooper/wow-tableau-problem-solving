"""Build country drill-down and an urban-share donut with native map layers."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_03_03_WW09_Map_Layers_Drill_Down"
REGIONS = {
    "Africa": "#025663",
    "Middle East": "#22707d",
    "Asia": "#4d806b",
    "The Americas": "#5a5177",
    "Oceania": "#959c9e",
    "Europe": "#b19a25",
}
BACKGROUND_LAYERS = [
    "background",
    "barrier_line-land-polygon",
    "barrier_line-land-line",
    "national_park",
    "pitch",
    "industrial",
    "built-up-area",
    "water",
    "waterway-river-canal",
    "aeroway-polygon",
    "aeroway-runway",
    "aeroway-taxiway",
    "parks",
    "landcover_wood",
    "landcover_scrub",
    "landcover_grass",
    "landcover_crop",
    "admin-0-boundaries-bg-sub",
    "admin-1-boundaries-supress-bg",
    "admin-1-boundaries-sm-parents-bg",
    "admin-1-boundaries-md-parents-bg",
    "admin-1-boundaries-lg-parents-bg",
    "admin-0-boundaries-dispute-sub",
    "admin-0-boundaries-sub",
    "admin-1-boundaries-supress",
    "admin-1-boundaries-sm-parents",
    "admin-1-boundaries-md-parents",
    "admin-1-boundaries-lg-parents",
    "admin1-water-lines-usa-tableau",
    "9-dash-line-casing",
    "9-dash-line",
    "admin-1-label-9th-tier",
    "admin-1-label-8th-tier",
    "admin-1-label-7th-tier",
    "admin-1-label-6th-tier",
    "admin-1-label-5th-tier",
    "admin-1-label-4th-tier",
    "admin-1-label-3rd-tier",
    "admin-1-label-2nd-tier",
    "admin-1-label-1st-tier",
    "us-admin-1-label-abbr-3rd-tier",
    "us-admin-1-label-abbr-2nd-tier",
    "us-admin-1-label-abbr-1st-tier",
    "admin-0-boundaries-bg",
    "admin-0-boundaries",
    "admin-0-boundaries-dispute",
]


def zone(kind, x, y, width, height, **options):
    return {
        "type": kind,
        "absolute": {"x": x, "y": y, "w": width, "h": height},
        "style": {
            "background-color": "#000000",
            "margin": 0,
            "border-style": "none",
            "border-width": 0,
        },
        **options,
    }


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/2021_03_03_WW09_World Indicators_Migrated Data.hyper")
    )
    editor.add_parameter(
        "pSelectedCountry", datatype="string", default_value="", domain_type="any"
    )
    for name, formula in (
        ("All Countries", "IF [pSelectedCountry]='' THEN [Country/Region] END"),
        (
            "Selected Country",
            "IF [pSelectedCountry]=[Country/Region] THEN [Country/Region] END",
        ),
    ):
        editor.add_calculated_field(
            name, formula, datatype="string", role="dimension", field_type="nominal"
        )
        editor.set_field_geographic_role(name, "country")
    editor.set_field_geographic_role("Country/Region", "country")
    editor.add_calculated_field(
        "Population Non-Urban",
        "1-[Population Urban]",
        datatype="real",
        default_format="p0%",
    )
    editor.set_field_format("Population Urban", "p0%")
    editor.set_field_format("Population Total", "n#,##0,,M;-#,##0,,M")
    editor.set_datasource_color_palette("Region", REGIONS)
    editor.add_worksheet("Map")
    tooltip = [
        "ATTR(Country/Region)",
        "Region",
        "SUM(Population Total)",
        "SUM(Population Urban)",
    ]
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="All Countries",
        map_layer_mode="native",
        filters=[{"column": "YEAR(Year)", "values": [2012]}],
        map_layers=[
            {
                "mark_type": "Multipolygon",
                "detail": "All Countries",
                "color": "Region",
                "tooltip": tooltip,
            },
            {
                "mark_type": "Multipolygon",
                "detail": "Selected Country",
                "color": "Region",
                "tooltip": tooltip,
            },
            {
                "mark_type": "Pie",
                "detail": "Selected Country",
                "inert": True,
                "color": "Measure Names",
                "wedge_size": "Multiple Values",
                "measure_values": [
                    "SUM(Population Urban)",
                    "SUM(Population Non-Urban)",
                ],
                "color_map": {
                    "SUM(Population Urban)": "#d3d3d3",
                    "SUM(Population Non-Urban)": "#767f8b",
                },
                "mark_size_value": "14.547999382019043",
                "has_stroke": True,
                "stroke_color": "#ffffff",
                "tooltip": tooltip,
            },
            {
                "mark_type": "Circle",
                "detail": "Selected Country",
                "color": "Region",
                "label": "SUM(Population Urban)",
                "mark_size_value": "12.034278869628906",
                "has_stroke": True,
                "stroke_color": "#ffffff",
                "tooltip": tooltip,
            },
        ],
    )
    BACKGROUND_LAYERS.extend(
        f"admin-0-label-{tier}"
        for tier in ("1st-tier", "2nd-tier", "3rd-tier", "4th-tier", "5th-tier")
    )
    editor.configure_worksheet_style(
        "Map",
        background_color="#000000",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        map_style={
            "map_style": "dark",
            "washout": 0,
            "layers": {name: False for name in BACKGROUND_LAYERS},
        },
        panes_style={
            "4": {"cell_style": {"text-align": "center", "vertical-align": "center"}}
        },
    )
    editor.configure_custom_label(
        "Map",
        [
            {"field": "SUM(Population Urban)", "fontsize": 16},
            {"text": "\nurban dwellers", "fontsize": 9},
        ],
        pane_index=4,
    )
    for index in range(1, 5):
        editor.configure_custom_tooltip(
            "Map",
            [
                {"field": "ATTR(Country/Region)", "bold": True},
                {"text": " | "},
                {"field": "Region"},
                {"text": "\nTotal Population: "},
                {"field": "SUM(Population Total)"},
                {"text": "\nUrban dwelling share: "},
                {"field": "SUM(Population Urban)"},
            ],
            pane_index=index,
        )
    children = [
        zone(
            "text",
            1200,
            1000,
            97600,
            6500,
            runs=[
                {
                    "text": "Can you hide a chart in the map layers?",
                    "bold": True,
                    "font_size": 18,
                    "font_alignment": "0",
                    "font_color": "#ffffff",
                }
            ],
        ),
        zone(
            "text",
            1200,
            7500,
            97600,
            4500,
            runs=[
                {
                    "text": "Click a country to see what share of its population is urban-dwelling",
                    "font_alignment": "0",
                    "font_size": 9,
                    "font_color": "#ffffff",
                }
            ],
        ),
        zone(
            "worksheet",
            800,
            12000,
            98400,
            79000,
            name="Map",
            show_title=False,
            fit="entire",
        ),
    ]
    for x, width, text, alignment in (
        (800, 24200, "CHALLENGE BY : CANDRA McRAE", "left"),
        (25000, 51800, "#WOW2021  |  WEEK 9  |  DATA: WORLD INDICATORS", "center"),
        (76800, 22400, "RECREATED WITH CWTWB", "right"),
    ):
        children.append(
            zone(
                "text",
                x,
                91000,
                width,
                4000,
                runs=[
                    {
                        "text": text,
                        "font_size": 8,
                        "font_color": "#ffffff",
                        "font_alignment": {"left": "0", "center": "1", "right": "2"}[
                            alignment
                        ],
                    }
                ],
            )
        )
    children.append(
        zone(
            "text",
            800,
            95000,
            98400,
            4000,
            runs=[
                {
                    "text": "https://www.workout-wednesday.com/2021w09tab/",
                    "font_size": 9,
                    "font_color": "#ffffff",
                    "font_alignment": "1",
                }
            ],
        )
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {
                "background-color": "#000000",
                "margin": 0,
                "border-style": "none",
                "border-width": 0,
            },
            "children": children,
        },
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Map",
        source_field="All Countries",
        target_parameter="pSelectedCountry",
        aggregation="attr",
        event_type="on-select",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
        caption="Select Country",
    )
    editor.set_worksheet_title("Map", "")
    editor.set_window_state("Map", hidden=False, zoom_entire_view=True)
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
