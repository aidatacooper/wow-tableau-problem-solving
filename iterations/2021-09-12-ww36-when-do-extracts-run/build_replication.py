"""Build the WoW 2021 Week 36 "When do extracts run during the day?" replica.

The workbook is rebuilt from an empty ``TWBEditor("")`` using only the locked
Hyper extract under ``inputs/`` and public ``cwtwb`` APIs.  The author TWB/TWBX
is never opened here: ``analysis.md`` records what the analysis phase observed.

Layout reproduced
-----------------
* ``Gantt``: a folded dual-axis Gantt chart.  The waiting-time bar starts at the
  normalised ``Created At`` instant and spans ``Waiting Time``; the processing
  bar starts at the normalised ``Started At`` instant and spans
  ``Processing Time``.  Rows are ``Site / Title / day(Created At)`` and the
  columns axis carries both baselined datetime axes, folded and synchronised.
* ``Key``: the two-bar legend built from the data itself (``MIN(1)`` bar sized by
  ``Site``, labelled ``Waiting``/``Processing``).
* ``Data``: the author's supporting crosstab sheet, kept hidden.
* Dashboard ``When Do Extracts Run During The Day?`` (1000x800): title, filter
  row (``pDaysToShow`` slider + ``Site`` filter), ``Key``, the two native colour
  legends, the Gantt chart and the footer.
"""

from __future__ import annotations

from pathlib import Path

from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"
HYPER_FILE = INPUTS / "TEMP_0za05zv08wbboi1164y2i07f3q8l.hyper"
OUTPUT_TWBX = OUTPUTS / "replicated-workbook.twbx"

DASHBOARD = "When Do Extracts Run During The Day?"
GANTT = "Gantt"
KEY = "Key"
DATA_SHEET = "Data"

# The author froze "now" for the static extract; 05 Feb 2021 16:30 is the last
# observed task instant in the locked data, so unfinished tasks stop there.
NOW = "#2021-02-05 16:30:00#"
DAYS_TO_SHOW = "5"
BASELINE_DAY = "#2021-01-01#"

# Author palette (read from analysis.md, not from the author workbook at build).
STATUS_COLORS = {
    "In Progress": "#4e79a7",
    "Success": "#bab0ac",
    "Failed": "#e15759",
}
WAIT_COLORS = {"false": "#bab0ac", "true": "#e15759"}
SITE_COLORS = {
    "Site 13": "#76b7b2",
    "Site 7": "#bab0ac",
    "Site 11": "#e15759",
    "Site 9": "#e15759",
}

WORKING_HOURS_BAND = "#f3faf9"
# The author's band endpoints are the 08:00 and 17:00 instants on the normalised
# day. They are declared as datetime fields so the reference line stays a real
# datetime endpoint instead of a bare number on a datetime axis.
WORKING_HOURS_START = "#2021-01-01 08:00:00#"
WORKING_HOURS_END = "#2021-01-01 17:00:00#"

WAITING_AXIS = "EXACTDATE(Created At Baseline)"
PROCESSING_AXIS = "EXACTDATE(Started At Baseline)"
WAITING_SIZE = "AVG(Waiting Time)"
PROCESSING_SIZE = "AVG(Processing Time)"


