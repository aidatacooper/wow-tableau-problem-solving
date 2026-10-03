"""Independent cohort retention reconstruction using extracted data/public SDK."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2019_12_11_WW50_Customer_Retention_Heatmap"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_parameter(
        "Time Period",
        datatype="integer",
        default_value="26",
        domain_type="range",
        min_value="10",
        max_value="26",
        granularity="1",
        default_format='n#,##0"-week";-#,##0"-week"',
    )
    calculations = [
        (
            "Cohort",
            "DATE({FIXED [customer_id]: MIN(DATETRUNC('week', [order_week], 'monday'))})",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "Week Index",
            "DATEDIFF('week',[Cohort],[order_week],'monday')",
            "integer",
            "dimension",
            "ordinal",
        ),
        (
            "New Customers",
            "{FIXED [Cohort]: COUNTD(IF [order_week]=[Cohort] THEN [customer_id] END)}",
            "integer",
            "measure",
            "ordinal",
        ),
        (
            "Customer Count",
            "COUNTD([customer_id])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "% of Customers",
            "[Customer Count]/SUM([New Customers])",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Count Customers at Time Period Param",
            "{FIXED [Cohort]:COUNTD(IF [Week Index]=[Time Period] THEN [customer_id] END)}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "FILTER:Complete Cohorts",
            "[Count Customers at Time Period Param]>0",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "FILTER:Weeks Index to Display",
            "[Week Index]>0 AND [Week Index]<[Time Period]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "FILTER:Time Period",
            "[Week Index]=[Time Period]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "LABEL:Week Index",
            "'Week ' + STR([Week Index])",
            "string",
            "dimension",
            "nominal",
        ),
        ("Background", "0.5", "real", "measure", "quantitative"),
        (
            "% BAN",
            "[Customer Count]/SUM([New Customers])",
            "real",
            "measure",
            "quantitative",
        ),
    ]
    for name, formula, datatype, role, kind in calculations:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=kind,
            default_format="p0.0%" if name.startswith("%") else "",
        )

    def filters(*names):
        return [{"column": name, "values": [True]} for name in names]

    tooltip = [
        "ATTR(order_week)",
        "AGG(Customer Count)",
        "SUM(New Customers)",
        "MIN(Week Index)",
        "AGG(% of Customers)",
    ]
    editor.add_worksheet("Heat Map")
    editor.configure_chart(
        "Heat Map",
        mark_type="Square",
        columns=["Week Index"],
        rows=["Cohort", "New Customers"],
        color="AGG(% of Customers)",
        tooltip=tooltip,
        filters=filters("FILTER:Complete Cohorts", "FILTER:Weeks Index to Display"),
        mark_sizing_off=True,
        sort_descending="MIN(Cohort)",
        sort_field="Cohort",
    )
    editor.configure_worksheet_style(
        "Heat Map",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
        pane_mark_style={"size": "1", "has-stroke": "true", "stroke-color": "#ffffff"},
        color_style={
            "field": "AGG(% of Customers)",
            "colors": [
                "#fde725",
                "#dde318",
                "#bade28",
                "#95d840",
                "#75d054",
                "#56c667",
                "#3dbc74",
                "#29af7f",
                "#20a386",
                "#1f968b",
                "#238a8d",
                "#287d8e",
                "#2d718e",
                "#33638d",
                "#39558c",
                "#404688",
                "#453781",
                "#482576",
                "#481467",
                "#440154",
            ],
        },
        label_formats=[
            {"field": "Cohort", "text-format": "*mmmm d, yyyy", "font-size": "8"},
            {"field": "New Customers", "font-size": "8"},
            {"field": "Week Index", "font-size": "8"},
        ],
        header_formats=[
            {"field": "Cohort", "width": 105},
            {"field": "New Customers", "width": 93},
        ],
    )
    editor.add_worksheet("Bar")
    editor.configure_chart(
        "Bar",
        columns=["LABEL:Week Index", "AGG(% of Customers)"],
        rows=["Cohort"],
        filters=filters("FILTER:Time Period"),
        sort_descending="MIN(Cohort)",
        sort_field="Cohort",
    )
    editor.configure_layered_chart(
        "Bar",
        axis_shelf="columns",
        columns=["LABEL:Week Index", "AGG(% of Customers)", "MIN(Background)"],
        rows=["Cohort"],
        synchronized=True,
        hide_axes=True,
        sort_descending="MIN(Cohort)",
        sort_field="Cohort",
        panes=[
            {
                "axis": "AGG(% of Customers)",
                "mark_type": "Bar",
                "tooltip": tooltip + ["FILTER:Time Period"],
                "mark_style": {
                    "mark-color": "#b3b3b3",
                    "size": "1.989",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                },
            },
            {
                "axis": "MIN(Background)",
                "mark_type": "Bar",
                "labels": ["AGG(% of Customers)"],
                "tooltip": tooltip + ["FILTER:Time Period"],
                "label_runs": [
                    {
                        "field": "AGG(% of Customers)",
                        "fontsize": 7,
                        "fontcolor": "#333333",
                    }
                ],
                "mark_style": {
                    "mark-color": "#e6e6e6",
                    "size": "1.989",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
            },
        ],
    )
    editor.configure_worksheet_style(
        "Bar",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
        hide_row_label="Cohort",
        axis_style={
            "encodings": [
                {
                    "field": "AGG(% of Customers)",
                    "attr": "space",
                    "type": "space",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": "0",
                    "max": "0.7",
                    "scope": "cols",
                    "class": "0",
                }
            ],
            "render-fold-reversed": "true",
        },
        label_formats=[
            {"field": "LABEL:Week Index", "font-size": "8", "text-align": "left"}
        ],
        pane_datalabel_style={"font-size": "7"},
    )
    editor.add_worksheet("BAN")
    editor.configure_chart(
        "BAN",
        mark_type="Text",
        label="AGG(% BAN)",
        tooltip=["SUM(New Customers)", "SUM(Count Customers at Time Period Param)"],
        filters=filters("FILTER:Time Period"),
        label_runs=[{"field": "AGG(% BAN)", "fontsize": 24, "bold": True}],
    )
    editor.configure_worksheet_style(
        "BAN",
        hide_borders=True,
        pane_cell_style={"text-align": "right", "vertical-align": "center"},
    )
    for sheet in ["Heat Map", "Bar"]:
        editor.configure_custom_tooltip(
            sheet,
            [
                {"text": "Cohort Beginning: "},
                {"field": "Cohort", "bold": True},
                {"text": "\nCustomers in Cohort: "},
                {"field": "New Customers", "bold": True},
                {"text": "\nCohort Week: "},
                {"field": "Week Index", "bold": True},
                {"text": "\nActual Week: "},
                {"field": "ATTR(order_week)", "bold": True},
                {"text": "\nReturning Customers: "},
                {"field": "AGG(Customer Count)", "bold": True},
                {"text": "\nCustomer Retention: "},
                {"field": "AGG(% of Customers)", "bold": True},
            ],
        )
    zones = [
        {
            "type": "text",
            "text": "What is our",
            "runs": [{"text": "What is our", "font_size": "14"}],
            "absolute": {"x": 800, "y": 842, "w": 11300, "h": 4660},
        },
        {
            "type": "paramctrl",
            "parameter": "Time Period",
            "show_title": False,
            "mode": "slider",
            "absolute": {"x": 12100, "y": 842, "w": 13800, "h": 4660},
        },
        {
            "type": "text",
            "text": "new customer retention?",
            "runs": [{"text": "new customer retention?", "font_size": "14"}],
            "absolute": {"x": 25900, "y": 842, "w": 34400, "h": 4660},
        },
        {
            "type": "worksheet",
            "name": "BAN",
            "show_title": False,
            "fit": "entire",
            "absolute": {"x": 60300, "y": 842, "w": 38900, "h": 4660},
        },
        {
            "type": "empty",
            "style": {"background-color": "#000000", "margin": "0"},
            "absolute": {"x": 800, "y": 8870, "w": 98400, "h": 105},
        },
        {
            "type": "worksheet",
            "name": "Heat Map",
            "show_title": False,
            "fit": "entire",
            "absolute": {"x": 800, "y": 11688, "w": 82400, "h": 79192},
        },
        {
            "type": "worksheet",
            "name": "Bar",
            "show_title": False,
            "fit": "entire",
            "absolute": {"x": 83200, "y": 11688, "w": 16000, "h": 79192},
        },
        {
            "type": "color",
            "worksheet": "Heat Map",
            "field": "AGG(% of Customers)",
            "show_title": False,
            "absolute": {"x": 17300, "y": 90880, "w": 69900, "h": 4107},
        },
    ]
    for text, x, width in [
        ("DESIGNED BY : CURTIS HARRIS", 800, 20500),
        ("#WORKOUTWEDNESDAY | 2019 | WEEK 50", 21300, 57800),
        ("RECREATED BY: DONNA COLES", 79100, 20100),
    ]:
        zones.append(
            {
                "type": "text",
                "text": text,
                "runs": [
                    {
                        "text": text,
                        "font_size": "8",
                        "font_color": "#228c8c",
                        "bold": True,
                    }
                ],
                "absolute": {"x": x, "y": 94987, "w": width, "h": 2065},
            }
        )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=950,
        worksheet_names=["Heat Map", "Bar", "BAN"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    output_path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    print(build())
