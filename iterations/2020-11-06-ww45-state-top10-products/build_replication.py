"""Rebuild the state profit map and context-sensitive product tooltip."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_11_04_WW45_Top10Products_Map"
SEABOARD = [
    "Vermont",
    "New Hampshire",
    "Massachusetts",
    "Connecticut",
    "Rhode Island",
    "New Jersey",
    "Delaware",
    "Maryland",
    "District of Columbia",
]
ABBREVIATIONS = "Alabama:AL|Alaska:AK|Arizona:AZ|Arkansas:AR|California:CA|Colorado:CO|Connecticut:CT|Delaware:DE|District of Columbia:DC|Florida:FL|Georgia:GA|Hawaii:HI|Idaho:ID|Illinois:IL|Indiana:IN|Iowa:IA|Kansas:KS|Kentucky:KY|Louisiana:LA|Maine:ME|Maryland:MD|Massachusetts:MA|Michigan:MI|Minnesota:MN|Mississippi:MS|Missouri:MO|Montana:MT|Nebraska:NE|Nevada:NV|New Hampshire:NH|New Jersey:NJ|New Mexico:NM|New York:NY|North Carolina:NC|North Dakota:ND|Ohio:OH|Oklahoma:OK|Oregon:OR|Pennsylvania:PA|Rhode Island:RI|South Carolina:SC|South Dakota:SD|Tennessee:TN|Texas:TX|Utah:UT|Vermont:VT|Virginia:VA|Washington:WA|West Virginia:WV|Wisconsin:WI|Wyoming:WY"
MAP_LAYERS = [
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
    "admin-0-boundaries-bg",
    "admin-0-boundaries",
    "admin-0-boundaries-dispute",
    "admin-0-label-5th-tier",
    "admin-0-label-4th-tier",
    "admin-0-label-3rd-tier",
    "admin-0-label-2nd-tier",
    "admin-0-label-1st-tier",
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
]


def zone(kind, x, y, w, h, **kwargs):
    return {
        "type": kind,
        "absolute": {
            "x": x * 100,
            "y": round(y * 125),
            "w": w * 100,
            "h": round(h * 125),
        },
        "style": {"margin": 4},
        **kwargs,
    }


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_1os3cs61c7l9y217lvvel1fi1aip.hyper"))
    e.set_field_geographic_role("State", "state")
    e.set_geocoding_context(country="United States")
    e.add_calculated_field(
        "State Abbrev",
        "CASE [State]\n"
        + "\n".join(
            "WHEN '%s' THEN '%s'" % tuple(pair.split(":"))
            for pair in ABBREVIATIONS.split("|")
        )
        + "\nEND",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Full Cell",
        "MIN(1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    e.add_calculated_field(
        "Seaboard Position",
        "CASE [State]\n"
        + "\n".join(f"WHEN '{s}' THEN {8 - n}" for n, s in enumerate(SEABOARD))
        + "\nEND",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    for metric in ("Sales", "Profit"):
        e.set_field_format(metric, 'c"$"#,##0;-"$"#,##0')
    for sheet in ("Map", "Seaboard States", "Top 10 Products"):
        e.add_worksheet(sheet)
    e.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State",
        color="SUM(Profit)",
        label="State Abbrev",
        tooltip=["State", "SUM(Profit)"],
    )
    e.configure_worksheet_style(
        "Map",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        color_style={"field": "SUM(Profit)", "palette": "red_black_10_0", "center": 0},
        map_style={"washout": 0, "layers": {name: False for name in MAP_LAYERS}},
        axis_style={
            "encodings": [
                {
                    "field": "Longitude (generated)",
                    "attr": "space",
                    "class": 0,
                    "field-type": "quantitative",
                    "min": -14206738.130375601,
                    "max": -7134432.7690936672,
                    "projection": "EPSG:3857",
                    "range-type": "fixed",
                    "scope": "cols",
                    "type": "space",
                },
                {
                    "field": "Latitude (generated)",
                    "attr": "space",
                    "class": 0,
                    "field-type": "quantitative",
                    "min": 2344644.1350612044,
                    "max": 6816113.4927179683,
                    "projection": "EPSG:3857",
                    "range-type": "fixed",
                    "scope": "rows",
                    "type": "space",
                },
            ]
        },
    )
    e.configure_chart(
        "Seaboard States",
        mark_type="Bar",
        columns=["Full Cell"],
        rows=["State"],
        sort_descending="MIN(Seaboard Position)",
        sort_field="State",
        label="State Abbrev",
        tooltip=["State"],
        filters=[{"column": "State", "values": SEABOARD}],
    )
    e.configure_worksheet_style(
        "Seaboard States",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_row_label="State",
        pane_mark_style={"mark-color": "#e6e6e6", "mark-labels-show": "true"},
        hide_table_dividers=True,
        axis_style={
            "encodings": [
                {
                    "attr": "space",
                    "class": 0,
                    "field": "Full Cell",
                    "field-type": "quantitative",
                    "min": 0,
                    "max": 1,
                    "range-type": "fixed",
                    "scope": "cols",
                    "type": "space",
                }
            ]
        },
        pane_datalabel_style={
            "font-size": "10",
            "color": "#000000",
            "text-align": "center",
        },
    )
    e.configure_chart(
        "Top 10 Products",
        mark_type="Square",
        rows=["State", "Product Name"],
        color="Multiple Values",
        measure_values=["COUNT(Order ID)", "SUM(Sales)", "SUM(Profit)"],
        separate_measure_domains=True,
        sort_descending="SUM(Sales)",
        sort_field="Product Name",
        filters=[{"column": "Product Name", "top": 10, "by": "SUM(Sales)"}],
    )
    e.set_measure_name_aliases("Top 10 Products", {"COUNT(Order ID)": "Orders"})
    e.configure_worksheet_style(
        "Top 10 Products",
        show_row_totals=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_sort_controls=True,
        hide_row_label="State",
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        pane_datalabel_style={"font-size": "8", "color-mode": "auto"},
        pane_cell_style={"text-align": "right", "vertical-align": "center"},
        label_formats=[{"field": "Product Name", "text-align": "left"}],
        cell_formats=[
            {"field": "Product Name", "height": 38},
            {"field": "Measure Names", "width": 99},
        ],
        header_formats=[
            {"field": "Product Name", "width": 248},
            {
                "field": "State",
                "attr": "total-label",
                "data-class": "total",
                "value": "Top 10 Total",
            },
        ],
        color_style={"field": "SUM(Profit)", "palette": "red_black_10_0", "center": 0},
    )
    for field in ("COUNT(Order ID)", "SUM(Sales)"):
        e.configure_worksheet_style(
            "Top 10 Products",
            color_style={
                "field": field,
                "colors": ["#ffffff", "#ffffff"],
                "num_steps": 2,
            },
        )
    for sheet in ("Map", "Seaboard States"):
        e.configure_custom_tooltip(
            sheet,
            [
                {"field": "State", "bold": True},
                {"text": " has total profits of "},
                {"field": "SUM(Profit)", "bold": True},
                {"text": "\nSee below for top 10 products by sales\n", "italic": True},
                {
                    "sheet": {
                        "name": "Top 10 Products",
                        "maxwidth": 500,
                        "maxheight": 350,
                        "filter_fields": ["State Abbrev", "State"],
                        "filter_context": True,
                    }
                },
            ],
        )
    children = [
        zone(
            "text",
            8,
            8,
            984,
            108,
            runs=[
                {
                    "text": "What are the Top 10 Products by Sales per State?",
                    "font_size": 18,
                    "font_name": "Times New Roman",
                    "font_color": "#666666",
                }
            ],
            style={"background-color": "#f5f5f5", "margin": 4},
        ),
        zone("color", 8, 116, 984, 59, worksheet="Map", field="SUM(Profit)"),
        zone("worksheet", 8, 175, 870, 553, name="Map", fit="entire", show_title=False),
        zone(
            "worksheet",
            878,
            282,
            59,
            374,
            name="Seaboard States",
            fit="entire",
            show_title=False,
        ),
        zone(
            "text",
            798,
            232,
            207,
            50,
            runs=[
                {
                    "text": "Eastern Seaboard States",
                    "font_size": 10,
                    "font_name": "Tableau Medium",
                    "font_color": "#000000",
                }
            ],
        ),
        zone(
            "text",
            8,
            728,
            328,
            32,
            runs=[{"text": "DESIGNED BY : SEAN MILLER", "font_size": 9}],
        ),
        zone(
            "text",
            336,
            728,
            328,
            32,
            runs=[{"text": "#WOW2020  |  WEEK 45", "font_size": 9}],
        ),
        zone(
            "text",
            664,
            728,
            328,
            32,
            runs=[{"text": "RECREATED BY : DONNA COLES", "font_size": 9}],
        ),
        zone(
            "text",
            8,
            760,
            984,
            32,
            runs=[
                {"text": "http://www.workout-wednesday.com/2020w45/", "font_size": 9}
            ],
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
    )
    e.set_window_state("Top 10 Products", hidden=False, zoom_entire_view=True)
    out = HERE / "outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
