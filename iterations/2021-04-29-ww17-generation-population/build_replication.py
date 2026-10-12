"""Rebuild the WW17 Generation Populations chart (Nathan Yau remake).

One sheet recreates Nathan Yau's "Generation Populations with rankings by most
people alive": a bar per birth year (1919-2019) grouped into seven generations,
each pane separated by a dashed divider and headed by the generation's rank,
name and total/percent, with the generation's first year labelled vertically.

The article's chain:

- ``Year = 2019 - [AGE]`` (the data only has AGE and the 2019 population).
- ``Generation`` buckets the years into Greatest Generation, Silent Generation,
  Baby Boomer, Generation X, Millennials, Generation Z and Gen Alpha.
- ``Total Population Per Generation = {FIXED [Generation], [SEX]:
  SUM([2019 Population])}`` then
  ``% of Total Population = SUM(...) / TOTAL(SUM(...))``.
- ``Rank = RANK_DENSE(SUM([Total Population Per Generation]))`` and
  ``Total | Percent`` builds the "72.1M | 22.0%" header string.
- ``Min Year per Generation = {FIXED [Generation], [SEX]: MIN([Year])}`` sorts
  the generations and supplies the dashed dividers.
- ``Point to Plot Year Label = IF [Year]=[Min Year per Generation] AND
  [Year]<>1919 THEN 4700000 END`` is a second row-axis measure; a tiny
  transparent Circle on it carries the vertical year label.
- ``Sort Position`` / ``Sort Position is +ve number`` alternate the two teal
  shades by pane.

The chart plots only ``SEX = 'Total'``.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/federated_13hsc36066ge55164w5tu1.hyper"
DASHBOARD = "2021_04_28_WW17_Generation_Population"

BACKGROUND = "#dcd2c4"
LIGHT_TEAL = "#00c3a9"
DARK_TEAL = "#00ad90"
PANE_COLORS = {"true": LIGHT_TEAL, "false": DARK_TEAL}


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Year and generation buckets ---------------------------------------
    editor.add_calculated_field(
        "Year",
        "2019-[AGE]",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    # The article's deliberate carriage returns in 'Greatest\nGeneration' and
    # 'Gen\nAlpha' wrap those headers onto two lines.
    editor.add_calculated_field(
        "Generation",
        "IF [Year]<= 1927 THEN 'Greatest \nGeneration'"
        " ELSEIF [Year]<= 1945 THEN 'Silent Generation'"
        " ELSEIF [Year]<=1964 THEN 'Baby Boomer'"
        " ELSEIF [Year] <= 1980 THEN 'Generation X'"
        " ELSEIF [Year]<=1996 THEN 'Millennials'"
        " ELSEIF [Year]<=2012 THEN 'Generation Z'"
        " ELSE 'Gen \nAlpha' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    # --- Population, percent, rank and header text -------------------------
    editor.add_calculated_field(
        "Total Population Per Generation",
        "{FIXED [Generation], [SEX]: SUM([2019 Population])}",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format="n#,##0,,.0M;-#,##0,,.0M",
    )
    editor.add_calculated_field(
        "% of Total Population",
        "SUM([Total Population Per Generation])"
        " / TOTAL(SUM([Total Population Per Generation]))",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0.0%",
    )
    editor.add_calculated_field(
        "Rank",
        "RANK_DENSE(SUM([Total Population Per Generation]))",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format='n"#"#,##0;-"#"#,##0',
    )
    editor.add_calculated_field(
        "Total | Percent",
        "STR(ROUND(SUM([Total Population Per Generation])/1000000,1)) + 'M'"
        " + ' | ' + STR(ROUND([% of Total Population] * 100,1)) +'%'",
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    # --- Sorting and pane shading ------------------------------------------
    editor.add_calculated_field(
        "Min Year per Generation",
        "{FIXED [Generation], [SEX]: MIN([Year])}",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Point to Plot Year Label",
        "IF [Year]=[Min Year per Generation] AND [Year]<>1919 THEN 4700000 END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Sort Position",
        "RANK_DENSE(MIN([Min Year per Generation]),'asc')",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Tooltip - 2019 Pop (1dpM)",
        "[2019 Population]",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format="n#,##0,,.0M;-#,##0,,.0M",
    )
    editor.add_calculated_field(
        "Sort Position is +ve number",
        "[Sort Position]%2=0",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )

    # --- The single chart sheet --------------------------------------------
    # Columns nest Rank / Total|Percent / Generation / Year so each generation
    # forms its own pane with a header stack.
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        # The outer column is the generation's first year, so panes run in
        # chronological order; the nested headers stack rank, name and totals.
        columns=[
            "Min Year per Generation",
            "Rank",
            "Generation",
            "Total | Percent",
            "Year",
        ],
        rows=["SUM(2019 Population)", "SUM(Point to Plot Year Label)"],
        axis_shelf="rows",
        fold_axes=True,
        synchronized=True,
        # No explicit sort: the outer column is the generation's first year, so
        # Tableau's natural ascending dimension order already runs 1919-2019.
        panes=[
            {
                "axis": "SUM(2019 Population)",
                "mark_type": "Bar",
                "color": "Sort Position is +ve number",
                "tooltip": ["SUM(2019 Population)", "Tooltip - 2019 Pop (1dpM)"],
                "selection_relaxation": "disallow",
            },
            {
                "axis": "SUM(Point to Plot Year Label)",
                "mark_type": "Circle",
                "label": "Min Year per Generation",
                "selection_relaxation": "disallow",
                "mark_style": {
                    "size": "0.1",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "color": "#00000000",
                },
            },
        ],
        filters=[{"column": "SEX", "values": ["Total"]}],
    )
    editor.set_datasource_color_palette(
        "Sort Position is +ve number", dict(PANE_COLORS)
    )
    editor.configure_worksheet_style(
        "Chart",
        background_color=BACKGROUND,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[
            {"field": "SUM(2019 Population)", "text-format": "n#,##0,,M;-#,##0,,M",
             "font-family": "Courier New", "font-size": "12"},
            # The per-year column headers and the first-year header are hidden;
            # the year is shown by the Circle pane's vertical label instead.
        ],
        # Only the Circle pane rotates its label vertically; the Year member
        # headers themselves are hidden (the year is shown by that label).
        header_formats=[
            {"field": "Year", "display": "false"},
            {"field": "Min Year per Generation", "display": "false"},
            {"field": "Rank", "font-family": "Courier New", "font-size": "14"},
            {"field": "Generation", "font-family": "Courier New", "font-size": "12"},
            {"field": "Total | Percent", "font-family": "Courier New", "font-size": "11"},
        ],
        axis_style={
            "per_field": [
                {"field": "SUM(2019 Population)", "attr": "title", "value": "Population [Millions]", "scope": "rows", "class": "0"},
                {"field": "SUM(Point to Plot Year Label)", "attr": "title", "value": "", "scope": "rows", "class": "0"},
            ],
            "encodings": [
                {
                    "field": "SUM(Point to Plot Year Label)",
                    "scope": "rows",
                    "class": "0",
                    "fold": "true",
                    "synchronized": "true",
                    "field-type": "quantitative",
                }
            ],
        },
        table_formats=[
            {"attr": "background-color", "value": BACKGROUND},
        ],
        # Dashed vertical pane dividers, as the article sets them.
        table_dividers=[
            {"scope": "rows", "stroke-size": "0", "line-visibility": "off"},
            {
                "scope": "cols",
                "line-visibility": "on",
                "line-pattern-only": "dashed",
                "stroke-color": "#000000",
                "stroke-size": "2",
            },
        ],
        pane_datalabel_style={
            "color-mode": "auto",
            "font-family": "Courier New",
            "font-size": "10",
        },
        # The Circle pane rotates its year label to vertical.
        panes_style={
            "2": {
                "cell_style": {
                    "text-orientation": "-90",
                    "text-align": "right",
                    "vertical-align": "top",
                },
                "datalabel_style": {
                    "color-mode": "auto",
                    "font-family": "Courier New",
                    "font-size": "10",
                },
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                },
            }
        },
    )

    # --- Dashboard ----------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "text",
                "runs": [
                    {"text": "BY BIRTH YEAR", "font_alignment": "1", "font_size": "12"},
                    {"text": "\nGENERATION POPULATIONS", "bold": True, "font_size": "20"},
                    {"text": "\nWITH RANKINGS BY MOST PEOPLE ALIVE", "font_size": "12"},
                ],
                "font_color": "#000000",
                "font_name": "Times New Roman",
                "absolute": {"x": 500, "y": 500, "w": 99000, "h": 9000},
            },
            {
                "type": "worksheet",
                "name": "Chart",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 500, "y": 10000, "w": 99000, "h": 85000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Inspiration: Nathan Yau | @FlowingData\nData: Census.gov",
                        "font_size": "10",
                        "font_alignment": "0",
                    }
                ],
                "font_name": "Times New Roman",
                "absolute": {"x": 500, "y": 96000, "w": 30000, "h": 4000},
            },
            {
                "type": "text",
                "runs": [
                    {"text": "#WOW2021 | 17", "font_size": "10", "font_alignment": "1"}
                ],
                "font_name": "Times New Roman",
                "absolute": {"x": 35000, "y": 96000, "w": 30000, "h": 4000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Sean Miller | @HipsterVizNinja",
                        "font_size": "10",
                        "font_alignment": "2",
                    }
                ],
                "font_name": "Times New Roman",
                "absolute": {"x": 66000, "y": 96000, "w": 33000, "h": 4000},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1250,
        height=800,
        layout=layout,
        worksheet_names=["Chart"],
    )
    editor.set_window_state("Chart", hidden=False)
    editor.set_worksheet_title("Chart", "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
