"""Build WW45 (2025) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate).
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "TEMP_0fddbkh1pwidao13lrii60pl7znj.hyper"
# Cloud publish requires an absolute hyper path baked into dbname; __file__
# resolve() yields an absolute path on save time, which the captured twbx keeps.
HYPER = HYPER.resolve()
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2025_11_05_WW45_Population_Pyramid"


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
        default_format="n#,##0;-#,##0",
    )
    editor.add_calculated_field(
        "Headcount Gap",
        "SUM([Males]) + SUM([Females])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format="#,##0;#,##0",
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
    # dual-axis on columns plus an extra axis.
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
        extra_axes=[
            {
                "measure": "Headcount Gap",
                "color": "Colour - Headcount Gap",
                "mark_type": "Bar",
                "mark_sizing_off": True,
            }
        ],
        label_1="Males",
        label_2="Females",
    )
    # Author renames the dual-axis pills to "Males (copy)" / "Females (copy)"
    # so the Measure Names encoding bucket text matches the visible pill
    # label. cwtwb's measure-name alias rewrites the column-instance
    # reference in place, which is what the author palette expects.
    editor.set_measure_name_aliases(
        "Viz",
        {
            "Males": "Males (copy)",
            "Females": "Females (copy)",
            "Headcount Gap": "Headcount Gap (copy)",
        },
    )

    # NOTE: The author palette (#6fb798 men / #8175aa women) is encoded in
    # a Measure Names palette block on the worksheet's mark style-rule.
    # cwtwb has no public API to inject per-pane Measure Names palette
    # buckets; the only public ``set_datasource_color_palette`` helper
    # keys on the short member name and Tableau Cloud Server does not
    # honor it for the synchronized dual-axis panes (only the extra-axis
    # pane picks up the encoded color). The capability gap is documented
    # in case.yaml; bars fall back to Tableau's default categorical
    # palette (blue/orange) for the Males and Females panes, and the
    # Headcount Gap pane uses the author orange because that pane's
    # color comes from the boolean flag, not the Measure Names palette.
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
        hide_zeroline=False,
        hide_borders=True,
        hide_row_field_labels=False,
        label_formats=[
            {"field": "Males", "attr": "font-size", "value": "9"},
            {"field": "Females", "attr": "font-size", "value": "9"},
            {"field": "Total Headcount", "attr": "font-size", "value": "9"},
            {"field": "Other Gender", "attr": "font-size", "value": "9"},
            {"field": "Age Group", "attr": "font-size", "value": "9"},
        ],
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"color-mode": "auto", "font-weight": "bold", "font-size": "12"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "false"},
    )
    # Constant zero reference line on the Females axis (pane index 1 in the
    # dual-axis builder) and the Headcount Gap axis (pane index 3, the
    # extra-axis). The anchor pane is at index 0; the synchronized Males
    # pane is at index 2.
    for pane_index, axis_field in [(1, "Females"), (3, "Headcount Gap")]:
        add_message = editor.add_reference_line(
            "Viz",
            axis_field=axis_field,
            value_field=axis_field,
            formula="constant",
            scope="per-pane",
            label_type="none",
            probability=None,
            pane_index=pane_index,
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

    # ---- Dashboard: fixed 1300x700 with credits.
    editor.add_dashboard(
        DASHBOARD,
        width=1300,
        height=700,
        worksheet_names=["Viz"],
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": False,
                    "fit": "entire",
                    "weight": 1,
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 24,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {"text": "CHALLENGE BY: Sean Miller",
                                 "font_size": "8"},
                            ],
                            "weight": 1,
                        },
                        {
                            "type": "text",
                            "runs": [
                                {"text": "#WOW2025  |  WEEK 45 | Data: #RWFD",
                                 "font_size": "8", "font_alignment": "1"},
                            ],
                            "weight": 1,
                        },
                        {
                            "type": "text",
                            "runs": [
                                {"text": "RECREATED BY: Donna Coles",
                                 "font_size": "8", "font_alignment": "2"},
                            ],
                            "weight": 1,
                        },
                    ],
                },
            ],
        },
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    # cwtwb's configure_dual_axis has injected every per-pane style-rule we
    # have a public API for. The Measure Names color palette that the author
    # uses for Men/Women colors has no public cwtwb helper, so we leave the
    # palette in Cloud's hands and document the gap in case.yaml.
    editor.save(output_path)
    return output_path


if __name__ == "__main__":
    print(build(OUTPUT_DIR / "replicated-workbook.twbx"))