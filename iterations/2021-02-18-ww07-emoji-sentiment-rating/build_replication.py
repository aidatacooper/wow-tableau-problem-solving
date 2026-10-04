"""Build an independently modeled emoji dashboard with its real sandbox extension."""

from pathlib import Path
import base64, json
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_02_17_WW07_Emoji_Sentiment_Rating"
SENTIMENT = (
    "2021_02_17_WW07_Emoji_Sentiment_Data_v1.0.csv_664A5C3CE90840128BDF439A1E215B3D"
)
DATABASE = "2021_02_17_WW07_emoji_df.csv_4B39AD59017B4FAE94DB173FF3B40B11"
CATEGORIES = [
    "Smileys & People",
    "Animals & Nature",
    "Food & Drink",
    "Activities",
    "Travel & Places",
    "Objects",
    "Symbols",
    "Flags",
]
GROUP_COLORS = dict(
    zip(
        CATEGORIES,
        [
            "#ffe914",
            "#804b24",
            "#ffa64c",
            "#3f3f3e",
            "#a2483d",
            "#d3d3d3",
            "#5a82a8",
            "#e00036",
        ],
    )
)
PERCENTAGES = ["[% Positive]", "[% Neutral]", "[% Negative]"]


def zone(kind, x, y, w, h, **kwargs):
    return {"type": kind, "absolute": {"x": x, "y": y, "w": w, "h": h}, **kwargs}


def chart(e, name, average=False):
    e.add_worksheet(name)
    position = "AVG(Position)" if average else "SUM(Position)"
    rows = ["Average Label"] if average else ["Emoji", "Unicode name", "[#]"]
    filters = (
        [{"column": "Group (group)", "values": [None], "exclude": True}]
        if average
        else [
            {"column": "Group (group)", "context": True},
            {"column": "Emoji", "top": 20, "by": "SUM(Occurrences)"},
        ]
    )
    tooltip = PERCENTAGES + [
        position,
        "AVG(Occurrences)" if average else "SUM(Occurrences)",
    ]
    e.configure_layered_chart(
        name,
        axis_shelf="columns",
        columns=["Multiple Values", position, "[One]"],
        rows=rows,
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Bar",
                "measure_values": PERCENTAGES,
                "color": "Measure Names",
                "color_map": {
                    "[% Positive]": "#a9d2d8",
                    "[% Neutral]": "#f9d3a0",
                    "[% Negative]": "#cc99af",
                },
                "tooltip": tooltip,
                "mark_style": {"mark-labels-show": "false"},
            },
            {
                "axis": position,
                "mark_type": "Circle",
                "tooltip": tooltip,
                "mark_style": {
                    "size": "0.86756908893585205",
                    "mark-labels-show": "false",
                    "mark-color": "#999999",
                },
            },
            {
                "axis": "[One]",
                "mark_type": "Bar",
                "tooltip": tooltip,
                "mark_style": {
                    "size": "0.0099999997764825821",
                    "mark-labels-show": "false",
                    "mark-color": "#999999",
                },
            },
        ],
        fold_axes=False,
        synchronized=False,
        hide_axes=True,
        filters=filters,
        sort_descending=None if average else "SUM(Occurrences)",
        sort_field=None if average else "Emoji",
    )
    e.configure_worksheet_style(
        name,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=average,
        hide_band_color=True,
        header_formats=[{"field": "Unicode name", "font-size": 8, "width": 315}]
        if not average
        else None,
        axis_style={
            "encodings": [
                {
                    "field": position,
                    "scope": "cols",
                    "range-type": "fixed",
                    "min": "0.0",
                    "max": "1.0",
                },
                {"field": "[One]", "scope": "cols", "fold": True, "synchronized": True},
            ],
            "per_field": [
                {"field": "[One]", "attr": "display", "scope": "cols", "value": "false"}
            ],
        },
        cell_formats=[{"attr": "height", "value": 19}],
    )


