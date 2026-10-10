"""Build WW32 (2022) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate).
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "federated_1dtv4ml0xnx8j811wlbmr1.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2022_08_10_WW32_Dumbbell_Chart"

# The author compares smartphone ownership for two survey years.
YEARS = (2015, 2019)
THRESHOLD = 0.2


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    for name, formula, datatype, role, field_type, fmt in [
        (
            "Ownership 2015",
            f"IF [Year] = {YEARS[0]} THEN [Ownership] END",
            "real",
            "measure",
            "quantitative",
            "p0%",
        ),
        (
            "Ownership 2019",
            f"IF [Year] = {YEARS[1]} THEN [Ownership] END",
            "real",
            "measure",
            "quantitative",
            "p0%",
        ),
        (
            "Difference",
            "SUM([Ownership 2019]) - SUM([Ownership 2015])",
            "real",
            "measure",
            "quantitative",
            "p0%",
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
        ),
        (
            "Difference>0.2",
            f"[Difference] > {THRESHOLD}",
            "boolean",
            "measure",
            "nominal",
            "",
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
        ),
    ]:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format=fmt,
        )

    editor.add_worksheet("Viz")
    # A dumbbell is two stacked Measure Values shelves folded onto one shared
    # scale: a Circle pane carrying both years, and a Line pane whose Path
    # connects them. Both panes bind to the same "Multiple Values" axis name
    # with y-index 0/1, and fold+synchronized makes the connector horizontal.
    editor.configure_layered_chart(
        "Viz",
        columns=["Age Group", "Dummy"],
        rows=["Multiple Values", "Multiple Values"],
        panes=[
            {
                "mark_type": "Circle",
                "axis": "Multiple Values",
                "measure_values": ["SUM(Ownership 2015)", "SUM(Ownership 2019)"],
                "color": "Multiple Values",
                "label": "Multiple Values",
                "mark_sizing_off": True,
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
            },
            {
                "mark_type": "Line",
                "axis": "Multiple Values",
                "measure_values": ["SUM(Ownership 2015)", "SUM(Ownership 2019)"],
                "path": "Measure Names",
                "color": "Difference>0.2",
                "label": "Difference",
                "mark_sizing_off": True,
            },
        ],
        synchronized=True,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[
            # The Age / Dummy nesting shows a second header row of "Dummy"
            # members; the author hides it with a label-display rule while
            # keeping the Age header visible.
            {"field": "Dummy", "attr": "display", "value": "false"},
            # The Difference label renders as an up/down triangle with the
            # author's number format.
            {"field": "Difference", "text-format": "*▲0%;▼0%"},
        ],
    )
    editor.configure_custom_tooltip(
        "Viz",
        runs=[
            {"field": "SUM(Ownership 2015)"},
            {"text": " of kids age "},
            {"field": "Age"},
            {"text": " had smartphones in 2015, compared to "},
            {"field": "SUM(Ownership 2019)"},
            {"text": " in 2019, a change of "},
            {"field": "Difference"},
        ],
    )

    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"background-color": "#ffffff"},
        "children": [
            {
                "type": "text",
                "text": "#WOW2022  W32 | Can you build a dumbbell chart?",
                "runs": [
                    {
                        "text": "#WOW2022  W32 | ",
                        "font_size": "18",
                        "bold": True,
                        "font_color": "#000000",
                        "font_alignment": "0",
                    },
                    {
                        "text": "Can you build a dumbbell chart?",
                        "font_size": "18",
                        "font_color": "#000000",
                        "font_alignment": "0",
                    },
                ],
                "absolute": {"x": 0, "y": 0, "w": 100000, "h": 8000},
            },
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 2000, "y": 8000, "w": 96000, "h": 84000},
            },
            {
                "type": "text",
                "text": "CHALLENGE BY: Kyle Yetter\nRECREATED BY: Donna Coles",
                "runs": [
                    {
                        "text": "CHALLENGE BY: Kyle Yetter\nRECREATED BY: Donna Coles",
                        "font_size": "9",
                        "font_color": "#666666",
                        "font_alignment": "0",
                    }
                ],
                "absolute": {"x": 2000, "y": 92500, "w": 96000, "h": 6000},
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
