"""Rebuild the WW24 John Snow cholera outbreak map.

The challenge (Lorna Brown, rebuilt by Donna Coles) recreates John Snow's 1854
cholera map: a density layer of the 489 individual deaths, a buffer around the
selected pump whose radius is that pump's average distance to every death, the
eight pumps, and the aggregated death locations sized by death count. Two bar
charts rank the pumps by average distance and by the number of deaths within
that distance. Selecting a pump anywhere updates everything.

Chain:
  data (water_pumps + deaths_individual + deaths_aggregate)
  → materialise ONE flat Extract at the (pump x individual death) grain, because
    Tableau Cloud refuses to connect to the author's three-table Hyper
    relationship (403132) and the DISTANCE calculation needs both rows anyway
  → Pump Location / Individual Death Location = MAKEPOINT(...)
  → Distance Pump to Death = DISTANCE(...,'m')
  → Avg Distance = {FIXED [PumpID]: AVG(...)}
  → Number Deaths within Avg Distance = SUM(INT(distance <= avg))
  → pSelectedPump + Is Selected Pump? + the {FIXED} selected-pump lat/lon,
    location and average distance that drive the buffer
  → Pump Buffer = BUFFER(selected location, selected avg distance,'m')
  → Avg Distance to Pump / Total Deaths within Avg Distance bar charts
  → 4-layer map (density, buffer, pumps, aggregated deaths)
  → dashboard: one parameter action (select a pump) and three True->False
    filter actions that stop the click from leaving a highlight behind
"""

import math
from pathlib import Path

from cwtwb import TWBEditor
from tableauhyperapi import (
    Connection,
    CreateMode,
    HyperProcess,
    Inserter,
    SqlType,
    TableDefinition,
    TableName,
    Telemetry,
)

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "inputs/water_pumps.hyper"
DERIVED = HERE / "outputs/cholera-extract.hyper"
DASHBOARD = "2021_06_15_WW24_Cholera_Outbreak_Map"

PUMPS_TABLE = "water_pumps.csv_9B7DA11BB1144B19BDD982A9268B75E0"
DEATHS_TABLE = "deaths_individual.csv_162009320E3A4F70866D724FA8898FC7"
AGG_TABLE = "deaths_aggregate.csv_1892F1A4B2974F6F83AF8CAD9933D259"

BACKGROUND = "#f5f1f0"
DENSITY = "#5b8fb9"
PUMP_COLOR = "#e4572e"
DEATH_COLOR = "#333333"
BAR_TITLE = "Pump ID"


def normalize():
    """Materialise one flat (pump x individual death) Extract table.

    The author relates three Hyper tables with 1=1 relationship calculations.
    Tableau Cloud returns 403132 for that multi-table datasource, and the
    ``DISTANCE`` calculation is defined per pump/death pair anyway, so the flat
    table carries every pair plus the aggregated location columns.
    """
    target = TableName("Extract", "Extract")
    definition = TableDefinition(
        target,
        [
            TableDefinition.Column("PumpID", SqlType.big_int()),
            TableDefinition.Column("Location", SqlType.text()),
            TableDefinition.Column("PumpLon", SqlType.double()),
            TableDefinition.Column("PumpLat", SqlType.double()),
            TableDefinition.Column("DeathID", SqlType.big_int()),
            TableDefinition.Column("DeathLon", SqlType.double()),
            TableDefinition.Column("DeathLat", SqlType.double()),
            TableDefinition.Column("LocID", SqlType.big_int()),
            TableDefinition.Column("Deaths", SqlType.big_int()),
        ],
    )
    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(SOURCE)) as source:
            pumps = source.execute_list_query(
                f'SELECT "PumpID","Location","PumpLon","PumpLat" '
                f'FROM {TableName("Extract", PUMPS_TABLE)} ORDER BY 1'
            )
            deaths = source.execute_list_query(
                f'SELECT "DeathID","DeathLon","DeathLat" '
                f'FROM {TableName("Extract", DEATHS_TABLE)} ORDER BY 1'
            )
            aggregates = source.execute_list_query(
                f'SELECT "LocID","Deaths","DeathLon","DeathLat" '
                f'FROM {TableName("Extract", AGG_TABLE)} ORDER BY 1'
            )

        # Map each individual death onto its aggregated location row.
        location_by_coords = {
            (round(lon, 9), round(lat, 9)): (loc_id, count)
            for loc_id, count, lon, lat in aggregates
        }
        assert len(pumps) == 8 and len(deaths) == 489 and len(aggregates) == 250
        assert sum(count for _l, count, _lon, _lat in aggregates) == len(deaths)

        with Connection(hyper.endpoint, str(DERIVED), CreateMode.CREATE_AND_REPLACE) as db:
            db.catalog.create_schema("Extract")
            db.catalog.create_table(definition)
            with Inserter(db, definition) as inserter:
                for pump_id, location, pump_lon, pump_lat in pumps:
                    for death_id, death_lon, death_lat in deaths:
                        key = (round(death_lon, 9), round(death_lat, 9))
                        loc_id, count = location_by_coords[key]
                        inserter.add_row(
                            [
                                pump_id, location, pump_lon, pump_lat,
                                death_id, death_lon, death_lat, loc_id, count,
                            ]
                        )
                inserter.execute()
    return DERIVED


