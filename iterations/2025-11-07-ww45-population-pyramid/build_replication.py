"""Build WW45 (2025) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate). Visual constants (palette hexes, axis titles,
number formats) are analysis-phase facts recorded in analysis.md, the same way
the challenge credits text is.
"""

import json
from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "TEMP_0fddbkh1pwidao13lrii60pl7znj.hyper"
# Cloud publish requires an absolute hyper path baked into dbname; __file__
# resolve() yields an absolute path on save time, which the captured twbx keeps.
HYPER = HYPER.resolve()
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2025_11_05_WW45_Population_Pyramid"

# Author mark size (bar thickness) on all three bar panes.
MARK_SIZE = "1.3403314352035522"
# Author palettes: Measure Names (gender bars + gap measure), the boolean
# gap-colour flag, and the Gender dimension.
MN_PALETTE = {"Females": "#6fb798", "Males": "#8175aa", "Headcount Gap": "#f28e2b"}
GAP_BOOL_PALETTE = {"true": "#6fb899", "false": "#8175aa"}
GENDER_PALETTE = {
    "Female": "#4e79a7",
    "Prefer Not to Say": "#76b7b2",
    "Non-Binary": "#e15759",
    "Male": "#f28e2b",
}


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # cwtwb has no numeric-bin primitive, so the author's 5-year bin is
    # expressed as a public calculated field producing the band start.
    editor.add_calculated_field(
        "Age Group",
        "INT([Age] / 5) * 5",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    # The author drags Total Headcount / Other Gender onto Rows as DISCRETE
    # pills to space the bands. cwtwb makes a measure discrete-on-rows via an
    # ordinal (:ok) instance, so we declare field_type="ordinal" rather than
    # wrapping in the non-existent DISCRETE() function.
    editor.add_calculated_field(
        "Total Headcount",
        "{FIXED [Age Group]: COUNT([Age])}",
        datatype="integer",
        role="measure",
        field_type="ordinal",
        default_format="n#,##0;-#,##0",
    )
    editor.add_calculated_field(
        "Other Gender",
        "{FIXED [Age Group]: SUM(IIF([Gender] <> 'Female' AND [Gender] <> 'Male', 1, 0))}",
        datatype="integer",
        role="measure",
        field_type="ordinal",
        default_format="n#,##0;-#,##0",
    )
    editor.add_calculated_field(
        "Males",
        "IIF([Gender] = 'Male', 1, 0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format="n#,##0;-#,##0",
    )
    # Negative so female bars extend left of the shared zero.
    editor.add_calculated_field(
        "Females",
        "IIF([Gender] = 'Female', -1, 0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        # Author format: negative section has no sign, so axis ticks and
        # labels render 99 rather than -99 (mirrored population-pyramid read).
        default_format="*#,##0;#,##0",
    )
    editor.add_calculated_field(
        "Headcount Gap",
        "SUM([Males]) + SUM([Females])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format="*#,##0;#,##0",
    )
    editor.add_calculated_field(
        "Colour - Headcount Gap",
        "[Headcount Gap] < 0",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Tooltip - Most Gender",
        "IIF([Colour - Headcount Gap], 'women', 'men')",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Tooltip - Least Gender",
        "IIF(NOT [Colour - Headcount Gap], 'women', 'men')",
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    # ---- Viz: mirrored population pyramid with a per-band gap column.
    # The author builds a dual axis (Females + Males, synchronized) and adds a
    # third independent axis for Headcount Gap. cwtwb expresses this as a
    # dual-axis on columns plus an extra axis. Each pane is labelled with its
    # OWN axis measure (author has no label shelf at all: mark-labels-show
    # auto-labels the axis measure), so label_1 is the first column measure.
    editor.add_worksheet("Viz")
    editor.configure_dual_axis(
        "Viz",
        mark_type_1="Bar",
        mark_type_2="Bar",
        dual_axis_shelf="cols",
        columns=["Females", "Males"],
        rows=["Age Group", "Total Headcount", "Other Gender"],
        color_by_measure_names=True,
        synchronized=True,
        show_labels=True,
        mark_sizing_off=True,
        size_value_1=MARK_SIZE,
        size_value_2=MARK_SIZE,
        extra_axes=[
            {
                "measure": "Headcount Gap",
                "color": "Colour - Headcount Gap",
                "mark_type": "Bar",
                "mark_sizing_off": True,
                "label": "Headcount Gap",
                "size_value": MARK_SIZE,
            }
        ],
        label_1="Females",
        label_2="Males",
    )

    # Author palettes live on the datasource <style> mark rule. Measure Names
    # buckets are the full measure references (quoted), exactly as the author
    # writes them; short member names do not match the rendered member value.
    def _full_ref(expression: str) -> str:
        ci = editor.field_registry.parse_expression(expression)
        return json.dumps(editor.field_registry.resolve_full_reference(ci.instance_name))

    editor.set_datasource_color_palette(
        "Measure Names",
        {_full_ref(expr): color for expr, color in MN_PALETTE.items()},
        is_measure_names=True,
    )
    editor.set_datasource_color_palette("Colour - Headcount Gap", dict(GAP_BOOL_PALETTE))
    editor.set_datasource_color_palette("Gender", dict(GENDER_PALETTE))
    editor.configure_custom_tooltip(
        "Viz",
        runs=[
            {"text": "Age Group:\t"},
            {"field": "Age Group", "bold": True},
            {"text": "\nTotal Headcount:\t"},
            {"field": "Total Headcount", "bold": True},
            {"text": "\nMales:\t"},
            {"field": "Males", "bold": True},
            {"text": "\nFemales:\t"},
            {"field": "Females", "bold": True},
            {"text": "\nOther Gender:\t"},
            {"field": "Other Gender", "bold": True},
            {"text": "\n\nThere are "},
            {"field": "Headcount Gap", "bold": True},
            {"text": " more "},
            {"field": "Tooltip - Most Gender", "bold": True},
            {"text": " than "},
            {"field": "Tooltip - Least Gender", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=False,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=False,
        # Author table-div: light row separators, no column dividers.
        table_dividers=[
            {"scope": "rows", "stroke-color": "#e6e6e6"},
            {"scope": "cols", "stroke-size": "0", "line-visibility": "off"},
        ],
        # Author label rule: black tick/label text at 9pt for every
        # visible field.
        label_formats=[
            {"field": "Males", "color": "#000000", "font-size": "9"},
            {"field": "Females", "color": "#000000", "font-size": "9"},
            {"field": "Total Headcount", "color": "#000000", "font-size": "9"},
            {"field": "Other Gender", "color": "#000000", "font-size": "9"},
            {"field": "Age Group", "color": "#000000", "font-size": "9"},
            {"field": "Headcount Gap", "color": "#000000", "font-size": "9"},
        ],
        # Author cell rule: row height 43, 8pt black text on the measure.
        cell_formats=[
            {"field": "Other Gender", "attr": "height", "value": "43"},
            {"field": "Females", "attr": "font-size", "value": "8"},
            {"field": "Females", "attr": "color", "value": "#000000"},
        ],
        # Author header rule: 58px header band, explicit column widths
        # that force two-line wraps.
        header_formats=[
            {"attr": "height-header", "value": "58"},
            {"field": "Age Group", "attr": "width", "value": "60"},
            {"field": "Total Headcount", "attr": "width", "value": "84"},
            {"field": "Other Gender", "attr": "width", "value": "60"},
        ],
        # Author axis rule: one visible bottom axis retitled "Headcount"
        # (the Females field) and the Males axis hidden. The encodings are
        # restated exactly as the author writes them (fold, NO synchronized
        # attr): the builder's synchronized flag makes the right axis domain
        # collapse to 150, while both author sides independently round to
        # 200 from their own extents.
        axis_style={
            "encodings": [
                {"field": "Males", "class": "0", "scope": "cols", "fold": True},
                {"field": "Headcount Gap", "class": "1", "scope": "cols", "fold": True},
            ],
            "per_field": [
                {"field": "Females", "attr": "title", "value": "Headcount",
                 "scope": "cols", "class": "0"},
                {"field": "Males", "attr": "display", "value": "false",
                 "scope": "cols", "class": "0"},
                # Author axis rule: fixed 53px axis band heights.
                {"field": "Females", "attr": "height", "value": "53"},
                {"field": "Males", "attr": "height", "value": "53"},
            ]
        },
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"color-mode": "auto", "font-weight": "bold", "font-size": "12"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        # Author repeats cell/datalabel/mark styling per bar pane; pane ids
        # come from the dual-axis builder (1, 2) plus the extra axis (4).
        panes_style={
            "1": {
                "cell_style": {"text-align": "center", "vertical-align": "center"},
                "datalabel_style": {"color-mode": "auto", "font-weight": "bold",
                                    "font-size": "11"},
            },
            "2": {
                "cell_style": {"text-align": "center", "vertical-align": "center"},
                "datalabel_style": {"color-mode": "auto", "font-weight": "bold",
                                    "font-size": "12"},
            },
            "4": {
                "cell_style": {"text-align": "center", "vertical-align": "center"},
                "datalabel_style": {"color-mode": "auto", "font-weight": "bold",
                                    "font-size": "12"},
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "true"},
            },
        },
    )
    # Author puts BOTH constant-zero reference lines in the anchor pane
    # (no x-axis-name), bound by axis-column to the Females and Gap axes
    # with unique ids refline0/refline1. Anchoring both on pane index 0
    # reproduces that structure; cwtwb numbers ids by per-pane count, so
    # two separate panes would collide on refline0 and Cloud drops the
    # duplicate.
    for axis_field in ("Females", "Headcount Gap"):
        add_message = editor.add_reference_line(
            "Viz",
            axis_field=axis_field,
            value_field=axis_field,
            formula="constant",
            scope="per-pane",
            label_type="none",
            probability=None,
            pane_index=0,
        )
        # add_reference_line returns "Added reference line 'reflineN'..."
        # so we can extract the id without touching the underlying XML.
        rid = add_message.split("'")[1]
        editor.configure_reference_line_style(
            "Viz",
            rid,
            {
                "line-visibility": "on",
                "line-pattern-only": "solid",
                "stroke-size": "2",
                "stroke-color": "#000000",
                "fill-above": "#00000000",
                "fill-below": "#00000000",
            },
        )

    # Author worksheet title: big centered heading plus the subtitle with the
    # Men/Women colour tokens. "Æ\n" is Tableau's own line-break marker in
    # formatted text (present in every author workbook).
    editor.set_worksheet_rich_title(
        "Viz",
        runs=[
            {"text": "Population Pyramids", "bold": True, "fontalignment": "1",
             "fontcolor": "#000000", "fontsize": "18"},
            {"text": "Æ\n", "fontalignment": "1"},
            {"text": "Showing the headcount distribution and variance of ",
             "fontalignment": "1", "fontcolor": "#000000", "fontsize": "12"},
            {"text": "Men", "bold": True, "fontalignment": "1",
             "fontcolor": "#8175aa", "fontsize": "12"},
            {"text": " vs ", "fontalignment": "1", "fontcolor": "#000000",
             "fontsize": "12"},
            {"text": "Women", "bold": True, "fontalignment": "1",
             "fontcolor": "#6fb798", "fontsize": "12"},
            {"text": " at ACME Inc.", "fontalignment": "1",
             "fontcolor": "#000000", "fontsize": "12"},
        ],
    )

    # ---- Dashboard: fixed 1300x700 with credits.
    editor.add_dashboard(
        DASHBOARD,
        width=1300,
        height=700,
        worksheet_names=["Viz"],
        layout={
            "type": "container",
            "direction": "vertical",
            # The author's dashboard root carries margin=8 and the Viz zone
            # margin=4, so the worksheet content is inset by 12 dashboard px.
            "style": {"margin": "8"},
            "children": [
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": True,
                    "fit": "entire",
                    "weight": 1,
                    "style": {"margin": "4"},
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 37,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {"text": "CHALLENGE BY: Sean Miller", "font_size": "8", "font_alignment": "0", "font_color": "#000000"},
                            ],
                            "weight": 1,
                            "style": {"margin": "4"},
                        },
                        {
                            "type": "text",
                            "runs": [
                                {"text": "#WOW2025  |  WEEK 45 | Data: #RWFD", "font_size": "8", "font_alignment": "1", "font_color": "#000000"},
                            ],
                            "weight": 1,
                            "style": {"margin": "4"},
                        },
                        {
                            "type": "text",
                            "runs": [
                                {"text": "RECREATED BY: Donna Coles", "font_size": "8", "font_alignment": "2", "font_color": "#000000"},
                            ],
                            "weight": 1,
                            "style": {"margin": "4"},
                        },
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 37,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {"text": "https://workout-wednesday.com/wow2025w45/", "font_size": "8", "font_alignment": "1", "font_color": "#000000", "hyperlink": "https://workout-wednesday.com/wow2025w45/"},
                            ],
                            "weight": 1,
                            "style": {"margin": "4"},
                        },
                    ],
                },
            ],
        },
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    editor.save(output_path)
    return output_path


if __name__ == "__main__":
    print(build(OUTPUT_DIR / "replicated-workbook.twbx"))
