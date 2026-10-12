"""Rebuild the WW25 "Can You Make Spine Charts?" dashboard.

The challenge (Sean Miller, resurrecting Emma Whyte's 2017 spine chart, rebuilt
by Donna Coles) shows one selected university's average agreement per question
against the overall average, with the min/max range and the inter-quartile band
drawn as reference lines. A parameter drives the university selection so the
overall average stays intact (no LoDs, no table calcs).

Chain:
  data (Question Number, Question Text, University, Sample Size, % Agree)
  → pUniversity (list, default "The University of Liverpool")
  → University Avg / Sample Size / Overall Avg / Delta / Colour
  → Lower Quartile / Upper Quartile (PERCENTILE(% Agree, 0.25/0.75))
  → Viz: Question Number / Question Text / Sample Size / University Avg /
    Overall Avg / Delta as discrete row pills, the University Avg axis on
    Columns, Circle mark coloured by Colour, AVG/MIN/MAX(% Agree) and the
    quartiles on Detail, and three reference lines/bands (avg line, min-max
    band, IQR band)
  → Legend: a fixed Middlesex University marker with labelled bands
  → dashboard: 1366x900 with the legend strip under the title
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_11t94k216ehodl0zrdp701x51e14.hyper"
DASHBOARD = "2021_06_23_WW25_Spine_Chart"

DEFAULT_UNIVERSITY = "The University of Liverpool"
LEGEND_UNIVERSITY = "Middlesex University"

POSITIVE = "#f2c14e"
NEGATIVE = "#5b9bd5"
OUTER_BAND = "#f5f5f5"
INNER_BAND = "#d9d9d9"
BACKGROUND = "#f5f1f0"

PCT = "p0.0%"
DELTA = '*0.00%▲;0.00%▼'

UNIVERSITY_AVG = "AVG(IF [University] = [pUniversity] THEN [% Agree] END)"
OVERALL_AVG = "AVG([% Agree])"


def add_measures(editor: TWBEditor) -> None:
    editor.add_parameter(
        "pUniversity",
        datatype="string",
        default_value=DEFAULT_UNIVERSITY,
        domain_type="list",
        allowed_values=[DEFAULT_UNIVERSITY, LEGEND_UNIVERSITY, "University of Aberdeen"],
    )

    # The row pills are discrete, so each measure gets a second ordinal copy for
    # the Rows shelf; the quantitative copies drive the Columns axis and the
    # reference lines.
    editor.add_calculated_field(
        "University Avg",
        UNIVERSITY_AVG,
        datatype="real",
        role="measure",
        field_type="ordinal",
        default_format=PCT,
    )
    editor.add_calculated_field(
        "University Avg Axis",
        UNIVERSITY_AVG,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PCT,
    )
    editor.add_calculated_field(
        "Sample Size (Selected)",
        "AVG(IF [University]=[pUniversity] THEN [Sample Size] END)",
        datatype="integer",
        role="measure",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Overall Avg",
        OVERALL_AVG,
        datatype="real",
        role="measure",
        field_type="ordinal",
        default_format=PCT,
    )
    editor.add_calculated_field(
        "Overall Avg Axis",
        OVERALL_AVG,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PCT,
    )
    editor.add_calculated_field(
        "Delta",
        "[University Avg Axis] - [Overall Avg Axis]",
        datatype="real",
        role="measure",
        field_type="ordinal",
        default_format=DELTA,
    )
    editor.add_calculated_field(
        "Colour",
        "[Delta]>=0",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Lower Quartile",
        "PERCENTILE([% Agree],0.25)",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PCT,
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Upper Quartile",
        "PERCENTILE([% Agree],0.75)",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PCT,
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Legend Avg",
        f"AVG(IF [University] = '{LEGEND_UNIVERSITY}' THEN [% Agree] END)",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PCT,
    )
    editor.add_calculated_field(
        "Legend Colour",
        "[Legend Avg] - [Overall Avg Axis] >=0",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.set_field_format("% Agree", PCT)


def build_viz(editor: TWBEditor) -> None:
    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        columns=["University Avg Axis"],
        rows=[
            "Question Number",
            "Question Text",
            "Sample Size (Selected)",
            "University Avg",
            "Overall Avg",
            "Delta",
        ],
        axis_shelf="columns",
        fold_axes=False,
        panes=[
            {
                "axis": "University Avg Axis",
                "mark_type": "Circle",
                "color": "Colour",
                "color_map": {"true": POSITIVE, "false": NEGATIVE},
                "detail_extra": ["AVG(% Agree)", "MIN(% Agree)", "MAX(% Agree)",
                                 "Lower Quartile", "Upper Quartile"],
                "mark_sizing_off": True,
            }
        ],
    )

    # Average line, then the min/max band, then the IQR band. The author adds
    # each band as a paired min/max reference line with a fill.
    editor.add_reference_line(
        "Viz",
        axis_field="University Avg Axis",
        value_field="AVG(% Agree)",
        formula="average",
        label_type="none",
        tooltip="Avg : <Value>",
        scope="per-pane",
    )
    editor.add_reference_band(
        "Viz",
        axis_field="University Avg Axis",
        lower_field="MIN(% Agree)",
        upper_field="MAX(% Agree)",
        lower_formula="min",
        upper_formula="max",
        scope="per-cell",
        fill_color=OUTER_BAND,
    )
    editor.add_reference_band(
        "Viz",
        axis_field="University Avg Axis",
        lower_field="Lower Quartile",
        upper_field="Upper Quartile",
        lower_formula="min",
        upper_formula="max",
        scope="per-pane",
        fill_color=INNER_BAND,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        pane_cell_style={"text-align": "center"},
        label_formats=[
            {"field": "Question Number", "font-weight": "bold"},
            {"field": "Sample Size (Selected)", "text-align": "right"},
            {"field": "University Avg", "text-align": "right"},
            {"field": "Overall Avg", "text-align": "right"},
            {"field": "Delta", "text-align": "center"},
        ],
        header_formats=[
            {"field": "Question Number", "width": "32"},
            {"field": "Question Text", "width": "680"},
            {"field": "Sample Size (Selected)", "width": "80"},
            {"field": "University Avg", "width": "80"},
            {"field": "Overall Avg", "width": "76"},
            {"field": "Delta", "width": "96"},
            {"attr": "height-header", "value": "52"},
        ],
        axis_style={
            "per_field": [
                {
                    "field": "University Avg Axis",
                    "scope": "cols",
                    "attr": "title",
                    "value": "",
                }
            ]
        },
        table_formats=[
            {"attr": "row-levels", "value": "16"},
            {"attr": "row-horiz-levels", "value": "16"},
            {"attr": "col-levels", "value": "16"},
            {"attr": "band-size", "scope": "rows", "value": "1"},
            {"attr": "band-level", "scope": "rows", "value": "6"},
        ],
    )
    editor.configure_reference_line_style(
        "Viz",
        "refline0",
        {"stroke-color": "#000000", "stroke-size": "2"},
    )


def build_legend(editor: TWBEditor) -> None:
    """The fixed "how to read" strip with labelled bands."""
    editor.add_worksheet("Legend")
    editor.configure_layered_chart(
        "Legend",
        columns=["Legend Avg"],
        axis_shelf="columns",
        fold_axes=False,
        panes=[
            {
                "axis": "Legend Avg",
                "mark_type": "Circle",
                "color": "Legend Colour",
                "color_map": {"true": POSITIVE, "false": NEGATIVE},
                "detail_extra": ["Upper Quartile", "Lower Quartile", "Overall Avg Axis",
                                 "MIN(% Agree)", "MAX(% Agree)"],
                "mark_sizing_off": True,
            }
        ],
    )
    editor.add_reference_line(
        "Legend",
        axis_field="Legend Avg",
        value_field="Overall Avg Axis",
        formula="average",
        label_type="custom",
        label="Overall Avg",
        tooltip="",
        scope="per-pane",
    )
    editor.add_reference_line(
        "Legend",
        axis_field="Legend Avg",
        value_field="MIN(% Agree)",
        formula="min",
        label_type="custom",
        label="Overall Min",
        tooltip="",
        scope="per-pane",
    )
    editor.add_reference_line(
        "Legend",
        axis_field="Legend Avg",
        value_field="MAX(% Agree)",
        formula="max",
        label_type="custom",
        label="Overall Max",
        tooltip="",
        scope="per-pane",
    )
    editor.add_reference_band(
        "Legend",
        axis_field="Legend Avg",
        lower_field="Lower Quartile",
        upper_field="Upper Quartile",
        lower_formula="min",
        upper_formula="max",
        scope="per-pane",
        fill_color=INNER_BAND,
    )
    editor.configure_worksheet_style(
        "Legend",
        background_color=BACKGROUND,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_axes=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
    )
    editor.set_worksheet_title("Legend", "How to read")


def build_dashboard(editor: TWBEditor) -> None:
    def pos(x, y, w, h):
        return {
            "x": round(x / 1366 * 100000),
            "y": round(y / 900 * 100000),
            "w": round(w / 1366 * 100000),
            "h": round(h / 900 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "Spine Chart",
                    "font_size": 20,
                    "font_color": "#000000",
                    "bold": True,
                }
            ],
            "absolute": pos(8, 6, 400, 30),
        },
        {
            "type": "worksheet",
            "name": "Legend",
            "show_title": True,
            "fit": "entire",
            "absolute": pos(8, 40, 1350, 90),
        },
        {
            "type": "worksheet",
            "name": "Viz",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 138, 1350, 754),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1366,
        height=900,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Legend", "Viz"],
    )

    for name in ("Viz", "Legend"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    add_measures(editor)
    build_viz(editor)
    build_legend(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
