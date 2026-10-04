"""Build state profit polygons, city circles and the city profit bar chart."""

from pathlib import Path
import csv
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_01_27_WW04_Map_Layers"
CURRENCY = 'c"$"#,##0;("$"#,##0)'
BACKGROUND_LAYERS = "background barrier_line-land-polygon barrier_line-land-line national_park pitch industrial built-up-area water waterway-river-canal aeroway-polygon aeroway-runway aeroway-taxiway parks landcover_wood landcover_scrub landcover_grass landcover_crop admin-0-boundaries-bg-sub admin-1-boundaries-supress-bg admin-1-boundaries-sm-parents-bg admin-1-boundaries-md-parents-bg admin-1-boundaries-lg-parents-bg admin-0-boundaries-dispute-sub admin-0-boundaries-sub admin-1-boundaries-supress admin-1-boundaries-sm-parents admin-1-boundaries-md-parents admin-1-boundaries-lg-parents admin1-water-lines-usa-tableau 9-dash-line-casing 9-dash-line admin-1-label-9th-tier admin-1-label-8th-tier admin-1-label-7th-tier admin-1-label-6th-tier admin-1-label-5th-tier admin-1-label-4th-tier admin-1-label-3rd-tier admin-1-label-2nd-tier admin-1-label-1st-tier us-admin-1-label-abbr-3rd-tier us-admin-1-label-abbr-2nd-tier us-admin-1-label-abbr-1st-tier admin-0-boundaries-bg admin-0-boundaries admin-0-boundaries-dispute".split()