def build():
    e = TWBEditor("")
    e.set_hyper_connection(
        str(HERE / "inputs/TEMP_1kvi1ok1gjuwra123at7r0vm5038.hyper"),
        tables=[
            {"name": "Sentiment", "table": SENTIMENT},
            {"name": "Emoji Database", "table": DATABASE},
        ],
        relationships=[
            {
                "left": "Sentiment",
                "right": "Emoji Database",
                "keys": [["Emoji", "emoji"]],
            }
        ],
    )
    e.add_group(
        "Group (group)",
        "group",
        {"Smileys & People": ["People & Body", "Smileys & Emotion"]},
        default_value=None,
        internal_name="[Group (group)]",
    )
    for name, formula in (
        ("% Positive", "SUM([Positive])/SUM([Occurrences])"),
        ("% Neutral", "SUM([Neutral])/SUM([Occurrences])"),
        ("% Negative", "SUM([Negative])/SUM([Occurrences])"),
    ):
        e.add_calculated_field(name, formula, datatype="real", default_format="p0.0%")
    e.add_calculated_field(
        "#",
        "SUM([Occurrences])",
        datatype="integer",
        role="measure",
        field_type="ordinal",
    )
    e.add_calculated_field("One", "MIN(1)", datatype="real")
    e.add_calculated_field("Zero", "MIN(0)", datatype="real")
    e.set_field_format("Position", "n0.00;-0.00")
    e.add_calculated_field(
        "Average Label",
        '"On Average"',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Category Sort",
        "CASE [Group (group)] "
        + " ".join(f"WHEN '{c}' THEN {-i}" for i, c in enumerate(CATEGORIES))
        + " END",
        datatype="integer",
    )
    e.set_datasource_color_palette("Group (group)", GROUP_COLORS)
    e.set_datasource_color_palette(
        "Measure Names",
        {"% Positive": "#a9d2d8", "% Neutral": "#f9d3a0", "% Negative": "#cc99af"},
        is_measure_names=True,
    )
    chart(e, "Top 20")
    chart(e, "Avg", True)
    e.add_worksheet("by Group")
    e.configure_layered_chart(
        "by Group",
        rows=["Group (group)"],
        columns=["Multiple Values"],
        axis_shelf="columns",
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Line",
                "measure_values": ["[Zero]", "SUM(Occurrences)"],
                "path": "Measure Names",
                "color": "Group (group)",
                "label": "SUM(Occurrences)",
                "tooltip": ["SUM(Occurrences)"],
                "mark_style": {
                    "size": "8.308629035949707",
                    "mark-labels-show": "true",
                    "mark-labels-mode": "line-ends",
                    "mark-labels-line-first": "false",
                    "mark-labels-cull": "false",
                },
            }
        ],
        filters=[{"column": "Group (group)", "values": [None], "exclude": True}],
        sort_descending="MIN(Category Sort)",
        sort_field="Group (group)",
        hide_axes=True,
    )
    e.configure_worksheet_style(
        "by Group",
        hide_band_color=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_row_label="Group (group)",
        pane_datalabel_style={"font-size": 8, "color": "#666666", "color-mode": "user"},
        axis_style={
            "per_field": [
                {
                    "field": "Multiple Values",
                    "attr": "height",
                    "value": 19,
                    "scope": "cols",
                }
            ]
        },
    )
    e.add_calculated_field(
        "Info Label",
        '"\u24d8"',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_worksheet("Info")
    e.configure_chart("Info", mark_type="Text", label="Info Label")
    e.configure_worksheet_style("Info", pane_datalabel_style={"font-size": 22})
    e.configure_custom_tooltip(
        "Info",
        [
            {
                "text": "Select an image category to show its twenty most frequently used emojis and compare their sentiment and position."
            }
        ],
    )
    children = [
        zone(
            "worksheet",
            37667,
            17833,
            61666,
            70167,
            name="Top 20",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            22915,
            17833,
            14752,
            70167,
            name="by Group",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            62168,
            12166,
            37165,
            5667,
            name="Avg",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            95000,
            1500,
            3917,
            6333,
            name="Info",
            show_title=False,
            fit="entire",
        ),
        zone(
            "text",
            667,
            1333,
            49334,
            16500,
            runs=[
                {
                    "text": "Can you use dashboard extensions?\nEMOJI Sentiment Rating 2015",
                    "font_size": 16,
                    "font_alignment": "0",
                    "font_color": "#888888",
                }
            ],
        ),
    ]
    for x, text in (
        (667, "CHALLENGE BY : LORNA BROWN"),
        (33554, "#WOW2021  |  WEEK 7"),
        (66444, "RECREATED WITH CWTWB"),
    ):
        children.append(
            zone("text", x, 88000, 32889, 5333, runs=[{"text": text, "font_size": 8}])
        )
    children.append(
        zone(
            "text",
            667,
            93333,
            98666,
            5334,
            runs=[
                {"text": "http://www.workout-wednesday.com/2021w07tab/", "font_size": 8}
            ],
        )
    )
    e.add_dashboard(
        DASHBOARD,
        width=1200,
        height=600,
        layout={"type": "container", "direction": "floating", "children": children},
    )
    manifest = json.loads((HERE / "inputs/extension-manifest.json").read_text())
    manifest["icon"] = base64.b64encode(
        (HERE / "inputs/extension-icon.png").read_bytes()
    ).decode("ascii")
    settings = json.loads((HERE / "inputs/extension-settings.json").read_text())
    settings["image"] = {
        "name": "Emoji-Font-209x300.",
        "ext": "png",
        "data": base64.b64encode(
            (HERE / "inputs/extension-category-image.png").read_bytes()
        ).decode("ascii"),
    }
    e.add_dashboard_extension(
        DASHBOARD, manifest, settings, x=667, y=17833, width=22248, height=70167
    )
    for name in ("Top 20", "Avg", "by Group", "Info"):
        e.set_worksheet_title(name, "")
        e.set_window_state(name, hidden=False, zoom_entire_view=True)
    out = HERE / "outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
