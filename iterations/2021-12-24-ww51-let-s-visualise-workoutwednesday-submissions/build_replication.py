"""Rebuild the 2021 Week 51 submission tracker from extracted data only.

The builder never opens the author TWB/TWBX. It reads ``inputs/`` (the extracted
Hyper extract) and this case's ``analysis.md``/``case.yaml``, and authors a new
workbook through public ``cwtwb`` APIs.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import tempfile
from pathlib import Path

import cwtwb
from cwtwb import TWBEditor, convert_workbook


HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"
HYPER = INPUTS / "federated_1j5rapc06zda391elx3h21.hyper"

USER_NS = "{http://www.tableausoftware.com/xml/user}"

SOURCE = "2021-12-22-WW51-WOW_Challenge_Tracker"
DASHBOARD = "2021_12_22_WOW_Submission_Tracker"
HEATMAP = "Heatmap"
TYPE_BAR = "Submission Type Bar"
CHALLENGE_BAR = "Challenges Bar"

SAME_WEEK = "Same Week Submission"
OTHER_WEEK = "Other Submission"
SAME_WEEK_COLOR = "#007ea7"
OTHER_WEEK_COLOR = "#a4b9dc"

HEADER_BLUE = "#258bae"

# The article applies the Software filter to every worksheet that uses this data
# source, so the heatmap and both bars are restricted to Tableau submissions.
SOFTWARE_FILTER = [{"column": "Software", "values": ["Tableau"]}]

ACTION_CAPTION = "Submission breakdown for the selected day"
# (year, week, weekday) identifies exactly one calendar day, so filtering the
# bars on these three fields reproduces the author's day-level drill path.
ACTION_LEVEL_LABELS = ["Week Submitted", "Weekday Submitted", "YEAR(Timestamp)"]
BARS = (TYPE_BAR, CHALLENGE_BAR)


def add_fields(editor: TWBEditor) -> None:
    """Declare the five calculated fields the dashboard needs."""
    editor.add_calculated_field(
        "Week Submitted",
        "DATEPART('week',[Timestamp])",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
        default_format="*00",
    )
    editor.add_calculated_field(
        "Weekday Submitted",
        "LEFT(DATENAME('weekday',[Timestamp]),3)",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Submissions",
        "COUNT([Timestamp])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Percentile of Submissions",
        "RANK_PERCENTILE(COUNT([Timestamp]))",
        datatype="real",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
        default_format="p0.0%",
    )
    editor.add_calculated_field(
        "Challenge Submitted",
        "STR([Challenge Year])+'w'+STR([Challenge Week])",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    # The author uses a boolean field with member aliases. The released SDK has
    # no public alias API for calculated fields, so this equivalent string
    # calculation emits the same two labels and keeps the same ordering.
    editor.add_calculated_field(
        SAME_WEEK,
        f'IF ([Challenge Week]=[Week Submitted]) AND '
        f'([Challenge Year]=YEAR([Timestamp])) THEN "{SAME_WEEK}" '
        f'ELSE "{OTHER_WEEK}" END',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )


def add_heatmap(editor: TWBEditor) -> None:
    """Year x weekday x week square heatmap coloured by the rank percentile."""
    editor.add_worksheet(HEATMAP)
    editor.configure_layered_chart(
        HEATMAP,
        columns=["Week Submitted"],
        rows=["YEAR(Timestamp)", "Weekday Submitted"],
        panes=[
            {
                "mark_type": "Square",
                "color": "Percentile of Submissions",
                "label": "Submissions",
                "detail": "DAYTRUNC(Timestamp)",
                "tooltip": "Submissions",
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "mark-labels-mode": "selection",
                },
            }
        ],
        filters=SOFTWARE_FILTER,
        table_calc_context=True,
        table_calc_overrides={
            "Percentile of Submissions": [
                {
                    "ordering_type": "Field",
                    "order": [
                        "Week Submitted",
                        "DAYTRUNC(Timestamp)",
                        "YEAR(Timestamp)",
                        "Weekday Submitted",
                    ],
                }
            ]
        },
    )
    editor.configure_worksheet_style(
        HEATMAP,
        hide_row_field_labels=True,
        hide_zeroline=True,
        table_dividers=[
            {"scope": "cols", "div-level": "1", "stroke-color": "#e6e6e6", "stroke-size": "1"},
            {"scope": "rows", "div-level": "2", "stroke-color": "#e6e6e6", "stroke-size": "1"},
        ],
        label_formats=[
            {"field": "Week Submitted", "text-format": "*00"},
            {"field": "YEAR(Timestamp)", "text-orientation": "-90"},
        ],
        cell_formats=[
            {"field": "Percentile of Submissions", "text-format": "p0.0%"},
        ],
        header_formats=[{"field": "Weekday Submitted", "width": "44"}],
        color_style={
            "field": "Percentile of Submissions",
            # Tableau 2021.4 rendered the named palette CB_PuBuGn as these four
            # steps; later Desktop versions resolve that name to a different
            # ramp, so the published colours are declared explicitly.
            "colors": ["#fff7fb", "#b4c4df", "#258bae", "#014636"],
            "min": 0,
            "max": 1,
            "num_steps": 4,
        },
    )
    editor.configure_custom_tooltip(
        HEATMAP,
        [
            {"text": "There were "},
            {"field": "Submissions", "bold": True},
            {"text": " submission on "},
            {"field": "DAYTRUNC(Timestamp)", "bold": True},
            {"text": ". Click for more details"},
        ],
    )
    editor.set_worksheet_selection_relaxation(HEATMAP, enabled=False)


def add_bars(editor: TWBEditor) -> None:
    """The two submission-breakdown bar charts."""
    editor.add_worksheet(TYPE_BAR)
    editor.configure_layered_chart(
        TYPE_BAR,
        columns=[SAME_WEEK],
        rows=["Submissions"],
        panes=[
            {
                "mark_type": "Bar",
                "color": SAME_WEEK,
                "color_map": {SAME_WEEK: SAME_WEEK_COLOR, OTHER_WEEK: OTHER_WEEK_COLOR},
            }
        ],
        filters=SOFTWARE_FILTER,
    )
    editor.configure_worksheet_style(
        TYPE_BAR,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        axis_style={"stroke-size": "0", "line-visibility": "off"},
    )

    editor.add_worksheet(CHALLENGE_BAR)
    editor.configure_layered_chart(
        CHALLENGE_BAR,
        columns=["Submissions"],
        rows=["Challenge Submitted"],
        panes=[
            {
                "mark_type": "Bar",
                "color": SAME_WEEK,
                "color_map": {SAME_WEEK: SAME_WEEK_COLOR, OTHER_WEEK: OTHER_WEEK_COLOR},
            }
        ],
        filters=SOFTWARE_FILTER,
        sort_descending="Submissions",
    )
    editor.configure_worksheet_style(
        CHALLENGE_BAR,
        hide_gridlines=True,
        hide_zeroline=True,
        label_formats=[{"field": "Challenge Submitted", "text-align": "left"}],
        header_formats=[{"field": "Challenge Submitted", "width": "144"}],
    )


def add_dashboard(editor: TWBEditor) -> None:
    """Fixed 1100x890 dashboard: heatmap on top, two bars underneath."""
    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "fixed_size": 40,
                "text": "Let's visualize #WorkoutWednesday submissions",
                "bold": True,
                "font_size": 20,
                "font_alignment": 0,
            },
            {
                "type": "text",
                "fixed_size": 26,
                "text": "The table below shows the number of tracker submissions "
                "by day over the past 4 years",
                "font_size": 11,
                "font_alignment": 0,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 44,
                "children": [
                    {
                        "type": "text",
                        "weight": 3,
                        "text": "click on a cell to see a submission breakdown",
                        "font_size": 11,
                        "font_alignment": 0,
                    },
                    {
                        "type": "filter",
                        "worksheet": HEATMAP,
                        "field": "Software",
                        "mode": "checkdropdown",
                        "fixed_size": 210,
                        "values": "database",
                    },
                    {
                        "type": "color",
                        "worksheet": HEATMAP,
                        "field": "Percentile of Submissions",
                        "fixed_size": 300,
                    },
                ],
            },
            {"type": "worksheet", "name": HEATMAP, "weight": 4, "fit": "entire", "show_title": False},
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 150,
                "children": [
                    {"type": "worksheet", "name": TYPE_BAR, "weight": 1},
                    {"type": "worksheet", "name": CHALLENGE_BAR, "weight": 2},
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 26,
                "children": [
                    {
                        "type": "text",
                        "weight": 1,
                        "text": "CHALLENGE BY : SEAN MILLER",
                        "font_size": 8,
                        "font_color": HEADER_BLUE,
                        "font_alignment": 0,
                    },
                    {
                        "type": "text",
                        "weight": 1,
                        "text": "#WOW2021  |  WEEK 51",
                        "font_size": 8,
                        "font_color": HEADER_BLUE,
                        "font_alignment": 1,
                    },
                    {
                        "type": "text",
                        "weight": 1,
                        "text": "RECREATED BY : DONNA COLES",
                        "font_size": 8,
                        "font_color": HEADER_BLUE,
                        "font_alignment": 2,
                    },
                ],
            },
            {
                "type": "text",
                "fixed_size": 22,
                "text": "http://www.workout-wednesday.com/2021w51tab/",
                "font_size": 8,
                "font_alignment": 1,
            },
        ],
    }
    editor.add_dashboard(DASHBOARD, 1100, 890, layout=layout)
    editor.add_dashboard_action(
        DASHBOARD,
        "filter",
        source_sheet=HEATMAP,
        target_sheets=[TYPE_BAR, CHALLENGE_BAR],
        caption=ACTION_CAPTION,
        clear_behavior="show-none",
    )
    editor.set_active_dashboard(DASHBOARD)


def _node(tag, attributes=None, children=None, text=None):
    node = {"tag": tag, "attributes": attributes or {}, "children": children or []}
    if text is not None:
        node["text"] = text
    return node


def _find_all(node, tag):
    if isinstance(node, dict):
        if node.get("tag") == tag:
            yield node
        for child in node.get("children", []):
            yield from _find_all(child, tag)
    elif isinstance(node, list):
        for child in node:
            yield from _find_all(child, tag)


def _level_nodes(view, levels):
    """Collect the column/column-instance declarations a filter level needs."""
    deps = next(_find_all(view, "datasource-dependencies"))
    collected, seen = [], set()
    for level in levels:
        instance = next(
            (
                node
                for node in deps["children"]
                if node.get("tag") == "column-instance"
                and node["attributes"].get("name") == level
            ),
            None,
        )
        base = instance["attributes"]["column"] if instance else level
        column = next(
            (
                node
                for node in deps["children"]
                if node.get("tag") == "column"
                and node["attributes"].get("name") == base
            ),
            None,
        )
        for node in (column, instance):
            if node is None:
                continue
            key = (node["tag"], node["attributes"].get("name"))
            if key in seen:
                continue
            seen.add(key)
            collected.append(copy.deepcopy(node))
    return collected


def materialize_empty_action_filter(staging: Path, output: Path, levels: list[str]) -> None:
    """Write the action filter's initial (nothing selected) state into the bars.

    ``add_dashboard_action`` creates the action and its clearing behaviour, but
    the released SDK cannot author the action-filter element Tableau stores on
    every target worksheet. Without it the bars render every submission until
    the first click, while the reference dashboard starts with empty bars.
    This structural pass edits our own generated document through the public
    native-JSON conversion API; it never reads the author workbook.
    """
    with tempfile.TemporaryDirectory(prefix="ww51-action-") as directory:
        native = Path(directory) / "native.json"
        convert_workbook(staging, native)
        payload = json.loads(native.read_text(encoding="utf-8"))
        root = payload["document"]["root"]
        datasource = next(_find_all(root, "datasource"))
        ds_name = datasource["attributes"]["name"]
        action = next(
            node
            for node in _find_all(root, "action")
            if node["attributes"].get("caption") == ACTION_CAPTION
        )
        action_name = action["attributes"]["name"]

        caption = "Action (" + ",".join(ACTION_LEVEL_LABELS) + ")"
        local = f"[{caption}]"
        full = f"[{ds_name}].{local}"

        group = _node(
            "group",
            {
                "caption": caption,
                "hidden": "true",
                "name": local,
                "name-style": "unqualified",
                USER_NS + "auto-column": "sheet_link",
            },
            [
                _node(
                    "groupfilter",
                    {"function": "crossjoin"},
                    [
                        _node("groupfilter", {"function": "level-members", "level": level})
                        for level in levels
                    ],
                )
            ],
        )
        anchor = next(
            index
            for index, node in enumerate(datasource["children"])
            if node.get("tag")
            in {"extract", "layout", "style", "semantic-values", "date-options", "object-graph"}
        )
        datasource["children"].insert(anchor, group)

        for sheet in BARS:
            worksheet = next(
                node
                for node in _find_all(root, "worksheet")
                if node["attributes"].get("name") == sheet
            )
            view = worksheet["children"][0]["children"][0]
            deps_index = next(
                index
                for index, node in enumerate(view["children"])
                if node.get("tag") == "datasource-dependencies"
            )
            deps = view["children"][deps_index]
            existing = {node["attributes"].get("name") for node in deps["children"]}
            for node in _level_nodes(view, levels):
                if node["attributes"].get("name") not in existing:
                    deps["children"].append(node)
                    existing.add(node["attributes"].get("name"))
            selection = _node(
                "filter",
                {"class": "categorical", "column": full},
                [
                    _node(
                        "groupfilter",
                        {
                            "function": "crossjoin",
                            USER_NS + "ui-action-filter": action_name,
                            USER_NS + "ui-domain": "database",
                            USER_NS + "ui-enumeration": "inclusive",
                            USER_NS + "ui-marker": "enumerate",
                        },
                        [
                            _node("groupfilter", {"function": "empty-level", "member": level})
                            for level in levels
                        ],
                    )
                ],
            )
            view["children"].insert(deps_index + 1, selection)
            slices = next((node for node in view["children"] if node.get("tag") == "slices"), None)
            if slices is None:
                slices = _node("slices", children=[])
                view["children"].append(slices)
            if not any(node.get("text") == full for node in slices["children"]):
                slices["children"].append(_node("column", text=full))

        native.write_text(json.dumps(payload), encoding="utf-8")
        convert_workbook(native, output, force=True)


def action_filter_levels(editor: TWBEditor) -> list[str]:
    """Resolve the action's filter levels from the field registry."""
    levels = []
    for label in ACTION_LEVEL_LABELS:
        instance = editor.field_registry.parse_expression(label)
        levels.append(
            instance.instance_name
            if instance.derivation != "None"
            else instance.column_local_name
        )
    return levels


