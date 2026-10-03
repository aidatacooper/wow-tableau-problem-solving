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
        editor.configure_layered_chart(f"{prefix} Select", rows=["Category"], filters=filters, sort_descending="SUM(Sales)", panes=[{"mark_type": "Circle", "color": f"Category Exists in {prefix} List", "color_map": {"true": "#76b7b2", "false": "#bab0ac"} if prefix == "Forecast" else {"true": "#ffffff", "false": "#b4b4b4"}, "detail_extra": [f"Add To {prefix} List", "True", "False"], "mark_style": {"size": "0.95", "mark-labels-show": "false", "has-stroke": "true" if prefix == "Target" else "false", "stroke-color": "#ffffff"}}])
        editor.configure_chart(f"{prefix} Reset", mark_type="Text", label="Reset Glyph", detail=f"{prefix} List Reset")
    editor.configure_layered_chart("Viz", columns=["Multiple Values", "Target"], rows=["Category"], axis_shelf="columns", filters=filters, sort_descending="SUM(Sales)", panes=[
        {"axis": "Multiple Values", "measure_values": ["Forecast", "SUM(Sales)"], "mark_type": "Bar", "breakdown": "off", "color": "Measure Names", "size": "Measure Names", "color_map": {"Forecast": "#76b7b2", "SUM(Sales)": "#4e79a7"}, "detail_extra": ["Target", "SUM(Sales)", "Forecast", "Sales v Target Diff", "Forecast v Target Diff"], "mark_style": {"size": "1.45", "mark-labels-show": "false"}},
        {"axis": "Target", "mark_type": "GanttBar", "breakdown": "off", "mark_style": {"mark-color": "#000000", "size": "1.8680663108825684", "mark-labels-show": "false"}},
    ])
    editor.configure_layered_chart("Labels", rows=["Category"], filters=filters, sort_descending="SUM(Sales)", panes=[{"mark_type": "Text", "labels": ["Target", "SUM(Sales)", "Forecast", "Sales Diff Text", "Forecast Diff Text"], "label_runs": [{"text": "Target: "}, {"field": "Target"}, {"text": "\nYTD: "}, {"field": "SUM(Sales)"}, {"text": " ("}, {"field": "Sales Diff Text"}, {"text": ")\nForecast: "}, {"field": "Forecast"}, {"text": " "}, {"field": "Forecast Diff Text"}], "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"}}])
    for sheet in ["Forecast Select", "Forecast Reset", "Target Select", "Target Reset", "Viz", "Labels"]:
        editor.configure_worksheet_style(sheet, hide_axes=True, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_table_dividers=True, hide_band_color=True, hide_col_field_labels=True, hide_row_field_labels=True, hide_sort_controls=True, hide_row_label="Category" if sheet in ["Viz", "Labels"] else None, pane_datalabel_style={"font-family": "Tableau Regular", "font-size": "9"})
    editor.configure_worksheet_style("Labels", pane_cell_style={"text-align": "left", "vertical-align": "center"})
    for prefix, color in [("Forecast", "#f5f5f5"), ("Target", "#b4b4b4")]:
        editor.configure_worksheet_style(f"{prefix} Select", background_color=color, header_formats=[{"field": "Category", "width": "120"}], label_formats=[{"field": "Category", "font-family": "Tableau Regular", "font-size": "9"}])
    for prefix,color in [("Forecast","#f5f5f5"),("Target","#b4b4b4")]:
        editor.configure_worksheet_style(f"{prefix} Reset", background_color=color, pane_cell_style={"text-align":"right","vertical-align":"center"}, pane_datalabel_style={"font-family":"Tableau Regular","font-size":"20","color":"#333333","color-mode":"user"}, pane_mark_style={"size":"5.3785600662231445"})
    def rect(x, y, w, h):
        return {"x": x*100, "y": y*200, "w": w*100, "h": h*200}
    def text_zone(text,x,y,w,h,*,size=9,color="#333333",bold=False,italic=False,align="center"):
        return {"type":"text","runs":[{"text":text,"font_size":size,"font_color":color,"bold":bold,"italic":italic,"font_alignment":{"left":"0","center":"1","right":"2"}[align]}],"absolute":rect(x,y,w,h)}
    panels=[]
    for prefix,x,color,caption in [("Forecast",8,"#f5f5f5","Sales Forecast"),("Target",822,"#b4b4b4","Sales Target")]:
        panels.append({"type":"container","direction":"vertical","absolute":rect(x,8,172,420),"style":{"background-color":color},"children":[
            {"type":"empty","fixed_size":74,"style":{"background-color":color}},
            {"type":"text","fixed_size":24,"runs":[{"text":caption,"font_size":9,"font_color":"#333333"}],"style":{"background-color":color}},
            {"type":"paramctrl","parameter":f"{prefix} Param","show_title":False,"fixed_size":25,"style":{"background-color":color}},
            {"type":"worksheet","name":f"{prefix} Select","show_title":False,"fit":"entire","fixed_size":190},
            {"type":"worksheet","name":f"{prefix} Reset","show_title":False,"fit":"entire","fixed_size":40},
            {"type":"empty","style":{"background-color":color}},
        ]})
    zones = [*panels,
        text_zone("WHAT HAPPENS IF?",198,10,616,30,size=15,bold=True,align="left"),
        text_zone("Use this dashboard to increase sales or target sales for each category",198,40,616,24,size=9,italic=True,align="left"),
        {"type":"worksheet","name":"Viz","show_title":False,"fit":"entire","absolute":rect(184,130,426,190)},
        {"type":"worksheet","name":"Labels","show_title":False,"fit":"entire","absolute":rect(612,130,206,190)},
        text_zone("DESIGNED BY : LORNA EDEN",15,437,250,22,size=8,color="#00a3a8",align="left"),
        text_zone("#WOW2020 | WEEK 7",360,437,280,22,size=8,color="#00a3a8"),
        text_zone("RECREATED WITH CWTWB",750,437,242,22,size=8,color="#00a3a8",align="right"),
        text_zone("http://www.workout-wednesday.com/2020w07/",280,469,440,22,size=8,color="#006080"),
    ]
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
