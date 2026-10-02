"""Rebuild the parameter-driven scatter and proportional brushing from extracted data."""
from pathlib import Path
import json
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
DASHBOARD = "2019_11_13_WW46_Dynamic_Scatter_Proportional_Brushing"
HYPER = HERE / "inputs/TEMP_1rs6x3z03rk5kn19aaa5k0h46p7f.hyper"


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    editor.add_group("Manufacturer", "Product Name", json.loads((HERE / "inputs/manufacturer-groups.json").read_text()), default_value=None)
    for name, value, values in [("Set Level of Detail", "Customer", ["Customer", "Manufacturer", "Product"]), ("Set X-Axis", "Quantity", ["Quantity", "Sales", "Orders", "Discount"]), ("Set Y-Axis", "Discount", ["Quantity", "Sales", "Orders", "Discount"])]:
        editor.add_parameter(name, datatype="string", default_value=value, domain_type="list", allowed_values=values)
    editor.add_calculated_field("LOD", "CASE [Set Level of Detail] WHEN 'Customer' THEN [Customer Name] WHEN 'Manufacturer' THEN [Manufacturer] WHEN 'Product' THEN [Product Name] END", datatype="string", role="dimension", field_type="nominal")
    for axis in ["X", "Y"]:
        editor.add_calculated_field(f"{axis}-Axis", f"CASE [Set {axis}-Axis] WHEN 'Quantity' THEN SUM([Quantity]) WHEN 'Sales' THEN SUM([Sales]) WHEN 'Orders' THEN COUNTD([Order ID]) WHEN 'Discount' THEN SUM([Discount]) END", datatype="real")
    editor.add_set("Selected LOD", "LOD")
    editor.add_calculated_field("# LOD", "COUNTD([LOD])", datatype="integer")
    for label, measure in [("LOD", "[# LOD]"), ("X", "[X-Axis]"), ("Y", "[Y-Axis]")]:
        editor.add_calculated_field(f"{label} Share", f"{measure} / WINDOW_SUM({measure})", datatype="real", table_calc="Rows", default_format="p0.0%")
        editor.add_calculated_field(f"{label} Total", f"WINDOW_SUM({measure})", datatype="real", table_calc="Rows")
        editor.add_calculated_field(f"{label} Selected", f"ZN(WINDOW_MAX(IF ATTR([Selected LOD]) THEN {measure} END))", datatype="real", table_calc="Rows")
        editor.add_calculated_field(f"{label} Selected Percent", f"[{label} Selected] / [{label} Total]", datatype="real", table_calc="Rows", default_format="p0.0%")
    editor.add_worksheet("Scatter")
    editor.configure_dual_axis("Scatter", mark_type_1="Circle", mark_type_2="Circle", columns=["X-Axis", "X-Axis"], rows=["Y-Axis"], dual_axis_shelf="columns", detail_1="LOD", detail_2="LOD", synchronized=True, show_labels=False, mark_color_1="#31a1b3", mark_color_2="#31a1b3")
    for pane in [0, 1, 2]:
        editor.configure_custom_tooltip("Scatter", [{"field":"LOD"}, {"text":"\nX: "}, {"field":"X-Axis"}, {"text":"\nY: "}, {"field":"Y-Axis"}], pane_index=pane)
    editor.configure_worksheet_style("Scatter", hide_gridlines=True, hide_borders=True, hide_table_dividers=True, axis_style={"per_field":[{"field":"X-Axis","attr":"title","scope":"cols","class":"0","value":""},{"field":"X-Axis","attr":"title","scope":"cols","class":"1","title_parameter":"Set X-Axis"},{"field":"Y-Axis","attr":"title","scope":"rows","class":"0","title_parameter":"Set Y-Axis"}],"encodings":[{"field":"X-Axis","scope":"cols","class":"0","major_show":False,"minor_show":False}]}, panes_style=[{"pane_mark_style":{"mark-transparency":"255","has-stroke":"true","stroke-color":"#1b1b1b"}} for _ in range(3)])
    for label in ["LOD", "X", "Y"]:
        sheet=f"{label} Bars"
        editor.add_worksheet(sheet)
        overrides={f"{label} Share":[{"ordering_type":"Field", "ordering_field":"Selected LOD"}],f"{label} Total":[{"ordering_type":"Field", "ordering_field":"Selected LOD"}],f"{label} Selected":[{"ordering_type":"Field", "ordering_field":"Selected LOD"}],f"{label} Selected Percent":[{"ordering_type":"Field", "ordering_field":"Selected LOD"}]}
        editor.configure_chart(sheet, mark_type="Bar", columns=[f"{label} Share"], color="Selected LOD", tooltip=[f"{label} Total", f"{label} Selected", f"{label} Selected Percent"], color_map={"true":"#1b4f59", "false":"#31a1b3"}, table_calc_overrides=overrides, axis_fixed_range={"field":f"{label} Share", "min":0,"max":1})
        editor.configure_worksheet_style(sheet, hide_gridlines=True, hide_borders=True, hide_zeroline=True, hide_table_dividers=True, pane_mark_style={"mark-labels-show":"false"},axis_style={"per_field":[{"field":f"{label} Share","attr":"title","scope":"cols","class":"0","value":""}],"encodings":[{"field":f"{label} Share","scope":"cols","class":"0","range_type":"fixed","min":"0","max":"1","major_origin":"0","major_spacing":"0.2","major_show":True,"minor_show":False}]})
    layout={"type":"container","direction":"vertical","children":[{"type":"text","text":"Can you build a dynamic scatter plot with proportional brushing?","font_size":"16","bold":False,"fixed_size":52},{"type":"container","direction":"horizontal","fixed_size":52,"children":[{"type":"paramctrl","parameter":name,"mode":"compact"} for name in ["Set Level of Detail","Set X-Axis","Set Y-Axis"]]},{"type":"container","direction":"horizontal","fixed_size":66,"children":[{"type":"worksheet","name":f"{label} Bars","show_title":False,"fit":"entire"} for label in ["LOD","X","Y"]]},{"type":"worksheet","name":"Scatter","show_title":False,"fit":"entire","weight":1},{"type":"text","text":"#WORKOUTWEDNESDAY | 2019 | WEEK 46","font_size":"9","fixed_size":30}]}
    editor.add_dashboard(DASHBOARD, width=1000, height=700, layout=layout, worksheet_names=["Scatter","LOD Bars","X Bars","Y Bars"])
    editor.add_dashboard_set_action(DASHBOARD, "Scatter", "Selected LOD", event_type="on-select", clear_option="exclude-all", caption="Select marks for proportional brushing")
    editor.set_active_dashboard(DASHBOARD)
    (HERE / "outputs").mkdir(exist_ok=True)
    editor.save(HERE / "outputs/replicated-workbook.twbx", validate=False)
    editor.save(HERE / "outputs/replicated-workbook.twb", validate=False)

if __name__ == "__main__":
    build()