def add_measures(editor: TWBEditor) -> None:
    editor.add_parameter(
        "pSelectedPump",
        datatype="integer",
        default_value="1",
        domain_type="any",
    )

    editor.add_calculated_field(
        "Pump Location",
        "MAKEPOINT([PumpLat],[PumpLon])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Individual Death Location",
        "MAKEPOINT([DeathLat],[DeathLon])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Death Location",
        "MAKEPOINT([DeathLat],[DeathLon])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Distance Pump to Death",
        "DISTANCE([Pump Location], [Individual Death Location],'m')",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Avg Distance",
        "{FIXED [PumpID]: AVG([Distance Pump to Death])}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='n#,##0"m";-#,##0"m"',
    )
    editor.add_calculated_field(
        "Number Deaths within Avg Distance",
        "SUM(INT([Distance Pump to Death] <= [Avg Distance]))",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Is Selected Pump?",
        "[PumpID]=[pSelectedPump]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Selected Pump Lat",
        "{FIXED: MIN(IIF([Is Selected Pump?],[PumpLat],NULL))}",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Selected Pump Long",
        "{FIXED: MIN(IIF([Is Selected Pump?],[PumpLon],NULL))}",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Selected Pump Location",
        "MAKEPOINT([Selected Pump Lat],[Selected Pump Long])",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Selected Pump Avg Distance",
        "{FIXED :SUM( IF [Is Selected Pump?] THEN [Avg Distance] END)}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='n#,##0"m";-#,##0"m"',
    )
    editor.add_calculated_field(
        "Pump Buffer",
        "BUFFER([Selected Pump Location],[Selected Pump Avg Distance],'m')",
        datatype="spatial",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "True",
        "True",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "False",
        "False",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    # The flat table repeats each aggregated location once per pump, so the
    # circle size uses a FIXED lookup of the location's own death count.
    editor.add_calculated_field(
        "Deaths (Location)",
        "{FIXED [LocID]: MIN([Deaths])}",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )


def build_bars(editor: TWBEditor) -> None:
    for sheet, measure in (
        ("Avg Distance to Pump", "Avg Distance"),
        ("Total Deaths within Avg Distance", "Number Deaths within Avg Distance"),
    ):
        editor.add_worksheet(sheet)
        editor.configure_chart(
            sheet,
            mark_type="Bar",
            rows=["PumpID"],
            columns=[measure],
            color="Is Selected Pump?",
            color_map={"true": "#000000", "false": BACKGROUND},
            label=measure,
            detail="True",
            tooltip=["PumpID", measure],
        )
        editor.configure_worksheet_style(
            sheet,
            background_color=BACKGROUND,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            pane_mark_style={
                "mark-labels-show": "true",
                "mark-labels-cull": "false",
                "has-stroke": "true",
                "stroke-color": "#000000",
            },
            cell_formats=[{"field": "PumpID", "height": "36"}],
            label_formats=[{"field": "PumpID", "font-size": "8"}],
            table_formats=[{"attr": "background-color", "value": BACKGROUND}],
        )
        editor.set_worksheet_title(sheet, sheet)


def build_map(editor: TWBEditor) -> None:
    editor.add_worksheet("Map")
    # A density (Heatmap) mark is gated behind the ``Heatmap`` manifest entry;
    # without it Desktop refuses the whole workbook even though the XML is
    # schema-valid.
    editor._ensure_manifest_entry("Heatmap")
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="Individual Death Location",
        map_layer_mode="native",
        map_layers=[
            # Bottom layer: the death density.
            {
                "mark_type": "Heatmap",
                "detail": ["Individual Death Location", "DeathID"],
                "tooltip": [],
            },
            # The selected pump's average-distance buffer.
            {
                "mark_type": "Automatic",
                "name": "Pump Buffer",
                "geometry": "Pump Buffer",
                "detail": ["PumpID"],
                "tooltip": ["Selected Pump Avg Distance"],
                "mark_color": BACKGROUND,
            },
            # The eight pumps.
            {
                "mark_type": "Circle",
                "name": "Pumps",
                "detail": ["Pump Location", "Is Selected Pump?", "True", "False"],
                "label": "PumpID",
                "tooltip": ["Location"],
                "mark_color": PUMP_COLOR,
                "has_stroke": True,
                "stroke_color": "#333333",
            },
            # Aggregated death locations, sized by the death count.
            {
                "mark_type": "Circle",
                "name": "Deaths Agg",
                "detail": ["Death Location", "LocID"],
                "size": "Deaths (Location)",
                "mark_color": DEATH_COLOR,
                "has_stroke": True,
                "stroke_color": "#ffffff",
            },
        ],
    )
    editor.configure_worksheet_style(
        "Map",
        background_color=BACKGROUND,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        map_style={
            "map_style": "normal",
            "washout": 0,
            "layers": {
                "base": False,
                "landcover": False,
                "terrain": False,
                "coastline": False,
                "park": False,
                "airport": False,
                "building": False,
                "streets": True,
                "highways": True,
                "routes": True,
                "admin-0-boundaries": False,
                "admin-1-boundaries": False,
                "admin-0-boundaries-bg": False,
                "admin-1-boundaries-bg": False,
            },
        },
    )