def add_calculations(editor: TWBEditor) -> None:
    """Add the author's calculated fields with readable, real dependencies.

    Every nested dependency is spelled out with the real physical fields
    (``created_at``, ``started_at``, ``completed_at``, the parameters) instead of
    referring to another calculated field by caption.  A calculated date used as
    a caption on a shelf can resolve to an unresolved table-calculation ordering
    field, which renders blank in Tableau Cloud.
    """
    # Readable display fields. cwtwb builds from the empty template, whose
    # physical extract columns carry their raw names; these thin aliases give the
    # data pane and tooltips the author's labels without touching workbook
    # internals. They are plain pass-throughs, so they add no table calculations.
    for caption, local, datatype, field_type in (
        ("Created At", "[created_at]", "datetime", "ordinal"),
        ("Started At", "[started_at]", "datetime", "ordinal"),
        ("Completed At", "[completed_at]", "datetime", "ordinal"),
        ("Id", "[id]", "integer", "ordinal"),
        ("Title", "[title]", "string", "nominal"),
        ("Notes", "[notes]", "string", "nominal"),
        ("Finish Code", "[finish_code]", "integer", "ordinal"),
    ):
        editor.add_calculated_field(
            caption,
            local,
            datatype=datatype,
            role="dimension",
            field_type=field_type,
        )

    created = "[created_at]"
    started = "[started_at]"
    completed = "[completed_at]"

    editor.add_calculated_field(
        "Extract Status",
        (
            "IF [finish_code] = 1 AND [progress] <> 100 THEN 'In Progress'\n"
            "ELSEIF [finish_code] = 0 AND NOT [progress] = 1 THEN 'Success'\n"
            "ELSE 'Failed'\n"
            "END"
        ),
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    editor.add_calculated_field(
        "Waiting Time",
        f"(DATEDIFF('second', {created}, IF ISNULL({started}) THEN "
        f"[Parameters].[Now] ELSE {started} END))/86400",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    editor.add_calculated_field(
        "Processing Time",
        f"(DATEDIFF('second', {started}, IF ISNULL({completed}) THEN "
        f"[Parameters].[Now] ELSE {completed} END))/86400",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )

    # Same-day normalisation: keep the time of day, move the calendar date.
    editor.add_calculated_field(
        "Created At Baseline",
        f"DATEADD('day', DATEDIFF('day', {created}, {BASELINE_DAY}), {created})",
        datatype="datetime",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Started At Baseline",
        f"DATEADD('day', DATEDIFF('day', {started}, {BASELINE_DAY}), {started})",
        datatype="datetime",
        role="dimension",
        field_type="ordinal",
    )

    editor.add_calculated_field(
        "Over Wait Time Threshold",
        "[Waiting Time] > 0.007",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    editor.add_calculated_field(
        "Filter: Days to Show",
        f"DATETRUNC('day', {created}) >= DATEADD('day', "
        f"([Parameters].[pDaysToShow]-1)*-1, DATETRUNC('day', [Parameters].[Now]))",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    editor.add_calculated_field(
        "Key Label",
        "IF [Site] = 'Site 9' THEN 'Waiting' ELSE 'Processing' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    # Declarative stand-in for the author's manual sort dictionary: the Waiting
    # bar belongs to Site 9, so it sorts first when Key Label is sorted by this.
    editor.add_calculated_field(
        "Key Order",
        "IF [Site] = 'Site 9' THEN 1 ELSE 0 END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    # Band endpoints as datetime fields (see add_reference_band below).
    editor.add_calculated_field(
        "Working Hours Start",
        WORKING_HOURS_START,
        datatype="datetime",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Working Hours End",
        WORKING_HOURS_END,
        datatype="datetime",
        role="measure",
        field_type="quantitative",
    )

    editor.add_calculated_field(
        "One",
        "MIN(1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )


def configure_palettes(editor: TWBEditor) -> None:
    """Apply the author's categorical colour assignments."""
    editor.set_datasource_color_palette("Extract Status", STATUS_COLORS)
    editor.set_datasource_color_palette("Over Wait Time Threshold", WAIT_COLORS)
    editor.set_datasource_color_palette("Site", SITE_COLORS)


def build_gantt(editor: TWBEditor) -> None:
    """Dual-axis folded Gantt chart on the baselined datetime axes."""
    editor.add_worksheet(GANTT)
    editor.configure_layered_chart(
        GANTT,
        # Both datetime axes must also be present on the shelf: a pane axis that
        # is only declared in <style> leaves the sheet blank.
        columns=[WAITING_AXIS, PROCESSING_AXIS],
        rows=["Site", "Title", "DISCRETE(DAYTRUNC(Created At))"],
        axis_shelf="columns",
        synchronized=True,
        fold_axes=True,
        filters=[
            {"column": "Filter: Days to Show", "values": [True]},
            {"column": "Site", "values": ["Site 9"]},
        ],
        panes=[
            {
                "axis": WAITING_AXIS,
                "mark_type": "GanttBar",
                "size": WAITING_SIZE,
                "color": "Over Wait Time Threshold",
                "color_map": WAIT_COLORS,
                "detail": "Id",
                "detail_extra": ["Notes"],
                "tooltip": [
                    "Created At Baseline",
                    "Started At Baseline",
                    "Id",
                    "Notes",
                    "Extract Status",
                ],
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "0.0099999997764825821",
                    "mark-transparency": "180",
                },
            },
            {
                "axis": PROCESSING_AXIS,
                "mark_type": "GanttBar",
                "size": PROCESSING_SIZE,
                "color": "Extract Status",
                "color_map": STATUS_COLORS,
                "detail": "Id",
                "detail_extra": ["Notes"],
                "tooltip": [
                    "Created At Baseline",
                    "Started At Baseline",
                    "Id",
                    "Notes",
                    "Extract Status",
                ],
                "mark_sizing_off": True,
                "mark_style": {"size": "0.0099999997764825821"},
            },
        ],
    )

    # Reference band over core working hours (08:00-17:00) on the waiting axis.
    editor.add_reference_band(
        GANTT,
        axis_field=WAITING_AXIS,
        lower_field="Working Hours Start",
        upper_field="Working Hours End",
        lower_formula="min",
        upper_formula="max",
        fill_color=WORKING_HOURS_BAND,
        pane_index=0,
    )

    editor.set_field_format("Created At Baseline", "*h:mm am/pm")
    editor.set_field_format("Started At Baseline", "*h:mm am/pm")
    editor.set_field_format("Created At", "*ddd dd mmm yyyy")
    editor.set_field_format("Started At", "*h:mm am/pm")
    editor.set_field_format("Completed At", "*h:mm am/pm")
    editor.set_field_format("Id", "n0;-0")

    # The author's tooltips name the row's day, site, object, job id, both
    # timestamps and the duration in hh:mm:ss.
    for pane_index, duration in ((0, WAITING_SIZE), (1, PROCESSING_SIZE)):
        editor.configure_custom_tooltip(
            GANTT,
            [
                {"field": "DISCRETE(DAYTRUNC(Created At))", "bold": True, "fontsize": "8"},
                {"text": " - ", "fontsize": "8"},
                {"field": "Extract Status", "bold": True, "fontsize": "8"},
                {"text": "\n", "fontsize": "8"},
                {"text": "Site:\t", "fontsize": "8"},
                {"field": "Site", "bold": True, "fontsize": "8"},
                {"text": "\nObject:\t", "fontsize": "8"},
                {"field": "Title", "bold": True, "fontsize": "8"},
                {"text": "\nJob ID:\t", "fontsize": "8"},
                {"field": "Id", "bold": True, "fontsize": "8"},
                {"text": "\nCreated Time:\t", "fontsize": "8"},
                {"field": "Created At", "bold": True, "fontsize": "8"},
                {"text": "\nStart Time:\t", "fontsize": "8"},
                {"field": "Started At", "bold": True, "fontsize": "8"},
                {"text": "\nDuration (hh:mm:ss):\t", "fontsize": "8"},
                {"field": duration, "bold": True, "fontsize": "8"},
                {"text": "\n", "fontsize": "8"},
                {"field": "Notes", "fontsize": "8"},
            ],
            pane_index=pane_index,
        )

    editor.configure_worksheet_style(
        GANTT,
        # Axis titles are hidden, not the axes themselves: the Gantt marks are
        # positioned by the two folded datetime axes.
        hide_axes=False,
        hide_gridlines=False,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_table_dividers=False,
        label_formats=[
            {"field": "DISCRETE(DAYTRUNC(Created At))", "text-format": "*ddd dd mmm yyyy", "font-size": "8"},
            {"field": WAITING_AXIS, "text-format": "*h:mm am/pm", "font-size": "8"},
            {"field": PROCESSING_AXIS, "text-format": "*h:mm am/pm", "font-size": "8"},
        ],
        cell_formats=[
            {"field": WAITING_SIZE, "text-format": "*hh:mm:ss"},
            {"field": PROCESSING_SIZE, "text-format": "*hh:mm:ss"},
            {"field": "Created At Baseline", "text-format": "*h:mm am/pm"},
            {"field": "Started At Baseline", "text-format": "*h:mm am/pm"},
        ],
        axis_style={
            "per_field": [
                {"attr": "title", "field": WAITING_AXIS, "scope": "cols", "value": ""},
                {"attr": "title", "field": PROCESSING_AXIS, "scope": "cols", "value": ""},
            ],
        },
    )


def build_key(editor: TWBEditor) -> None:
    """Two-bar legend: Waiting (Site 9) versus Processing (Site 7)."""
    editor.add_worksheet(KEY)
    # Waiting must be listed before Processing. The author used a manual sort
    # dictionary; sorting Key Label descending by Key Order is the declarative
    # equivalent and yields the same rendered order.
    editor.configure_layered_chart(
        KEY,
        columns=["Key Label", "One"],
        axis_shelf="columns",
        filters=[{"column": "Site", "values": ["Site 7", "Site 9"]}],
        sort_descending="Key Order",
        sort_field="Key Label",
        panes=[
            {
                "axis": "One",
                "mark_type": "Square",
                "color": "Site",
                "color_map": SITE_COLORS,
                "size": "Site",
                "tooltip": ["Key Label", "Site", "One"],
                "mark_sizing_off": True,
                "mark_style": {"size": "1.5", "mark-transparency": "129"},
            }
        ],
    )
    editor.configure_worksheet_style(
        KEY,
        # Axes hidden and the MIN(1) column axis fixed to 0-1, as the author set
        # it, so both key bars fill their cell.
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        disable_tooltip=True,
        label_formats=[{"field": "Key Label", "font-size": "8"}],
        axis_style={
            "encodings": [
                {
                    "field": "One",
                    "scope": "cols",
                    "class": "0",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                }
            ],
        },
    )


def build_data_sheet(editor: TWBEditor) -> None:
    """Supporting crosstab sheet the author kept hidden on the dashboard."""
    editor.add_worksheet(DATA_SHEET)
    editor.configure_chart(
        DATA_SHEET,
        mark_type="Text",
        columns=["Measure Names"],
        rows=[
            "Id",
            "Created At",
            "Created At Baseline",
            "Started At",
            "Started At Baseline",
            "Completed At",
        ],
        measure_values=["Waiting Time", "Processing Time"],
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        DATA_SHEET,
        hide_gridlines=False,
        hide_zeroline=True,
        hide_borders=False,
        panes_style=[{"mark_style": {"mark-labels-show": "true"}}],
    )


def build_dashboard(editor: TWBEditor) -> None:
    """Recreate the 1000x800 dashboard frame with its controls and legends."""

    def px(x: int, y: int, w: int, h: int) -> dict:
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 800 * 100000),
        }

    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "text",
                "runs": [
                    {
                        "text": "WHEN DO EXTRACTS RUN DURING THE DAY?",
                        "bold": True,
                        "font_color": "#000000",
                        "font_size": "16",
                    },
                    {"text": "\n"},
                    {
                        "text": "Understand the pattern of each extract refresh on a daily basis",
                        "font_color": "#000000",
                        "font_size": "11",
                    },
                ],
                "absolute": px(0, 0, 1000, 60),
                "style": {
                    "border-style": "none",
                    "border-width": "0",
                    "margin": "0",
                    "background-color": "#ffffff",
                },
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "FILTERS",
                        "font_color": "#000000",
                        "font_name": "Tableau Medium",
                        "font_size": "11",
                    }
                ],
                "absolute": px(5, 62, 75, 69),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "paramctrl",
                "parameter": "pDaysToShow",
                "mode": "slider",
                "show_title": True,
                "caption": "Show data for last...",
                "absolute": px(80, 62, 215, 69),
                "style": {
                    "border-style": "none",
                    "border-width": "0",
                    "margin": "4",
                    "background-color": "#f5f5f5",
                },
            },
            {
                "type": "filter",
                "worksheet": GANTT,
                "field": "Site",
                "mode": "checkdropdown",
                "values": "database",
                "show_apply": True,
                "absolute": px(295, 62, 168, 69),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "KEY",
                        "font_color": "#000000",
                        "font_name": "Tableau Medium",
                        "font_size": "11",
                    }
                ],
                "absolute": px(5, 136, 44, 48),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "worksheet",
                "name": KEY,
                "show_title": False,
                "absolute": px(49, 136, 227, 48),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "color",
                "worksheet": GANTT,
                "field": "Extract Status",
                "pane_index": 2,
                "mode": "horz",
                "show_title": False,
                "absolute": px(336, 136, 383, 48),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "color",
                "worksheet": GANTT,
                "field": "Over Wait Time Threshold",
                "pane_index": 1,
                "mode": "horz",
                "show_title": False,
                "absolute": px(719, 136, 276, 48),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "worksheet",
                "name": GANTT,
                "show_title": False,
                "absolute": px(0, 189, 1000, 581),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "CHALLENGE BY : DONNA COLES",
                        "font_color": "#000000",
                        "font_name": "Tableau Medium",
                        "font_size": "8",
                    }
                ],
                "absolute": px(0, 770, 514, 30),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "#WOW2021  |  WEEK 36",
                        "font_color": "#000000",
                        "font_name": "Tableau Medium",
                        "font_size": "8",
                        "font_alignment": "2",
                    }
                ],
                "absolute": px(514, 770, 486, 30),
                "style": {"border-style": "none", "border-width": "0", "margin": "4"},
            },
        ],
    }

    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout=layout,
        worksheet_names=[GANTT, KEY],
    )
    editor.set_worksheet_hidden(DATA_SHEET, True)
    editor.set_active_dashboard(DASHBOARD)


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    editor = TWBEditor("")
    # Reuse the template datasource for the locked extract so the artifact
    # carries exactly one data source and packages only the Hyper file.
    editor.set_hyper_connection(str(HYPER_FILE), table_name="Extract")

    editor.add_parameter(
        "Now",
        datatype="datetime",
        default_value=NOW,
        domain_type="any",
    )
    editor.add_parameter(
        "pDaysToShow",
        datatype="integer",
        default_value=DAYS_TO_SHOW,
        domain_type="range",
        min_value="1",
        max_value="10",
        default_format='n#,##0" days";-#,##0" days"',
    )

    add_calculations(editor)
    configure_palettes(editor)
    build_gantt(editor)
    build_key(editor)
    build_data_sheet(editor)
    build_dashboard(editor)

    editor.save(OUTPUT_TWBX)
    return OUTPUT_TWBX


if __name__ == "__main__":
    print(build())