def build() -> Path:
    if not HYPER.is_file():
        raise FileNotFoundError(HYPER)
    OUTPUTS.mkdir(exist_ok=True)

    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HYPER),
        table_name="Extract",
        field_overrides={
            "Challenge Week": {"role": "dimension", "field_type": "quantitative"},
            "Challenge Year": {"role": "dimension", "field_type": "quantitative"},
        },
    )
    editor.set_date_options(start_of_week="sunday")

    add_fields(editor)
    add_heatmap(editor)
    add_bars(editor)
    # Workbook-level shared filter: Tableau's "apply to all worksheets using this
    # data source". The per-worksheet filters above also write the <slices>
    # entries that Tableau expects on every participating view.
    editor.add_shared_filter("Software", values=["Tableau"])
    add_dashboard(editor)
    levels = action_filter_levels(editor)

    output = OUTPUTS / "replicated-workbook.twbx"
    with tempfile.TemporaryDirectory(prefix="ww51-build-") as directory:
        staging = Path(directory) / "replicated-workbook.twbx"
        editor.save(staging)
        materialize_empty_action_filter(staging, output, levels)

    provenance = {
        "sdk_version": importlib.metadata.version("cwtwb"),
        "sdk_module": str(Path(cwtwb.__file__).resolve()),
        "authoring_route": "blank TWBEditor plus public chart, style and dashboard APIs",
        "structural_steps": [
            "materialize the dashboard action's empty initial filter state through "
            "convert_workbook native JSON (no public SDK entry point exists)"
        ],
        "workbook_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (OUTPUTS / "build-provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    print(build())
