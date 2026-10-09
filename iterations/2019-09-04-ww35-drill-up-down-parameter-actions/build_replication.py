"""Build WW35 from the locked Superstore Hyper, without author-workbook access."""

from pathlib import Path
import sys
from lxml import etree


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


HYPER = HERE / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUTS = HERE / "outputs"


def build(path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    editor._datasource.set("caption", "Orders (Sample - Superstore)")

    editor.add_parameter(
        "Select Category",
        datatype="string",
        default_value="Office Supplies",
        domain_type="list",
        allowed_values=["Furniture", "Office Supplies", "Technology"],
    )
    editor.add_parameter(
        "Level Param",
        datatype="integer",
        default_value="2",
        domain_type="range",
        min_value="1",
        max_value="2",
        granularity="1",
    )
    editor.add_calculated_field(
        "Sales Per Year Per Category",
        "{ FIXED YEAR([Order Date]), [Category] : SUM([Sales]) }",
        datatype="real",
    )
    editor.add_calculated_field(
        "Sales Per Year Per Category Per Sub Cat",
        "{ FIXED YEAR([Order Date]), [Category], [Sub-Category] : SUM([Sales]) }",
        datatype="real",
    )
    editor.add_calculated_field(
        "Level",
        "IF [Category] = [Parameters].[Select Category] AND [Parameters].[Level Param] = 2 THEN 2 ELSE 1 END",
        datatype="integer",
    )
    editor.add_calculated_field(
        "Max Level", "IIF([Parameters].[Level Param] = 1, 2, 1)", datatype="integer"
    )
    editor.add_calculated_field(
        "Display",
        "IF [Category] = [Parameters].[Select Category] AND [Level] = 2 THEN "
        "'    ↳ ' + [Sub-Category] ELSE '' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Display Sales",
        "IF [Level] = 2 THEN [Sales Per Year Per Category Per Sub Cat] ELSE [Sales Per Year Per Category] END",
        datatype="real",
    )

    editor.add_worksheet("Viz")
    editor.configure_chart(
        "Viz",
        mark_type="Bar",
        columns=["YEAR(Order Date)", "MIN(Display Sales)"],
        rows=["Category", "Display"],
        label="MIN(Display Sales)",
        tooltip=["Category", "Sub-Category", "Max Level", "MIN(Display Sales)"],
    )
    editor.configure_subtotals(
        "Viz",
        measure_fields=["Display Sales"],
        aggregation="Sum",
        subtotal_fields=["Category"],
        label="",
    )
    view = editor._find_worksheet("Viz").find("table/view")
    category = f"[{editor._datasource.get('name')}].[none:Category:nk]"
    # A manual sort is <manual-sort>, not <sort class="manual">; the latter is
    # not in the XSD sequence and Desktop refuses to open the workbook.
    category_sort = etree.Element(
        "manual-sort", column=category, direction="ASC"
    )
    # Tableau requires this manifest flag for <manual-sort>.
    manifest = editor.root.find("document-format-change-manifest")
    if manifest is not None and manifest.find("SortTagCleanup") is None:
        etree.SubElement(manifest, "SortTagCleanup")
    dictionary = etree.SubElement(category_sort, "dictionary")
    for value in ("Technology", "Office Supplies", "Furniture"):
        etree.SubElement(dictionary, "bucket").text = f'"{value}"'
    anchor = view.find("shelf-sorts")
    if anchor is None:
        anchor = view.find("aggregation")
    if anchor is None:
        view.append(category_sort)
    else:
        anchor.addprevious(category_sort)
    editor.set_worksheet_caption(
        "Viz", "Select a category and increase Level Param to drill to sub-categories"
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        pane_datalabel_style={"font-size": "9", "font-family": "Tableau Book"},
        pane_mark_style={"mark-color": "#eca88f"},
    )
    editor.add_dashboard(
        "WW35 Drill Up and Down",
        width=800,
        height=650,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "Drill Down & Up on Sales with Subtotals using Parameter Actions\nSales by Category, and Sub-Category\nClick the arrow beside a Category to expand or collapse it",
                    "font_size": "11",
                    "fixed_size": 105,
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
                    "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 35",
                    "font_size": "8",
                    "bold": True,
                    "fixed_size": 32,
                },
            ],
        },
        worksheet_names=["Viz"],
    )
    editor.add_dashboard_action(
        "WW35 Drill Up and Down",
        "parameter",
        "Viz",
        source_field="Category",
        target_parameter="Select Category",
        aggregation="attr",
        caption="Select Category",
    )
    editor.add_dashboard_action(
        "WW35 Drill Up and Down",
        "parameter",
        "Viz",
        source_field="Max Level",
        target_parameter="Level Param",
        aggregation="attr",
        caption="Drill Up or Down",
    )
    OUTPUTS.mkdir(exist_ok=True)
    editor.save(path, validate=False)
    return path


if __name__ == "__main__":
    for name in (
        "2019-09-04-ww35-drill-up-down-parameter-actions-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUTS / name))
