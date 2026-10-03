"""Forecast and target parameter-string dashboard, built independently."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_02_12_WW07_Parameters_As_Datasource"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    for name, datatype, value in [("Forecast Param", "integer", "70000"), ("Forecast List", "string", ""), ("Target Param", "integer", "270000"), ("Target List", "string", ""), ("Delimiter", "string", ":")]:
        editor.add_parameter(name, datatype, value, domain_type="any")
    editor.add_calculated_field("2019 Orders", "YEAR([Order Date])=2019", datatype="boolean", role="dimension")
    editor.add_calculated_field("True", "TRUE", datatype="boolean", role="dimension")
    editor.add_calculated_field("False", "FALSE", datatype="boolean", role="dimension")
    editor.add_calculated_field("Reset Glyph", "'↺'", datatype="string", role="dimension")
    for prefix in ["Forecast", "Target"]:
        editor.add_calculated_field(f"Category Exists in {prefix} List", f"CONTAINS([{prefix} List],[Category])", datatype="boolean", role="dimension")
        condition = "<>0" if prefix == "Forecast" else ">0"
        # Replace an existing category entry before appending its new value.
        editor.add_calculated_field(f"Add To {prefix} List", f"IF [{prefix} Param]{condition} THEN REGEXP_REPLACE([{prefix} List],[Category]+'_(-?\\d+)'+[Delimiter],'')+[Category]+'_'+STR([{prefix} Param])+[Delimiter] ELSE '' END", datatype="string", role="dimension")
        editor.add_calculated_field(f"{prefix} List Reset", "''", datatype="string", role="dimension")
        name = "Current FC Value" if prefix == "Forecast" else "Current Target Value"
        editor.add_calculated_field(name, f"INT(IF CONTAINS([{prefix} List],[Category]) THEN REGEXP_EXTRACT([{prefix} List],[Category]+'_(-?\\d+)') END)", datatype="integer")
    editor.add_calculated_field("Forecast", "SUM([Sales])+MAX([Current FC Value])")
    editor.add_calculated_field("Target", "IF ZN(MAX([Current Target Value]))=0 THEN MIN(CASE [Category] WHEN 'Furniture' THEN 270000 WHEN 'Office Supplies' THEN 260000 WHEN 'Technology' THEN 250000 END) ELSE MAX([Current Target Value]) END")
    editor.add_calculated_field("Sales v Target Diff", "(SUM([Sales])-[Target])/[Target]")
    editor.add_calculated_field("Forecast v Target Diff", "([Forecast]-[Target])/[Target]")
    for name in ["Sales", "Forecast", "Target"]:
        editor.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Sales v Target Diff", "p0%")
    editor.set_field_format("Forecast v Target Diff", "p0%")
    for prefix in ["Sales", "Forecast"]:
        editor.add_calculated_field(f"{prefix} Diff Text", f"IF ISNULL([{prefix} v Target Diff]) THEN '' ELSE IF [{prefix} v Target Diff]>=0 THEN '{chr(0x25b2)}' ELSE '{chr(0x25bc)}' END+STR(INT(ROUND(ABS([{prefix} v Target Diff])*100)))+'%' END", datatype="string")
    for name in ["Forecast Select", "Forecast Reset", "Target Select", "Target Reset", "Viz", "Labels"]:
        editor.add_worksheet(name)
    filters = [{"column": "2019 Orders", "values": [True]}]
    for prefix in ["Forecast", "Target"]:
        editor.configure_layered_chart(f"{prefix} Select", rows=["Category"], filters=filters, sort_descending="SUM(Sales)", panes=[{"mark_type": "Circle", "color": f"Category Exists in {prefix} List", "color_map": {"true": "#76b7b2", "false": "#bab0ac"} if prefix == "Forecast" else {"true": "#b4b4b4", "false": "#ffffff"}, "detail_extra": [f"Add To {prefix} List", "True", "False"], "mark_style": {"size": "0.3", "mark-labels-show": "true"}}])
        editor.configure_chart(f"{prefix} Reset", mark_type="Text", label="Reset Glyph", detail=f"{prefix} List Reset")
    editor.configure_layered_chart("Viz", columns=["Multiple Values", "Target"], rows=["Category"], axis_shelf="columns", filters=filters, sort_descending="SUM(Sales)", panes=[
        {"axis": "Multiple Values", "measure_values": ["Forecast", "SUM(Sales)"], "mark_type": "Bar", "breakdown": "off", "color": "Measure Names", "size": "Measure Names", "color_map": {"Forecast": "#76b7b2", "SUM(Sales)": "#4e79a7"}, "detail_extra": ["Target", "SUM(Sales)", "Forecast", "Sales v Target Diff", "Forecast v Target Diff"], "mark_style": {"size": "0.6", "mark-labels-show": "false"}},
        {"axis": "Target", "mark_type": "GanttBar", "breakdown": "off", "mark_style": {"mark-color": "#000000", "size": "0.7", "mark-labels-show": "false"}},
    ])
    editor.configure_layered_chart("Labels", rows=["Category"], filters=filters, sort_descending="SUM(Sales)", panes=[{"mark_type": "Text", "labels": ["Target", "SUM(Sales)", "Forecast", "Sales Diff Text", "Forecast Diff Text"], "label_runs": [{"text": "Target: "}, {"field": "Target"}, {"text": "\nSales: "}, {"field": "SUM(Sales)"}, {"text": " ("}, {"field": "Sales Diff Text"}, {"text": ")\nForecast: "}, {"field": "Forecast"}, {"text": " "}, {"field": "Forecast Diff Text"}], "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"}}])
    for sheet in ["Forecast Select", "Forecast Reset", "Target Select", "Target Reset", "Viz", "Labels"]:
        editor.configure_worksheet_style(sheet, hide_axes=True, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_col_field_labels=True, hide_row_field_labels=True, hide_sort_controls=True, hide_row_label="Category" if sheet in ["Viz", "Labels"] else None, pane_datalabel_style={"font-family": "Tableau Regular", "font-size": "9"})
    editor.configure_worksheet_style("Labels", pane_cell_style={"text-align": "left", "vertical-align": "center"})
    for prefix, color in [("Forecast", "#f5f5f5"), ("Target", "#b4b4b4")]:
        editor.configure_worksheet_style(f"{prefix} Select", background_color=color, header_formats=[{"field": "Category", "width": "120"}], label_formats=[{"field": "Category", "font-family": "Tableau Regular", "font-size": "9"}])
    def rect(x, y, w, h):
        return {"x": x*100, "y": y*200, "w": w*100, "h": h*200}
    zones = [
        {"type": "text", "text": "WHAT HAPPENS IF? SALES FORECAST AND TARGETS", "absolute": rect(8, 8, 984, 40)},
        {"type": "text", "text": "SALES INCREASE", "absolute": rect(8, 65, 172, 30)},
        {"type": "paramctrl", "parameter": "Forecast Param", "show_title": False, "absolute": rect(8, 95, 172, 35)},
        {"type": "text", "text": "SALES TARGET", "absolute": rect(822, 65, 170, 30)},
        {"type": "paramctrl", "parameter": "Target Param", "show_title": False, "absolute": rect(822, 95, 170, 35)},
        {"type": "worksheet", "name": "Viz", "show_title": False, "fit": "entire", "absolute": rect(180, 136, 430, 156)},
        {"type": "worksheet", "name": "Labels", "show_title": False, "fit": "entire", "absolute": rect(612, 136, 210, 156)},
        {"type": "text", "text": "#WOW2020 WEEK 7 | PARAMETERS AS DATA SOURCE", "absolute": rect(8, 450, 984, 35)},
    ]
    for prefix, x in [("Forecast", 8), ("Target", 822)]:
        zones.extend([{"type": "worksheet", "name": f"{prefix} Select", "show_title": False, "fit": "entire", "absolute": rect(x, 136, 172, 156)}, {"type": "worksheet", "name": f"{prefix} Reset", "show_title": False, "fit": "entire", "absolute": rect(x, 292, 172, 60)}])
    editor.add_dashboard(DASHBOARD, width=1000, height=500, worksheet_names=["Forecast Select", "Forecast Reset", "Target Select", "Target Reset", "Viz", "Labels"], layout={"type": "container", "direction": "floating", "children": zones})
    for prefix in ["Forecast", "Target"]:
        editor.add_dashboard_action(DASHBOARD, "parameter", source_sheet=f"{prefix} Select", source_field=f"Add To {prefix} List", target_parameter=f"{prefix} List", event_type="on-select", clear_behavior="keep-current", caption=f"Set {prefix.lower()} category")
        editor.add_dashboard_action(DASHBOARD, "parameter", source_sheet=f"{prefix} Reset", source_field=f"{prefix} List Reset", target_parameter=f"{prefix} List", event_type="on-select", clear_behavior="keep-current", caption=f"Reset {prefix.lower()} list")
        editor.add_dashboard_action(DASHBOARD, "filter", source_sheet=f"{prefix} Select", target_sheet=f"{prefix} Select", field_mappings={"True": "False"}, event_type="on-select", clear_behavior="show-all", caption=f"Deselect {prefix.lower()}")
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
