"""Rebuild the WW21 "favourite songs" scatter + timeline dashboard.

The challenge (Sean Miller, built by Donna Coles) shows one dot per song
(x = days between first and last listen, y = total plays) and, when a song is
selected, replaces its dot with a stepped running-total timeline of that song's
plays. The whole thing lives on a single dual-axis worksheet whose marks switch
meaning depending on set membership.

Chain:
  data (SongID, Performer, Song, TimeStamp_UTC)
  → Date Played = DATE(DATEPARSE("MM/dd/yyyy HH:mm", [TimeStamp_UTC]))
  → Min/Max Date per Song ({FIXED [SongID]: ...}), Days since first listen,
    Total Plays = COUNT(*), Total Plays per Song ({FIXED [SongID]: [Total Plays]})
  → Days To Date = DATEDIFF('day', [Min Date per Song], [Date Played])
  → Days to Plot  = IF ATTR([Selected Song]) THEN AVG([Days To Date]) ELSE SUM([Days since first listen]) END
  → Plays to Plot = IF ATTR([Selected Song]) THEN RUNNING_SUM([Total Plays]) ELSE SUM([Total Plays per Song]) END
  → Is Last? / Last Plays to Plot (the circle riding the Total Plays axis)
  → one worksheet: circles (scatter) + stepped line (timeline) + a
    set-driven colour/size on the Selected Song set
  → dashboard with a change-set action and a True-only highlight action
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/2021_05_26_WW21_My Streaming Activity.hyper"
DASHBOARD = "2021_05_26_WW21_Favourite_Songs"

GREEN = "#3dde3c"
TITLE_GREEN = "#30b130"
LINE_BLACK = "#1b1b1b"

DATE_PLAYED = (
    'DATE(IF NOT ISNULL( DATEPARSE ( "MM/dd/yyyy HH:mm", [TimeStamp_UTC] ) ) '
    'THEN DATEPARSE ( "MM/dd/yyyy HH:mm", [TimeStamp_UTC] ) '
    'ELSEIF NOT ISNULL ( DATEPARSE ( "MM/dd/yyyy hh:mm:ss a", [TimeStamp_UTC] ) ) '
    'THEN DATEPARSE ( "MM/dd/yyyy hh:mm:ss a", [TimeStamp_UTC] ) END)'
)

TOOLTIP_FIELDS = [
    "Song",
    "Performer",
    "Total Plays per Song",
    "Days to Plot",
]

TOOLTIP_RUNS = [
    {"field": "Song", "bold": True},
    {"text": " by "},
    {"field": "Performer", "bold": True},
    {"text": "\n"},
    {"text": "I've listened to this song ", "fontsize": 8},
    {"field": "Total Plays per Song", "bold": True, "fontsize": 8},
    {"text": " times in ", "fontsize": 8},
    {"field": "Days to Plot", "bold": True, "fontsize": 8},
    {"text": " days (", "fontsize": 8},
    {"field": "Min Date per Song", "bold": True, "fontsize": 8},
    {"text": " - ", "fontsize": 8},
    {"field": "Max Date per Song", "bold": True, "fontsize": 8},
    {"text": ")", "fontsize": 8},
]


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Dates and per-song aggregates -------------------------------------
    editor.add_calculated_field(
        "Date Played",
        DATE_PLAYED,
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dd mmm yyyy",
    )
    editor.add_calculated_field(
        "Min Date per Song",
        "{FIXED [SongID]:MIN([Date Played])}",
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dd mmm yyyy",
    )
    editor.add_calculated_field(
        "Max Date per Song",
        "{FIXED [SongID] : MAX([Date Played])}",
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dd mmm yyyy",
    )
    editor.add_calculated_field(
        "Days since first listen",
        "DATEDIFF('day', [Min Date per Song], [Max Date per Song])",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Total Plays",
        "COUNT([SongID])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Days To Date",
        "DATEDIFF('day',[Min Date per Song],[Date Played])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Total Plays per Song",
        "{FIXED [SongID]: [Total Plays]}",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )

    # --- The selected-song set and the plotting switch ---------------------
    editor.add_set("Selected Song", "SongID", use_all=False)
    editor.add_calculated_field(
        "Days to Plot",
        "IF ATTR([Selected Song]) THEN AVG([Days To Date]) "
        "ELSE SUM([Days since first listen]) END",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Plays to Plot",
        "IF ATTR([Selected Song]) THEN RUNNING_SUM([Total Plays]) "
        "ELSE SUM([Total Plays per Song]) END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Is Last?",
        "LAST()=0",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Last Plays to Plot",
        "IF [Is Last?] THEN Sum([Total Plays per Song]) END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "True",
        "True",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # The running total must be addressed by the continuous date, or Tableau's
    # default "table down" gives the wrong cumulative value. The other two
    # fields keep Tableau's default addressing (the author's own setting).
    date_addressing = {
        "ordering_type": "Field",
        "order": ["EXACTDATE(Date Played)"],
    }

    # --- Single dual-axis worksheet ----------------------------------------
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["Days to Plot"],
        rows=["Last Plays to Plot", "Plays to Plot"],
        axis_shelf="rows",
        fold_axes=True,
        synchronized=True,
        filters=[{"column": "Total Plays per Song", "min": "50", "max": "100"}],
        table_calc_overrides={"Plays to Plot": [date_addressing]},
        panes=[
            {
                "axis": "Last Plays to Plot",
                "mark_type": "Circle",
                "size": "Selected Song",
                "detail_extra": ["SongID", "True"],
                "tooltip": TOOLTIP_FIELDS,
                "mark_style": {
                    "size": "1.9010497331619263",
                    "mark-color": GREEN,
                    "has-stroke": "true",
                    "stroke-color": "#333333",
                    "mark-transparency": "193",
                },
            },
            {
                "axis": "Plays to Plot",
                "mark_type": "Line",
                "color": "Selected Song",
                "color_map": {"true": LINE_BLACK, "false": GREEN},
                "detail_extra": ["SongID", "True"],
                "path": "EXACTDATE(Date Played)",
                "tooltip": TOOLTIP_FIELDS,
                "mark_style": {
                    "size": "0.2738673985004425",
                    "mark-color": LINE_BLACK,
                    "has-stroke": "true",
                    "stroke-color": "#333333",
                    "line-interpolation": "step",
                    "mark-transparency": "255",
                },
            },
        ],
    )
    for pane_index in (0, 1):
        editor.configure_custom_tooltip("Chart", TOOLTIP_RUNS, pane_index=pane_index)
    editor.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_zeroline=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        pane_datalabel_style={"font-size": "8"},
        axis_style={
            "render-fold-reversed": "true",
            "per_field": [
                {
                    "field": "Days to Plot",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Days since first listen",
                },
                {
                    "field": "Last Plays to Plot",
                    "scope": "rows",
                    "attr": "title",
                    "value": "Total Plays (Since 2017)",
                },
            ],
        },
    )

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 800 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "How often has Sean been listening to his favourite songs?",
                    "font_size": "15",
                    "font_color": TITLE_GREEN,
                },
                {"text": "\n"},
                {
                    "text": "Click on a song for additional details",
                    "font_size": "10",
                    "font_color": "#000000",
                },
            ],
            "absolute": pos(8, 8, 984, 70),
        },
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 78, 984, 650),
        },
        {
            "type": "filter",
            "worksheet": "Chart",
            "field": "Total Plays per Song",
            "mode": "slider",
            "show_title": True,
            "caption": "Filter by Total Plays",
            "absolute": pos(99, 83, 144, 66),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "CHALLENGE BY : SEAN MILLER",
                    "font_size": "8",
                    "bold": True,
                    "font_color": TITLE_GREEN,
                    "font_alignment": "0",
                }
            ],
            "absolute": pos(8, 728, 328, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021  |  WEEK 21",
                    "font_size": "8",
                    "bold": True,
                    "font_color": TITLE_GREEN,
                    "font_alignment": "1",
                }
            ],
            "absolute": pos(336, 728, 328, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "RECREATED BY : DONNA COLES",
                    "font_size": "8",
                    "bold": True,
                    "font_color": TITLE_GREEN,
                    "font_alignment": "2",
                }
            ],
            "absolute": pos(664, 728, 328, 32),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Chart"],
    )

    # Clicking a mark assigns it to the Selected Song set (single select).
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet="Chart",
        target_set="Selected Song",
        event_type="on-select",
        caption="Set1",
        single_select=True,
        selection_mode="assign",
        clear_option="exclude-all",
    )
    # Highlight only the True constant so marks keep a constant transparency.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="highlight",
        source_sheet="Chart",
        target_sheet="Chart",
        fields=["True"],
        caption="Highlight1",
    )

    editor.set_worksheet_title("Chart", "")
    editor.set_window_state("Chart", hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
