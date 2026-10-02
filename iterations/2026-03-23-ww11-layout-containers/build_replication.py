"""Independent Superstore overview constructed with public SDK APIs."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
DASHBOARD="#WOW2026 Week 11"
def build():
    e=TWBEditor("");e.set_hyper_connection(str(next((HERE/"inputs").glob("*.hyper"))),table_name="Orders_ECFCA1FB690A41FE803BC071773BA862")
    calculations=[("CY","{MAX(YEAR([Order Date]))}","integer"),("PY","[CY]-1","integer"),("Month","DATEPART('month',[Order Date])","integer"),("Profit Ratio","SUM([Profit])/SUM([Sales])","real")]
    for metric in ["Sales","Profit"]:
        for year in ["CY","PY"]:calculations.append(("Total "+metric+" "+year,"IF ["+year+"]=YEAR([Order Date]) THEN ["+metric+"] END","real"))
        calculations.append((metric+" % Increase","(SUM([Total "+metric+" CY])-SUM([Total "+metric+" PY]))/SUM([Total "+metric+" PY])","real"))
    for year in ["CY","PY"]:calculations.append(("Total Profit Ratio "+year,"{INCLUDE YEAR([Order Date]),[Month]: IF MAX(["+year+"])=MAX(YEAR([Order Date])) THEN [Profit Ratio] END}","real"))
    calculations += [("PR % Increase","ZN([Total Profit Ratio CY])-ZN([Total Profit Ratio PY])","real"),("Total Orders CY","COUNTD(IF [CY]=YEAR([Order Date]) THEN [Order ID] END)","integer"),("Above Below CY Sales & Profit","IF WINDOW_AVG(SUM([Total Sales CY])) >= SUM([Total Sales CY]) AND WINDOW_AVG(SUM([Total Profit CY])) >= SUM([Total Profit CY]) THEN 'Below Both' ELSEIF WINDOW_AVG(SUM([Total Sales CY])) <= SUM([Total Sales CY]) AND WINDOW_AVG(SUM([Total Profit CY])) >= SUM([Total Profit CY]) THEN 'Above Sales Below Profit' ELSEIF WINDOW_AVG(SUM([Total Sales CY])) <= SUM([Total Sales CY]) AND WINDOW_AVG(SUM([Total Profit CY])) <= SUM([Total Profit CY]) THEN 'Above Sales Above Profit' ELSE 'Below Sales Above Profit' END","string")]
    for name,formula,datatype in calculations:
        kw={}
        if name=="Month":kw={"role":"dimension","field_type":"ordinal"}
        if name=="Above Below CY Sales & Profit":kw={"role":"measure","field_type":"nominal","table_calc":"Rows"}
        e.add_calculated_field(name,formula,datatype=datatype,**kw)
        if 'Ratio' in name or 'Increase' in name:e.set_field_format(name,"p0.0%")
        elif name.startswith('Total') and 'Orders' not in name:e.set_field_format(name,'n"\u00a3"#,##0,.0K;-"$"#,##0,.0K')
    palettes={}
    left=[];sheets=[]
    for index,(metric,change) in enumerate([("Sales","Sales % Increase"),("Profit","Profit % Increase"),("Profit Ratio","PR % Increase")]):
        cy="SUM(Total "+metric+" CY)";py="SUM(Total "+metric+" PY)"
        for expr,col in [(cy,"#3d455d"),(py,"#82a6a4")]:palettes[expr]=col
        total="Total "+metric+" CY vs PY";delta=metric+" % Change";line=metric+" Over Time"
        display_metric="Profit" if metric=="Profit Ratio" else metric
        sheets += [total,delta,line]
        e.add_worksheet(total)
        e.configure_chart(total,mark_type="Text",label=cy,label_extra=[py],label_runs=[{"text":"Total "+display_metric+" CY","fontsize":12,"fontalignment":"0"},{"text":"\n"},{"field":cy,"fontsize":20,"fontalignment":"0"},{"text":"\n"},{"text":"\n"},{"field":py,"fontsize":14,"fontcolor":"#82a6a4","fontalignment":"0"},{"text":"\n"},{"text":"Total "+display_metric+" PY","fontsize":10,"fontcolor":"#82a6a4","fontalignment":"0"}])
        e.configure_worksheet_style(total,hide_gridlines=True,hide_borders=True,pane_cell_style={"text-align":"left","vertical-align":"center"})
        e.add_worksheet(delta)
        change_expr="SUM(PR % Increase)" if metric=="Profit Ratio" else change
        e.set_field_format(change, "*\u25b20.0%;\u25bc0.0%")
        e.configure_chart(delta,mark_type="Square",label=change_expr,color=change_expr,mark_sizing_off=True)
        e.configure_worksheet_style(delta,disable_tooltip=True,pane_mark_style={"size":"14.548","mark-labels-show":"true"},pane_datalabel_style={"font-size":"15"},color_style={"field":change_expr,"colors":["#f9a655","#aaaaff"],"center":0})
        e.add_worksheet(line)
        e.configure_dual_axis(line,mark_type_1="Line",mark_type_2="Line",columns=["Month"],rows=[cy,py],mark_color_1="#3d455d",mark_color_2="#82a6a4",size_value_1="1",size_value_2="1",show_labels=False,hide_axes=True,hide_zeroline=True)
        e.configure_worksheet_style(line,hide_gridlines=True,hide_borders=True,hide_axes=True,hide_row_label="Month",hide_col_field_labels=True,panes_style=[{"pane_mark_style":{"mark-labels-show":"false"}} for _ in range(3)])
        left.append({"type":"container","direction":"horizontal","corner_radius":0,"style":{"background-color":"#ffffff","margin":2,"margin-left":5},"children":[{"type":"worksheet","name":total,"fit":"entire","fixed_size":140,"show_title":False,"style":{"padding":10,"margin":0}},{"type":"worksheet","name":delta,"fit":"entire","fixed_size":130,"show_title":False,"corner_radius":20,"style":{"margin-top":80,"margin-right":15,"margin-bottom":20,"margin-left":15,"padding":0}},{"type":"worksheet","name":line,"show_title":False,"fit":"entire","style":{"padding":15,"margin":0}}]})
    e.set_datasource_color_palette("Measure Names",palettes,is_measure_names=True)
    e.add_worksheet("Scatter");sheets.append("Scatter")
    e.configure_layered_chart("Scatter",columns=["SUM(Total Sales CY)"],rows=["SUM(Total Profit CY)"],panes=[{"mark_type":"Circle","color":"Above Below CY Sales & Profit","size":"Total Orders CY","detail":"Sub-Category","color_map":{"Above Sales Above Profit":"#76b7b2","Below Sales Above Profit":"#848e93","Above Sales Below Profit":"#b07aa1","Below Both":"#bab0ac"}}],table_calc_overrides={"Above Below CY Sales & Profit":[{"ordering_type":"Field","ordering_field":"Sub-Category"}]})
    e.configure_worksheet_style("Scatter",hide_gridlines=True,hide_zeroline=True,pane_mark_style={"size":"2","mark-transparency":"139","has-stroke":"true","stroke-color":"#888888"},axis_style={"per_field":[{"field":"SUM(Total Sales CY)","attr":"title","value":"Total Sales CY","scope":"cols"},{"field":"SUM(Total Profit CY)","attr":"title","value":"Total Profit CY","scope":"rows"}]})
    e.set_worksheet_rich_title("Scatter",[{"text":"Current Year Total Sales vs Total Profit\n","fontsize":15},{"text":"Sized by Current Year Total Orders, Coloured by Above Average Sales & Profit","fontsize":12}])
    for axis in ["SUM(Total Sales CY)","SUM(Total Profit CY)"]:
        receipt=e.add_reference_line("Scatter",axis_field=axis,value_field=axis,formula="average",label_type="none")
        e.configure_reference_line_style("Scatter",receipt.split("\'")[1],{"line-pattern-only":"dashed","stroke-size":2,"stroke-color":"#888888"})
    layout={"type":"container","direction":"vertical","style":{"padding":10},"children":[{"type":"container","direction":"horizontal","fixed_size":137,"corner_radius":5,"style":{"background-color":"#e6e6e6"},"children":[{"type":"text","corner_radius":0,"style":{"background-color":"#ffffff","margin":2,"margin-left":5,"padding":15},"text":"Superstore Overview\nShowing Current vs Last Year","runs":[{"text":"Superstore Overview\n","font_size":22,"font_color":"#737373","font_alignment":0},{"text":"Showing Current vs Last Year","font_size":15,"font_color":"#737373","font_alignment":0}]}]},{"type":"container","direction":"horizontal","layout_strategy":"distribute-evenly","style":{"margin-top":10},"children":[{"type":"container","direction":"vertical","layout_strategy":"distribute-evenly","style":{"margin-right":5},"children":[{"type":"container","direction":"horizontal","corner_radius":5,"style":{"background-color":"#e6e6e6","margin-bottom":10},"children":[row]} for row in left]},{"type":"container","direction":"horizontal","corner_radius":5,"style":{"background-color":"#e6e6e6","margin-left":5,"margin-bottom":10},"children":[{"type":"worksheet","name":"Scatter","show_title":True,"fit":"entire","style":{"background-color":"#ffffff","margin":2,"margin-left":5,"padding":15}}]}]},{"type":"container","direction":"horizontal","fixed_size":30,"children":[{"type":"text","text":"CHALLENGE BY: Lorna Brown","font_size":8},{"type":"text","text":"#WOW2026 | WEEK 11","font_size":8},{"type":"text","text":"RECREATED WITH: cwtwb","font_size":8}]},{"type":"text","text":"https://www.workout-wednesday.com/2026w11tab/","font_size":8,"fixed_size":25}]}
    e.add_dashboard(DASHBOARD,width=1200,height=800,worksheet_names=sheets,layout=layout)
    output=HERE/"outputs/replicated-workbook.twbx";output.parent.mkdir(exist_ok=True);e.save(output,validate=False);return output
if __name__=="__main__":print(build())