def zone(kind, x, y, w, h, **kwargs):
    return {"type": kind, "absolute": {"x": x, "y": y, "w": w, "h": h}, **kwargs}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_09vl5zs0qiliw116rxe6l1c03ozv.hyper"))
    e.set_geocoding_context(country="United States")
    e.set_field_geographic_role("State", "state")
    e.set_field_geographic_role("City", "city")
    with (HERE / "inputs/state-abbreviations.csv").open(
        encoding="utf8", newline=""
    ) as f:
        pairs = list(csv.DictReader(f))
    formula = (
        "CASE [State] "
        + " ".join(f"WHEN '{p['state']}' THEN '{p['abbreviation']}'" for p in pairs)
        + " END"
    )
    for name, expression in (
        ("State Abbrev", formula),
        ("City, State", "[City] + ', ' + [State Abbrev]"),
    ):
        e.add_calculated_field(
            name, expression, datatype="string", role="dimension", field_type="nominal"
        )
    e.add_calculated_field(
        "Profit +ve?",
        "SUM([Profit])>=0",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )
    for name, expression in (
        ("+ve Profit", "IF [Profit +ve?] THEN SUM([Profit]) END"),
        ("-ve Profit", "IF NOT([Profit +ve?]) THEN SUM([Profit]) END"),
    ):
        e.add_calculated_field(
            name, expression, datatype="real", default_format=CURRENCY
        )
    e.set_field_format("Profit", CURRENCY)
    e.add_calculated_field("Loss Sort", "-[Profit]", datatype="real")
    e.set_datasource_color_palette(
        "[Profit +ve?]", {"true": "#5c6068", "false": "#e15759"}
    )
    e.add_worksheet("Map")
    e.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State",
        map_layers=[
            {
                "mark_type": "Multipolygon",
                "detail": "State",
                "color": "SUM(Profit)",
                "inert": True,
            },
            {
                "mark_type": "Circle",
                "detail": "City",
                "color": "[Profit +ve?]",
                "size": "SUM(Profit)",
                "mark_sizing_off": True,
                "mark_size_value": "2.2346642017364502",
                "has_stroke": True,
                "stroke_color": "#d4d4d4",
                "tooltip": ["ATTR(State Abbrev)", "[+ve Profit]", "[-ve Profit]"],
            },
        ],
    )
    e.configure_worksheet_style(
        "Map",
        background_color="#ffffff",
        hide_gridlines=True,
        hide_table_dividers=True,
        legend_style={"font-size": 8},
        map_style={
            "washout": 100,
            "layers": {name: False for name in BACKGROUND_LAYERS},
        },
        color_style={"field": "SUM(Profit)", "palette": "red_black_10_0", "center": 0},
        size_style={
            "field": "SUM(Profit)",
            "type": "centersize",
            "min": -13837.7674,
            "max": 62036.9837,
            "min_size": 0,
            "max_size": 1,
        },
    )
    e.add_worksheet("Bar")
    e.configure_chart(
        "Bar",
        mark_type="Bar",
        rows=["City, State"],
        columns=["SUM(Profit)"],
        color="[Profit +ve?]",
        sort_descending="SUM(Loss Sort)",
        sort_field="City, State",
        detail="City",
        tooltip=["ATTR(State Abbrev)", "[+ve Profit]", "[-ve Profit]"],
    )
    e.configure_worksheet_style(
        "Bar",
        background_color="#ffffff",
        hide_gridlines=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_table_dividers=True,
        header_formats=[{"field": "City, State", "font-size": 9}],
    )
    for sheet, pane, identity in (("Map", 2, "City"), ("Bar", 0, "City, State")):
        e.configure_custom_tooltip(
            sheet,
            [
                {"field": identity, "bold": True, "fontsize": 9},
                {"text": ", "},
                {"field": "ATTR(State Abbrev)", "bold": True},
                {"text": " had a total profit of "},
                {"field": "[+ve Profit]", "bold": True},
                {"field": "[-ve Profit]", "bold": True, "fontcolor": "#da020e"},
            ],
            pane_index=pane,
        )
    children = [
        zone("worksheet", 586, 6143, 68082, 84482, name="Map", show_title=False),
        zone("worksheet", 68668, 6143, 30746, 84482, name="Bar", show_title=False),
        zone(
            "text",
            586,
            1042,
            98828,
            5101,
            runs=[
                {
                    "text": "Can you use map layers to overlay cities on top of states?",
                    "font_size": 16,
                    "font_alignment": "0",
                }
            ],
        ),
        zone("text", 732, 71615, 13250, 4688, text="Profit Legend"),
        zone(
            "color",
            732,
            76303,
            13250,
            6250,
            worksheet="Map",
            field="SUM(Profit)",
            pane_index=1,
            show_title=False,
        ),
        zone(
            "size",
            732,
            81000,
            13250,
            18000,
            worksheet="Map",
            field="SUM(Profit)",
            pane_index=2,
            show_title=False,
        ),
    ]
    children = [
        node
        for node in children
        if node["type"] not in ("color", "size") and node.get("text") != "Profit Legend"
    ]
    children.append(
        zone(
            "container",
            732,
            68000,
            13250,
            31000,
            direction="vertical",
            children=[
                {
                    "type": "text",
                    "text": "Profit Legend",
                    "font_size": 12,
                    "fixed_size": 32,
                    "style": {"background-color": "#f4f4f4"},
                },
                {
                    "type": "color",
                    "worksheet": "Map",
                    "field": "SUM(Profit)",
                    "pane_index": 1,
                    "show_title": False,
                    "fixed_size": 42,
                },
                {
                    "type": "size",
                    "worksheet": "Map",
                    "field": "SUM(Profit)",
                    "pane_index": 2,
                    "show_title": False,
                    "fixed_size": 160,
                },
            ],
        )
    )
    children.append(
        zone(
            "text",
            586,
            6800,
            67500,
            5000,
            runs=[
                {"text": "Where are we ", "font_size": 12, "font_alignment": "0"},
                {"text": "not making money", "font_size": 12, "font_color": "#e00000"},
                {"text": "?", "font_size": 12},
            ],
        )
    )
    for x, text in (
        (33529, "#WOW2021  |  WEEK 4\nhttp://www.workout-wednesday.com/2021w04tab/"),
        (66471, "CHALLENGE BY : SEAN MILLER\nRECREATED WITH CWTWB"),
    ):
        children.append(
            zone("text", x, 90625, 32942, 8333, runs=[{"text": text, "font_size": 8}])
        )
    e.add_dashboard(
        DASHBOARD,
        width=1366,
        height=768,
        layout={"type": "container", "direction": "floating", "children": children},
    )
    e.add_dashboard_action(
        DASHBOARD,
        "highlight",
        source_sheet="Bar",
        target_sheet="Map",
        fields=["ATTR(State Abbrev)", "City"],
        event_type="on-hover",
        caption="Highlight1",
    )
    for name in ("Map", "Bar"):
        e.set_window_state(name, hidden=False, zoom_entire_view=name == "Map")
        e.set_worksheet_title(name, "")
    out = HERE / "outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
