"""Rebuild the Regional Sales Readout with native map layers.

One sheet, no table calculations and no LoDs (the challenge's constraints). The
map is segmented by state into the four sales regions, each region drawn as its
own multipolygon layer so its border can take its own colour, with the cities
sized by sales, per-region sales text, and a hover set action that stores the
hovered city and shows its sales and share of the region.

Chain:
  data (City, State, Region, Sales)
  → Region given the geographic role "State" so it segments the map
  → four region filters (IF [Region]='West' THEN [Region] END, ...) as geographic
    multipolygon layers, each with a distinct border colour
  → City layer sized by SUM(Sales), coloured by Region
  → Sales Text layer (mark Text) showing per-region SUM(Sales)
  → Selected City set + Selected City Sales / % of Total Sales / Selected City
    Name / Selected City Sub Text, all driven by a hover change-set action
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_05_12_WW19_Map_Layers"

# Region border colours from the article.
REGION_BORDERS = {
    "West State": "#7ec886",
    "Central State": "#82d7d6",
    "East State": "#b6b6dd",
    "South State": "#fd8b59",
}
# City fill colours by region (opacity is set per layer).
REGION_FILL = {
    "West": "#7ec886",
    "Central": "#82d7d6",
    "East": "#b6b6dd",
    "South": "#fd8b59",
}
BACKGROUND = "#3b3b3b"


def zone(kind, x, y, width, height, **options):
    return {
        "type": kind,
        "absolute": {"x": x, "y": y, "w": width, "h": height},
        "style": {"margin": 0, "border-style": "none", "border-width": 0},
        **options,
    }


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))

    # The State/City names must geocode as United States places; without this
    # context Tableau resolves "Florida" etc. against world provinces.
    editor.set_geocoding_context(country="United States")

    # Region must segment the map, so it carries the geographic role "State".
    editor.set_field_geographic_role("Region", "state")
    editor.set_field_geographic_role("State", "state")
    editor.set_field_geographic_role("City", "city")

    # --- One geographic filter field per region (map layers) ---------------
    # The article creates a "Region, created from State" geographic role so each
    # region becomes a polygon. The SDK exposes standard roles only, so the
    # equivalent is one State-geocoded field per region: its values are real
    # state names, and it is null outside its region.
    for name, region in (
        ("West State", "West"),
        ("Central State", "Central"),
        ("East State", "East"),
        ("South State", "South"),
    ):
        editor.add_calculated_field(
            name,
            f"IF [Region]='{region}' THEN [State] END",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        editor.set_field_geographic_role(name, "state")

    # --- Selected-city set and its readouts --------------------------------
    editor.add_set("Selected City", "City", use_all=False)
    editor.add_calculated_field(
        "Selected City Sales",
        "IF [Selected City] THEN [Sales] END",
        datatype="real",
        role="measure",
        default_format='c"$"#,##0',
    )
    editor.add_calculated_field(
        "% of Total Sales",
        "SUM([Selected City Sales])/SUM([Sales])",
        datatype="real",
        role="measure",
        default_format="p0.0%",
    )
    editor.add_calculated_field(
        "Selected City Name",
        "MIN(IF [Selected City] THEN [City] END)",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Selected City Sub Text",
        "MIN(IF [Selected City] THEN 'OF REGION TOTAL' END)",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.set_field_format("Sales", 'c"$"#,##0')

    # --- Single map worksheet with native layers ---------------------------
    editor.add_worksheet("Map")
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State",
        map_layer_mode="native",
        map_layers=[
            # Layer 1: the state multipolygons, which segment the map by region.
            {
                "mark_type": "Multipolygon",
                "detail": "State",
                "color": "Region",
                "color_map": {region: "#555555" for region in REGION_FILL},
                "has_stroke": False,
                "tooltip": [],
            },
            # Layers 2-5: one per region, no fill colour encoding (so they do
            # not fight the Region palette) and a per-layer coloured stroke.
            *[
                {
                    "mark_type": "Multipolygon",
                    "detail": name,
                    "has_stroke": True,
                    "stroke_color": REGION_BORDERS[name],
                    "tooltip": [],
                }
                for name in ("West State", "Central State", "East State", "South State")
            ],
            # Layer 6: cities sized by sales, coloured by region.
            {
                "mark_type": "Circle",
                "detail": "City",
                "color": "Region",
                "color_map": REGION_FILL,
                "size": "SUM(Sales)",
                "tooltip": [],
            },
            # Layer 7: the per-region sales text.
            {
                "mark_type": "Text",
                "detail": "State",
                "color": "Region",
                "color_map": {region: "#ffffff" for region in REGION_FILL},
                "label": "SUM(Sales)",
                "tooltip": [],
            },
        ],
    )
    editor.configure_worksheet_style(
        "Map",
        background_color=BACKGROUND,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        map_style={
            "map_style": "normal",
            "washout": 1,
            "layers": {
                "background": True,
                "base": False,
                "admin-0-boundaries": False,
                "admin-1-boundaries": False,
                "admin-0-boundaries-bg": False,
                "admin-1-boundaries-bg": False,
                "water": False,
                "landcover": False,
                "park": False,
            },
        },
    )
    # The Sales Text layer shows the per-region sales; the transparent
    # multipolygon layers must not show a label. The selected-city readout is a
    # separate text sheet so it can reference the set cleanly.
    editor.configure_custom_label(
        "Map",
        [
            {"field": "SUM(Sales)", "fontsize": 10, "bold": True},
        ],
        pane_index=7,
    )

    # --- Selected-city readout sheet ---------------------------------------
    # The article keeps this text on the Sales Text layer; a dedicated sheet
    # avoids the label resolver traversing the set calculation while preserving
    # the same hover-driven readout.
    editor.add_worksheet("Selected City")
    editor.configure_layered_chart(
        "Selected City",
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "labels": ["Measure Names"],
                "measure_values": [
                    "Selected City Name",
                    "Selected City Sales",
                    "% of Total Sales",
                    "Selected City Sub Text",
                ],
            }
        ],
    )
    editor.configure_worksheet_style(
        "Selected City",
        background_color="#00000000",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_axes=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_borders=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
    )

    # --- Dashboard ---------------------------------------------------------
    children = [
        zone(
            "text",
            1000,
            1000,
            98000,
            6000,
            runs=[
                {
                    "text": "REGIONAL SALES READOUT",
                    "bold": True,
                    "font_size": 18,
                    "font_alignment": "0",
                    "font_color": "#ffffff",
                }
            ],
        ),
        zone(
            "worksheet",
            1000,
            8000,
            98000,
            86000,
            name="Map",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            30000,
            15000,
            40000,
            12000,
            name="Selected City",
            show_title=False,
            fit="entire",
        ),
        zone(
            "text",
            1000,
            94500,
            32000,
            4000,
            runs=[
                {
                    "text": "CHALLENGE BY : ANN JACKSON",
                    "font_size": 8,
                    "font_color": "#ffffff",
                    "font_alignment": "0",
                }
            ],
        ),
        zone(
            "text",
            34000,
            94500,
            32000,
            4000,
            runs=[
                {
                    "text": "#WOW2021  |  WEEK 19",
                    "font_size": 8,
                    "font_color": "#ffffff",
                    "font_alignment": "1",
                }
            ],
        ),
        zone(
            "text",
            66000,
            94500,
            33000,
            4000,
            runs=[
                {
                    "text": "RECREATED WITH CWTWB",
                    "font_size": 8,
                    "font_color": "#ffffff",
                    "font_alignment": "2",
                }
            ],
        ),
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=900,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {
                "background-color": BACKGROUND,
                "margin": 0,
                "border-style": "none",
                "border-width": 0,
            },
            "children": children,
        },
    )
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet="Map",
        target_set="Selected City",
        event_type="on-hover",
        caption="Select City",
    )
    editor.set_worksheet_title("Map", "")
    editor.set_worksheet_title("Selected City", "")
    editor.set_window_state("Map", hidden=False, zoom_entire_view=True)
    editor.set_window_state("Selected City", hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
