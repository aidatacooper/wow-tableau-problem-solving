"""Build NFL player drilldown, sortable header and page controls through public APIs."""

from pathlib import Path
import re
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_09_30_WW40_NFLStats_Table_Layout"
PARAMETERS = [
    {
        "name": "pLevel",
        "datatype": "integer",
        "default_value": "2",
        "domain_type": "any",
    },
    {
        "name": "pPath",
        "datatype": "string",
        "default_value": "Overall",
        "domain_type": "any",
    },
    {
        "name": "pSelected Player ID",
        "datatype": "integer",
        "default_value": "10638",
        "domain_type": "any",
    },
    {
        "name": "pHeader MeasureNames ",
        "datatype": "string",
        "default_value": "Measure1",
        "domain_type": "any",
    },
    {
        "name": "pHeader Position",
        "datatype": "string",
        "default_value": "FB",
        "domain_type": "any",
    },
    {
        "name": "pRows Per Page",
        "datatype": "integer",
        "default_value": "10",
        "domain_type": "any",
    },
    {
        "name": "pPage No",
        "datatype": "integer",
        "default_value": "1",
        "domain_type": "any",
    },
]
CALCULATIONS = [
    {
        "name": "TDs",
        "formula": "[touchdown]",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "DD Level",
        "formula": "IIF([Max Level]=2 AND [player_id]=[pSelected Player ID],2,1)",
        "datatype": "integer",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "name": "Season to Display",
        "formula": "IF [pSelected Player ID] = [player_id] AND [Max Level]=2 THEN STR([season])\r\nELSE ''\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Max Level",
        "formula": "IIF([pLevel]=1,2,1)",
        "datatype": "integer",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "name": "Carries",
        "formula": "COUNT([player_id])",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Avg YPC",
        "formula": "SUM([yards])/[Carries]",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Measure1",
        "formula": "MIN(0.0)",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Measure Rows",
        "formula": "IF [position] = 'FB' THEN -1\r\nELSEIF [position] = 'H' THEN 0\r\nELSEIF [position] = 'P' THEN 1\r\nEND",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Measure1 | tf",
        "formula": "IF [pHeader MeasureNames ] = 'Measure1' \r\nAND [pHeader Position] = [position]\r\nTHEN TRUE\r\nELSE FALSE\r\nEND",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure1 |On",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]='Measure1'\r\nTHEN 'Carries'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "true",
        "formula": "TRUE",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "false",
        "formula": "FALSE",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Sort Measure Value",
        "formula": "CASE [pHeader MeasureNames ]\r\nWHEN 'Measure1' THEN [Carries]\r\nWHEN 'Measure2' THEN SUM([yards])\r\nWHEN 'Measure3' THEN [Avg YPC]\r\nWHEN 'Measure4' THEN SUM([TDs])\r\nEND",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Sort",
        "formula": "IF [pHeader Position] = 'P'\r\n//up arrow selected, sort ascending\r\nTHEN -1 * [Sort Measure Value]\r\nELSE [Sort Measure Value]\r\nEND",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Tooltip - Sort",
        "formula": "IF [Measure Rows] = 1 THEN 'Sort Ascending'\r\nELSEIF  [Measure Rows] = -1 THEN 'Sort Descending'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Player ID Index",
        "formula": "INDEX()",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Page | Player ID Index",
        "formula": "((([Player ID Index]-1) - (([Player ID Index]-1) % [pRows Per Page]))/[pRows Per Page])+1",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Is Page No?",
        "formula": "[Page | Player ID Index] = [pPage No]",
        "datatype": "boolean",
        "role": "measure",
        "field_type": "nominal",
    },
    {
        "name": "Page No Minus 1",
        "formula": "IIF([pPage No]=1,1,[pPage No]-1)",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Page No Plus 1",
        "formula": "IF [pPage No] = [Total Pages]\r\nTHEN [Total Pages]\r\nELSE [pPage No]+1\r\nEND",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Current Page No",
        "formula": "[pPage No]",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Total Pages",
        "formula": "FLOOR({COUNTD([player_id])}/[pRows Per Page])+1",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "First Page No",
        "formula": "1",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Display Player ID",
        "formula": "[player_id]",
        "datatype": "integer",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "name": "Measure1 |Off",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]<>'Measure1'\r\nTHEN 'Carries'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure2",
        "formula": "MIN(0.0)",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Measure2 | tf",
        "formula": "IF [pHeader MeasureNames ] = 'Measure2' \r\nAND [pHeader Position] = [position]\r\nTHEN TRUE\r\nELSE FALSE\r\nEND",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure3 | tf",
        "formula": "IF [pHeader MeasureNames ] = 'Measure3' \r\nAND [pHeader Position] = [position]\r\nTHEN TRUE\r\nELSE FALSE\r\nEND",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure4 | tf",
        "formula": "IF [pHeader MeasureNames ] = 'Measure4' \r\nAND [pHeader Position] = [position]\r\nTHEN TRUE\r\nELSE FALSE\r\nEND",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure2 |Off",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]<>'Measure2'\r\nTHEN 'Yards'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure2 |On",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]='Measure2'\r\nTHEN 'Yards'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure3 |On",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]='Measure3'\r\nTHEN 'Avg YPC'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure4 |On",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]='Measure4'\r\nTHEN 'TDs'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure3",
        "formula": "MIN(0.0)",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Measure3 |Off",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]<>'Measure3'\r\nTHEN 'Avg YPC'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure4 |Off",
        "formula": "IF [Measure Rows] = 0 AND [pHeader MeasureNames ]<>'Measure4'\r\nTHEN 'TDs'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "name": "Measure4",
        "formula": "MIN(0.0)",
        "datatype": "real",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "name": "Player ID Arrow",
        "formula": "IF [pSelected Player ID] = [player_id] AND [Max Level]=2 THEN '\u25bc' ELSE '\u25b6' END",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    for parameter in PARAMETERS:
        e.add_parameter(**parameter)
    table_fields = {"Player ID Index", "Page | Player ID Index", "Is Page No?"}
    pending = {field["name"]: dict(field) for field in CALCULATIONS}
    pending["Player ID Arrow"]["formula"] = (
        "IF [pSelected Player ID] = [player_id] AND [Max Level]=2 "
        "THEN '\u25bc' ELSE '\u25b6' END"
    )
    ordered = []
    while pending:
        ready = [
            name
            for name, item in pending.items()
            if not (set(re.findall(r"\[([^\]]+)\]", item["formula"])) & set(pending))
        ]
        if not ready:
            raise ValueError(f"Calculation cycle: {list(pending)}")
        ordered.extend(pending.pop(name) for name in ready)
    for field in ordered:
        kwargs = {
            "field_name": field["name"],
            "formula": field["formula"],
            "datatype": field["datatype"],
            "role": field["role"],
            "field_type": field["field_type"],
        }
        if field["name"] in table_fields:
            kwargs["table_calc"] = "Columns"
        e.add_calculated_field(**kwargs)
    e.add_calculated_field(
        "Player Header",
        '"Player ID"',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Header Position",
        "[Measure Rows]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    for i, label in enumerate(["Carries", "Yards", "Avg YPC", "TDs"], 1):
        e.add_calculated_field(
            f"Header Label{i}",
            f"CASE [Measure Rows] WHEN -1 THEN '\u25bc' WHEN 1 THEN '\u25b2' ELSE '{label}' END",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        e.set_datasource_color_palette(
            f"Measure{i} | tf", {True: "#5c6068", False: "#d3d3d3"}
        )
        e.add_calculated_field(
            f"Header Selected{i}",
            f"IF [position]='H' THEN [pHeader MeasureNames ]='Measure{i}' ELSE [Measure{i} | tf] END",
            datatype="boolean",
            role="dimension",
            field_type="nominal",
        )
        e.set_datasource_color_palette(
            f"Header Selected{i}", {True: "#5c6068", False: "#d3d3d3"}
        )
    e.set_field_format("Avg YPC", "n0.00;-0.00")
    for field in ["Carries", "yards", "TDs"]:
        e.set_field_format(field, "n#,##0;-#,##0")
    for sheet in ["Header", "Table", "Prev Page", "Curr Page", "Next Page"]:
        e.add_worksheet(sheet)
    e.configure_layered_chart(
        "Header",
        rows=["Player Header", "Header Position"],
        columns=[f"Measure{i}" for i in range(1, 5)],
        panes=[
            {
                "axis": f"Measure{i}",
                "mark_type": "Text",
                "color": f"Header Selected{i}",
                "labels": [f"Header Label{i}"],
                "detail": "position",
                "detail_extra": [
                    "MIN(First Page No)",
                    "true",
                    "false",
                    f"Measure{i} | tf",
                ],
                "label_runs": [{"field": f"Header Label{i}", "fontsize": 9}],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
            for i in range(1, 5)
        ],
        filters=[{"column": "position", "values": ["FB", "H", "P"]}],
        fold_axes=False,
        axis_shelf="columns",
    )
    e.configure_layered_chart(
        "Table",
        rows=["player_id", "Player ID Arrow", "Display Player ID", "Season to Display"],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Automatic",
                "label": "Multiple Values",
                "measure_values": ["Carries", "SUM(yards)", "Avg YPC", "SUM(TDs)"],
                "color": "DD Level",
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
        ],
        filters=[{"column": "Is Page No?", "values": [True]}],
        sort_field="player_id",
        sort_descending="Sort",
        sort_mode="computed",
        table_calc_overrides={
            "Is Page No?": [
                {"ordering_type": "Columns"},
                {"field": "Page | Player ID Index", "ordering_type": "Columns"},
                {"field": "Player ID Index", "ordering_type": "Columns"},
            ]
        },
    )
    e.set_datasource_color_palette("DD Level", {"1": "#333333", "2": "#008682"})
    e.add_calculated_field(
        "Previous Page Glyph",
        "'\u25c0'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Next Page Glyph",
        "'\u25b6'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    for name, field, glyph in [
        ("Prev Page", "Page No Minus 1", "Previous Page Glyph"),
        ("Next Page", "Page No Plus 1", "Next Page Glyph"),
    ]:
        e.configure_layered_chart(
            name,
            panes=[
                {
                    "mark_type": "Text",
                    "detail": f"MIN({field})",
                    "detail_extra": ["true", "false"],
                    "labels": [glyph],
                    "label_runs": [{"field": glyph, "fontsize": 14}],
                    "mark_style": {
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                    },
                }
            ],
        )
    e.configure_layered_chart(
        "Curr Page",
        panes=[
            {
                "mark_type": "Text",
                "labels": ["MIN(Current Page No)", "MIN(Total Pages)"],
                "label_runs": [
                    {"field": "MIN(Current Page No)"},
                    {"text": " of "},
                    {"field": "MIN(Total Pages)"},
                ],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
        ],
    )
    for sheet in ["Header", "Table", "Prev Page", "Curr Page", "Next Page"]:
        e.configure_worksheet_style(
            sheet,
            hide_axes=sheet != "Table",
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
            pane_datalabel_style={"font-size": 9},
            pane_cell_style={
                "text-align": "center" if sheet == "Table" else "right",
                "vertical-align": "center",
            },
            cell_formats=[{"height": 14}],
            table_formats=[
                {"attr": "band-color", "value": "#f5f5f5", "scope": "rows"},
                {"attr": "band-size", "value": "1", "scope": "rows"},
                {"attr": "band-level", "value": "3", "scope": "rows"},
            ],
        )
    e.configure_worksheet_style(
        "Header",
        hide_row_label="Header Position",
        hide_axes=True,
        header_formats=[{"field": "Player Header", "width": 196}],
        table_formats=[{"attr": "band-color", "value": "#ffffff", "scope": "rows"}],
    )
    e.configure_worksheet_style(
        "Table",
        hide_row_label="player_id",
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        cell_formats=[{"text-align": "center"}],
        header_formats=[
            {"field": "Player ID Arrow", "width": 32},
            {"field": "Display Player ID", "width": 100},
            {"field": "Season to Display", "width": 64},
        ],
        label_formats=[
            {"scope": "rows", "text-align": "center", "vertical-align": "center"},
            {"scope": "cols", "text-align": "center", "vertical-align": "center"},
            {"field": "Measure Names", "display": "false"},
            {
                "field": "Display Player ID",
                "text-format": "n0;-0",
                "font-size": 9,
                "font-weight": "normal",
                "font-color": "#666666",
                "text-align": "left",
                "vertical-align": "auto",
            },
        ],
        table_dividers=[
            {
                "scope": "rows",
                "line-visibility": "on",
                "line-pattern-only": "solid",
                "stroke-color": "#e0e0e0",
            }
        ],
    )

    def zone(kind, x, y, w, h, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 900 * 100000),
                "y": round(y / 600 * 100000),
                "w": round(w / 900 * 100000),
                "h": round(h / 600 * 100000),
            },
            "style": {"margin": 4},
            **kwargs,
        }

    zones = [
        zone(
            "text",
            8,
            8,
            884,
            40,
            runs=[
                {
                    "text": "NFL Running Back Statistics (2017 - 2019)",
                    "font_size": 20,
                    "bold": True,
                    "font_color": "#5c6068",
                    "font_alignment": "0",
                }
            ],
        ),
        zone(
            "text",
            8,
            48,
            884,
            63,
            runs=[
                {
                    "text": "Check the total statistics for NFL players that have participated in a running play from 2017-2019. Click the headers to sort, expand a player to see seasons, then scroll through the pages at the bottom right.",
                    "font_size": 8,
                    "font_alignment": "0",
                }
            ],
        ),
        zone(
            "worksheet",
            8,
            111,
            884,
            69.33,
            name="Header",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            8,
            180.33,
            884,
            346.67,
            name="Table",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            661,
            530,
            76,
            59,
            name="Prev Page",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            737,
            530,
            76,
            59,
            name="Curr Page",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            813,
            530,
            76,
            59,
            name="Next Page",
            fit="entire",
            show_title=False,
        ),
        zone(
            "text",
            8,
            527,
            592,
            65,
            runs=[
                {
                    "text": "#WOW2020 | WEEK 40  /  SportsVizSunday  /  Recreated by @DonnaColes30",
                    "font_size": 8,
                    "font_alignment": "0",
                }
            ],
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=900,
        height=600,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": zones,
        },
    )
    for caption, sheet, field, target in [
        ("Selected Player", "Table", "Display Player ID", "pSelected Player ID"),
        ("Set Level", "Table", "DD Level", "pLevel"),
        ("Set Sort Direction", "Header", "position", "pHeader Position"),
        ("Set Sort Measure", "Header", "Measure Names", "pHeader MeasureNames "),
        ("Reset Page", "Header", "MIN(First Page No)", "pPage No"),
        ("Page -", "Prev Page", "MIN(Page No Minus 1)", "pPage No"),
        ("Page +", "Next Page", "MIN(Page No Plus 1)", "pPage No"),
    ]:
        e.add_dashboard_action(
            DASHBOARD,
            "parameter",
            source_sheet=sheet,
            source_field=field,
            target_parameter=target,
            caption=caption,
            event_type="on-select",
            aggregation="attr",
        )
    for sheet in ["Header", "Prev Page", "Next Page"]:
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"true": "false"},
            caption=f"{sheet} deselect",
            event_type="on-select",
        )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
