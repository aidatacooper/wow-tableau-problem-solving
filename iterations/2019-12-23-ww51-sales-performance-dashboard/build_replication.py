"""Sales performance reconstruction from preserved Hyper using public SDK APIs."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2019_12_18_WW51_SalesPerfDashboard"
SHEETS = [
    "Sales By Week ",
    "Year Filter",
    "Sales by Month",
    "Dot by Sub Cat ",
    "Bar by Sub Cat",
    "Map",
]
COLORS = [
    "#f1f1f1",
    "#e6dddb",
    "#dbcac7",
    "#d0b8b4",
    "#c5a6a2",
    "#ba9691",
    "#af8681",
    "#a47872",
    "#996a63",
    "#8e5d56",
    "#83514a",
]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_geocoding_context(country="United States")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_calculated_field(
        "Order Date Week",
        "DATE(DATETRUNC('week',[Order Date],'sunday'))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dd mmmm yyyy",
    )
    editor.add_calculated_field("Zero", "0", datatype="integer")
    for name in SHEETS:
        editor.add_worksheet(name)
    editor.configure_chart(
        "Sales By Week ",
        mark_type="Area",
        columns=["[Order Date Week]"],
        rows=["SUM(Sales)"],
    )
    editor.configure_chart(
        "Year Filter",
        mark_type="Circle",
        columns=["YEAR(Order Date)"],
        rows=["MIN(Zero)"],
        label="YEAR(Order Date)",
        mark_sizing_off=True,
    )
    editor.configure_chart(
        "Sales by Month",
        mark_type="Bar",
        columns=["MY(Order Date)"],
        rows=["SUM(Sales)"],
        color="SUM(Sales)",
    )
    editor.configure_chart(
        "Dot by Sub Cat ",
        mark_type="Circle",
        columns=["MY(Order Date)"],
        rows=["Sub-Category", "MIN(Zero)"],
        color="SUM(Sales)",
        sort_descending="SUM(Sales)",
        sort_field="Sub-Category",
        mark_sizing_off=True,
    )
    editor.configure_chart(
        "Bar by Sub Cat",
        mark_type="Bar",
        columns=["SUM(Sales)"],
        rows=["Sub-Category"],
        color="SUM(Sales)",
        label="SUM(Sales)",
        sort_descending="SUM(Sales)",
    )
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State",
        color="SUM(Sales)",
        map_fields=["Country"],
    )
    for sheet in SHEETS:
        options = dict(
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_col_field_labels=True,
            hide_row_field_labels=True,
            hide_table_dividers=True,
        )
        if sheet not in ["Sales By Week ", "Year Filter"]:
            options["color_style"] = {"field": "SUM(Sales)", "colors": COLORS}
        if sheet == "Sales By Week ":
            options.update(
                hide_row_label="Order Date Week",
                pane_mark_style={"mark-color": "#a97e79"},
            )
        if sheet == "Year Filter":
            options.update(
                pane_cell_style={"text-align": "center", "vertical-align": "center"},
                pane_datalabel_style={
                    "font-size": "10",
                    "font-weight": "bold",
                    "color-mode": "user",
                    "color": "#ffffff",
                },
                hide_row_label="YEAR(Order Date)",
                pane_mark_style={
                    "mark-color": "#a97e79",
                    "size": "1.9",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
            )
        if sheet == "Sales by Month":
            options.update(
                hide_row_label="MY(Order Date)",
                pane_mark_style={
                    "size": "1.824",
                    "has-stroke": "true",
                    "stroke-color": "#cbb1ae",
                },
            )
        if sheet == "Dot by Sub Cat ":
            options.update(
                hide_row_label="MY(Order Date)",
                pane_mark_style={
                    "size": "1.395",
                    "has-stroke": "true",
                    "stroke-color": "#a97e79",
                },
                label_formats=[{"field": "Sub-Category", "font-size": "8"}],
                header_formats=[{"field": "Sub-Category", "width": 88}],
            )
        if sheet == "Bar by Sub Cat":
            options.update(
                hide_row_label="Sub-Category",
                pane_datalabel_style={"font-size": "8"},
                pane_mark_style={
                    "has-stroke": "true",
                    "stroke-color": "#d0b8b4",
                    "mark-labels-show": "true",
                },
            )
        axis = (
            "MIN(Zero)" if sheet in ["Year Filter", "Dot by Sub Cat "] else "SUM(Sales)"
        )
        if sheet != "Map":
            options["axis_style"] = {
                "per_field": [
                    {
                        "field": axis,
                        "scope": "cols" if sheet == "Bar by Sub Cat" else "rows",
                        "display": "false",
                    }
                ]
            }
        editor.configure_worksheet_style(sheet, **options)
        if sheet != "Year Filter":
            editor.configure_custom_tooltip(
                sheet,
                [
                    {
                        "field": "State"
                        if sheet == "Map"
                        else "[Order Date Week]"
                        if sheet == "Sales By Week "
                        else "Sub-Category"
                        if sheet == "Bar by Sub Cat"
                        else "MY(Order Date)",
                        "bold": True,
                        "fontsize": 14,
                    },
                    {"text": " | "},
                    {"field": "SUM(Sales)", "bold": True, "fontsize": 14},
                ],
            )
    zones = []
    positions = [
        ("Sales By Week ", 800, 1000, 98400, 7573),
        ("Year Filter", 800, 13165, 98400, 9874),
        ("Sales by Month", 9800, 28548, 69198, 14926),
        ("Map", 78998, 28548, 20202, 14926),
        ("Dot by Sub Cat ", 800, 43474, 78199, 47526),
        ("Bar by Sub Cat", 78999, 43474, 20201, 47526),
    ]
    for sheet, x, y, w, h in positions:
        zones.append(
            {
                "type": "worksheet",
                "name": sheet,
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": x, "y": y, "w": w, "h": h},
            }
        )
    for text, y, height in [
        ("SALES PERFORMANCE", 8573, 4592),
        ("SUBCATEGORY SALES MARGINAL HISTOGRAM", 23039, 5509),
    ]:
        zones.append(
            {
                "type": "text",
                "text": text,
                "runs": [
                    {
                        "text": text,
                        "font_size": "18",
                        "font_color": "#ffffff",
                        "bold": True,
                        "font_alignment": "1",
                    }
                ],
                "style": {
                    "background-color": "#cbb1ae"
                    if text == "SALES PERFORMANCE"
                    else "#d0b8b4",
                    "margin": "0",
                },
                "absolute": {"x": 800, "y": y, "w": 98400, "h": height},
            }
        )
    for text, x, width, y in [
        ("DESIGNED BY : LORN EDEN", 800, 32800, 91000),
        ("#WORKOUTWEDNESDAY | 2019 | WEEK 51", 33600, 32800, 91000),
        ("RECREATED BY :DONNA COLES", 66400, 32800, 91000),
        (
            "http://www.workout-wednesday.com/week-51-sales-performance-dashboard/",
            800,
            98400,
            95000,
        ),
    ]:
        zones.append(
            {
                "type": "text",
                "text": text,
                "runs": [
                    {
                        "text": text,
                        "font_size": "8",
                        "font_color": "#a97e79",
                        "bold": True,
                        "font_alignment": "1",
                    }
                ],
                "absolute": {"x": x, "y": y, "w": width, "h": 4000},
            }
        )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        worksheet_names=SHEETS,
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    editor.configure_worksheet_style(
        "Map",
        map_style={
            "layers": {
                "background": False,
                "barrier_line-land-polygon": False,
                "barrier_line-land-line": False,
                "national_park": False,
                "pitch": False,
                "industrial": False,
                "built-up-area": False,
                "water": False,
                "waterway-river-canal": False,
                "aeroway-polygon": False,
                "aeroway-runway": False,
                "aeroway-taxiway": False,
                "parks": False,
                "landcover_wood": False,
                "landcover_scrub": False,
                "landcover_grass": False,
                "landcover_crop": False,
                "admin-0-boundaries-bg": False,
                "admin-0-boundaries": False,
                "admin-0-boundaries-dispute": False,
                "admin-0-label-5th-tier": False,
                "admin-0-label-4th-tier": False,
                "admin-0-label-3rd-tier": False,
                "admin-0-label-2nd-tier": False,
                "admin-0-label-1st-tier": False,
                "admin-0-boundaries-bg-sub": False,
                "admin-1-boundaries-supress-bg": False,
                "admin-1-boundaries-sm-parents-bg": False,
                "admin-1-boundaries-md-parents-bg": False,
                "admin-1-boundaries-lg-parents-bg": False,
                "admin-0-boundaries-dispute-sub": False,
                "admin-0-boundaries-sub": False,
                "admin-1-boundaries-supress": False,
                "admin-1-boundaries-sm-parents": False,
                "admin-1-boundaries-md-parents": False,
                "admin-1-boundaries-lg-parents": False,
                "admin1-water-lines-usa-tableau": False,
                "9-dash-line-casing": False,
                "9-dash-line": False,
                "admin-1-label-9th-tier": False,
                "admin-1-label-8th-tier": False,
                "admin-1-label-7th-tier": False,
                "admin-1-label-6th-tier": False,
                "admin-1-label-5th-tier": False,
                "admin-1-label-4th-tier": False,
                "admin-1-label-3rd-tier": False,
                "admin-1-label-2nd-tier": False,
                "admin-1-label-1st-tier": False,
                "us-admin-1-label-abbr-3rd-tier": False,
                "us-admin-1-label-abbr-2nd-tier": False,
                "us-admin-1-label-abbr-1st-tier": False,
            }
        },
    )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Year Filter",
        target_sheets=SHEETS,
        event_type="on-select",
        caption="Filter 1 (generated)",
    )
    bottom = ["Sales by Month", "Dot by Sub Cat ", "Bar by Sub Cat"]
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="highlight",
        source_sheets=bottom,
        target_sheets=bottom,
        event_type="on-hover",
        caption="Highlight1",
    )
    output_path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    print(build())