def build_dashboard(editor: TWBEditor) -> None:
    def pos(x, y, w, h):
        return {
            "x": round(x / 989 * 100000),
            "y": round(y / 590 * 100000),
            "w": round(w / 989 * 100000),
            "h": round(h / 590 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "1854 Cholera Outbreak",
                    "font_size": 20,
                    "font_color": "#000000",
                    "bold": True,
                },
                {"text": "\u00c6\n"},
                {
                    "text": "Click a pump to show the Average Distance and the "
                            "number of deaths within that distance",
                    "font_size": 11,
                    "font_color": "#000000",
                },
            ],
            "absolute": pos(10, 8, 600, 44),
        },
        {
            "type": "worksheet",
            "name": "Map",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 58, 520, 500),
        },
        {
            "type": "worksheet",
            "name": "Avg Distance to Pump",
            "show_title": True,
            "fit": "entire",
            "absolute": pos(534, 58, 450, 230),
        },
        {
            "type": "worksheet",
            "name": "Total Deaths within Avg Distance",
            "show_title": True,
            "fit": "entire",
            "absolute": pos(534, 296, 450, 262),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "CHALLENGE BY : LORNA BROWN",
                    "font_size": 9,
                    "font_color": "#333333",
                    "bold": True,
                }
            ],
            "absolute": pos(8, 562, 300, 22),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021  |  WEEK 24",
                    "font_size": 9,
                    "font_color": "#333333",
                    "bold": True,
                    "font_alignment": 1,
                }
            ],
            "absolute": pos(400, 562, 200, 22),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "RECREATED BY : DONNA COLES",
                    "font_size": 9,
                    "font_color": "#333333",
                    "bold": True,
                    "font_alignment": 2,
                }
            ],
            "absolute": pos(690, 562, 292, 22),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=989,
        height=590,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=[
            "Map",
            "Avg Distance to Pump",
            "Total Deaths within Avg Distance",
        ],
    )

    # Selecting a pump on any of the three sheets sets the parameter. The
    # author uses one action with no worksheet attribute (all dashboard
    # sheets); the SDK needs an explicit source, so one action per sheet is the
    # equivalent construction.
    for sheet in (
        "Map",
        "Avg Distance to Pump",
        "Total Deaths within Avg Distance",
    ):
        editor.add_dashboard_action(
            DASHBOARD,
            action_type="parameter",
            source_sheet=sheet,
            source_field="PumpID",
            target_parameter="pSelectedPump",
            aggregation="sum",
            caption="Select Pump" if sheet == "Map" else f"Select Pump - {sheet}",
        )
    # Clicking must not leave a highlight behind on any of the three sheets.
    for sheet in (
        "Map",
        "Avg Distance to Pump",
        "Total Deaths within Avg Distance",
    ):
        editor.add_dashboard_action(
            DASHBOARD,
            action_type="filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"True": "False"},
            caption=f"{sheet} - Unhighlight",
        )

    for name in ("Map", "Avg Distance to Pump", "Total Deaths within Avg Distance"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)


def build():
    data = normalize()
    editor = TWBEditor("")
    editor.set_hyper_connection(str(data))

    add_measures(editor)
    build_bars(editor)
    build_map(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
