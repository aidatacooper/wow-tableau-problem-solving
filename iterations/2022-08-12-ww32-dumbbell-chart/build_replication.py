"""Build WW32 (2022) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate). Visual constants (palette hexes, axis rules,
label formats, dashboard furniture) mirror the analysis notes in analysis.md.
"""

import json
from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "federated_1dtv4ml0xnx8j811wlbmr1.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2022_08_10_WW32_Dumbbell_Chart"
POST_URL = "https://www.workout-wednesday.com/2022w32tab/"

# The author compares smartphone ownership for two survey years.
YEARS = (2015, 2019)
THRESHOLD = 0.2

# Author mark sizes (marks-scaling-off with an explicit size per pane).
CIRCLE_SIZE = "1.5052486658096313"
LINE_SIZE = "4.5644211769104004"

# Author palettes live on the datasource <style> mark rule:
# circles colour by Measure Names (2015 green / 2019 purple), connectors
# colour by the boolean delta flag (false gray / true red).
MN_PALETTE = (
    ("SUM(Ownership 2019)", "#5e50a4"),
    ("SUM(Ownership 2015)", "#98d3a2"),
)
DELTA_PALETTE = {"false": "#a2a2a2", "true": "#cd3e4c"}

# Author rich worksheet title (the subtitle block above the plot).
# Tableau titles only break lines on the "Æ\n" paragraph separator (a raw
# newline is dropped); the author writes the same sequence, and the Æ glyph
# renders invisibly.
TITLE_RUNS = [
    {
        "text": "Youth cell phone ownership growth is highest amongst "
        "Middle Schoolers.",
        "bold": True,
    },
    {"text": "Æ\n"},
    {
        "text": "While cell phone ownership has grown amongst all ages (8-18), "
        "from ",
        "fontsize": "10",
    },
    {"text": "2015", "bold": True, "fontsize": "10", "fontcolor": "#97d1a1"},
    {"text": " to ", "fontsize": "10"},
    {"text": "2019", "bold": True, "fontsize": "10", "fontcolor": "#5e50a3"},
    {"text": ", ", "fontsize": "10"},
    {"text": "ages 11-14", "bold": True, "fontsize": "10", "fontcolor": "#cd3e4c"},
    {
        "text": " have all experienced an increase of over 20%.",
        "fontsize": "10",
    },
    {"text": "Æ\n"},
    {"text": "Æ ", "fontsize": "10"},
    {"text": "Æ\n"},
]


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # The delta (range) label anchors at the lexicographic minimum of the
    # range field, and its Measure Names members are the quoted full field
    # references. With cwtwb's per-build UUID names the smaller reference is
    # random, so the ▲ label flipped between the top and bottom circle across
    # rebuilds. Pinned internal names keep Ownership 2015 sorting before
    # Ownership 2019, anchoring the label under the 2015 circle like the
    # author's workbook (whose own field names happen to sort that way too).
    for name, formula, datatype, role, field_type, fmt, internal_name in [
        (
            "Ownership 2015",
            f"IF [Year] = {YEARS[0]} THEN [Ownership] END",
            "real",
            "measure",
            "quantitative",
            "p0%",
            "[Calculation_Ownership2015]",
        ),
        (
            "Ownership 2019",
            f"IF [Year] = {YEARS[1]} THEN [Ownership] END",
            "real",
            "measure",
            "quantitative",
            "p0%",
            "[Calculation_Ownership2019]",
        ),
        (
            "Difference",
            "SUM([Ownership 2019]) - SUM([Ownership 2015])",
            "real",
            "measure",
            "quantitative",
            "p0%",
            None,
        ),
        (
            # Age is an integer in the extract, so the SDK infers it as a
            # measure. The author uses it as a discrete dimension; an explicit
            # ordinal calculated field produces the [none:...:ok] instance.
            "Age Group",
            "[Age]",
            "integer",
            "dimension",
            "ordinal",
            "",
            None,
        ),
        (
            "Difference>0.2",
            f"[Difference] > {THRESHOLD}",
            "boolean",
            "measure",
            "nominal",
            "",
            None,
        ),
        (
            # The author nests a constant "Dummy" dimension inside Age on
            # Columns (Age / Dummy). It adds no visual split (one member), but
            # it is what makes Cloud render the fold as one shared scale.
            "Dummy",
            "'Dummy'",
            "string",
            "dimension",
            "nominal",
            "",
            None,
        ),
    ]:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format=fmt,
            internal_name=internal_name,
        )

    editor.add_worksheet("Viz")
    # A dumbbell is two stacked Measure Values shelves folded onto one shared
    # scale: a Circle pane carrying both years, and a Line pane whose Path
    # connects them. Both panes bind to the same "Multiple Values" axis name
    # with y-index 0/1, and fold+synchronized makes the connector vertical.
    editor.configure_layered_chart(
        "Viz",
        columns=["Age Group", "Dummy"],
        rows=["Multiple Values", "Multiple Values"],
        panes=[
            {
                "mark_type": "Circle",
                "axis": "Multiple Values",
                "measure_values": ["SUM(Ownership 2015)", "SUM(Ownership 2019)"],
                "color": "Measure Names",
                "tooltip": ["SUM(Ownership 2015)", "SUM(Ownership 2019)", "Difference"],
                "mark_sizing_off": True,
                "selection_relaxation": "disallow",
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "size": CIRCLE_SIZE,
                },
            },
            {
                "mark_type": "Line",
                "axis": "Multiple Values",
                "measure_values": ["SUM(Ownership 2015)", "SUM(Ownership 2019)"],
                "path": "Measure Names",
                "color": "Difference>0.2",
                "label": "Difference",
                "tooltip": ["SUM(Ownership 2015)", "SUM(Ownership 2019)"],
                "mark_sizing_off": True,
                "selection_relaxation": "disallow",
                "mark_style": {
                    "size": LINE_SIZE,
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "range",
                    "mark-labels-range-scope": "multi-mark",
                    "mark-labels-range-min": "true",
                    "mark-labels-range-max": "false",
                    "mark-labels-range-field": "Measure Names",
                },
            },
        ],
        synchronized=True,
    )

    # Author palettes: Measure Names buckets are the full measure references
    # (quoted), exactly as the author writes them; short member names do not
    # match the rendered member value.
    def _full_ref(expression: str) -> str:
        ci = editor.field_registry.parse_expression(expression)
        return json.dumps(editor.field_registry.resolve_full_reference(ci.instance_name))

    editor.set_datasource_color_palette(
        "Measure Names",
        {_full_ref(expression): color for expression, color in MN_PALETTE},
        is_measure_names=True,
    )
    editor.set_datasource_color_palette("Difference>0.2", dict(DELTA_PALETTE))

    editor.configure_worksheet_style(
        "Viz",
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
        # Author gridline rule: row gridlines off (column gridlines stay at
        # the Tableau default of off).
        gridline_style={"rows": {"stroke-size": "0", "line-visibility": "off"}},
        label_formats=[
            # The Age / Dummy nesting shows a second header row of "Dummy"
            # members; the author hides it with a label-display rule while
            # keeping the Age header visible (bold, 12pt).
            {"field": "Dummy", "attr": "display", "value": "false"},
            {"field": "Age Group", "font-size": "12"},
            {"field": "Age Group", "font-weight": "bold"},
        ],
        # The Difference label renders as an up/down triangle with the
        # author's number format (cell rule, so it applies to mark labels).
        cell_formats=[
            {"field": "Difference", "text-format": "*▲0%;▼0%"},
        ],
        axis_style={
            # Folded y-axis: both classes hidden, fold direction reversed.
            "render-fold-reversed": "true",
            "per_field": [
                {
                    "field": "Multiple Values",
                    "attr": "display",
                    "value": "false",
                    "class": 0,
                    "scope": "rows",
                },
                {
                    "field": "Multiple Values",
                    "attr": "display",
                    "value": "false",
                    "class": 1,
                    "scope": "rows",
                },
            ],
        },
        # Per-pane cell/datalabel styling: labels centered inside the circles,
        # delta labels bottom-centred under the connector, bold Tableau Bold
        # auto-coloured datalabels.
        panes_style={
            "1": {
                "cell_style": {"vertical-align": "center", "text-align": "center"},
                "datalabel_style": {
                    "color-mode": "auto",
                    "font-weight": "bold",
                    "font-family": "Tableau Bold",
                },
            },
            "2": {
                "cell_style": {"text-align": "center", "vertical-align": "bottom"},
                "datalabel_style": {
                    "color-mode": "auto",
                    "font-weight": "bold",
                    "font-family": "Tableau Bold",
                },
            },
        },
    )

    editor.configure_custom_tooltip(
        "Viz",
        runs=[
            {"field": "SUM(Ownership 2015)", "bold": True},
            {"text": " of kids age "},
            {"field": "Age Group", "bold": True},
            {"text": " had smartphones in 2015, compared to "},
            {"field": "SUM(Ownership 2019)", "bold": True},
            {"text": " in 2019, a change of "},
            {"field": "Difference", "bold": True},
        ],
        pane_index=0,
    )
    # The author's connector pane carries an empty custom tooltip.
    editor.configure_custom_tooltip("Viz", runs=[{"text": " "}], pane_index=1)
    # Delta labels use the author's template: a line break followed by the
    # <Difference> field markup, so Tableau substitutes the field with its
    # cell text-format (▲/▼ percent). configure_custom_label maps the newline
    # to the "Æ\n" paragraph separator and writes the field as <ref>.
    editor.configure_custom_label(
        "Viz",
        runs=[
            {"text": "\n"},
            {"field": "Difference"},
        ],
        pane_index=1,
    )

    editor.set_worksheet_rich_title("Viz", TITLE_RUNS)

    def _credit(text: str, alignment: str, x: int, width: int) -> dict:
        return {
            "type": "text",
            "runs": [
                {
                    "text": text,
                    "bold": True,
                    "font_size": "8",
                    "font_color": "#5e50a3",
                    "font_name": "Tableau Medium",
                    "font_alignment": alignment,
                }
            ],
            "absolute": {"x": x, "y": 91000, "w": width, "h": 4000},
            "style": {"margin": "4"},
        }

    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"margin": "8"},
        "children": [
            {
                "type": "text",
                "text": "Can you build a dumbbell chart?",
                "runs": [
                    {
                        "text": "Can you build a dumbbell chart?",
                        "font_size": "20",
                        "bold": True,
                        "font_color": "#333333",
                        "font_alignment": "1",
                    }
                ],
                "absolute": {"x": 800, "y": 1000, "w": 98400, "h": 5750},
                "style": {"margin": "4"},
            },
            {
                # Thin gray rule bar under the title.
                "type": "empty",
                "fixed_size": 2,
                "absolute": {"x": 800, "y": 6750, "w": 98400, "h": 250},
                "style": {"background-color": "#555555", "margin": "0"},
            },
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": True,
                "fit": "entire",
                "absolute": {"x": 800, "y": 7000, "w": 98400, "h": 84000},
                "style": {"margin": "4"},
            },
            _credit("CHALLENGE BY : KYLE YETTER", "0", 800, 34533),
            _credit("#WOW2022  |  WEEK 32", "1", 35333, 32133),
            _credit("RECREATED BY : DONNA COLES", "2", 67466, 31733),
            {
                "type": "text",
                "text": POST_URL,
                "runs": [
                    {
                        "text": POST_URL,
                        "font_size": "8",
                        "font_alignment": "1",
                        "hyperlink": f"tabdoc:load-url url=&quot;{POST_URL}&quot;",
                    }
                ],
                "absolute": {"x": 800, "y": 95000, "w": 98400, "h": 4000},
                "style": {"margin": "4"},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout=layout,
        worksheet_names=["Viz"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2022-08-12-ww32-dumbbell-chart-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
