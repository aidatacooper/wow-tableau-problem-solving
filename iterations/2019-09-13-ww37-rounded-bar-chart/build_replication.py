"""Build WW37's region-selected rounded-bar comparison from locked Hyper."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from cwtwb.twb_editor import TWBEditor  # noqa: E402
from lxml import etree  # noqa: E402

HYPER = next((HERE / "inputs").glob("*.hyper"))
OUTPUTS = HERE / "outputs"


def configure_rounded_measure_values(editor: TWBEditor) -> None:
    """Match Tableau's Bar + Circle overlay used for rounded bar ends."""
    editor.configure_chart(
        "Viz",
        mark_type="Text",
        rows=["Sub-Category"],
        label="LABEL: % Sales",
        measure_values=["Region % of Sales", "MIN(Rounded Bar Start)", "MIN(Full Bar)"],
    )
    worksheet = editor._find_worksheet("Viz")
    table = worksheet.find("table")
    panes = table.find("panes")
    panes.clear()
    ds_name = editor._datasource.get("name", "")
    multiple_values = f"[{ds_name}].[Multiple Values]"
    measure_names = f"[{ds_name}].[:Measure Names]"
    label_ci = editor.field_registry.parse_expression("LABEL: % Sales")
    label_ref = editor.field_registry.resolve_full_reference(label_ci.instance_name)

    def add_pane(pane_id: str, mark: str, *, axis: bool = False, circle: bool = False):
        pane = etree.SubElement(
            panes,
            "pane",
            id=pane_id,
            **{"selection-relaxation-option": "selection-relaxation-disallow"},
        )
        if axis:
            pane.set("x-axis-name", multiple_values)
        if circle:
            pane.set("x-index", "1")
        view = etree.SubElement(pane, "view")
        etree.SubElement(view, "breakdown", value="off")
        etree.SubElement(pane, "mark", {"class": mark})
        etree.SubElement(
            pane, "mark-sizing", {"mark-sizing-setting": "marks-scaling-off"}
        )
        enc = etree.SubElement(pane, "encodings")
        etree.SubElement(enc, "color", column=measure_names)
        if mark == "Bar":
            etree.SubElement(enc, "text", column=label_ref)
        style = etree.SubElement(pane, "style")
        if mark == "Bar":
            cell_rule = etree.SubElement(style, "style-rule", element="cell")
            etree.SubElement(cell_rule, "format", attr="text-align", value="right")
            etree.SubElement(cell_rule, "format", attr="vertical-align", value="center")
        rule = etree.SubElement(style, "style-rule", element="mark")
        etree.SubElement(rule, "format", attr="size", value="0.53773480653762817")
        etree.SubElement(
            rule,
            "format",
            attr="mark-labels-show",
            value="true" if mark == "Bar" else "false",
        )
        etree.SubElement(rule, "format", attr="mark-labels-cull", value="true")
        return pane

    add_pane("3", "Automatic")
    add_pane("4", "Bar", axis=True)
    add_pane("5", "Circle", axis=True, circle=True)
    table.find("cols").text = f"({multiple_values} + {multiple_values})"

    view = table.find("view")
    sort = etree.Element(
        "sort", column=measure_names, direction="ASC", **{"class": "manual"}
    )
    dictionary = etree.SubElement(sort, "dictionary")
    for expression in ("Region % of Sales", "MIN(Rounded Bar Start)", "MIN(Full Bar)"):
        ci = editor.field_registry.parse_expression(expression)
        etree.SubElement(
            dictionary, "bucket"
        ).text = f'"{editor.field_registry.resolve_full_reference(ci.instance_name)}"'
    slices = view.find("slices")
    if slices is not None:
        slices.addprevious(sort)
    else:
        aggregation = view.find("aggregation")
        if aggregation is None:
            view.append(sort)
        else:
            aggregation.addprevious(sort)

    table_style = table.find("style")
    if table_style is None:
        table_style = etree.SubElement(table, "style")
    axis_rule = etree.SubElement(table_style, "style-rule", element="axis")
    etree.SubElement(
        axis_rule,
        "encoding",
        attr="space",
        **{
            "class": "1",
            "field": multiple_values,
            "field-type": "quantitative",
            "fold": "true",
            "scope": "cols",
            "synchronized": "true",
            "type": "space",
        },
    )
    etree.SubElement(
        axis_rule,
        "encoding",
        attr="space",
        **{
            "class": "0",
            "field": multiple_values,
            "field-type": "quantitative",
            "min": "-0.01",
            "range-type": "fixedmin",
            "scope": "cols",
            "type": "space",
        },
    )
    for axis_class in ("0", "1"):
        etree.SubElement(
            axis_rule,
            "format",
            attr="display",
            **{
                "class": axis_class,
                "field": multiple_values,
                "scope": "cols",
                "value": "false",
            },
        )

    ds_style = editor._datasource.find("style")
    if ds_style is None:
        ds_style = etree.Element("style")
        anchor = editor._datasource.find("semantic-values")
        if anchor is None:
            anchor = editor._datasource.find("date-options")
        if anchor is None:
            editor._datasource.append(ds_style)
        else:
            anchor.addprevious(ds_style)
    rule = etree.SubElement(ds_style, "style-rule", element="mark")
    palette = etree.SubElement(
        rule, "encoding", attr="color", field="[:Measure Names]", type="palette"
    )
    for expression, color in (
        ("Region % of Sales", "#ed7370"),
        ("MIN(Rounded Bar Start)", "#ed7370"),
        ("MIN(Full Bar)", "#d3d3d3"),
    ):
        ci = editor.field_registry.parse_expression(expression)
        mapping = etree.SubElement(palette, "map", to=color)
        etree.SubElement(
            mapping, "bucket"
        ).text = f'"{editor.field_registry.resolve_full_reference(ci.instance_name)}"'


