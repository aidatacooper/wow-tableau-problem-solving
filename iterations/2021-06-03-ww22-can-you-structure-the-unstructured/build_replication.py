"""Rebuild the WW22 "Can you structure the unstructured?" Airbnb dashboard.

The challenge (Candra McEniry, built by Donna Coles) parses the free-text
Airbnb description with regular expressions to extract the number of bedrooms,
then shows a price histogram and a map that filter each other.

Chain:
  data (description, price, lattitude, longitude, listing_url, name, room_type)
  → Step 1 - Clean Up Bedroom: REGEXP_REPLACE([description], '<word list>', ' Bedroom ')
  → Step 2 - Group Sizes: Studio when the text contains "studio", otherwise
    REGEXP_EXTRACT(..., '(\d+ ?(Bedroom))')
  → a categorical group folds 5+ bedrooms into "More Than 5 Bedrooms"
  → Step 3 - Create the Prince Bins: (sys_numbin([price],[Bin Size])*[Bin Size])+[Bin Size]
  → Bin End Range = bins - Bin Size;  # of Listings = COUNTD([name])
  → Window Avg Price = WINDOW_SUM(SUM([price])) / WINDOW_SUM([# of Listings])
  → histo: bars per price bin with the average reference line and a bedroom filter
  → map: latitude/longitude points with listing detail and a price tooltip
  → dashboard: two filter actions plus a "See the listing" URL action
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/listings copy_listings copy (WOW Week 22 Data).hyper"
DASHBOARD = "Can You Find a Place to Stay?"

BIN_SIZE = 100
BAR_COLOR = "#97d2d4"

# The article's ordered bedroom selector. The workbook uses a quick filter on
# the grouped bedroom field; the replica exposes the same groups.
BEDROOM_GROUPS = {
    "Studio": ["Studio"],
    "1 Bedroom": ["1 Bedroom"],
    "2 Bedrooms": ["2 Bedroom"],
    "3 Bedrooms": ["3 Bedroom"],
    "4 Bedrooms": ["4 Bedroom"],
    "More Than 5 Bedrooms": [
        "5 Bedroom", "6 Bedroom", "7 Bedroom", "8 Bedroom",
        "9 Bedroom", "10 Bedroom", "12 Bedroom", "16 Bedroom",
    ],
}


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    editor.add_parameter(
        "Bin Size",
        datatype="integer",
        default_value=str(BIN_SIZE),
        domain_type="any",
    )

    # --- Regex bedroom extraction ------------------------------------------
    editor.add_calculated_field(
        "Step 1 - Clean Up Bedroom",
        "REGEXP_REPLACE([description], "
        "'\\s+\\b(?:BR|br|BDRM|bdrm|beds|bed|bd|rooms|Room|bed |BEDS|bedroom"
        "|-bedroom|bedrooms)\\b', ' Bedroom ')",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Step 2 - Group Sizes",
        'IF CONTAINS([Step 1 - Clean Up Bedroom], "studio") THEN "Studio"\n'
        "ELSE\n"
        "REGEXP_EXTRACT([Step 1 - Clean Up Bedroom], '(\\d+ ?(Bedroom))')\n"
        "END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_group(
        "Step 2 - Group Sizes (group)",
        "Step 2 - Group Sizes",
        BEDROOM_GROUPS,
        default_value="Other",
    )

    # --- Price bins and aggregates -----------------------------------------
    # The article documents FLOOR([Price]/100)*100 as the portable equivalent
    # of Tableau's internal sys_numbin bin helper.
    editor.add_calculated_field(
        "Price per Night Min",
        "FLOOR([price]/[Bin Size])*[Bin Size]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
        default_format='c"$"#,##0;("$"#,##0)',
    )
    editor.add_calculated_field(
        "Price per Night Max",
        "[Price per Night Min]+[Bin Size]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
        default_format='c"$"#,##0;("$"#,##0)',
    )
    editor.add_calculated_field(
        "# of Listings",
        "COUNTD([name])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Window Avg Price",
        "WINDOW_SUM(SUM([price])) / WINDOW_SUM([# of Listings])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;("$"#,##0)',
    )
    editor.set_field_format("price", 'c"$"#,##0;("$"#,##0)')

    # --- Histogram ----------------------------------------------------------
    editor.add_worksheet("histo")
    editor.configure_chart(
        "histo",
        mark_type="Bar",
        columns=["Price per Night Min"],
        rows=["# of Listings"],
        detail="Window Avg Price",
        tooltip=["AVG(Price per Night Max)", "# of Listings"],
        mark_sizing_off=True,
        filters=[{"column": "Step 2 - Group Sizes (group)", "values": list(BEDROOM_GROUPS)}],
    )
    editor.configure_worksheet_style(
        "histo",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_row_field_labels=False,
        pane_cell_style={"text-align": "center"},
        table_formats=[{"attr": "line-visibility", "value": "off"}],
    )
    editor.configure_worksheet_style(
        "histo",
        axis_style={
            "per_field": [
                {
                    "field": "Price per Night Min",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Price per Night",
                },
                {
                    "field": "# of Listings",
                    "scope": "rows",
                    "attr": "title",
                    "value": "# of Listings",
                },
            ]
        },
    )
    editor.add_reference_line(
        "histo",
        axis_field="Price per Night Min",
        value_field="Window Avg Price",
        formula="average",
        label="Avg: <Value>",
        label_type="custom",
        scope="per-pane",
    )
    editor.configure_worksheet_style(
        "histo",
        pane_mark_style={
            "mark-color": BAR_COLOR,
            "has-stroke": "true",
            "stroke-color": "#f5f5f5",
        },
        label_formats=[{"field": "Price per Night Min", "text-format": 'c"$"#,##0;("$"#,##0)'}],
    )
    editor.configure_reference_line_style(
        "histo",
        "refline0",
        {
            "line-pattern-only": "dotted",
            "stroke-color": "#1a2a47",
            "line-visibility": "on",
        },
    )
    editor.set_worksheet_title("histo", "What is the Price Spread for AirBnBs in Seattle?")

    # --- Map ----------------------------------------------------------------
    # A MAKEPOINT field is the portable way to plot latitude/longitude rows;
    # the extract's own lat/lon columns are not exposed as geographic roles.
    editor.add_calculated_field(
        "Listing Location",
        "MAKEPOINT([lattitude],[longitude])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_worksheet("map")
    editor.configure_chart(
        "map",
        mark_type="Map",
        geographic_field="Listing Location",
        detail="listing_url",
        tooltip=["SUM(price)", "Name"],
        filters=[{"column": "Step 2 - Group Sizes (group)", "values": list(BEDROOM_GROUPS)}],
    )
    editor.configure_worksheet_style(
        "map",
        hide_axes=True,
        hide_borders=True,
        hide_table_dividers=True,
        map_style={
            "map_style": "light",
            "washout": 0,
            "layers": {"Area Code Boundaries": True},
        },
        pane_mark_style={
            "mark-transparency": "139",
            "has-stroke": "true",
            "stroke-color": BAR_COLOR,
        },
    )
    editor.configure_custom_tooltip(
        "map",
        [
            {"field": "Name", "bold": True, "fontsize": 12},
            {"text": "  \n\nPrice per Night: "},
            {"field": "SUM(price)"},
            {"text": "\n\n"},
        ],
    )

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 500 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 500 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW W22: How Much Do AirBNBs Cost in Seattle?",
                    "bold": True,
                    "font_size": 16,
                    "font_color": "#1b1b1b",
                },
                {"text": "\n"},
                {
                    "text": "Click on a mark in the chart to filter or show link listing",
                    "font_size": 11,
                    "font_color": "#1b1b1b",
                },
            ],
            "absolute": pos(8, 8, 805, 88),
        },
        {
            "type": "worksheet",
            "name": "histo",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(12, 96, 399, 392),
        },
        {
            "type": "worksheet",
            "name": "map",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(411, 96, 398, 392),
        },
        {
            "type": "filter",
            "worksheet": "histo",
            "field": "Step 2 - Group Sizes (group)",
            "mode": "radiolist",
            "show_title": False,
            "show_all": False,
            "caption": "How Many Bedrooms?",
            "absolute": pos(813, 8, 179, 169),
        },
        {
            "type": "text",
            "runs": [{"text": "Data: AirBNB", "font_size": 12}],
            "absolute": pos(813, 177, 179, 25),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=500,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["histo", "map"],
    )

    # Each chart filters the other ("Use as Filter").
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="histo",
        target_sheet="map",
        caption="Filter 1 (generated)",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="map",
        target_sheet="histo",
        caption="Filter 2 (generated)",
    )
    # The map tooltip's listing name opens the listing URL.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="url",
        source_sheet="map",
        target_sheet="map",
        url="<[listing_url]>",
        caption="See the listing",
    )

    for name in ("histo", "map"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
