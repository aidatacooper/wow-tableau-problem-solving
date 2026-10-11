"""Rebuild the Hans Rosling animated bubble chart from locked Hyper extracts.

The locked extract holds three separate wide matrices (life expectancy,
population, income) plus a region lookup. The article pivots each matrix and
relates them on country and year. This builder reproduces that reshape by
materialising one normalized ``Extract`` table (Country, Year, Life Expectancy,
Income, Population, Region) from the locked tables, then builds the scatter from
it. The scatter plots Income (log axis) against Life Expectancy, sizes by
Population, colours by Region and is driven by a Year parameter. A large grey
Year sheet sits behind a transparent floating scatter, and a Region bar drives a
highlight action onto the scatter.

Reshaping into one table is a documented local workaround: native multi-table
Hyper relationships with duplicate physical column names (``Pivot Field Names``,
``Pivot Field Values``) produce a datasource Tableau Cloud refuses to connect
to. See analysis.md and case.yaml (capability_gaps).
"""

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
HYPER = HERE / "inputs/TEMP_0ifbnuy0gfkhjf1guow3w183tnim.hyper"
DERIVED = HERE / "outputs/rosling-extract.hyper"
DASHBOARD = "2021_03_17_Hans_Rosling"

LE_TABLE = "Extract (Extract.Extract)_1A34BF9035E143049C56F3B620E979E3"
POP_TABLE = "Extract (Extract.Extract)_0243FA6460B04031BAB2F3510CA4ACE1"
INC_TABLE = "Extract (Extract.Extract)_B6DF8AE667624AD89112BA1378751D0A"
REGION_TABLE = "list-of-countries-etc_9E3A85DC981044D1ACD35A49A8CDC359"

# Region colours approximate the author's eight-region palette closely enough to
# keep the regions distinguishable; exact RGB is an allowed visual difference.
REGION_COLORS = {
    "SUB-SAHARAN AFRICA": "#7f8c8d",
    "SOUTH ASIA": "#e67e22",
    "EAST ASIA & PACIFIC": "#c0392b",
    "EUROPE & CENTRAL ASIA": "#2980b9",
    "MIDDLE EAST & NORTH AFRICA": "#16a085",
    "AMERICA": "#8e44ad",
    "NORTH AMERICA": "#27ae60",
    "OCEANIA": "#f1c40f",
}


def normalize():
    """Materialise one Country/Year facts table from the locked wide matrices."""
    target = TableName("Extract", "Extract")
    definition = TableDefinition(
        target,
        [
            TableDefinition.Column("Country", SqlType.text()),
            TableDefinition.Column("Year", SqlType.big_int()),
            TableDefinition.Column("Life Expectancy", SqlType.double()),
            TableDefinition.Column("Income", SqlType.big_int()),
            TableDefinition.Column("Population", SqlType.big_int()),
            TableDefinition.Column("Region", SqlType.text()),
        ],
    )
    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as source:

            def facts(table):
                return {
                    (country, year): value
                    for country, year, value in source.execute_list_query(
                        f'SELECT "country","Pivot Field Names","Pivot Field Values" '
                        f'FROM {TableName("Extract", table)}'
                    )
                }

            life = facts(LE_TABLE)
            population = facts(POP_TABLE)
            income = facts(INC_TABLE)
            regions = {
                name: region
                for name, region in source.execute_list_query(
                    f'SELECT "name","eight_regions" FROM {TableName("Extract", REGION_TABLE)}'
                )
            }

        def display_region(value):
            return None if value is None else value.upper().replace("_", " ")

        assert set(life) == set(population) == set(income)
        with Connection(hyper.endpoint, str(DERIVED), CreateMode.CREATE_AND_REPLACE) as target_db:
            target_db.catalog.create_schema("Extract")
            target_db.catalog.create_table(definition)
            with Inserter(target_db, definition) as inserter:
                for (country, year) in sorted(life):
                    inserter.add_row(
                        [
                            country,
                            year,
                            life[(country, year)],
                            income[(country, year)],
                            population[(country, year)],
                            display_region(regions.get(country)),
                        ]
                    )
                inserter.execute()
    return DERIVED


