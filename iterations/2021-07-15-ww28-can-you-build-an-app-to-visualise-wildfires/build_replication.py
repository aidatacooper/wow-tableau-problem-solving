"""Rebuild the WW28 "visualise wildfires" fire-size app.

The challenge (Josh Jackson, built by Donna Coles) is a parameter-driven map: the
user types a latitude/longitude and an acreage, and a buffer sized to that many
acres is drawn around the point so its scale can be compared to a known place.
A location list plus an Apply button sets the lat/long parameters.

Chain:
  data (5 dummy rows: Data, F2)
  → pLocation (integer list 1-4 with location aliases)
  → pLatitude / pLongtitude (real inputs), Acres (5000), pZoom (list)
  → Acres to Feet = SQRT(([Acres]*43560)/PI())
  → Location = MAKEPOINT([pLatitude], [pLongtitude])
  → Fire Size = BUFFER([Location], [Acres to Feet], 'ft')
  → Zoom = BUFFER([Location], [pZoom] * [Acres to Feet], 'ft')
  → Location Lat/Long = CASE [pLocation] WHEN n THEN <coords> END
  → Map: two native buffer layers (the visible pale-red fire and the invisible
    zoom ring) over the dark base map
  → Apply sheet: a text 'Apply' mark carrying the location coordinates
  → dashboard: two parameter actions (Set Lat / Set Long) plus a True->False
    filter action that removes the Apply button's selection highlight
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_1jwgr0f03ffbka1cghu3i1qjdugo.hyper"
DASHBOARD = "2021_07_14_WW28_FireSize_Map"

LOCATIONS = {
    1: "Didcot, UK",
    2: "Central Park, New York",
    3: "Big Ben, London",
    4: "Eiffel Tower, Paris",
}
LOCATION_LAT = {1: 51.6080, 2: 40.7812, 3: 51.5007, 4: 48.8584}
LOCATION_LONG = {1: -1.2448, 2: -73.9665, 3: 0.1246, 4: 2.2945}
ZOOM_VALUES = ["1", "2", "5", "10", "50", "500"]
FIRE_COLOR = "#fb9f8c"

LOCATION_LAT_FORMULA = (
    "CASE [pLocation]\n"
    + "\n".join(f"WHEN {key} THEN {value}" for key, value in LOCATION_LAT.items())
    + "\nEND"
)
LOCATION_LONG_FORMULA = (
    "CASE [pLocation]\n"
    + "\n".join(f"WHEN {key} THEN {value}" for key, value in LOCATION_LONG.items())
    + "\nEND"
)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Parameters ---------------------------------------------------------
    editor.add_parameter(
        "pLocation",
        datatype="integer",
        default_value="1",
        domain_type="list",
        allowed_values=[str(key) for key in LOCATIONS],
        allowed_aliases={str(key): name for key, name in LOCATIONS.items()},
    )
    editor.add_parameter(
        "pLatitude",
        datatype="real",
        default_value="51.608",
        domain_type="any",
    )
    editor.add_parameter(
        "pLongtitude",
        datatype="real",
        default_value="-1.2448",
        domain_type="any",
    )
    editor.add_parameter(
        "Acres",
        datatype="integer",
        default_value="5000",
        domain_type="any",
    )
    editor.add_parameter(
        "pZoom",
        datatype="integer",
        default_value="2",
        domain_type="list",
        allowed_values=ZOOM_VALUES,
    )

    # --- Geographic calculations -------------------------------------------
    editor.add_calculated_field(
        "Location",
        "MAKEPOINT([pLatitude], [pLongtitude])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Acres to Feet",
        "SQRT(([Acres]*43560)/PI())",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Fire Size",
        "BUFFER([Location],[Acres to Feet],'ft')",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Zoom",
        "BUFFER([Location],[pZoom] * [Acres to Feet],'ft')",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Location Lat",
        LOCATION_LAT_FORMULA,
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Location Long",
        LOCATION_LONG_FORMULA,
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Apply Label",
        "'Apply'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "True", "True", datatype="boolean", role="dimension", field_type="nominal"
    )
    editor.add_calculated_field(
        "False", "False", datatype="boolean", role="dimension", field_type="nominal"
    )

    # --- Map ----------------------------------------------------------------
    # Two native buffer layers: the visible fire and the invisible zoom ring.
    # The zoom ring is what sets the map extent, so it must be a real layer
    # even though it is transparent and inert.
    editor.add_worksheet("Map")
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="Fire Size",
        map_layer_mode="native",
        map_layers=[
            {
                "geometry": "Fire Size",
                "mark_type": "Automatic",
                "mark_color": FIRE_COLOR,
                "detail": "Fire Size",
                "tooltip": [],
            },
            {
                "geometry": "Zoom",
                "mark_type": "Automatic",
                "inert": True,
                "detail": "Zoom",
                "tooltip": [],
                "mark_style": {
                    "mark-transparency": "0",
                    "has-stroke": "false",
                },
            },
        ],
    )
    editor.configure_worksheet_style(
        "Map",
        hide_axes=True,
        hide_borders=True,
        hide_table_dividers=True,
        # Pane 2 is the transparent zoom ring that only sets the map extent.
        panes_style={
            "2": {
                "mark_style": {
                    "mark-transparency": "0",
                    "has-stroke": "false",
                }
            }
        },
        map_style={
            "map_style": "dark",
            "washout": 0.15,
            "layers": {
                "background": True,
                "base": True,
                "hillshade_highlight_bright": True,
                "hillshade_highlight_med": True,
                "hillshade_shadow_faint": True,
                "hillshade_shadow_med": True,
                "hillshade_shadow_dark": True,
                "hillshade_shadow_extreme": True,
                "water-label": True,
            },
        },
    )

    # --- Apply button -------------------------------------------------------
    editor.add_worksheet("Apply")
    editor.configure_chart(
        "Apply",
        mark_type="Text",
        label="Apply Label",
        detail="Location Lat",
        label_extra=["Location Long"],
        tooltip=[],
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        "Apply",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={
            "text-align": "center",
            "vertical-align": "center",
            "color": "#000000",
        },
        pane_datalabel_style={"color-mode": "user", "color": "#000000", "font-size": "11"},
    )

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 800 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {"text": "Fire Size Visualiser", "font_size": 14, "bold": True},
                {"text": "\n"},
                {
                    "text": "Type a latitude/longitude and acreage, or pick a "
                            "location and press Apply.",
                    "font_size": 10,
                },
            ],
            "absolute": pos(8, 8, 984, 50),
        },
        {
            "type": "worksheet",
            "name": "Map",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 62, 984, 470),
        },
        {
            "type": "paramctrl",
            "parameter": "Acres",
            "mode": "type_in",
            "caption": "Acres",
            "absolute": pos(8, 538, 300, 40),
        },
        {
            "type": "paramctrl",
            "parameter": "pZoom",
            "mode": "slider",
            "caption": "Zoom",
            "absolute": pos(8, 584, 600, 60),
        },
        {
            "type": "paramctrl",
            "parameter": "pLocation",
            "mode": "compact",
            "caption": "Location",
            "absolute": pos(620, 538, 372, 48),
        },
        {
            "type": "paramctrl",
            "parameter": "pLatitude",
            "mode": "type_in",
            "show_title": False,
            "absolute": pos(8, 660, 300, 40),
        },
        {
            "type": "paramctrl",
            "parameter": "pLongtitude",
            "mode": "type_in",
            "show_title": False,
            "absolute": pos(320, 660, 300, 40),
        },
        {
            "type": "worksheet",
            "name": "Apply",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(650, 660, 342, 60),
        },
        {
            "type": "text",
            "runs": [
                {"text": "Latitude", "font_size": 9, "font_color": "#333333"},
            ],
            "absolute": pos(8, 700, 300, 24),
        },
        {
            "type": "text",
            "runs": [
                {"text": "Longitude", "font_size": 9, "font_color": "#333333"},
            ],
            "absolute": pos(320, 700, 300, 24),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Map", "Apply"],
    )

    # The Apply button pushes the chosen location's coordinates into the inputs.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Apply",
        source_field="Location Lat",
        target_parameter="pLatitude",
        aggregation="min",
        caption="Set Lat",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Apply",
        source_field="Location Long",
        target_parameter="pLongtitude",
        aggregation="sum",
        caption="Set Long",
    )
    # Map True -> False so the Apply button never keeps a selection highlight.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Apply",
        target_sheet="Apply",
        field_mappings={"True": "False"},
        caption="Deslect Apply",
    )

    for name in ("Map", "Apply"):
        editor.set_worksheet_title(name, "")
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
