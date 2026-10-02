"""Rebuild WW47 charts and authored explanation views using public SDK APIs."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
DASHBOARD = "2019_11_20_WW47_High_Level_Sales"
EXPLANATIONS = "2019_11_20_WW47_ExplainData_Dashboard"


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"), table_name="Extract")
    definitions=[("Latest Year","{FIXED : MAX(YEAR([Order Date]))}","integer"),("Previous Year","[Latest Year]-1","integer"),("Sales This Year","IF YEAR([Order Date]) = [Latest Year] THEN [Sales] END","real"),("Sales Last Year","IF YEAR([Order Date]) = [Previous Year] THEN [Sales] END","real"),("Jitter","(INT(RIGHT([Order ID],6))*7919 % 997)/997.0","real")]
    for name,formula,datatype in definitions:
        editor.add_calculated_field(name,formula,datatype=datatype)
    editor.add_calculated_field("Quarter Date", "DATETRUNC('quarter',[Order Date])", datatype="date", role="dimension", field_type="quantitative")
    editor.add_worksheet("Trend")
    editor.configure_chart("Trend",mark_type="Line",columns=["DAYTRUNC(Quarter Date)"],rows=["Sub-Category","SUM(Sales)"],tooltip=["Sub-Category","SUM(Sales)"])
    editor.add_worksheet("This Year v Last Year Bars")
    editor.configure_chart("This Year v Last Year Bars",mark_type="Bar",columns=["SUM(Sales This Year)"],rows=["Sub-Category"],detail="SUM(Sales Last Year)",tooltip=["Sub-Category","SUM(Sales This Year)","SUM(Sales Last Year)"])
    editor.add_reference_line("This Year v Last Year Bars",axis_field="SUM(Sales This Year)",value_field="SUM(Sales Last Year)",scope="per-cell",formula="average",label_type="none",tooltip="Previous year sales: <Value>")
    editor.add_worksheet("Jitter Dot Plot")
    editor.configure_chart("Jitter Dot Plot",mark_type="Circle",columns=["SUM(Sales)"],rows=["Sub-Category","ATTR(Jitter)"],detail="Order ID",tooltip=["Order ID","Sub-Category","SUM(Sales)"])
    editor.add_reference_line("Jitter Dot Plot",axis_field="SUM(Sales)",value_field="SUM(Sales)",scope="per-pane",formula="average",label_type="none",tooltip="Average order sales: <Value>")
    editor.add_worksheet("Average Value of Records")
    editor.configure_chart("Average Value of Records",mark_type="Circle",columns=["AVG(Sales)"],rows=["Sub-Category","ATTR(Jitter)"],detail="Order ID",tooltip=["Order ID","Sub-Category","AVG(Sales)"])
    editor.add_reference_line("Average Value of Records",axis_field="AVG(Sales)",value_field="AVG(Sales)",scope="per-pane",formula="average",label_type="none")
    editor.add_worksheet("Average Sales by Category")
    editor.configure_chart("Average Sales by Category",mark_type="Bar",columns=["Category"],rows=["AVG(Sales)"],tooltip=["Category","AVG(Sales)"])
    for sheet in ["Trend","This Year v Last Year Bars","Jitter Dot Plot","Average Value of Records","Average Sales by Category"]:
        editor.configure_worksheet_style(sheet,hide_axes=sheet!="Average Sales by Category",hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_col_field_labels=True,hide_row_field_labels=True,hide_row_label="Sub-Category" if sheet in ["This Year v Last Year Bars","Jitter Dot Plot"] else None,pane_mark_style={"mark-color":"#a9bed4","mark-labels-show":"false","has-stroke":"true","stroke-color":"#898989","mark-transparency":"178"} if sheet in ["Jitter Dot Plot","Average Value of Records"] else {"mark-color":"#a9bed4","mark-labels-show":"false"})
    editor.configure_worksheet_style("Trend", axis_style={"encodings":[{"field":"SUM(Sales)","scope":"rows","class":"0","range_type":"independent"}]})
    for sheet in ["This Year v Last Year Bars","Jitter Dot Plot","Average Value of Records"]:
        editor.configure_reference_line_style(sheet,"refline0",{"stroke-color":"#1b1b1b","stroke-size":"2","line-pattern-only":"dashed" if sheet!="This Year v Last Year Bars" else "solid"})
    for name,sheets in [(DASHBOARD,["Trend","This Year v Last Year Bars","Jitter Dot Plot"]),(EXPLANATIONS,["Average Value of Records","Average Sales by Category"])]:
        layout={"type":"container","direction":"vertical","children":[{"type":"text","text":"High Level Sales Dashboard" if name==DASHBOARD else "Explain Data: Saved Explanation Charts","font_size":"16","bold":False,"fixed_size":60},{"type":"container","direction":"horizontal","weight":1,"children":[{"type":"container","direction":"vertical","weight":([30,29,41][i] if name==DASHBOARD else 1),"children":[{"type":"text","text":title,"font_size":"11","fixed_size":32},{"type":"worksheet","name":sheet,"show_title":False,"fit":"entire","weight":1}]} for i,(sheet,title) in enumerate(zip(sheets,["Sales by Quarter","This Year vs Last Year","Sales by Order ID"] if name==DASHBOARD else ["Average Value of Records","Average Sales by Category"]))]},{"type":"text","text":"#WORKOUTWEDNESDAY | 2019 | WEEK 47","font_size":"9","fixed_size":35}]}
        if name == DASHBOARD:
            panels=[(800,29500),(30300,28600),(58900,40300)]
            zones=[{"type":"text","text":"High Level Sales Dashboard","font_size":"16","absolute":{"x":800,"y":1000,"w":98400,"h":6000}}]
            for sheet,title,(x,width) in zip(sheets,["Sales by Quarter","This Year v Last Year","Sales by Order ID"],panels):
                zones.append({"type":"text","text":title,"font_size":"14","absolute":{"x":x,"y":7900,"w":width,"h":5750}})
                zones.append({"type":"worksheet","name":sheet,"show_title":False,"fit":"entire","absolute":{"x":x,"y":13750,"w":width,"h":77250}})
            zones.append({"type":"text","text":"#WORKOUTWEDNESDAY | 2019 | WEEK 47","font_size":"9","absolute":{"x":800,"y":92500,"w":98400,"h":5500}})
            layout={"type":"container","direction":"floating","children":zones}
        editor.add_dashboard(name,width=1000,height=800,layout=layout,worksheet_names=sheets)
    editor.set_active_dashboard(DASHBOARD)
    (HERE / "outputs").mkdir(exist_ok=True)
    editor.save(HERE / "outputs/replicated-workbook.twbx",validate=False)
    editor.save(HERE / "outputs/replicated-workbook.twb",validate=False)

if __name__ == "__main__":
    build()
