"""Build the WW01 2022 wildlife-strikes dashboard with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from ``inputs/`` (see
``verify_replication.py`` for the independent Hyper oracle). Visual constants
(palette hexes, dashboard geometry, footer credits) mirror ``analysis.md``.

The author's filled map uses a packaged spatial table related to the strike
extract on ``State Name = NAME``. The released SDK inspects that Hyper
``TABLEAU.TABGEOGRAPHY`` column as a string, so a geometry encoding produces no
marks (verified on Cloud: the map view exports zero rows). The replica keeps the
author's two-table logical relationship but renders the map through Tableau's
native state geographic role, which yields the same per-state filled map. See
``analysis.md`` and ``case.yaml`` for the recorded workaround.
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = (
    ITERATION_DIR
    / "inputs"
    / "2022_01_05_WW01_FAA Wildlife strikes (1990-2021).hyper"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2022_01_05_WW01_WildlifeWStrikes"
POST_URL = "https://www.workout-wednesday.com/2022w01tab/"
DATA_URL = "https://wildlife.faa.gov/search"

# Physical Extract tables inside the packaged Hyper file.
STRIKES_TABLE = (
    "2022_01_05_WW01_FAA Wildlife strikes (1990-2021).csv_"
    "C67D25C483BA4EAB884EC73253D02E3D"
)
STATES_TABLE = "Extract (Extract.Extract)_C91EDBA13DE94D71AF94506067CAD581"

# The author's red-gold sequential range for the map legend.
MAP_PALETTE = "red_gold_10_0"
SALMON = "#ee8d78"
OTHER_GRAY = "#a2a2a2"
UNKNOWN_RED = "#e15759"

# Tableau's background map layers, all switched off like the author's Map >
# Map Layers configuration.
DISABLED_MAP_LAYERS = {
    name: False
    for name in (
        "background",
        "barrier_line-land-polygon",
        "barrier_line-land-line",
        "national_park",
        "pitch",
        "industrial",
        "built-up-area",
        "water",
        "waterway-river-canal",
        "aeroway-polygon",
        "aeroway-runway",
        "aeroway-taxiway",
        "parks",
        "landcover_wood",
        "landcover_scrub",
        "landcover_grass",
        "landcover_crop",
        "admin-0-boundaries-bg",
        "admin-0-boundaries",
        "admin-0-boundaries-dispute",
        "admin-0-label-5th-tier",
        "admin-0-label-4th-tier",
        "admin-0-label-3rd-tier",
        "admin-0-label-2nd-tier",
        "admin-0-label-1st-tier",
        "admin-0-boundaries-bg-sub",
        "admin-1-boundaries-supress-bg",
        "admin-1-boundaries-sm-parents-bg",
        "admin-1-boundaries-md-parents-bg",
        "admin-1-boundaries-lg-parents-bg",
        "admin-0-boundaries-dispute-sub",
        "admin-0-boundaries-sub",
        "admin-1-boundaries-supress",
        "admin-1-boundaries-sm-parents",
        "admin-1-boundaries-md-parents",
        "admin-1-boundaries-lg-parents",
        "admin1-water-lines-usa-tableau",
        "9-dash-line-casing",
        "9-dash-line",
        "admin-1-label-9th-tier",
        "admin-1-label-8th-tier",
        "admin-1-label-7th-tier",
        "admin-1-label-6th-tier",
        "admin-1-label-5th-tier",
        "admin-1-label-4th-tier",
        "admin-1-label-3rd-tier",
        "admin-1-label-2nd-tier",
        "admin-1-label-1st-tier",
        "us-admin-1-label-abbr-3rd-tier",
        "us-admin-1-label-abbr-2nd-tier",
        "us-admin-1-label-abbr-1st-tier",
    )
}

TITLE_RUNS_BAR = [{"text": "Incidents by Animal Type <Title: Selected State>"}]
TITLE_RUNS_AREA = [
    {"text": "<[Parameters].pSelectedSpecies> Incidents Over Time "},
    {"text": "<Title: Selected State>"},
]


def _footer(text: str, alignment: str, x: int, width: int) -> dict:
    return {
        "type": "text",
        "runs": [
            {
                "text": text,
                "bold": True,
                "font_size": "8",
                "font_color": SALMON,
                "font_name": "Tableau Medium",
                "font_alignment": alignment,
            }
        ],
        "absolute": {"x": x, "y": 93111, "w": width, "h": 3556},
        "style": {"margin": "4"},
    }


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    # The author's logical model: strike records related to the state geometry
    # table on State Name = NAME. The relationship is preserved even though the
    # geometry itself cannot be encoded (see module docstring).
    editor.set_hyper_connection(
        str(HYPER),
        tables=[
            {"name": "Strikes", "table": STRIKES_TABLE},
            {"name": "States", "table": STATES_TABLE},
        ],
        relationships=[
            {"left": "Strikes", "right": "States", "keys": [("State Name", "NAME")]}
        ],
    )

    # --- parameters: the two selection titles and cross-filter drivers -----
    editor.add_parameter(
        "pSelectedState", datatype="string", default_value='""', domain_type="any"
    )
    editor.add_parameter(
        "pSelectedSpecies", datatype="string", default_value='""', domain_type="any"
    )

    # --- calculations -------------------------------------------------------
    editor.add_calculated_field(
        "Wildlife Incidents", "COUNT([Species Type])", datatype="integer"
    )
    # Top 10 species by record count, exactly the author's set definition.
    editor.add_set(
        "Species Type Set",
        "Species Type",
        basis_field="Species Type",
        aggregation="Count",
        top_n=10,
        direction="DESC",
    )
    editor.add_calculated_field(
        "Species Type to Display",
        "IF [Species Type Set] THEN [Species Type] ELSE 'Other' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Title: Selected State",
        "IF [Parameters].[pSelectedState] <> '' "
        "THEN 'in ' + [Parameters].[pSelectedState] ELSE '' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Title: Selected Species",
        "IF [Parameters].[pSelectedSpecies] <> '' "
        "THEN [Parameters].[pSelectedSpecies] ELSE '' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    # The author's native action filters are re-expressed as parameter-driven
    # filters so the default (no selection) state keeps all 251,818 records.
    editor.add_calculated_field(
        "State Filter",
        "IF [Parameters].[pSelectedState] = '' THEN TRUE "
        "ELSE [State Name] = [Parameters].[pSelectedState] END",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Species Filter",
        "IF [Parameters].[pSelectedSpecies] = '' THEN TRUE "
        "ELSE [Species Type to Display] = [Parameters].[pSelectedSpecies] END",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Unknown Location",
        "'Unknown Location'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    # Incident Year is a dimension in the extract; the author's area axis is
    # continuous, so expose a quantitative alias with the author's axis title.
    editor.add_calculated_field(
        "Year",
        "[Incident Year]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )

    editor.set_datasource_color_palette(
        "Species Type Set", {"false": OTHER_GRAY, "true": SALMON}
    )

    # --- bar: top 10 species plus Other ------------------------------------
    editor.add_worksheet("Bar")
    editor.configure_chart(
        "Bar",
        mark_type="Automatic",
        columns=["Wildlife Incidents"],
        rows=["Species Type Set", "Species Type to Display"],
        color="Species Type Set",
        detail="Title: Selected State",
        sort_descending="Wildlife Incidents",
        filters=[{"column": "State Filter", "values": ["true"]}],
        tooltip=["Species Type to Display", "Wildlife Incidents"],
    )
    editor.configure_custom_tooltip(
        "Bar",
        runs=[
            {"field": "Species Type to Display", "bold": True},
            {"text": " was struck "},
            {"field": "Wildlife Incidents", "bold": True},
            {"text": " times"},
        ],
    )
    editor.configure_worksheet_style(
        "Bar",
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_table_dividers=True,
        hide_gridlines=True,
        hide_zeroline=True,
        label_formats=[
            {"field": "Species Type Set", "attr": "display", "value": "false"}
        ],
        header_formats=[
            {"field": "Species Type to Display", "attr": "width", "value": "196"}
        ],
        cell_formats=[
            {"field": "Species Type to Display", "attr": "height", "value": "42"}
        ],
    )
    editor.set_worksheet_rich_title("Bar", TITLE_RUNS_BAR)

    # --- map: incidents per state ------------------------------------------
    editor.set_field_geographic_role("State Name", "state")
    editor.set_geocoding_context(country="United States")
    editor.add_worksheet("Map")
    editor.configure_chart(
        "Map",
        mark_type="Map",
        geographic_field="State Name",
        color="Wildlife Incidents",
        detail="State Name",
        map_fields=["NAME"],
        filters=[{"column": "Species Filter", "values": ["true"]}],
        tooltip=["NAME", "Wildlife Incidents"],
    )
    editor.configure_custom_tooltip(
        "Map",
        runs=[
            {"field": "NAME", "bold": True},
            {"text": " had "},
            {"field": "Wildlife Incidents", "bold": True},
            {"text": " wildlife incidents"},
        ],
    )
    editor.configure_worksheet_style(
        "Map",
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        color_style={
            "field": "Wildlife Incidents",
            "palette": MAP_PALETTE,
            "min": "0",
        },
        map_style={"washout": 0, "layers": dict(DISABLED_MAP_LAYERS)},
    )

    # --- area: incidents over time -----------------------------------------
    editor.add_worksheet("Area")
    editor.configure_layered_chart(
        "Area",
        columns=["Year"],
        rows=["Wildlife Incidents"],
        panes=[
            {
                "mark_type": "Area",
                "detail": "Title: Selected Species",
                "detail_extra": ["Title: Selected State"],
                "tooltip": ["Wildlife Incidents", "Year"],
                "mark_style": {"mark-color": SALMON, "mark-transparency": "255"},
            }
        ],
        filters=[
            {"column": "State Filter", "values": ["true"]},
            {"column": "Species Filter", "values": ["true"]},
        ],
    )
    editor.configure_custom_tooltip(
        "Area",
        runs=[
            {"text": "There were "},
            {"field": "Wildlife Incidents", "bold": True},
            {"text": " wildlife incidents in "},
            {"field": "Year", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Area",
        hide_zeroline=True,
        gridline_style={"cols": {"line-visibility": "off", "stroke-size": "0"}},
    )
    editor.set_worksheet_rich_title("Area", TITLE_RUNS_AREA)

    # --- unknown-location indicator ----------------------------------------
    editor.add_worksheet("Unknown")
    editor.configure_chart(
        "Unknown",
        mark_type="Square",
        label="Unknown Location",
        tooltip=["Wildlife Incidents"],
        filters=[
            {"column": "State Name", "values": [None]},
            {"column": "Species Filter", "values": ["true"]},
        ],
    )
    editor.configure_custom_tooltip(
        "Unknown",
        runs=[
            {"field": "Unknown Location", "bold": True},
            {"text": " had "},
            {"field": "Wildlife Incidents", "bold": True},
            {"text": " wildlife incidents"},
        ],
    )
    editor.configure_worksheet_style(
        "Unknown",
        pane_mark_style={
            "mark-color": UNKNOWN_RED,
            "size": "14.547999382019043",
            "has-stroke": "false",
            "mark-labels-show": "true",
            "mark-labels-cull": "true",
        },
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
    )

    # --- dashboard ---------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "text",
                "text": "Let's Analyse Wildlife Strikes",
                "runs": [
                    {
                        "text": "Let's Analyse Wildlife Strikes",
                        "font_size": "22",
                        "bold": True,
                        "font_color": "#000000",
                        "font_alignment": "0",
                    }
                ],
                "absolute": {"x": 0, "y": 0, "w": 100000, "h": 6556},
                "style": {"margin": "4"},
            },
            {
                "type": "worksheet",
                "name": "Bar",
                "fit": "entire",
                "absolute": {"x": 0, "y": 6556, "w": 40667, "h": 60444},
                "style": {"margin": "4"},
            },
            {
                "type": "worksheet",
                "name": "Map",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 40667, "y": 6556, "w": 59333, "h": 60444},
                "style": {"margin": "4"},
            },
            {
                "type": "worksheet",
                "name": "Area",
                "fit": "entire",
                "absolute": {"x": 0, "y": 67000, "w": 100000, "h": 26111},
                "style": {"margin": "4"},
            },
            {
                "type": "color",
                "worksheet": "Map",
                "field": "Wildlife Incidents",
                "absolute": {"x": 81417, "y": 6889, "w": 17750, "h": 9111},
            },
            {
                "type": "worksheet",
                "name": "Unknown",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 84750, "y": 56000, "w": 11083, "h": 6111},
            },
            _footer("CHALLENGE BY : SEAN MILLER", "0", 0, 35333),
            _footer("#WOW2022 | WEEK 01", "1", 35333, 32333),
            _footer("RECREATED BY : DONNA COLES", "2", 67666, 32333),
            {
                "type": "text",
                "runs": [
                    {
                        "text": "DATA: ",
                        "bold": True,
                        "font_size": "8",
                        "font_color": SALMON,
                        "font_name": "Tableau Medium",
                        "font_alignment": "0",
                    },
                    {
                        "text": DATA_URL,
                        "bold": True,
                        "font_size": "8",
                        "font_color": SALMON,
                        "font_name": "Tableau Medium",
                        "font_alignment": "0",
                        "hyperlink": f'tabdoc:load-url url=&quot;{DATA_URL}&quot;',
                    },
                ],
                "absolute": {"x": 0, "y": 96667, "w": 48666, "h": 3333},
                "style": {"margin": "4"},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": POST_URL,
                        "bold": True,
                        "font_size": "8",
                        "font_color": SALMON,
                        "font_name": "Tableau Medium",
                        "font_alignment": "2",
                        "hyperlink": f'tabdoc:load-url url=&quot;{POST_URL}&quot;',
                    }
                ],
                "absolute": {"x": 48666, "y": 96667, "w": 51333, "h": 3333},
                "style": {"margin": "4"},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=900,
        layout=layout,
        worksheet_names=["Bar", "Map", "Area", "Unknown"],
    )

    # --- interactions: parameter actions drive both titles and cross-filters
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Map",
        source_field="State Name",
        target_parameter="pSelectedState",
        aggregation="attr",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
        caption="Select State",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Bar",
        source_field="Species Type to Display",
        target_parameter="pSelectedSpecies",
        aggregation="attr",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
        caption="Select Species",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(str(output_path), validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2022-01-06-ww01-let-s-analyse-wildlife-strikes-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
