"""Fixed-date YoY state map and daily/weekly viz-in-tooltip trend."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_09_09_WW37_YoY_Trend"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.set_field_geographic_role("State", "state")
    editor.set_geocoding_context(country="United States")
    formulas = [
        ("Today", "#2020-07-15#", "date", "dimension", "ordinal"),
        ("Current Year", "YEAR([Today])", "integer", "measure", "quantitative"),
        (
            "Baseline Date",
            "MAKEDATE([Current Year],MONTH([Subscription Date]),DAY([Subscription Date]))",
            "date",
            "dimension",
            "quantitative",
        ),
        (
            "CY",
            "IF YEAR([Subscription Date])=[Current Year] THEN [Subscription] END",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "PY",
            "IF YEAR([Subscription Date])=[Current Year]-1 THEN [Subscription] END",
            "integer",
            "measure",
            "quantitative",
        ),
        ("YoY%", "(SUM([CY])-SUM([PY]))/SUM([PY])", "real", "measure", "quantitative"),
        (
            "Include Dates <Today",
            "[Baseline Date]<[Today]",
            "boolean",
            "dimension",
            "nominal",
        ),
        ("Min Date", "{MIN([Baseline Date])}", "date", "dimension", "ordinal"),
        ("Max Date", "{MAX([Baseline Date])}", "date", "dimension", "ordinal"),
        (
            "Days between Min & Max",
            "DATEDIFF('day',[Min Date],[Max Date])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Day of Week Min Date",
            "DATEPART('weekday',[Min Date])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Daily | Weekly",
            "IF [Days between Min & Max]<=30 THEN 'Daily' ELSE 'Weekly' END",
            "string",
            "dimension",
            "nominal",
        ),
    ]
    for field in ["Baseline Date", "Max Date"]:
        name = "Baseline Date Week" if field == "Baseline Date" else "Max Date Week"
        formula = (
            "CASE [Day of Week Min Date] "
            + " ".join(
                "WHEN "
                + str(i)
                + " THEN DATETRUNC('week',["
                + field
                + "],'"
                + weekday
                + "')"
                for i, weekday in enumerate(
                    [
                        "Sunday",
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                    ],
                    1,
                )
            )
            + " END"
        )
        formulas.append((name, formula, "datetime", "dimension", "ordinal"))
    formulas.extend(
        [
            (
                "Date To Plot",
                "IF [Days between Min & Max]<=30 THEN [Baseline Date] ELSE [Baseline Date Week] END",
                "datetime",
                "dimension",
                "quantitative",
            ),
            (
                "Full Weeks only",
                "IF [Daily | Weekly]='Weekly' THEN [Date To Plot]<[Max Date Week] ELSE TRUE END",
                "boolean",
                "dimension",
                "nominal",
            ),
            ("Legend Label", "'# of Subs'", "string", "dimension", "nominal"),
            ("One", "1", "integer", "measure", "quantitative"),
        ]
    )
    for name, formula, datatype, role, kind in formulas:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    editor.add_calculated_field(
        "Date",
        "[Baseline Date]",
        datatype="date",
        role="dimension",
        field_type="quantitative",
    )
    editor.set_field_format("Date", "*mmmm dd")
    editor.add_calculated_field(
        "% of Total CY", "SUM([CY])/WINDOW_SUM(SUM([CY]))", table_calc="Rows"
    )
    editor.set_field_format("YoY%", "p0.0%")
    editor.set_field_format("% of Total CY", "p0.0%")
    editor.set_field_format("Baseline Date", "*mmmm dd")
    editor.set_field_format("Date To Plot", "*mmm dd")
    for name in ["Subscription", "CY", "PY"]:
        editor.set_field_format(name, "#,##0")
    filters = [
        {
            "column": "[Date]",
            "type": "quantitative",
            "min": "#2020-01-01#",
            "max": "#2020-07-14#",
            "context": True,
        },
        {"column": "Include Dates <Today", "values": [True], "context": True},
    ]
    editor.add_worksheet("Trend")
    editor.configure_layered_chart(
        "Trend",
        columns=["Daily | Weekly", "[Date To Plot]"],
        rows=["State", "SUM(Subscription)"],
        panes=[
            {
                "mark_type": "Line",
                "color": "YEAR(Subscription Date)",
                "color_map": {"2019": "#2cb5c0", "2020": "#a2b627"},
                "tooltip": ["MIN(Min Date)", "MAX(Max Date)"],
            }
        ],
        filters=filters + [{"column": "Full Weeks only", "values": [True]}],
    )
    editor.configure_worksheet_style(
        "Trend",
        hide_gridlines=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_row_label="State",
        axis_style={"title": ""},
    )
    editor.add_worksheet("Map")
    editor.configure_layered_chart(
        "Map",
        columns=["Longitude (generated)"],
        rows=["Latitude (generated)", "Latitude (generated)"],
        synchronized=True,
        fold_axes=True,
        hide_axes=True,
        panes=[
            {
                "axis": "Latitude (generated)",
                "mark_type": "Automatic",
                "geometry": "Geometry (generated)",
                "detail": "State",
                "color": "YoY%",
                "tooltip": ["SUM(CY)", "SUM(PY)", "MIN(Min Date)", "MAX(Max Date)"],
            },
            {
                "axis": "Latitude (generated)",
                "mark_type": "Circle",
                "detail": "State",
                "size": "SUM(CY)",
                "tooltip": ["SUM(CY)", "% of Total CY"],
                "mark_style": {"mark-color": "#000000", "size": "1.0"},
            },
        ],
        filters=filters + [{"column": "Full Weeks only", "values": [True]}],
        table_calc_overrides={
            "% of Total CY": [{"ordering_type": "Field", "ordering_field": "State"}]
        },
    )
    editor.configure_worksheet_style(
        "Map",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        color_style={"field": "YoY%", "palette": "blue_red_10_0", "center": "0"},
        map_style={"washout": "100"},
    )
    for pane in [0, 1]:
        editor.configure_custom_tooltip(
            "Map",
            runs=[
                {"field": "State", "bold": True, "fontsize": 15},
                {"text": "\nCY: "},
                {"field": "SUM(CY)", "fontcolor": "#a2b627"},
                {"text": " | PY: "},
                {"field": "SUM(PY)", "fontcolor": "#2cb5c0"},
                {"text": " | YoY: "},
                {"field": "YoY%"},
                {"text": "\n"},
                {
                    "sheet": {
                        "name": "Trend",
                        "filter_fields": ["State"],
                        "maxwidth": 500,
                        "maxheight": 400,
                    }
                },
            ],
            pane_index=pane,
        )
    editor.add_worksheet("# Subs Legend")
    editor.configure_layered_chart(
        "# Subs Legend",
        columns=["Legend Label"],
        panes=[
            {
                "mark_type": "Circle",
                "mark_sizing_off": True,
                "mark_style": {"mark-color": "#000000", "size": "0.999502778"},
            }
        ],
    )
    editor.configure_worksheet_style(
        "# Subs Legend",
        hide_col_field_labels=True,
        hide_borders=True,
        hide_gridlines=True,
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=700,
        worksheet_names=["Map", "# Subs Legend"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "horizontal",
                    "fixed_size": 74,
                    "children": [
                        {
                            "type": "text",
                            "text": "WHAT IS THE YEAR-OVER-YEAR TREND?",
                            "font_size": 15,
                            "fixed_size": 495,
                        },
                        {
                            "type": "worksheet",
                            "name": "# Subs Legend",
                            "show_title": False,
                            "fit": "entire",
                            "fixed_size": 120,
                        },
                        {
                            "type": "color",
                            "worksheet": "Map",
                            "field": "YoY%",
                            "pane_index": 1,
                            "fixed_size": 170,
                        },
                        {
                            "type": "filter",
                            "worksheet": "Map",
                            "field": "[Date]",
                            "caption": "Date",
                            "values": "relevant",
                            "show_domain": False,
                            "show_null_controls": False,
                        },
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Map",
                    "show_title": False,
                    "fit": "entire",
                },
                {
                    "type": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "text": "DESIGNED BY : KYLE YETTER",
                            "font_size": 8,
                            "font_color": "#4e79a7",
                        },
                        {
                            "type": "text",
                            "text": "#WOW2020 | WEEK 37",
                            "font_size": 8,
                            "font_color": "#4e79a7",
                        },
                        {
                            "type": "text",
                            "text": "DONNA COLES REFERENCE | CWTWB",
                            "font_size": 8,
                            "font_color": "#4e79a7",
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "https://www.workout-wednesday.com/2020w37/",
                    "font_size": 8,
                    "fixed_size": 30,
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
