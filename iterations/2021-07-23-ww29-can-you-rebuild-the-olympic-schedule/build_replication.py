"""Rebuild the WW29 "Olympic Schedule" dashboard.

The challenge (Lorna Brown, rebuilt by Donna Coles) turns the Tokyo 2020 event
schedule into a per-sport calendar: one row per Sport Group / Sport, one column
per day, a mark on every day the sport runs, and a medal shape when that day
carries a final. Hovering a mark lists the individual events and compares the
sport with every other sport that day; the sport selector is a set that the
viewer adds and removes sports from.

Chain:
  data (Sport Group, Event, UK Date Time, Date, Sport)
  → pTimeAdjust (-12..12, step 1) and pSportToExclude ("")
  → Date Time Adjust = DATEADD('hour', pTimeAdjust, UK Date Time)
  → Day of Adjusted Date = DATE(DATETRUNC('day', Date Time Adjust))
  → Is Victory Ceremony? / Is Final? flags
  → #Events by Sport Per Day and #Event Finals by Sport Per Day  {FIXED …}
  → # Events Per Day, #Events Per Day of Other Sports
  → X-Axis (3 / 5 / 7) so finals and non-finals sit side by side
  → Sport Selector (MIN(1) bars coloured by the Sport Group Set)
  → Date Chart (month / day / X-Axis columns, Shape marks)
  → two viz-in-tooltip sheets (event listing, other-sports bars)
  → dashboard: hide/show selector, two set actions, hover parameter action,
    dummy-field highlight action
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = next((HERE / "inputs").glob("*.hyper"))
DASHBOARD = "2021_07_21_WW29_Olympic_Schedule"

SELECTOR = "Sport Selector"
SCHEDULE = "Date Chart"
EVENT_LIST = "VIT-Event Listing"
OTHER_BARS = "VIT-Other Event Bar"

SET_NAME = "Sport Group Set"
INITIAL_SET = ["Boxing", "Gymnastics", "Martial Arts"]

FINAL_COLOR = "#000000"
NON_FINAL_COLOR = "#898989"
SELECTED_COLOR = "#80deea"
UNSELECTED_COLOR = "#d3d3d3"

# Author formulas (kept verbatim in meaning, written against display names).
DATE_TIME_ADJUST = "DATEADD('hour', [pTimeAdjust], [UK Date Time])"
DAY_OF_ADJUSTED_DATE = "DATE(DATETRUNC('day',[Date Time Adjust]))"
IS_VICTORY = "CONTAINS([Event],'Victory Ceremony')"
IS_FINAL = "CONTAINS([Event],'Gold Medal') OR CONTAINS([Event],' Final')"
EVENTS_PER_DAY = (
    "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?] : COUNT([Event])}"
)
EVENTS_BY_SPORT = (
    "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]: COUNT([Event])}"
)
FINALS_BY_SPORT = (
    "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]:"
    " SUM(IIF([Is Final?],1,0))}"
)
X_AXIS = (
    "IF [#Event Finals by Sport Per Day] =0 THEN 5\n"
    "ELSEIF [#Event Finals by Sport Per Day]-[#Events by Sport Per Day] =0 THEN 5\n"
    "ELSEIF [Is Final?] THEN 7\n"
    "ELSE 3\n"
    " END"
)
OTHER_SPORTS = "SUM([# Events Per Day]) - SUM([#Events by Sport Per Day])"
EXCLUDED_SPORT = "[Sport]=[pSportToExclude]"
DUMMY = "'Dummy'"
EVENT_MEDAL = "IF [Is Final?] THEN '\u2af1' ELSE '' END"

TIME_FORMAT = "*dd mmm yyyy h:nn AMPM"

# Bracketed references pin a discrete binding. A bare date-looking field name is
# auto-wrapped as MONTH(...) by the SDK's default view expression, which would
# collapse the day column and the tooltip filter to one mark per month.
DAY = "[Day of Adjusted Date]"
DATETIME = "[Date Time Adjust]"


def add_parameters(editor: TWBEditor) -> None:
    """The timezone shifter and the hover-driven sport-to-exclude parameter."""
    # Declaration order mirrors the author workbook (pSportToExclude is
    # [Parameter 1], pTimeAdjust is [Parameter 2]).
    editor.add_parameter(
        "pSportToExclude",
        datatype="string",
        default_value="",
        domain_type="any",
    )
    editor.add_parameter(
        "pTimeAdjust",
        datatype="integer",
        default_value="0",
        domain_type="range",
        min_value="-12",
        max_value="12",
        granularity="1",
    )


def add_calculations(editor: TWBEditor) -> None:
    """The schedule calculation chain, in dependency order."""
    fields = [
        ("Event", "[Events Split]", "string", "dimension", "nominal"),
        (
            "Date Time Adjust",
            DATE_TIME_ADJUST,
            "datetime",
            "dimension",
            "ordinal",
        ),
        (
            "Day of Adjusted Date",
            DAY_OF_ADJUSTED_DATE,
            "date",
            "dimension",
            "ordinal",
        ),
        ("Is Victory Ceremony?", IS_VICTORY, "boolean", "dimension", "nominal"),
        ("Is Final?", IS_FINAL, "boolean", "dimension", "nominal"),
        ("# Events Per Day", EVENTS_PER_DAY, "integer", "measure", "quantitative"),
        (
            "#Events by Sport Per Day",
            EVENTS_BY_SPORT,
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "#Event Finals by Sport Per Day",
            FINALS_BY_SPORT,
            "integer",
            "measure",
            "quantitative",
        ),
        # X-Axis is a dimension with a continuous type (the author's
        # [none:...:qk] instance): aggregating it would multiply the 3/5/7
        # offset by the number of events in the cell and push the mark off the
        # fixed 0..10 axis.
        ("X-Axis", X_AXIS, "integer", "dimension", "quantitative"),
        (
            "#Events Per Day of Other Sports",
            OTHER_SPORTS,
            "integer",
            "measure",
            "quantitative",
        ),
        ("Excluded Sport", EXCLUDED_SPORT, "boolean", "dimension", "nominal"),
        ("Dummy", DUMMY, "string", "dimension", "nominal"),
        ("Event Medal Symbol", EVENT_MEDAL, "string", "dimension", "nominal"),
        ("MIN(1)", "MIN(1)", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, field_type in fields:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
        )
    # The set is the sport-selector toggle target; the author seeds three sports.
    editor.add_set(SET_NAME, "Sport Group", members=list(INITIAL_SET))
    editor.set_field_format("Date Time Adjust", TIME_FORMAT)


def build_selector(editor: TWBEditor) -> None:
    """One horizontal bar per sport group, coloured by set membership."""
    editor.add_worksheet(SELECTOR)
    editor.configure_chart(
        SELECTOR,
        mark_type="Bar",
        columns=["MIN(1)"],
        rows=["Sport Group"],
        color=SET_NAME,
        label="Sport Group",
        detail="Dummy",
        tooltip=[SET_NAME],
        color_map={"true": SELECTED_COLOR, "false": UNSELECTED_COLOR},
        axis_fixed_range={"field": "MIN(1)", "min": 0, "max": 1, "scope": "cols"},
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        SELECTOR,
        hide_axes=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_band_color=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"font-size": "8", "color": "#000000"},
        header_formats=[{"field": "Sport Group", "height": "38"}],
    )
    editor.set_worksheet_title(SELECTOR, "Select Sport")


def build_schedule(editor: TWBEditor) -> None:
    """Month / day / X-Axis columns against Sport Group / Sport rows."""
    editor.add_worksheet(SCHEDULE)
    editor.configure_layered_chart(
        SCHEDULE,
        columns=[
            "MONTH(Date Time Adjust)",
            "DAY(Date Time Adjust)",
            "X-Axis",
        ],
        rows=["Sport Group", "Sport", "MIN(1)"],
        axis_shelf="columns",
        fold_axes=False,
        synchronized=False,
        panes=[
            {
                "axis": "X-Axis",
                "mark_type": "Shape",
                "shape": "Is Final?",
                "shape_map": {"true": ":filled/diamond", "false": ":filled/circle"},
                "size": "Is Final?",
                "detail_extra": ["Sport", DAY],
                "tooltip": [
                    "#Events by Sport Per Day",
                    "#Event Finals by Sport Per Day",
                    "#Events Per Day of Other Sports",
                ],
                "mark_style": {"mark-color": NON_FINAL_COLOR},
            }
        ],
        filters=[
            {"column": SET_NAME, "values": [True]},
            {"column": "Is Victory Ceremony?", "values": [False]},
        ],
    )
    editor.configure_worksheet_style(
        SCHEDULE,
        # Both numeric axes are scaffolding, not information: the author hides
        # the 0..10 X-Axis and the MIN(1) row axis and keeps only the month/day
        # headers.
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_band_color=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        header_formats=[
            {"field": "Sport Group", "width": "108"},
            {"field": "Sport", "width": "140"},
        ],
        axis_style={
            "encodings": [
                {
                    "field": "X-Axis",
                    "attr": "space",
                    "scope": "cols",
                    "class": 0,
                    "type": "space",
                    "range-type": "fixed",
                    "min": 0,
                    "max": 10,
                }
            ],
            "per_field": [
                {"field": "MIN(1)", "attr": "display", "scope": "rows", "value": "false"}
            ],
        },
    )
    editor.configure_custom_tooltip(
        SCHEDULE,
        [
            {"field": "Sport", "bold": True},
            {"text": "  |  "},
            {"field": "Sport Group", "bold": True},
            {"text": "\n"},
            {"field": DAY, "bold": True},
            {"text": "\nNumber of Events: "},
            {"field": "#Events by Sport Per Day"},
            {"text": "\nNumber of Finals: "},
            {"field": "#Event Finals by Sport Per Day"},
            {"text": "\nTotal Number of Events across all other Sports: "},
            {"field": "#Events Per Day of Other Sports"},
            {"text": "\nEvent Details ( \u2af1 denotes final/gold medal event)\n"},
            {
                "sheet": {
                    "name": EVENT_LIST,
                    "maxwidth": 650,
                    "maxheight": 500,
                    "filter_fields": ["Sport", DAY],
                }
            },
            {"text": "\nOther Sports\n"},
            {
                "sheet": {
                    "name": OTHER_BARS,
                    "maxwidth": 650,
                    "maxheight": 500,
                    "filter_fields": [DAY],
                }
            },
        ],
    )


def build_event_listing(editor: TWBEditor) -> None:
    """The tooltip sheet that lists every event for one sport on one day."""
    editor.add_worksheet(EVENT_LIST)
    editor.configure_chart(
        EVENT_LIST,
        mark_type="Text",
        rows=[
            "MONTH(Date Time Adjust)",
            "DAY(Date Time Adjust)",
            "Sport Group",
            "Sport",
            "Event Medal Symbol",
            DATETIME,
        ],
        label="Event",
        detail=DAY,
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        EVENT_LIST,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_band_color=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[{"field": "Sport Group", "display": "false"}],
        cell_formats=[{"field": DATETIME, "text-format": TIME_FORMAT}],
        header_formats=[
            {"field": "Event", "width": "304"},
            {"field": DATETIME, "width": "244"},
            {"field": "Sport", "width": "156"},
        ],
    )
    editor.set_worksheet_hidden(EVENT_LIST, True)


def build_other_bars(editor: TWBEditor) -> None:
    """The tooltip sheet that compares the hovered day across other sports."""
    editor.add_worksheet(OTHER_BARS)
    editor.configure_chart(
        OTHER_BARS,
        mark_type="Bar",
        columns=["COUNT(Event)"],
        rows=[DAY, "Sport Group"],
        color="Is Final?",
        label="COUNT(Event)",
        detail=DAY,
        tooltip=[DATETIME, "Is Final?", "Sport Group", "COUNT(Event)"],
        filters=[{"column": "Excluded Sport", "values": [False]}],
        color_map={"true": FINAL_COLOR, "false": NON_FINAL_COLOR},
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        OTHER_BARS,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_band_color=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[{"field": DAY, "display": "false"}],
        header_formats=[{"field": "Sport Group", "height": "24"}],
    )
    editor.set_worksheet_hidden(OTHER_BARS, True)


def dashboard_layout() -> dict:
    """Title band, sport selector and schedule side by side, footer strip."""

    def rect(x, y, w, h):
        return {
            "x": round(x / 1200 * 100000),
            "y": round(y / 900 * 100000),
            "w": round(w / 1200 * 100000),
            "h": round(h / 900 * 100000),
        }

    return {
        "type": "container",
        "direction": "vertical",
        "style": {"margin": 8},
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 56,
                "children": [
                    {
                        "type": "text",
                        "fixed_size": 160,
                        "runs": [
                            {
                                "text": "TOKYO 2020",
                                "font_size": 10,
                                "font_color": "#898989",
                                "bold": True,
                                "font_alignment": "1",
                            }
                        ],
                    },
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "OLYMPIC SCHEDULE",
                                "font_size": 26,
                                "font_color": "#898989",
                                "bold": True,
                                "font_alignment": "0",
                            }
                        ],
                    },
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "children": [
                    # The selector lives in its own layout-flow container so the
                    # native hide/show button can target exactly that container.
                    {
                        "type": "container",
                        "direction": "vertical",
                        "fixed_size": 176,
                        "children": [
                            {
                                "type": "worksheet",
                                "name": SELECTOR,
                                "show_title": True,
                                "fit": "entire",
                            }
                        ],
                    },
                    {
                        "type": "worksheet",
                        "name": SCHEDULE,
                        "show_title": False,
                        "fit": "entire",
                    },
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 46,
                "children": [
                    {
                        "type": "text",
                        "fixed_size": 220,
                        "runs": [
                            {
                                "text": "CHALLENGE BY: LORNA BROWN\n",
                                "font_size": 8,
                                "font_color": "#898989",
                                "bold": True,
                            },
                            {
                                "text": "RECREATED WITH CWTWB",
                                "font_size": 8,
                                "font_color": "#898989",
                                "bold": True,
                            },
                        ],
                    },
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "#WOW2021  |  WEEK 29\n",
                                "font_size": 8,
                                "font_color": "#898989",
                                "bold": True,
                                "font_alignment": "1",
                            },
                            {
                                "text": "https://www.workout-wednesday.com/2021w29tab/",
                                "font_size": 8,
                                "font_color": "#3b54a7",
                                "font_alignment": "1",
                                "hyperlink": "https://www.workout-wednesday.com/2021w29tab/",
                            },
                        ],
                    },
                    {
                        "type": "text",
                        "fixed_size": 200,
                        "runs": [
                            {
                                "text": "All times in BST. Use the parameter to adjust",
                                "font_size": 8,
                                "font_color": "#898989",
                                "font_alignment": "1",
                            }
                        ],
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pTimeAdjust",
                        "mode": "slider",
                        "fixed_size": 200,
                        "show_title": False,
                    },
                ],
            },
        ],
    }


def build_dashboard(editor: TWBEditor) -> None:
    """Assemble the dashboard and the five author interactions."""
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=900,
        layout=dashboard_layout(),
        worksheet_names=[SELECTOR, SCHEDULE],
    )
    for name in (SELECTOR, SCHEDULE):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)

    # Add to / remove from the sport set, from the selector's menu.
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet=SELECTOR,
        target_set=SET_NAME,
        event_type="on-menu",
        caption="Add to Schedule",
        clear_option="do-nothing",
        selection_mode="add",
    )
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet=SELECTOR,
        target_set=SET_NAME,
        event_type="on-menu",
        caption="Remove from Schedule",
        clear_option="do-nothing",
        selection_mode="remove",
    )
    # Hovering a schedule mark sets pSportToExclude for the other-sports bars.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet=SCHEDULE,
        event_type="on-hover",
        caption="Set Sport to Exclude",
        source_field="Sport",
        target_parameter="pSportToExclude",
        aggregation="attr",
        clear_behavior="set-value",
        clear_value="s:LROOT:",
    )
    # The selector must not highlight the schedule. Tableau stores the sheets to
    # leave out of the brush, so the action is declared against the selector and
    # therefore excludes "Date Chart" exactly like the author workbook.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="highlight",
        source_sheet=SELECTOR,
        target_sheet=SELECTOR,
        fields=["Dummy"],
        event_type="on-select",
        caption="Stop Sport Selector highlighting",
    )
    editor.add_dashboard_toggle_button(
        DASHBOARD,
        target_worksheets=[SELECTOR],
        caption_shown="Hide Sport Selector",
        caption_hidden="Show Sport Selector",
        position={"x": 8, "y": 8, "w": 150, "h": 26},
    )


def build() -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    add_parameters(editor)
    add_calculations(editor)
    build_selector(editor)
    build_event_listing(editor)
    build_other_bars(editor)
    build_schedule(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
