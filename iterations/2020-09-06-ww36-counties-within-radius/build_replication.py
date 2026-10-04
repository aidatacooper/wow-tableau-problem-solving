"""County distance, native set membership control and hospital resource maps."""

import csv
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_09_02_WW36_Covid_Cases_Within_n_Miles"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    with (HERE / "inputs/county-members.csv").open(encoding="utf-8", newline="") as f:
        counties = list(csv.DictReader(f))
    editor.set_geocoding_context(country="United States")
    editor.set_field_geographic_role("County", "county")
    editor.set_field_geographic_role("State", "state")
    editor.add_set(
        "Selected County",
        "County, State",
        members=[r["County, State"] for r in counties],
    )
    editor.add_parameter(
        "n miles",
        datatype="integer",
        default_value="100",
        domain_type="range",
        min_value="0",
        max_value="500",
        granularity="1",
    )
    formulas = [
        (
            "Selected County Lat",
            "{FIXED:AVG(IF [Selected County] THEN [latitude] END)}",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Selected County Long",
            "{FIXED:AVG(IF [Selected County] THEN [longitude] END)}",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Selected County Start Point",
            "MAKEPOINT([Selected County Lat],[Selected County Long])",
            "spatial",
            "measure",
            "nominal",
        ),
        (
            "End Point",
            "MAKEPOINT([latitude],[longitude])",
            "spatial",
            "measure",
            "nominal",
        ),
        (
            "Distance",
            "DISTANCE([Selected County Start Point],[End Point],'miles')",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Count Selected States",
            "{FIXED:COUNTD(IF [Selected County] THEN [County, State] END)}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Within n miles",
            "([Count Selected States]=1 AND [Distance]<=[n miles]) OR [Count Selected States]>1",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "States with n miles",
            "IF [Within n miles] THEN [State] END",
            "string",
            "dimension",
            "nominal",
        ),
    ]
    for name, formula, datatype, role, kind in formulas:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    editor.set_field_geographic_role("States with n miles", "state")
    editor.add_calculated_field(
        "Percentile Beds",
        "RANK_PERCENTILE(SUM([num_staffed_beds]),'asc')",
        table_calc="Columns",
    )
    editor.set_field_format("Percentile Beds", "p0.00%")
    editor.set_field_format("Date", "*mm/dd/yyyy")
    for field in [
        "Cumulative Case Count",
        "num_staffed_beds",
        "num_icu_beds",
        "num_ventilators_est",
    ]:
        editor.set_field_format(field, "#,##0")
    within = [{"column": "Within n miles", "values": [True]}]
    editor.add_worksheet("Cases Bar")
    editor.configure_layered_chart(
        "Cases Bar",
        columns=["SUM(Cumulative Case Count)"],
        rows=["Selected County", "County, State"],
        panes=[
            {"mark_type": "Bar", "color": "Percentile Beds", "tooltip": ["ATTR(Date)"]}
        ],
        filters=within,
        sort_descending="SUM(Cumulative Case Count)",
        table_calc_context=True,
        table_calc_overrides={
            "Percentile Beds": [
                {
                    "ordering_type": "Field",
                    "order": ["Selected County", "County, State"],
                }
            ]
        },
    )
    editor.configure_worksheet_style(
        "Cases Bar",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_row_field_labels=True,
        label_formats=[
            {"field": "Selected County", "display": "false"},
            {"field": "County, State", "font-size": "8", "color": "#555555"},
        ],
        header_formats=[{"field": "County, State", "width": "192"}],
        axis_style={"title": ""},
        color_style={"field": "Percentile Beds", "palette": "green_gold_10_0"},
    )
    editor.add_worksheet("Data")
    editor.configure_layered_chart(
        "Data",
        columns=["Measure Names"],
        rows=["County, State", "State"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": ["Percentile Beds", "SUM(num_staffed_beds)"],
            }
        ],
        filters=within,
        table_calc_context=True,
        table_calc_overrides={
            "Percentile Beds": [
                {"ordering_type": "Field", "order": ["County, State", "State"]}
            ]
        },
    )
    states = sorted({r["State"] for r in counties})
    for name, selected in [
        ("Map - Main", [s for s in states if s not in ["Alaska", "Hawaii"]]),
        ("Map - AL", ["Alaska"]),
        ("Map - HI", ["Hawaii"]),
    ]:
        editor.add_worksheet(name)
        editor.configure_layered_chart(
            name,
            columns=["Longitude (generated)"],
            rows=["Latitude (generated)", "Latitude (generated)"],
            axis_shelf="rows",
            synchronized=True,
            fold_axes=True,
            hide_axes=True,
            panes=[
                {
                    "axis": "Latitude (generated)",
                    "mark_type": "Multipolygon",
                    "geometry": "Geometry (generated)",
                    "detail": "States with n miles",
                    "mark_style": {
                        "mark-color": "#ffffff",
                        "has-stroke": "true",
                        "stroke-color": "#ffffff",
                    },
                },
                {
                    "axis": "Latitude (generated)",
                    "mark_type": "Multipolygon",
                    "geometry": "Geometry (generated)",
                    "detail": "County",
                    "detail_extra": ["State", "County, State"],
                    "color": "Percentile Beds",
                    "tooltip": [
                        "SUM(Cumulative Case Count)",
                        "SUM(num_staffed_beds)",
                        "SUM(num_icu_beds)",
                        "SUM(num_ventilators_est)",
                        "ATTR(Date)",
                    ],
                },
            ],
            filters=within + [{"column": "State", "values": selected}],
            table_calc_context=True,
            table_calc_overrides={
                "Percentile Beds": [
                    {
                        "ordering_type": "Field",
                        "order": ["County", "County, State", "State"],
                    }
                ]
            },
        )
        editor.configure_worksheet_style(
            name,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            color_style={"field": "Percentile Beds", "palette": "green_gold_10_0"},
            map_style={"washout": "100", "map-style": "normal"},
        )
        editor.configure_custom_tooltip(
            name,
            runs=[
                {"text": "As of "},
                {"field": "ATTR(Date)"},
                {"text": ", "},
                {"field": "County, State"},
                {"text": " had "},
                {"field": "SUM(Cumulative Case Count)"},
                {"text": " cases of COVID19\nHospital beds: "},
                {"field": "SUM(num_staffed_beds)"},
                {"text": "\nICU beds: "},
                {"field": "SUM(num_icu_beds)"},
                {"text": "\nVentilators: "},
                {"field": "SUM(num_ventilators_est)"},
            ],
            pane_index=1,
        )
    editor.add_worksheet("Utilisation Bar")
    editor.configure_layered_chart(
        "Utilisation Bar",
        columns=["Measure Names"],
        rows=["Multiple Values"],
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Bar",
                "measure_values": [
                    "SUM(num_staffed_beds)",
                    "SUM(num_icu_beds)",
                    "SUM(num_ventilators_est)",
                ],
                "mark_style": {"mark-color": "#59a14f"},
            }
        ],
        filters=within,
    )
    editor.set_measure_name_aliases(
        "Utilisation Bar",
        {
            "SUM(num_icu_beds)": "ICU Beds",
            "SUM(num_staffed_beds)": "Hospital Beds",
            "SUM(num_ventilators_est)": "Ventilators (est)",
        },
    )
    editor.configure_worksheet_style(
        "Utilisation Bar",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_gridlines=True,
        axis_style={"title": ""},
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1366,
        height=968,
        worksheet_names=[
            "Cases Bar",
            "Utilisation Bar",
            "Map - Main",
            "Map - AL",
            "Map - HI",
        ],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "Can you find all counties within ",
                            "font_size": 15,
                            "font_color": "#000000",
                        },
                        {
                            "parameter": "n miles",
                            "font_size": 15,
                            "font_color": "#000000",
                        },
                        {
                            "text": " miles of a selected county?",
                            "font_size": 15,
                            "font_color": "#000000",
                        },
                    ],
                    "fixed_size": 60,
                },
                {
                    "type": "horizontal",
                    "fixed_size": 76,
                    "style": {"background-color": "#f5f5f5"},
                    "children": [
                        {
                            "type": "set_control",
                            "field": "Selected County",
                            "worksheet": "Map - Main",
                            "mode": "dropdown",
                            "caption": "Selected County",
                            "fixed_size": 209,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "n miles",
                            "caption": "And all counties within n miles",
                            "mode": "type_in",
                            "fixed_size": 200,
                        },
                        {
                            "type": "color",
                            "worksheet": "Map - Main",
                            "field": "Percentile Beds",
                            "pane_index": 2,
                            "fixed_size": 280,
                        },
                        {"type": "empty"},
                    ],
                },
                {"type": "empty", "fixed_size": 36},
                {
                    "type": "horizontal",
                    "children": [
                        {
                            "type": "vertical",
                            "fixed_size": 568,
                            "children": [
                                {
                                    "type": "text",
                                    "text": "Cases by County",
                                    "font_size": 15,
                                    "font_color": "#333333",
                                    "fixed_size": 30,
                                    "style": {"background-color": "#f5f5f5"},
                                },
                                {
                                    "type": "worksheet",
                                    "name": "Cases Bar",
                                    "show_title": False,
                                    "fit": "width",
                                    "fixed_size": 283,
                                },
                                {
                                    "type": "text",
                                    "text": "Estimated Utilization",
                                    "font_size": 15,
                                    "font_color": "#333333",
                                    "fixed_size": 30,
                                    "style": {"background-color": "#f5f5f5"},
                                },
                                {
                                    "type": "worksheet",
                                    "name": "Utilisation Bar",
                                    "show_title": False,
                                    "fit": "entire",
                                },
                            ],
                        },
                        {"type": "empty", "fixed_size": 30},
                        {
                            "type": "vertical",
                            "children": [
                                {
                                    "type": "text",
                                    "text": "Map of Hospital Beds by County",
                                    "font_size": 15,
                                    "font_color": "#333333",
                                    "fixed_size": 30,
                                    "style": {"background-color": "#f5f5f5"},
                                },
                                {
                                    "type": "horizontal",
                                    "children": [
                                        {
                                            "type": "vertical",
                                            "fixed_size": 190,
                                            "children": [
                                                {
                                                    "type": "worksheet",
                                                    "name": "Map - AL",
                                                    "show_title": False,
                                                    "fit": "entire",
                                                },
                                                {
                                                    "type": "worksheet",
                                                    "name": "Map - HI",
                                                    "show_title": False,
                                                    "fit": "entire",
                                                },
                                            ],
                                        },
                                        {
                                            "type": "worksheet",
                                            "name": "Map - Main",
                                            "show_title": False,
                                            "fit": "entire",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "horizontal",
                    "fixed_size": 40,
                    "children": [
                        {
                            "type": "text",
                            "text": "DESIGNED BY : SEAN MILLER",
                            "font_size": 8,
                            "bold": True,
                        },
                        {
                            "type": "text",
                            "text": "#WOW2020 | WEEK36",
                            "font_size": 8,
                            "bold": True,
                        },
                        {
                            "type": "text",
                            "text": "DONNA COLES REFERENCE | CWTWB",
                            "font_size": 8,
                            "bold": True,
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "DATA: https://www.cerner.com/covid-19/predictive-models/us-utilization-forecasting | https://www.workout-wednesday.com/wow2020w36/",
                    "font_size": 9,
                    "fixed_size": 36,
                },
            ],
        },
    )
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
