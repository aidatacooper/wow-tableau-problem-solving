"""Rebuild the Olympics bump chart with native logical relationships and VIT."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_29_WW31_Olympic_Rank_Bump_Chart"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(
        str(HERE / "inputs/Extract (Multiple Connections).hyper"),
        tables=[
            {
                "name": "Host",
                "table": "Extract (Extract.Extract)_40C876C051114093BAFB7F02A036CAF2",
            },
            {
                "name": "Medals",
                "table": "Extract (Extract.Extract)_72FC953A3CC8413E948D79B8CD93DB49",
            },
            {
                "name": "Medalists",
                "table": "Extract (Extract.Extract)_1E9BB58A261F452EBE047898ABB2452A",
            },
        ],
        relationships=[
            {"left": "Host", "right": "Medals", "keys": [["Year", "Year"]]},
            {
                "left": "Medals",
                "right": "Medalists",
                "keys": [["Year", "Year"], ["Country", "Country"]],
            },
        ],
    )
    specs = [
        ("Country Name", "[Country (Medals)]", "string", "dimension", "nominal", None),
        (
            "Score",
            "IFNULL(SUM([Bronze]),0)+2*IFNULL(SUM([Silver]),0)+3*IFNULL(SUM([Gold]),0)",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Rank Score",
            "RANK_UNIQUE([Score])",
            "integer",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Top 10 Rank Only",
            "IF [Rank Score]<11 THEN [Rank Score] END",
            "integer",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Is Host?",
            "[Host Country]=[Country Name]",
            "boolean",
            "dimension",
            "nominal",
            None,
        ),
        (
            "COLOUR Country",
            "IF [Is Host?] THEN [Host Country] END",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        (
            "# Medals",
            "IFNULL(SUM([Bronze]),0)+IFNULL(SUM([Silver]),0)+IFNULL(SUM([Gold]),0)",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Hosted | Participated",
            "IF [Is Host?] THEN 'hosted' ELSE 'participated' END",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        (
            "Is Host in Top 10?",
            "WINDOW_MAX(IF ATTR([Is Host?]) AND [Rank Score]<=10 THEN 1 ELSE 0 END)",
            "integer",
            "dimension",
            "ordinal",
            "Rows",
        ),
        (
            "Host Indicator Size",
            "[Is Host in Top 10?]",
            "integer",
            "measure",
            "quantitative",
            "Rows",
        ),
        ("Index = Size", "INDEX()=SIZE()", "boolean", "dimension", "nominal", "Rows"),
        (
            "Score for Host",
            "WINDOW_MAX(IF ATTR([Is Host?]) THEN [Score] END)",
            "integer",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Medals for Host",
            "WINDOW_MAX(IF ATTR([Is Host?]) THEN [# Medals] END)",
            "integer",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Is Host or Top 10",
            "ATTR([Is Host?]) OR [Rank Score]<=10",
            "boolean",
            "dimension",
            "nominal",
            "Rows",
        ),
        (
            "COLOUR Host",
            "IF [Rank Score]>10 THEN 'Red' ELSEIF ATTR([Is Host?]) THEN 'Blue' ELSE 'Grey' END",
            "string",
            "dimension",
            "nominal",
            "Rows",
        ),
        (
            "Medalist Score",
            "CASE [Medal] WHEN 'Gold' THEN 3 WHEN 'Silver' THEN 2 WHEN 'Bronze' THEN 1 END",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Total Score per Athlete",
            "{FIXED [Year (Medalists)],[Country (Medalists)],[Athlete]:SUM([Medalist Score])}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
    ]
    for name, f, dt, role, kind, tc in specs:
        e.add_calculated_field(
            name, f, datatype=dt, role=role, field_type=kind, table_calc=tc
        )
    country = "Country Name"
    rank = [{"ordering_type": "Field", "ordering_field": country}]
    nested = [
        {"ordering_type": "Rows"},
        {
            "field": "Rank Score",
            "ordering_type": "Field",
            "order": [country, "COLOUR Country", "Is Host?"],
        },
    ]
    palette = {
        "Brazil": "#23b18d",
        "Australia": "#2bb5c0",
        "Canada": "#2ea865",
        "Belgium": "#32bdb1",
        "China": "#459f3b",
        "West Germany": "#4f7cba",
        "United States": "#7674c0",
        "Finland": "#8cb12c",
        "Sweden": "#9e6dc2",
        "Spain": "#c86abf",
        "France": "#c8bc21",
        "Japan": "#e33233",
        "Soviet Union": "#e670b6",
        "Italy": "#e9501f",
        "Germany": "#ecb921",
        "Mexico": "#ef3957",
        "Netherlands": "#f8557f",
        "Greece": "#f88113",
        "Great Britain": "#f8a21b",
        "South Korea": "#fe7caa",
        "%null%": "#b4b4b4",
    }
    e.add_worksheet("Bump")
    common = {
        "axis": "AGG(Top 10 Rank Only)",
        "detail": country,
        "tooltip": [
            "AGG(Score)",
            "AGG(# Medals)",
            "ATTR(Hosted | Participated)",
            "SUM(Gold)",
            "SUM(Silver)",
            "SUM(Bronze)",
        ],
    }
    e.configure_layered_chart(
        "Bump",
        columns=["Year"],
        rows=["AGG(Top 10 Rank Only)", "AGG(Top 10 Rank Only)"],
        panes=[
            {
                **common,
                "mark_type": "Line",
                "mark_style": {"size": "0.01", "mark-color": "#b4b4b4"},
            },
            {
                **common,
                "mark_type": "Shape",
                "shape": "Is Host?",
                "shape_map": {True: ":filled/asterisk", False: ":filled/circle"},
                "size": "Is Host?",
                "color": "COLOUR Country",
                "color_map": palette,
                "mark_style": {"size": "1.76468"},
            },
        ],
        table_calc_overrides={"AGG(Top 10 Rank Only)": nested},
        hide_axes=True,
    )
    e.configure_worksheet_style(
        "Bump",
        hide_gridlines=True,
        hide_borders=True,
        hide_zeroline=True,
        hide_sort_controls=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        axis_style={
            "encodings": [
                {"field": "AGG(Top 10 Rank Only)", "scope": "rows", "reverse": True}
            ]
        },
        label_formats=[{"field": "Year", "text-orientation": "0", "font-size": "8"}],
        pane_mark_style={
            "line-interpolation": "linear",
            "line-null-interpolation": "false",
        },
    )
    e.add_worksheet("Medals")
    e.configure_layered_chart(
        "Medals",
        columns=["Multiple Values"],
        rows=["Year", country, "Measure Names"],
        axis_shelf="columns",
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Bar",
                "measure_values": ["SUM(Gold)", "SUM(Silver)", "SUM(Bronze)"],
                "color": "Measure Names",
                "label": "Multiple Values",
                "color_map": {
                    "SUM(Gold)": "#edc948",
                    "SUM(Silver)": "#bab0ac",
                    "SUM(Bronze)": "#de8529",
                },
            }
        ],
        fold_axes=False,
    )
    e.add_worksheet("Top 10 Medalists")
    e.add_set(
        "Top Athletes",
        "Athlete",
        basis_field="Total Score per Athlete",
        aggregation="Sum",
        top_n=10,
    )
    e.configure_chart(
        "Top 10 Medalists",
        mark_type="Bar",
        rows=["Year", country, "Athlete"],
        columns=["Medal", "COUNT(Medal)"],
        color="Medal",
        label="COUNT(Medal)",
        filters=[{"column": "Top Athletes", "values": [True]}],
        sort_descending="SUM(Total Score per Athlete)",
        sort_field="Athlete",
    )
    e.add_worksheet("Top 10 Countries")
    e.configure_chart(
        "Top 10 Countries",
        mark_type="Bar",
        rows=["Year", "Host Country", country],
        columns=["AGG(Score)"],
        color="COLOUR Host",
        color_map={"Red": "#ff0000", "Blue": "#4e79a7", "Grey": "#bab0ac"},
        label="AGG(Score)",
        tooltip=["Is Host or Top 10"],
        filters=[{"column": "Is Host or Top 10", "values": [True]}],
        table_calc_overrides={
            "Is Host or Top 10": [
                {"ordering_type": "Columns"},
                {"field": "Rank Score", "ordering_type": "Field", "order": [country]},
            ],
            "COLOUR Host": [
                {"ordering_type": "Columns"},
                {"field": "Rank Score", "ordering_type": "Field", "order": [country]},
            ],
        },
        sort_descending="AGG(Score)",
        sort_field=country,
    )
    e.add_worksheet("Host in Top 10")
    e.configure_layered_chart(
        "Host in Top 10",
        columns=["Year"],
        rows=[],
        panes=[
            {
                "mark_type": "Shape",
                "detail": country,
                "shape": "Is Host in Top 10?",
                "shape_map": {1: ":filled/circle", 0: ":filled/times"},
                "size": "AGG(Host Indicator Size)",
                "tooltip": [
                    "AGG(Score for Host)",
                    "AGG(Medals for Host)",
                    "Index = Size",
                    "ATTR(Host Country)",
                ],
                "mark_style": {"mark-color": "#ff0000", "size": "1"},
            }
        ],
        filters=[{"column": "Index = Size", "values": [True]}],
        table_calc_overrides={
            "Is Host in Top 10?": [
                *rank,
                {"field": "Rank Score", "ordering_type": "Field", "order": [country]},
            ],
            "AGG(Host Indicator Size)": [
                *rank,
                {
                    "field": "Is Host in Top 10?",
                    "ordering_type": "Field",
                    "order": [country],
                },
                {"field": "Rank Score", "ordering_type": "Field", "order": [country]},
            ],
            "Index = Size": rank,
            "AGG(Score for Host)": rank,
            "AGG(Medals for Host)": rank,
        },
    )
    for sheet in ["Medals", "Top 10 Medalists", "Top 10 Countries", "Host in Top 10"]:
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_sort_controls=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
        )
    e.configure_worksheet_style(
        "Host in Top 10",
        label_formats=[{"field": "Year", "display": "false"}],
        size_style={
            "field": "AGG(Host Indicator Size)",
            "min": 0,
            "max": 1,
            "min_size": 0.2,
            "max_size": 1,
            "reverse": True,
        },
    )
    for pane in [0, 1]:
        e.configure_custom_tooltip(
            "Bump",
            [
                {"field": "Year"},
                {"text": " | "},
                {"field": country},
                {"text": "\n"},
                {"field": "AGG(Score)"},
                {"text": " score\n"},
                {
                    "sheet": {
                        "name": "Medals",
                        "maxwidth": 500,
                        "maxheight": 100,
                        "filter_fields": ["Year", country],
                    }
                },
                {"text": "\nTop 10 Athletes\n"},
                {
                    "sheet": {
                        "name": "Top 10 Medalists",
                        "maxwidth": 500,
                        "maxheight": 300,
                        "filter_fields": ["Year", country],
                        "filter_context": True,
                    }
                },
            ],
            pane_index=pane,
        )
    e.configure_custom_tooltip(
        "Host in Top 10",
        [
            {"field": "Year"},
            {"text": " host "},
            {"field": "Host Country"},
            {
                "sheet": {
                    "name": "Top 10 Countries",
                    "maxwidth": 500,
                    "maxheight": 300,
                    "filter_fields": ["Year"],
                }
            },
        ],
        pane_index=0,
    )

    def zone(kind, x, y, w, h, **kw):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1000 * 100000),
                "y": round(y / 700 * 100000),
                "w": round(w / 1000 * 100000),
                "h": round(h / 700 * 100000),
            },
            **kw,
        }

    children = [
        zone(
            "text",
            8,
            8,
            984,
            47,
            text="Can you show the Top 10 rank over time for each Olympic country?",
            font_size=14,
        ),
        zone("worksheet", 8, 55, 984, 541, name="Bump", show_title=False, fit="entire"),
        zone(
            "worksheet",
            8,
            596,
            984,
            32,
            name="Host in Top 10",
            show_title=False,
            fit="entire",
        ),
        zone(
            "text",
            8,
            628,
            308,
            32,
            text="DESIGNED BY: LORNA BROWN & SEAN MILLER",
            font_size=8,
        ),
        zone("text", 316, 628, 430, 32, text="#WOW2020 | WEEK 31", font_size=8),
        zone("text", 746, 628, 246, 32, text="RECREATED WITH CWTWB", font_size=8),
        zone(
            "text",
            8,
            660,
            492,
            32,
            text="https://www.workout-wednesday.com/2020w31/",
            font_size=8,
        ),
        zone("text", 500, 660, 492, 32, text="DATA: PREPPIN DATA WEEK 31", font_size=8),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=700,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Bump", "Host in Top 10"],
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