def build(path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    editor._datasource.set("caption", "Orders (Sample - Superstore)")
    editor.add_parameter(
        "Region Param",
        datatype="string",
        default_value="East",
        domain_type="list",
        allowed_values=["Central", "East", "South", "West"],
    )
    editor.add_calculated_field(
        "Region Sales",
        "IF [Region] = [Parameters].[Region Param] THEN [Sales] END",
        datatype="real",
    )
    editor.add_calculated_field(
        "Region % of Sales", "SUM([Region Sales]) / SUM([Sales])", datatype="real"
    )
    editor.add_calculated_field(
        "LABEL: % Sales",
        "STR(ROUND([Region % of Sales] * 100, 0)) + '%'",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field("Rounded Bar Start", "0", datatype="real")
    editor.add_calculated_field("Full Bar", "1", datatype="real")
    editor.add_calculated_field(
        "Dynamic Title",
        "'WEEK 37: WHAT PERCENT OF SALES IS FROM THE ' + UPPER([Parameters].[Region Param]) + ' REGION?'",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_worksheet("Title")
    editor.configure_chart("Title", mark_type="Text", label="Dynamic Title")
    editor.configure_worksheet_style(
        "Title",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        pane_datalabel_style={
            "font-size": "14",
            "font-family": "Tableau Medium",
            "font-weight": "bold",
            "text-align": "left",
            "vertical-align": "center",
        },
    )
    editor.add_worksheet("Viz")
    configure_rounded_measure_values(editor)
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=False,
        hide_row_field_labels=True,
        pane_datalabel_style={"font-size": "8"},
    )
    editor.add_worksheet("Data")
    editor.configure_chart(
        "Data",
        mark_type="Text",
        columns=["Sub-Category"],
        rows=["SUM(Sales)", "SUM(Region Sales)"],
    )
    editor.add_dashboard(
        "WW37 Rounded Bar Chart",
        width=600,
        height=800,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 80,
                    "children": [
                        {
                            "type": "worksheet",
                            "name": "Title",
                            "show_title": False,
                            "fit": "entire",
                            "weight": 1,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "Region Param",
                            "show_title": False,
                            "mode": "compact",
                            "fixed_size": 120,
                        },
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "fit": "entire",
                    "show_title": False,
                    "weight": 1,
                },
                {
                    "type": "text",
                    "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 37\nDESIGNED BY: LUKE STANKE                       RECREATED BY: DONNA COLES",
                    "font_size": "8",
                    "color": "#ed7370",
                    "fixed_size": 52,
                },
            ],
        },
        worksheet_names=["Title", "Viz"],
    )
    OUTPUTS.mkdir(exist_ok=True)
    editor.save(path, validate=False)
    return path


if __name__ == "__main__":
    for name in (
        "2019-09-13-ww37-rounded-bar-chart-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUTS / name))
