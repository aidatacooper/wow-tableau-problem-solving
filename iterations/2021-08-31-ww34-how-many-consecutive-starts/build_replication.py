"""Rebuild WW34 (2021) "How many consecutive starts?" from the locked Hyper extract.

The challenge (Luke Stanke, rebuilt by Donna Coles) asks for one row per NFL
franchise, drawn as a 240-bar strip covering 2006 week 1 to 2020 week 17. Each
bar is the length of the running consecutive-start streak at that game, the row
is labelled with the streak carried on the team's last game, and the bars sit on
one dense index axis instead of a real date axis.

Chain:
  qb_starters (season, week, offense_franchise_id, player_id, player)
  ⨝ NFL_Teams (franchise_id, team)   -- logical Hyper relationship, many:1
  → week filter 1..17 (the extract also carries weeks 28-32; the article
    excludes them because the challenge is the 17-week regular season)
  → Prev Player ID        LOOKUP(MIN([player_id]),-1)
  → Match Prev Player ID  MIN([player_id]) = [Prev Player ID]
  → Consecutive Streak    IF NOT match OR NULL THEN 1 ELSE 1 + PREVIOUS_VALUE(-1)
  → Current Streak        WINDOW_MAX(IF LAST()=0 THEN [Consecutive Streak] END)
  → INDEX()               the dense game index used as the continuous x axis
  → Viz: Bar, INDEX on Columns (continuous), Consecutive Streak on Rows,
    Team / Current Streak on Rows, Season / Week / Player Id on Detail.
    Every table calculation is addressed Season → Week → Player Id and
    partitioned by Team, because Team is the first Rows pill.

The author workbook is analysis evidence only; nothing here reads it.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs" / "federated.hyper"
OUTPUT_DIR = HERE / "outputs"

DASHBOARD = "2021_08_25_WW34_Consecutive_Starts"
BAR_SHEET = "Viz"
DATA_SHEET = "Data"

# Physical Extract tables inside the packaged author extract.
QB_TABLE = (
    "qb_starters.csv_4409EE5639A8403FBF385663A826525D "
    "(Extract.qb_starters.csv_4409EE5639A8403FBF385663A826525D)_"
    "A0D406B8C1C34B02B729E64E73803396"
)
TEAMS_TABLE = (
    "NFL_Teams.csv_C13053C1D84841CABFE32E1A7B6258E5 "
    "(Extract.NFL_Teams.csv_C13053C1D84841CABFE32E1A7B6258E5)_"
    "00B9020E3A584ABA910F5F61074D85E8"
)

BAR_COLOR = "#4f15c2"
BACKGROUND = "#f5f5f5"
GRIDLINE = "#e6e6e6"

# The author's addressing: every table calculation restarts per Team (Team is
# the outermost Rows pill) and runs down Season → Week → Player Id.
GRAIN = ["Season", "Week", "Player Id"]

# Nested table-calculation dependencies: each formula's referenced calculations.
NESTED = {
    "Prev Player ID": [],
    "Match Prev Player ID": ["Prev Player ID"],
    "Consecutive Streak": ["Match Prev Player ID", "Prev Player ID"],
    "Current Streak": ["Consecutive Streak", "Match Prev Player ID", "Prev Player ID"],
    "INDEX": [],
}


def streak_contexts(names, grains=GRAIN):
    """Build ``table_calc_overrides`` for the streak chain.

    ``ordering_field`` entries reproduce the author's Season → Week → Player Id
    addressing and the ``field`` entries declare the nested calculation
    dependencies, so the chain keeps its addressing after cwtwb rewrites the
    column instances. cwtwb resolves ``ordering_field`` against the worksheet's
    own bound fields, so callers pass only the grains their view binds.
    """
    order = [{"field": grain, "reference": "instance"} for grain in grains]
    return {
        name: [{"ordering_type": "Field", "order": order}]
        + [{"field": dependency, "ordering_type": "Field", "order": order}
           for dependency in NESTED[name]]
        for name in names
    }



def build(output_path: Path | None = None) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HYPER),
        tables=[
            {"name": "qb_starters", "table": QB_TABLE},
            {"name": "NFL_Teams", "table": TEAMS_TABLE},
        ],
        relationships=[
            {
                "left": "qb_starters",
                "right": "NFL_Teams",
                "keys": [["offense_franchise_id", "franchise_id"]],
            }
        ],
    )

    # --- Dimension aliases --------------------------------------------------
    # The extract stores season/week/player_id as integers, which cwtwb's
    # connection inspection can only register as measures, and a bare "Week"
    # would be bound as MONTH(Week) by the date-name heuristic. The article puts
    # all three on Rows/Detail as discrete dimensions, so each is re-exposed as
    # an explicit discrete calculated field.
    for alias, source, field_type in (
        ("Season", "season", "ordinal"),
        ("Week", "week", "ordinal"),
        ("Player Id", "player_id", "ordinal"),
        # Continuous copy of the week number, used by the in-range filter.
        ("Week Number", "week", "quantitative"),
    ):
        editor.add_calculated_field(
            alias,
            f"[{source}]",
            datatype="integer",
            role="dimension",
            field_type=field_type,
        )

    # --- Table calculations, exactly the article's formulas ------------------
    editor.add_calculated_field(
        "Prev Player ID",
        "LOOKUP(MIN([player_id]),-1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Match Prev Player ID",
        "MIN([player_id])=[Prev Player ID]",
        datatype="boolean",
        role="measure",
        field_type="nominal",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Consecutive Streak",
        "IF (NOT([Match Prev Player ID])) OR ISNULL([Match Prev Player ID]) THEN 1\r\n"
        "ELSE 1+PREVIOUS_VALUE(-1)\r\n\r\nEND",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Current Streak",
        "WINDOW_MAX(IF LAST()=0 THEN [Consecutive Streak] END)",
        datatype="integer",
        role="measure",
        field_type="ordinal",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "INDEX",
        "INDEX()",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
    )

    # The regular season only: the extract also carries weeks 28-32. The filter
    # is a native in-range filter on the week number, as in the author workbook.
    week_filter = {
        "column": "Week Number",
        "type": "quantitative",
        "min": "1",
        "max": "17",
    }

    # --- Data sheet: the tabular build the article walks through -------------
    # Team is not on this shelf, so the table calculations here are addressed by
    # the three grain fields alone.
    editor.add_worksheet(DATA_SHEET)
    editor.configure_chart(
        DATA_SHEET,
        mark_type="Automatic",
        rows=[
            "Team",
            "Season",
            "Week",
            "INDEX",
            "Player Id",
            "Prev Player ID",
            "Match Prev Player ID",
            "Current Streak",
        ],
        label="Consecutive Streak",
        filters=[week_filter],
        table_calc_overrides=streak_contexts(NESTED.keys()),
    )

    # --- Viz sheet: the strip chart -----------------------------------------
    editor.add_worksheet(BAR_SHEET)
    editor.configure_layered_chart(
        BAR_SHEET,
        columns=["INDEX"],
        rows=["Team", "Current Streak", "Consecutive Streak"],
        panes=[
            {
                "mark_type": "Bar",
                "detail_extra": ["Season", "Week", "Player Id"],
                "tooltip": "Player",
                "mark_sizing": {
                    "mark_sizing_setting": "marks-scaling-on",
                    "use_custom_mark_size": True,
                    "custom_mark_size_in_axis_units": 1.0,
                    "mark_alignment": "mark-alignment-right",
                },
                "mark_style": {
                    "mark_color": BAR_COLOR,
                    "mark_labels_show": "false",
                    "has_stroke": "false",
                    "size": "0.0099999997764825821",
                },
            }
        ],
        # The index is the continuous axis; Rows carries the discrete Team /
        # Current Streak headers plus the continuous streak measure, so the
        # axis shelf is Columns and Rows uses Tableau's dimension-shelf nesting.
        axis_shelf="columns",
        filters=[week_filter],
        table_calc_context=True,
        table_calc_overrides=streak_contexts(
            ["INDEX", "Consecutive Streak", "Current Streak"]
        ),
    )
    editor.configure_worksheet_style(
        BAR_SHEET,
        background_color=BACKGROUND,
        hide_table_dividers=True,
        pane_formats=[
            {"attr": "minheight", "value": "52"},
            {"attr": "maxheight", "value": "52"},
            {"attr": "minwidth", "value": "528"},
            {"attr": "maxwidth", "value": "528"},
        ],
        header_formats=[
            {"field": "Current Streak", "attr": "width", "value": "56"},
            {"field": "Team", "attr": "width", "value": "60"},
            {"attr": "height-header", "value": "48"},
        ],
        gridline_style={
            "cols": {"stroke-color": GRIDLINE},
            "rows": {"line-visibility": "off", "stroke-size": "0"},
        },
        # The author hides the Consecutive Streak axis and retitles the index.
        axis_style={
            "per_field": [
                {
                    "field": "Consecutive Streak",
                    "attr": "display",
                    "value": "false",
                    "scope": "rows",
                    "class": "0",
                },
                {
                    "field": "INDEX",
                    "attr": "title",
                    "value": "Regular Season Games Since 2006",
                    "scope": "cols",
                    "class": "0",
                },
            ]
        },
    )
    editor.set_worksheet_rich_title(
        BAR_SHEET,
        [
            {"text": "Consecutive Starts in a Row\n", "bold": True, "fontsize": "18"},
            {
                "text": "Total Consecutive Quarterback Starts for a Single Team Since 2006\n\n",
                "fontsize": "10",
                "fontcolor": "#898989",
            },
            {
                "text": "Data Courtesy of Pro Football Focus (PFF)",
                "fontsize": "10",
                "fontcolor": "#898989",
            },
        ],
    )

    # --- Dashboard ----------------------------------------------------------
    def text_zone(text, x, y, width, height, alignment="0", bold=True,
                  color="#000000", url=None):
        run = {
            "text": text,
            "font_size": "8",
            "font_color": color,
            "font_alignment": alignment,
        }
        if bold:
            run["bold"] = True
        if url:
            run["url"] = url
        return {
            "type": "text",
            "text": text,
            "runs": [run],
            "style": {"margin": 4, "border-style": "none", "border-width": 0},
            "absolute": {"x": x, "y": y, "w": width, "h": height},
        }

    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "worksheet",
                "name": BAR_SHEET,
                "show_title": True,
                "fit": "entire",
                "style": {
                    "margin": 0,
                    "border-style": "none",
                    "border-width": 0,
                    "background-color": BACKGROUND,
                },
                "absolute": {"x": 1000, "y": 444, "w": 98000, "h": 95556},
            },
            text_zone("CHALLENGE BY : LUKE STANKE", 1000, 96000, 32666, 1778),
            text_zone("#WOW2021  |  WEEK 34", 33666, 96000, 32668, 1778, alignment="1"),
            text_zone("RECREATED BY : DONNA COLES", 66334, 96000, 32666, 1778, alignment="2"),
            text_zone(
                "http://www.workout-wednesday.com/2021-week-34-how-many-consecutive-starts/",
                1000,
                97778,
                98000,
                1778,
                alignment="1",
                bold=False,
                color="#1f77b4",
                url="http://www.workout-wednesday.com/2021-week-34-how-many-consecutive-starts/",
            ),
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=800,
        height=1800,
        layout=layout,
        worksheet_names=[BAR_SHEET],
    )

    target = output_path or (OUTPUT_DIR / "replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
