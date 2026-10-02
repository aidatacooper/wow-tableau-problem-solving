"""Independent WW07 construction; category hiding preserves denominators."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
DASHBOARD = "2026_02_17_WW07_TableCalcs_and_LODs"
REGIONS = ["Central", "East", "South", "West"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
CATEGORIES = ["Furniture", "Office Supplies", "Technology"]
def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_calculated_field("TC - % of Sales", "SUM([Sales]) / TOTAL(SUM([Sales]))", table_calc="Rows", default_format="p0.0%")
    editor.add_calculated_field("TC - Filter Category", "LOOKUP(MIN([Category]),0)", datatype="string", role="measure", field_type="nominal", table_calc="Columns")
    editor.add_calculated_field("LOD - Sales per Region & Segment", "{FIXED [Region], [Segment]:SUM([Sales])}")
    editor.add_calculated_field("LOD - % of Sales", "SUM([Sales]) / SUM([LOD - Sales per Region & Segment])", default_format="p0.0%")
    children = [{"type":"text", "text":"WOW2026 Week 7\nExploring Table Calcs vs LODs\nBuild the following percent-of-total chart using only Table Calculations on the left and only LODs on the right.\nEach bar represents the percentage of Sales that each Category contributes to its Region. Filter by Segment, Region and Category.\n[For Segment, percentages change so that each Region still totals 100%. Category filtering preserves the other percentages.]", "runs":[{"text":"WOW2026 Week 7\n", "font_size":"12"},{"text":"Exploring Table Calcs vs LODs\n", "font_size":"20", "bold":"true"},{"text":"Build the following percent-of-total chart using only Table Calculations on the left and only LODs on the right.\nEach bar represents the percentage of Sales that each Category contributes to its Region. Filter by Segment, Region and Category.\n[For Segment, percentages change so that each Region still totals 100%. Category filtering preserves the other percentages.]", "font_size":"10"}], "absolute":{"x":1500,"y":1500,"w":97000,"h":22000}}]
    for index, (sheet, measure, category_filter, heading) in enumerate([
        ("Table Calcs", "TC - % of Sales", "TC - Filter Category", "Table Calculations"),
        ("LODs", "LOD - % of Sales", "Category", "Level of Detail (LODs)"),
    ]):
        editor.add_worksheet(sheet)
        kwargs = {}
        if index == 0:
            kwargs["table_calc_overrides"] = {measure:[{"ordering_type":"Field", "ordering_field":"Category"}], category_filter:[{"ordering_type":"Columns"}]}
        editor.configure_chart(sheet, mark_type="Bar", columns=[measure], rows=["Region","Category"], label=measure,
            tooltip=["SUM(Sales)"], sort_descending="SUM(Sales)",
            filters=[{"column":"Region","values":REGIONS}, {"column":"Segment","values":SEGMENTS}, {"column":category_filter,"values":CATEGORIES}], **kwargs)
        editor.configure_worksheet_style(sheet, background_color="#fefaf1" if index==0 else "#f4faf9", hide_gridlines=True, hide_borders=True, hide_row_field_labels=True,
            pane_mark_style={"mark-color":"#f28e2b" if index==0 else "#4e79a7", "size":"1.076464056968689", "mark-labels-show":"true"},
            cell_formats=[{"field":"Category","height":22}], label_formats=[{"field":"Region","font-size":"8"},{"field":"Category","font-size":"8"},{"field":measure,"font-size":"8"}], axis_style={"title":"% of Total Sales"})
        x=index*50000
        background="#fefaf1" if index==0 else "#f4faf9"
        border="#f28e2b" if index==0 else "#4e79a7"
        children.append({"type":"empty","style":{"background-color":background,"border-color":border,"border-style":"solid","border-width":1},"absolute":{"x":x+900,"y":25500,"w":48200,"h":65000}})
        children.append({"type":"text","text":"% of Total with\n"+("TABLE CALCULATIONS" if index==0 else "LEVEL OF DETAIL CALCULATIONS"),"runs":[{"text":"% of Total with\n"+("TABLE CALCULATIONS" if index==0 else "LEVEL OF DETAIL CALCULATIONS"),"font_size":"12","font_color":border}],"style":{"background-color":background},"absolute":{"x":x+1909,"y":26756,"w":46182,"h":7432}})
        children.append({"type":"worksheet","name":sheet,"show_title":False,"fit":"entire","style":{"background-color":background},"absolute":{"x":x+1909,"y":40945,"w":46182,"h":48243}})
        for j,(field,caption) in enumerate([("Segment","Segment"),("Region","Region"),(category_filter,"Category")]):
            children.append({"type":"filter","worksheet":sheet,"field":field,"caption":caption,"mode":"checkdropdown","style":{"background-color":background},"absolute":{"x":x+4636+j*13576,"y":34188,"w":13576,"h":6757}})
    for x,w,text in [(1000,33000,"CHALLENGE BY: Erica Hughes"),(35000,30000,"#WOW2026 | WEEK 7"),(68000,31000,"RECREATED WITH: cwtwb | Donna Coles")]:
        children.append({"type":"text","text":text,"runs":[{"text":text,"font_size":"9"}],"absolute":{"x":x,"y":91800,"w":w,"h":3500}})
    children.append({"type":"text","text":"https://www.workout-wednesday.com/2026w07tab/","runs":[{"text":"https://www.workout-wednesday.com/2026w07tab/","font_size":"9"}],"absolute":{"x":1500,"y":95700,"w":97000,"h":3500}})
    editor.add_dashboard(DASHBOARD, width=1100, height=740, worksheet_names=["Table Calcs","LODs"], layout={"type":"container","direction":"floating","children":children})
    output=HERE/"outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(output,validate=False)
    return output
if __name__ == "__main__":
    print(build())
