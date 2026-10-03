"""Build WW08 from extracted data and public SDK calls only."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2026_02_25_WW08_DMZ_Filters"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    e.add_parameter("pSelectedState", "string", "")
    for name, formula, kind in [
        ("Profit Ratio", "SUM([Profit])/SUM([Sales])", "real"),
        (
            "Is Selected State",
            "[pSelectedState]='' OR [State/Province]=[pSelectedState]",
            "boolean",
        ),
        ("State param is not empty?", "[pSelectedState] <> ''", "boolean"),
        ("State - Reset", "''", "string"),
        ("Reset Label", "'Reset'", "string"),
    ]:
        e.add_calculated_field(
            name,
            formula,
            datatype=kind,
            **(
                {"role": "dimension", "field_type": "nominal"} if kind != "real" else {}
            ),
        )
    e.set_field_format("Profit Ratio", "p0.0%")
    e.set_field_format("Sales", 'n"$"#,##0,.0K;-"$"#,##0,.0K')
    e.set_field_format("Profit", 'n"$"#,##0,.0K;-"$"#,##0,.0K')
    measures = ["SUM(Sales)", "SUM(Profit)", "Profit Ratio", "SUM(Quantity)"]
    for sheet in ["KPIs-Main", "KPIs-Customer"]:
        e.add_worksheet(sheet)
        filters = [{"column": "Is Selected State", "values": [True]}]
        if sheet.endswith("Customer"):
            filters.append({"column": "Customer Name", "values": []})
        e.configure_chart(
            sheet,
            mark_type="Text",
            measure_values=measures,
            filters=filters,
            label_runs=[
                {
                    "field": "Multiple Values",
                    "fontsize": 12,
                    "bold": True,
                    "fontalignment": "1",
                },
                {"text": "\n"},
                {"field": "Measure Names", "fontsize": 10, "fontalignment": "1"},
            ],
        )
        e.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_borders=True,
            hide_col_field_labels=True,
            hide_row_label="Measure Names",
            pane_cell_style={"text-align": "center", "vertical-align": "center"},
            pane_mark_style={"mark-labels-show": "true"},
            label_formats=[{"field": "Measure Names", "font-size": "12"}],
        )
    e.add_worksheet("Customer Orders")
    e.configure_chart(
        "Customer Orders",
        mark_type="Text",
        rows=["Product Name"],
        measure_values=["SUM(Quantity)", "SUM(Sales)"],
        filters=[
            {"column": "Is Selected State", "values": [True]},
            {"column": "Customer Name", "values": []},
        ],
    )
    e.configure_worksheet_style(
        "Customer Orders",
        hide_gridlines=True,
        header_formats=[
            {"field": "Product Name", "width": "296"},
            {"field": "Measure Names", "width": "85"},
        ],
        cell_formats=[{"field": "SUM(Sales)", "text-format": "n0.0"}],
        pane_datalabel_style={"font-size": "10", "font-weight": "normal"},
        label_formats=[
            {"field": "Product Name", "font-size": "10", "font-weight": "normal"},
            {"field": "Measure Names", "font-size": "10", "font-weight": "normal"},
        ],
    )
    e.link_worksheet_filters("Customer Name", ["Customer Orders", "KPIs-Customer"])
    e.set_field_geographic_role("State/Province", "state")
    e.set_geocoding_context(country="United States")
    e.add_worksheet("Map")
    e.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State/Province",
        color="SUM(Sales)",
        tooltip=["State/Province", "SUM(Sales)"],
    )
    e.set_worksheet_rich_title(
        "Map",
        [
            {"text": "Sales by State\n", "fontsize": 16},
            {"text": "select a state to see a customer breakdown", "fontsize": 10},
        ],
    )
    e.configure_worksheet_style(
        "Map",
        map_style={
            "map_style": "light",
            "washout": 0,
            "layers": {
                "admin-0-label-1st-tier": False,
                "admin-0-label-2nd-tier": False,
                "admin-0-label-3rd-tier": False,
                "admin-0-label-4th-tier": False,
                "admin-0-label-5th-tier": False,
                "admin-1-label-1st-tier": False,
                "admin-1-label-2nd-tier": False,
                "admin-1-label-3rd-tier": False,
                "admin-1-label-4th-tier": False,
                "admin-1-label-5th-tier": False,
                "admin-1-label-6th-tier": False,
                "admin-1-label-7th-tier": False,
                "admin-1-label-8th-tier": False,
                "admin-1-label-9th-tier": False,
                "us-admin-1-label-abbr-1st-tier": False,
                "us-admin-1-label-abbr-2nd-tier": False,
                "us-admin-1-label-abbr-3rd-tier": False,
                "admin-0-boundaries-bg": False,
                "admin-0-boundaries": False,
                "admin-0-boundaries-dispute": False,
                "admin-0-boundaries-bg-sub": False,
                "admin-0-boundaries-dispute-sub": False,
                "admin-0-boundaries-sub": False,
                "parks": False,
                "landcover_wood": False,
                "landcover_scrub": False,
                "landcover_grass": False,
                "landcover_crop": False,
            },
        },
    )
    e.add_worksheet("Reset Button")
    e.configure_chart(
        "Reset Button",
        mark_type="Square",
        label="Reset Label",
        detail="State - Reset",
        mark_sizing_off=True,
    )
    e.configure_worksheet_style(
        "Reset Button",
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_mark_style={
            "mark-color": "#4e79a7",
            "size": "14.55",
            "mark-labels-show": "true",
        },
        pane_datalabel_style={"font-size": "14", "font-color": "#f3f9f8"},
    )
    panel = {
        "type": "container",
        "direction": "vertical",
        "fixed_size": 500,
        "visibility": {
            "field": "State param is not empty?",
            "initially_visible": False,
        },
        "style": {"padding": 10, "background-color": "#e6e6e6"},
        "children": [
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Customer behaviour for ",
                        "font_size": 10,
                        "font_alignment": 0,
                    },
                    {
                        "parameter": "pSelectedState",
                        "bold": True,
                        "font_size": 10,
                        "font_alignment": 0,
                    },
                    {
                        "text": " - select a customer below",
                        "font_size": 10,
                        "font_alignment": 0,
                    },
                ],
                "fixed_size": 29,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 77,
                "children": [
                    {
                        "type": "filter",
                        "worksheet": "Customer Orders",
                        "field": "Customer Name",
                        "mode": "dropdown",
                        "values": "relevant",
                        "show_all": False,
                        "style": {"background-color": "#e6e6e6"},
                        "fixed_size": 311,
                    },
                    {
                        "type": "worksheet",
                        "name": "Reset Button",
                        "show_title": False,
                        "fit": "entire",
                    },
                ],
            },
            {
                "type": "worksheet",
                "name": "KPIs-Customer",
                "show_title": False,
                "fit": "entire",
                "fixed_size": 71,
            },
            {
                "type": "worksheet",
                "name": "Customer Orders",
                "fixed_size": 410,
                "show_title": True,
            },
        ],
    }
    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "text": "#WOW2026 | WEEK 8 | DZV & Filter Actions",
                "font_size": 20,
                "bold": True,
                "fixed_size": 53,
            },
            {
                "type": "worksheet",
                "name": "KPIs-Main",
                "show_title": False,
                "fit": "entire",
                "fixed_size": 84,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "children": [
                    {"type": "worksheet", "name": "Map", "show_title": True},
                    panel,
                ],
            },
            {
                "type": "text",
                "text": "CHALLENGE BY: Sean Miller                         #WOW2026 | WEEK 8                         RECREATED WITH: cwtwb",
                "font_size": 8,
                "fixed_size": 30,
            },
            {
                "type": "text",
                "text": "https://www.workout-wednesday.com/wow2025w9tab/",
                "font_size": 8,
                "fixed_size": 26,
            },
        ],
    }
    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        worksheet_names=[
            "Map",
            "KPIs-Main",
            "KPIs-Customer",
            "Customer Orders",
            "Reset Button",
        ],
        layout=layout,
    )
    e.add_dashboard_action(
        DASHBOARD,
        "parameter",
        "Map",
        source_field="State/Province",
        target_parameter="pSelectedState",
        caption="Set State",
        clear_behavior="keep-current",
    )
    e.add_dashboard_action(
        DASHBOARD,
        "parameter",
        "Reset Button",
        source_field="State - Reset",
        target_parameter="pSelectedState",
        caption="Reset State",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
    )
    for target in ["Customer Orders", "KPIs-Customer"]:
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            "Reset Button",
            target_sheet=target,
            fields=["Customer Name"],
            caption="Reset Customer Filter - " + target,
            clear_behavior="show-all",
        )
    out = HERE / "outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(out, validate=False)
    return out


if __name__ == "__main__":
    print(build())
