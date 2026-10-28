"""Build WW41 from the locked raw Hyper through public cwtwb APIs only."""
from pathlib import Path
import colorsys
from cwtwb import TWBEditor
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    data = next((HERE / "inputs").glob("*.hyper"))
    # This is data preparation, not an expected-results/oracle input.
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, str(data)) as connection:
            categories = connection.execute_list_query(
                'SELECT "Sub-Category", SUM("Sales") FROM "Extract"."Extract" '
                'GROUP BY "Sub-Category" ORDER BY SUM("Sales") DESC, "Sub-Category"'
            )
    ordered = {name: f"{index:02d} {name}" for index, (name, _) in enumerate(categories, 1)}
    palette = {}
    for index, (name, _) in enumerate(categories):
        rgb = colorsys.hsv_to_rgb(index / len(categories), .68, .82)
        palette[name] = "#" + "".join(f"{round(value * 255):02x}" for value in rgb)

    editor = TWBEditor("")
    editor.set_hyper_connection(str(data), table_name="Extract")
    editor.add_parameter("pTopN", datatype="integer", default_value="5",
                         domain_type="range", min_value="1", max_value="17", granularity="1")
    editor.add_set("Top Sub-Categories", dimension_field="Sub-Category",
                   basis_field="Sales", aggregation="Sum", top_n="pTopN", direction="DESC")
    editor.add_calculated_field("Total Sales", "{FIXED : SUM([Sales])}")
    editor.add_calculated_field("Group Order", "IF [Top Sub-Categories] THEN 0 ELSE 1 END",
                                datatype="integer", role="dimension", field_type="ordinal")
    editor.add_calculated_field("Sales Group", "IF [Top Sub-Categories] THEN 'IN TOP ' + STR([pTopN]) ELSE 'ALL ELSE' END",
                                datatype="string", role="dimension")
    editor.add_calculated_field("Top Share", "IF MIN([Group Order]) = 0 THEN SUM([Sales]) / MIN([Total Sales]) END", default_format="p0%")
    editor.add_calculated_field("Top Label", "IF [Top Sub-Categories] THEN 'TOP ' + STR([pTopN]) END", datatype="string", role="dimension")
    editor.add_calculated_field("Pie Label", "IF MIN([Group Order]) = 0 THEN STR(INT(ROUND([Top Share] * 100, 0))) + '%' + CHAR(10) + 'TOP ' + STR([pTopN]) END", datatype="string", role="measure", field_type="nominal")
    editor.add_calculated_field("Contribution Caption", "'TOP ' + STR([pTopN]) + '  ·  ' + STR(INT(ROUND(SUM(IF [Top Sub-Categories] THEN [Sales] ELSE 0 END) / MIN([Total Sales]) * 100, 0))) + '% OF SALES'", datatype="string", role="measure", field_type="nominal")
    # a1 dual-axis sort cannot target a color dimension. A data-derived lexical
    # key keeps slices in sales order without modifying generated XML.
    clauses = ["WHEN '" + name.replace("'", "''") + "' THEN '" + key.replace("'", "''") + "'" for name, key in ordered.items()]
    editor.add_calculated_field("Ordered Sub-Category", "CASE [Sub-Category] " + " ".join(clauses) + " END", datatype="string", role="dimension")
    editor.add_calculated_field("Outer Axis", "MIN(0)")
    editor.add_calculated_field("Inner Axis", "MIN(0)")
    editor.add_calculated_field("Bar Width", "MIN(1)")
    editor.add_calculated_field("Sales Rank", "RANK(SUM([Sales]), 'desc')", datatype="integer", table_calc="Rows", default_format='n"#"0')
    editor.add_calculated_field("Category Count", "{FIXED : COUNTD([Sub-Category])}", datatype="integer")
    # Tableau recalculates table calculations in its separate subtotal partition.
    # That partition has one/two group marks; the detail partition has all 17
    # categories. Suppress only the subtotal rank, including singleton groups.
    editor.add_calculated_field("Rank Prefix", "IF SIZE() = MIN([Category Count]) THEN '#' + STR(INT([Sales Rank])) + ' · ' ELSE '' END", datatype="string", role="measure", field_type="nominal", table_calc="Rows")
    editor.set_field_format("Sales", 'c"$"#,##0')
    editor.set_datasource_color_palette("Sub-Category", palette)
    editor.set_datasource_color_palette("Ordered Sub-Category", {ordered[name]: color for name, color in palette.items()})
    editor.set_datasource_color_palette("Group Order", {"0": "#353535", "1": "#dedede"})

    editor.add_worksheet("Contribution Pie")
    editor.configure_dual_axis("Contribution Pie", rows=["Outer Axis", "Inner Axis"],
        mark_type_1="Pie", mark_type_2="Pie", color_1="Ordered Sub-Category",
        color_2="Group Order", detail_1="Sales Group", detail_2="Sales Group",
        wedge_size_1="SUM(Sales)", wedge_size_2="SUM(Sales)",
        label_2="Pie Label", size_value_1="6.8", size_value_2="5.6",
        synchronized=True, hide_axes=True, hide_zeroline=True)
    editor.configure_custom_label("Contribution Pie", [{"text": ""}], pane_index=1)
    editor.configure_custom_label("Contribution Pie", [{"text": ""}], pane_index=2)
    editor.configure_worksheet_style("Contribution Pie", panes_style={str(i): {"mark_style": {"mark-labels-show": "false"}} for i in [1, 2]})
    editor.configure_custom_tooltip("Contribution Pie", [
        {"field": "ATTR(Sub-Category)", "bold": True}, {"text": "\nSales: "},
        {"field": "SUM(Sales)"}, {"text": "\n"}, {"field": "Sales Group"}], pane_index=1)
    editor.configure_custom_tooltip("Contribution Pie", [{"field": "Sales Group"},
        {"text": "\nSales: "}, {"field": "SUM(Sales)"}], pane_index=2)

    editor.add_worksheet("Highlight Table")
    editor.configure_chart("Highlight Table", mark_type="Bar",
        rows=["Group Order", "Sales Group", "Sub-Category"], columns=["Bar Width"],
        color="Sub-Category", label="SUM(Sales)", label_extra=["Rank Prefix"], sort_descending="SUM(Sales)",
        sort_field="Sub-Category", tooltip=["Sales Group", "Sales Rank"],
        table_calc_overrides={
            "Sales Rank": [{"ordering_type": "Field", "order": ["Group Order", "Sales Group", "Sub-Category"]}],
            "Rank Prefix": [
                {"ordering_type": "Field", "order": ["Group Order", "Sales Group", "Sub-Category"]},
                {"field": "Sales Rank", "ordering_type": "Field", "order": ["Group Order", "Sales Group", "Sub-Category"]}]})
    editor.configure_custom_label("Highlight Table", [{"field": "Rank Prefix"}, {"field": "SUM(Sales)"}])
    editor.configure_subtotals("Highlight Table", measure_fields=["Sales"],
        aggregation="Sum", subtotal_fields=["Sales Group"], label="SUBTOTAL FOR GROUP")
    editor.configure_custom_tooltip("Highlight Table", [
        {"field": "ATTR(Sub-Category)", "bold": True}, {"text": "\nSales: "},
        {"field": "SUM(Sales)"}, {"text": "\n"}, {"field": "Sales Group"}])
    for sheet in ["Contribution Pie", "Highlight Table"]:
        editor.configure_worksheet_style(sheet, hide_axes=True, hide_gridlines=True,
            hide_zeroline=True, hide_borders=True, hide_band_color=True,
            hide_row_field_labels=True, hide_col_field_labels=True)
    editor.configure_worksheet_style("Contribution Pie", panes_style={
        "2": {"datalabel_style": {"color": "#ffffff", "font-size": "22", "font-weight": "bold",
                "text-align": "center", "vertical-align": "center"},
              "mark_style": {"mark-labels-cull": "false"}}})
    editor.configure_worksheet_style("Highlight Table", hide_row_label="Group Order",
        pane_mark_style={"size": "1", "mark-labels-cull": "false"}, pane_datalabel_style={"font-size": "11"})
    # A single, unfiltered summary mark is readable at every N. Tableau positions
    # native pie labels outside the slice; a separate heading avoids clipping
    # and leaves every pie mark available for the existing hover interaction.
    editor.add_worksheet("Contribution Summary")
    editor.configure_chart("Contribution Summary", mark_type="Text", label="Contribution Caption")
    editor.configure_worksheet_style("Contribution Summary", hide_axes=True,
        hide_gridlines=True, hide_borders=True, hide_band_color=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"font-size": "22", "font-weight": "bold", "color": "#353535"})
    def zone(kind, x, y, w, h, **kwargs):
        return {"type": kind, "absolute": {"x": round(x / 1400 * 100000), "y": round(y / 900 * 100000),
                "w": round(w / 1400 * 100000), "h": round(h / 900 * 100000)}, **kwargs}
    editor.add_dashboard("Top Sub-Category Contribution", width=1400, height=900,
        worksheet_names=["Contribution Summary", "Contribution Pie", "Highlight Table"],
        layout={"type": "container", "direction": "floating", "children": [
            zone("text", 15, 10, 1370, 65, text="How much do top sub-categories contribute to sales?", font_size=26, bold=True),
            zone("text", 15, 80, 1100, 45, text="Choose Top N. Hover either view to highlight its group across both views.", font_size=14),
            zone("paramctrl", 1190, 78, 190, 55, parameter="pTopN"),
            zone("worksheet", 15, 145, 765, 65, name="Contribution Summary", fit="entire", show_title=False),
            zone("worksheet", 15, 210, 765, 630, name="Contribution Pie", fit="entire", show_title=False),
            zone("worksheet", 800, 145, 585, 695, name="Highlight Table", fit="entire", show_title=False),
            zone("text", 15, 855, 1370, 35, text="#WOW2021 Week 41 | Challenge: Ann Jackson | Article: Donna Coles", font_size=11)]})
    editor.add_dashboard_action("Top Sub-Category Contribution", "highlight",
        source_sheets=["Contribution Pie", "Highlight Table"],
        target_sheets=["Contribution Pie", "Highlight Table"], fields=["Sales Group"],
        event_type="on-hover", caption="Highlight sales membership")
    output = OUTPUTS / "replicated-workbook.twbx"
    editor.save(output)
    return output


if __name__ == "__main__":
    print(build())
