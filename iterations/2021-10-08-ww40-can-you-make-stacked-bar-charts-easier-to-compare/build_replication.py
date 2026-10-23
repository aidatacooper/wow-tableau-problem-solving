"""WW40: native parameter-driven stack ordering from locked input only."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_10_06_WW40_Compare_Stacked_Bar_Charts"
PARAMETER = "pSelectedCategpry"  # Preserve the published author caption, including its typo.
COLORS = {"Furniture":"#1170aa", "Technology":"#a3acb9", "Office Supplies":"#fc7d0b"}

def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))), table_name="Extract")
    editor.add_parameter(PARAMETER, datatype="string", default_value="Office Supplies", domain_type="any")
    editor.add_calculated_field("State Initial ASCII", "ASCII(UPPER(LEFT([State],1)))", datatype="integer", role="dimension", field_type="ordinal")
    editor.add_calculated_field("State Group", "IF [State Initial ASCII] <= 77 THEN 'A-M' ELSE 'N-Z' END", datatype="string", role="dimension", field_type="nominal")
    editor.add_calculated_field("Sort", "IF [pSelectedCategpry]=[Category] THEN 0 ELSE 1 END", datatype="integer")
    editor.add_calculated_field("Total Sales per State Group", "{FIXED [State Group]: SUM([Sales])}", datatype="real", default_format='c"$"#,##0,K;-"$"#,##0,K')
    for field, formula in [("True","True"),("False","False")]:
        editor.add_calculated_field(field, formula, datatype="boolean", role="dimension", field_type="nominal")
    editor.set_field_format("Sales", 'c"$"#,##0,K;-"$"#,##0,K')
    editor.add_worksheet("Chart")
    editor.configure_layered_chart("Chart", columns=["State Group"], rows=["SUM(Sales)"], axis_shelf="rows", sort_descending="SUM(Sort)", sort_field="Category", sort_mode="computed", panes=[{
        "axis":"SUM(Sales)", "mark_type":"Bar", "breakdown":"auto", "color":"Category", "color_map":COLORS,
        "label":"SUM(Sales)", "detail_extra":["SUM(Total Sales per State Group)","True","False"],
        "mark_style":{"size":"1.0544751882553101", "mark-labels-show":"true", "mark-labels-cull":"true"},
        "datalabel_style":{"color-mode":"user","color":"#ffffff","font-weight":"bold"}
    }])
    editor.configure_custom_tooltip("Chart", [
        {"text":"State Group: "},{"field":"State Group","bold":True},
        {"text":"\nCategory: "},{"field":"Category","bold":True},
        {"text":"\nTotal Sales per State Group: "},{"field":"SUM(Total Sales per State Group)","bold":True},
        {"text":"\nSales: "},{"field":"SUM(Sales)","bold":True}
    ])
    editor.add_reference_line("Chart", axis_field="SUM(Sales)", value_field="SUM(Total Sales per State Group)", scope="per-cell", formula="total", label_type="value", probability=None, tooltip="")
    editor.configure_reference_line_style("Chart", "refline0", {"fill-above":"#00000000","fill-below":"#00000000","stroke-size":"0","line-visibility":"off","text-align":"center","vertical-align":"top"})
    editor.configure_worksheet_style("Chart", hide_axes=True, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_col_field_labels=True, pane_datalabel_style={"color-mode":"user","color":"#ffffff","font-weight":"bold"})
    editor.set_worksheet_rich_title("Chart", [
        {"text":"Sales by Category", "bold":True, "fontsize":14},
        {"text":"\nSelect a category to re-order the stack\n", "fontsize":10},
        {"text":"Furniture", "fontcolor":COLORS["Furniture"], "bold":True, "fontsize":10},
        {"text":"  |  ", "fontsize":10},
        {"text":"Office Supplies", "fontcolor":COLORS["Office Supplies"], "bold":True, "fontsize":10},
        {"text":"  |  ", "fontsize":10},
        {"text":"Technology", "fontcolor":COLORS["Technology"], "bold":True, "fontsize":10},
    ])
    layout={"type":"container","direction":"vertical","style":{"padding":8},"children":[
        {"type":"text","text":"Can you make stacked bar charts easier to compare?","font_size":18,"font_color":"#ffffff","bold":True,"fixed_size":102,"style":{"background-color":"#898989","padding":4}},
        {"type":"worksheet","name":"Chart","fit":"entire","show_title":True,"style":{"margin":4}},
        {"type":"text","text":"#WOW2021  |  WEEK 40","font_size":8,"fixed_size":24},
        {"type":"text","text":"CHALLENGE BY CANDRA McRAE  |  RECREATED WITH cwtwb","font_size":8,"fixed_size":44},
        {"type":"text","text":"http://www.workout-wednesday.com/tab2021w40/","font_size":8,"fixed_size":26}
    ]}
    editor.add_dashboard(DASHBOARD,width=400,height=800,worksheet_names=["Chart"],layout=layout)
    editor.add_dashboard_action(DASHBOARD,"parameter",source_sheet="Chart",source_field="Category",target_parameter=PARAMETER,caption="Select Category",aggregation="attr",clear_behavior="keep-current")
    editor.add_dashboard_action(DASHBOARD,"filter",source_sheet="Chart",target_sheet="Chart",field_mappings={"True":"False"},caption="Clear Selection",clear_behavior="show-all")
    editor.set_window_state(DASHBOARD,zoom_entire_view=True)
    out=HERE/"outputs/replicated-workbook.twbx"
    editor.save(out,validate=False)
    return out

if __name__=="__main__":
    print(build())

