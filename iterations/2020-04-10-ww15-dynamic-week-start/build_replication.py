"""Rebuild dynamic weekday sales lines from locked Superstore data."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_04_08_WW15_Dynamic_Week_Start"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/daily-calendar.hyper"))
    e.add_parameter("1a.Week Ending On", "date", "#2019-10-24#", domain_type="any")
    e.add_parameter("1b.Include X Prior Weeks", "integer", "10", domain_type="any")
    specs = [
        (
            "Start of Selected Week",
            "DATEADD('day',-6,[1a.Week Ending On])",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "Day of Week Start",
            "DATENAME('weekday',[Start of Selected Week])",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Day of Week End",
            "DATENAME('weekday',[1a.Week Ending On])",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Dates To Include",
            "[Order Date]>=DATEADD('week',-[1b.Include X Prior Weeks],[Start of Selected Week]) AND [Order Date]<=[1a.Week Ending On]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Order Date Week",
            "DATE(DATEADD('day',-((DATEDIFF('day',[Start of Selected Week],[Order Date]) % 7 + 7) % 7),[Order Date]))",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "Order Date Baseline",
            "DATE(DATEADD('day',DATEDIFF('day',[Order Date Week],[Order Date]),[Start of Selected Week]))",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "Is Latest Week",
            "[Order Date Week]=[Start of Selected Week]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Inc Null Sales",
            "IFNULL(LOOKUP(SUM([Sales]),0),0)",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Tooltip Sales",
            "IF [Inc Null Sales]<>0 THEN SUM([Sales]) END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Tooltip No Sales",
            "IF [Inc Null Sales]=0 THEN 'no sales' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Tooltip Order Date",
            "IFNULL(ATTR([Order Date]),IFNULL(DATEADD('day',1,LOOKUP(ATTR([Order Date]),-1)),DATEADD('day',-1,LOOKUP(ATTR([Order Date]),1))))",
            "date",
            "dimension",
            "ordinal",
        ),
    ]
    specs.append(
        (
            "Week Series",
            "IF [Is Latest Week] THEN 'Current' ELSE 'Previous' END",
            "string",
            "dimension",
            "nominal",
        )
    )
    for name, formula, datatype, role, field_type in specs:
        options = (
            {"table_calc": "Rows"}
            if name
            in {
                "Inc Null Sales",
                "Tooltip Sales",
                "Tooltip No Sales",
                "Tooltip Order Date",
            }
            else {}
        )
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            **options,
        )
    for name, fmt in [
        ("Order Date Baseline", "*dddd"),
        ("Tooltip Order Date", "*mmmm d, yyyy"),
        ("Sales", 'c"$"#,##0;-"$"#,##0'),
        ("Inc Null Sales", 'c"$"#,##0;-"$"#,##0'),
        ("Tooltip Sales", 'c"$"#,##0;-"$"#,##0'),
    ]:
        e.set_field_format(name, fmt)
    e.add_worksheet("Viz")
    e.configure_layered_chart(
        "Viz",
        columns=["[Order Date Baseline]"],
        rows=["Inc Null Sales"],
        panes=[
            {
                "mark_type": "Line",
                "axis": "Inc Null Sales",
                "color": "Week Series",
                "detail": "[Order Date Week]",
                # Constant weekday dimensions must be view LOD fields: title tokens
                # cannot obtain their values from tooltip-only dependencies.
                "detail_extra": ["Day of Week Start", "Day of Week End"],
                "color_map": {"Current": "#19626b", "Previous": "#d6d6d6"},
                "tooltip": [
                    "Is Latest Week",
                    "Tooltip Order Date",
                    "Tooltip Sales",
                    "Tooltip No Sales",
                ],
            }
        ],
        fold_axes=False,
        filters=[{"column": "Dates To Include", "values": [True]}],
    )
    e.configure_worksheet_domain_range("Viz", ["[Order Date Baseline]"])
    e.configure_custom_tooltip(
        "Viz",
        [
            {"field": "Tooltip Order Date", "bold": True},
            {"text": "\nSales : "},
            {"field": "Tooltip Sales", "bold": True},
            {"field": "Tooltip No Sales", "bold": True},
            {"text": "\n\nWeeks are trended "},
            {"field": "Day of Week Start", "bold": True},
            {"text": " to "},
            {"field": "Day of Week End", "bold": True},
        ],
    )
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_sort_controls=True,
        pane_mark_style={"mark-markers-mode": "all", "mark-labels-show": "false"},
        axis_style={
            "encodings": [
                {
                    "field": "Inc Null Sales",
                    "attr": "space",
                    "type": "space",
                    "scope": "rows",
                    "field-type": "quantitative",
                    "min": "-1803.6639041945873",
                    "max": "18874.50433600786",
                    "range-type": "fixed",
                }
            ],
            "per_field": [
                {
                    "field": "Inc Null Sales",
                    "attr": "title",
                    "value": "Sales",
                    "scope": "rows",
                }
            ],
        },
    )
    e.set_worksheet_rich_title(
        "Viz",
        runs=[
            {"text": "DAILY SALES TREND | Weeks trended ", "fontsize": "12"},
            {"text": "<Day of Week Start>", "bold": True, "fontsize": "10"},
            {"text": " to ", "fontsize": "10"},
            {"text": "<Day of Week End>", "bold": True, "fontsize": "10"},
            {"text": "\nWeek ending on ", "fontsize": "9"},
            {
                "text": "<[Parameters].[1a.Week Ending On]>",
                "fontcolor": "#19626b",
                "fontsize": "9",
            },
            {"text": " vs prior ", "fontsize": "9"},
            {"text": "<[Parameters].[1b.Include X Prior Weeks]>", "fontsize": "9"},
            {"text": " weeks", "fontsize": "9"},
        ],
    )

    def zone(kind, x, y, w, h, **options):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1300 * 100000),
                "y": round(y / 700 * 100000),
                "w": round(w / 1300 * 100000),
                "h": round(h / 700 * 100000),
            },
            **options,
        }

    e.add_dashboard(
        DASHBOARD,
        width=1300,
        height=700,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone("worksheet", 8, 8, 1284, 612, name="Viz", fit="entire"),
                zone(
                    "paramctrl",
                    935,
                    15,
                    160,
                    48,
                    parameter="1a.Week Ending On",
                    caption="Week Ending On",
                    mode="datetime",
                ),
                zone(
                    "paramctrl",
                    1131,
                    15,
                    160,
                    48,
                    parameter="1b.Include X Prior Weeks",
                    caption="Include X Prior Weeks",
                    mode="type_in",
                ),
                zone(
                    "text",
                    8,
                    628,
                    428,
                    32,
                    text="DESIGNED BY : ANN JACKSON",
                    font_size="8",
                    font_color="#00646d",
                ),
                zone(
                    "text",
                    436,
                    628,
                    428,
                    32,
                    text="#WOW2020 | WEEK 15",
                    font_size="8",
                    font_color="#00646d",
                ),
                zone(
                    "text",
                    864,
                    628,
                    428,
                    32,
                    text="RECREATED WITH CWTWB",
                    font_size="8",
                    font_color="#00646d",
                ),
                zone(
                    "text",
                    8,
                    660,
                    1284,
                    32,
                    text="https://www.workout-wednesday.com/2020w15/",
                    font_size="8",
                    font_color="#006080",
                ),
            ],
        },
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