def zone(kind, x, y, width, height, **options):
    """Floating dashboard zone helper using absolute 1/100000 coordinates.

    No background colour is emitted: the author leaves the Year sheet visible
    through the transparent floating Scatter, so a white zone would hide it.
    """
    return {
        "type": kind,
        "absolute": {"x": x, "y": y, "w": width, "h": height},
        "style": {
            "margin": 0,
            "border-style": "none",
            "border-width": 0,
        },
        **options,
    }


def build():
    data = normalize()

    editor = TWBEditor("")
    editor.set_hyper_connection(str(data))

    # Income and life expectancy are continuous *dimensions* on the axes, exactly
    # as the article specifies ("change to Dimension"). Aggregate (``AGG``) shelf
    # expressions render an empty view on this extract, so each axis is an
    # explicit dimension-typed calculated field.
    editor.add_calculated_field(
        "Income Axis",
        "[Income]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Life Expectancy Axis",
        "[Life Expectancy]",
        datatype="real",
        role="dimension",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Has Region",
        "NOT ISNULL([Region])",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # --- Year parameter: the interactive equivalent of the Pages shelf -------
    editor.add_parameter(
        "Year Parameter",
        datatype="integer",
        default_value="2021",
        domain_type="list",
        allowed_values=[str(year) for year in range(1800, 2022)],
        alias="Year",
    )
    editor.add_calculated_field(
        "Selected Year",
        "[Year]=[Year Parameter]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Year Label",
        "STR([Year Parameter])",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    filters = [
        {"column": "Selected Year", "values": ["true"]},
        {"column": "Has Region", "values": ["true"]},
    ]

    # --- Scatter ------------------------------------------------------------
    editor.add_worksheet("Scatter")
    editor.configure_chart(
        "Scatter",
        mark_type="Circle",
        columns=["Income Axis"],
        rows=["Life Expectancy Axis"],
        color="Region",
        size="SUM(Population)",
        detail="Country",
        color_map=REGION_COLORS,
        tooltip=[
            "Country",
            "Region",
            "Year",
            "SUM(Population)",
            "Income Axis",
            "Life Expectancy Axis",
        ],
        filters=filters,
    )
    editor.configure_worksheet_style(
        "Scatter",
        background_color="#00000000",
        hide_gridlines=True,
        hide_sort_controls=True,
        axis_style={
            "encodings": [
                {"field": "Income Axis", "scope": "cols", "scale": "log"},
            ],
        },
    )

    # --- Year card ----------------------------------------------------------
    editor.add_worksheet("Year")
    editor.configure_chart("Year", mark_type="Text", label="Year Label")
    editor.configure_custom_label(
        "Year",
        [{"field": "Year Label", "fontsize": "72", "bold": True, "fontcolor": "#d4d4d4"}],
    )
    editor.configure_worksheet_style(
        "Year",
        background_color="#00000000",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_axes=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_borders=True,
        hide_row_label="Year Label",
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
    )

    # --- Region bar ---------------------------------------------------------
    editor.add_worksheet("Region")
    editor.configure_chart(
        "Region",
        mark_type="Text",
        columns=["Region"],
        label="Region",
        filters=[{"column": "Has Region", "values": ["true"]}],
    )
    editor.configure_worksheet_style(
        "Region",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_axes=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_borders=True,
        header_formats=[{"field": "Region", "display": False}],
    )

    # --- Dashboard ----------------------------------------------------------
    children = [
        zone("worksheet", 1000, 10187, 98000, 8207, name="Region", show_title=False),
        zone("worksheet", 0, 16250, 100000, 75000, name="Year", show_title=False),
        zone(
            "worksheet",
            0,
            16875,
            100000,
            73750,
            name="Scatter",
            show_title=False,
            fit="entire",
        ),
        zone("paramctrl", 84000, 1000, 15000, 8207, param="Year Parameter"),
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=900,
        layout={"type": "container", "direction": "floating", "children": children},
    )

    editor.add_dashboard_action(
        DASHBOARD,
        "highlight",
        source_sheet="Region",
        target_sheet="Scatter",
        fields=["Region"],
        event_type="on-hover",
        caption="Highlight Region",
    )

    for name in ("Scatter", "Region", "Year"):
        editor.set_window_state(name, hidden=False)
        editor.set_worksheet_title(name, "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
