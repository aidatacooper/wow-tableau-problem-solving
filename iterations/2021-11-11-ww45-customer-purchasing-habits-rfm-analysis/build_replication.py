"""Build RFM from extracted Hyper using public cwtwb APIs only."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent

def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_0hqe4ej0o53vlw1ghl4fi0mgozri.hyper"))
    e.add_parameter("Reference Date", datatype="date", default_value="#2022-01-01#", domain_type="any")
    e.add_parameter("Active Threshold", datatype="integer", default_value="90", domain_type="range", min_value="0", max_value="2000", granularity="1")
    choices=["Recency ascending","Orders descending","Revenue descending","Average order value descending","Quantity descending"]
    e.add_parameter("Sort Metric",datatype="string",default_value=choices[0],domain_type="list",allowed_values=choices)
    definitions = [
        ("Last Purchase", "{FIXED [Customer ID]: MAX([Order Date])}", "date", "dimension", "ordinal"),
        ("Recency", "DATEDIFF('day',[Last Purchase],[Parameters].[Reference Date])", "integer", "measure", "quantitative"),
        ("Orders", "COUNTD([Order ID])", "integer", "measure", "quantitative"),
        ("Average Order Value", "SUM([Sales])/[Orders]", "real", "measure", "quantitative"),
        ("Unique Products", "COUNTD([Product ID])", "integer", "measure", "quantitative"),
        ("Active", "[Recency]<=[Parameters].[Active Threshold]", "boolean", "dimension", "nominal"),
        ("Days Label", "IF [Recency]<365 THEN [Recency] END", "integer", "measure", "quantitative"),
        ("Years Label", "IF [Recency]>=365 THEN [Recency]/365.0 END", "real", "measure", "quantitative"),
        ("Sort Key", "CASE [Parameters].[Sort Metric] WHEN 'Recency ascending' THEN -MIN([Recency]) WHEN 'Orders descending' THEN [Orders] WHEN 'Revenue descending' THEN SUM([Sales]) WHEN 'Average order value descending' THEN [Average Order Value] WHEN 'Quantity descending' THEN SUM([Quantity]) END", "real", "measure", "quantitative"),
        ("Recency Label", "IF [Recency]<365 THEN STR([Recency])+' days' ELSE STR(ROUND([Recency]/365.0,1))+' years' END", "string", "dimension", "nominal"),
        ("Recency Axis", "1", "integer", "measure", "quantitative"),
        ("Quantity Axis", "0", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, field_type in definitions:
        fmt = {"Days Label":'0" days"',"Years Label":'0.0" years"',"Average Order Value":'$#,##0.00'}.get(name, "")
        e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=field_type, default_format=fmt)
    e.add_worksheet("Customers")
    e.configure_layered_chart("Customers", columns=["MIN(Recency Axis)","Orders","SUM(Sales)","Average Order Value","MIN(Quantity Axis)"], rows=["Customer ID","Customer Name"], axis_shelf="cols", synchronized=False, fold_axes=False, hide_axes=True,
        sort_descending="Sort Key", sort_field="Customer ID", sort_mode="computed", panes=[
            {"axis":"MIN(Recency Axis)","mark_type":"Text","color":"Active","label":"Recency Label","tooltip":["MIN(Last Purchase)","MIN(Recency)"],"color_map":{"true":"#229c83","false":"#bf554c"}},
            {"axis":"Orders","mark_type":"Bar","label":"Orders"},
            {"axis":"SUM(Sales)","mark_type":"Bar","label":"SUM(Sales)"},
            {"axis":"Average Order Value","mark_type":"Bar","label":"Average Order Value"},
            {"axis":"MIN(Quantity Axis)","mark_type":"Circle","label":"SUM(Quantity)","tooltip":["Unique Products"]},
        ])
    e.configure_worksheet_style("Customers",hide_axes=True,hide_row_label="Customer ID",hide_row_field_labels=True,hide_gridlines=True,hide_borders=True)
    e.add_calculated_field("Product Rank", "RANK_UNIQUE(SUM([Sales]), 'desc')", datatype="integer", role="measure", field_type="quantitative", table_calc="Rows", default_format='"#"0')
    e.add_worksheet("Help")
    e.add_calculated_field("Help Text", '"Sort customers by recency, orders, revenue, average order value or quantity. Active customers purchased within the selected number of days, inclusive. Hover quantity to see the top ten products for the selected customer. Reference date: 1 January 2022."', datatype="string", role="dimension", field_type="nominal")
    e.configure_chart("Help", mark_type="Text", label="Help Text")
    e.configure_worksheet_style("Help", disable_tooltip=True, hide_gridlines=True, hide_borders=True, background_color="#ffffff")
    e.add_worksheet("Top Products")
    e.configure_layered_chart("Top Products",columns=["Measure Names"],rows=["Product Name"],panes=[{"mark_type":"Text","label":"Multiple Values","measure_values":["Product Rank","SUM(Sales)","SUM(Quantity)"]}],fold_axes=False,sort_descending="SUM(Sales)",sort_field="Product Name",filters=[{"column":"Product Rank","type":"quantitative","min":"1","max":"10"}],table_calc_overrides={"Product Rank":[{"ordering_type":"Field","ordering_field":"Product Name"}]},table_calc_context=True)
    e.configure_custom_tooltip("Customers", [{"text":"Quantity: "},{"field":"SUM(Quantity)"},{"text":"; unique products: "},{"field":"Unique Products"},{"text":"\nTop products by revenue\n"},{"sheet":{"name":"Top Products","maxwidth":600,"maxheight":400,"filter_fields":["Customer ID"],"filter_context":True}}],pane_index=4)
    def zone(kind,x,y,w,h,**kw):
        return dict(type=kind,absolute={"x":round(x/1600*100000),"y":round(y/900*100000),"w":round(w/1600*100000),"h":round(h/900*100000)},**kw)
    children=[zone("text",15,5,1500,60,text="Customer purchasing habits | RFM | as of 1 January 2022"),zone("paramctrl",20,70,400,60,parameter="Sort Metric"),zone("paramctrl",450,70,400,60,parameter="Active Threshold"),zone("worksheet",20,190,1560,680,name="Customers",fit="width",show_title=False)]
    # One 260-pixel customer header and five equally sized metric panes.
    e.configure_worksheet_style("Customers",header_formats=[{"field":"Customer Name","width":260}],cell_formats=[{"field":field,"width":260} for field in ["MIN(Recency Axis)","Orders","SUM(Sales)","Average Order Value","MIN(Quantity Axis)"]])
    for i,title in enumerate(["Customer","Recency","Orders","Revenue","Average order value","Quantity"]):
        children.append(zone("text",20+260*i,140,260,40,text=title,align="center",style={"margin":0}))
    children.append(zone("container",30,195,900,200,direction="vertical",style={"background-color":"#ffffff"},children=[{"type":"worksheet","name":"Help","fit":"entire","show_title":False}]))
    e.add_dashboard("RFM",width=1600,height=900,worksheet_names=["Customers","Help"],layout={"type":"container","direction":"floating","children":children})
    e.add_dashboard_toggle_button("RFM",target_worksheets=["Help"],caption_shown="X",caption_hidden="?",initially_hidden=True,position={"x":1530,"y":15,"w":45,"h":40})
    e.set_active_dashboard("RFM")
    out=HERE/"outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out
if __name__ == "__main__": print(build())
