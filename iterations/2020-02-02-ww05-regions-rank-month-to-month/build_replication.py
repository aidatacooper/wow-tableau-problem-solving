"""Advanced region bump chart, authored from extracted data and public APIs."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_01_29_WW05_Rank_Bump_Chart - Advanced"
SHEET = "Viz - Advanced"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    editor.add_parameter("Offset", "real", "0.4")
    fields = [
        ("COLOUR:Region (Line)", "[Region]", "string", None),
        ("COLOUR:Region (Block)", "[Region]", "string", None),
        ("Rank", "RANK(SUM([Sales]))", "real", "Rows"),
        ("Rank Line", "[Rank]+[Offset]", "real", "Rows"),
        ("LABEL:Rank", "CASE [Rank] WHEN 1 THEN '1st' WHEN 2 THEN '2nd' WHEN 3 THEN '3rd' WHEN 4 THEN '4th' END", "string", "Rows"),
        ("LABEL To Display", "CASE MIN(MONTH([Order Date])) WHEN 1 THEN [LABEL:Rank] WHEN 12 THEN ATTR([Region]) END", "string", "Rows"),
        ("size", "0.9", "real", None),
    ]
    for name, formula, datatype, tc in fields:
        editor.add_calculated_field(name, formula, datatype=datatype, table_calc=tc)
    editor.set_field_format("Order Date", "*mmm")
    editor.add_worksheet(SHEET)
    address = {"ordering_type": "Field", "ordering_field": "COLOUR:Region (Line)"}
    overrides = {
        "Rank": [{"ordering_type": "Field", "ordering_field": "COLOUR:Region (Block)"}],
        "Rank Line": [address, {"field": "Rank", **address}],
        "LABEL To Display": [{"ordering_type": "Rows"}, {"field": "LABEL:Rank", **address}, {"field": "Rank", **address}],
    }
    regions = ["West", "Central", "South", "East"]
    editor.configure_layered_chart(SHEET, columns=["MONTH(Order Date)"], rows=["Rank Line", "Rank"], axis_shelf="rows", hide_axes=True, table_calc_overrides=overrides, panes=[
        {"axis": "Rank Line", "mark_type": "Line", "color": "COLOUR:Region (Line)", "color_map": dict(zip(regions, ["#004500", "#5557eb", "#8db1f9", "#d81159"])), "label": "LABEL To Display", "mark_style": {"size": "1.0", "mark-labels-show": "true", "mark-labels-cull": "false"}},
        {"axis": "Rank", "mark_type": "GanttBar", "color": "COLOUR:Region (Block)", "size": "MIN(size)", "color_map": dict(zip(regions, ["#7b9f7b", "#a7a8f5", "#bcd1fb", "#eb84a9"])), "mark_sizing_off": True, "mark_style": {"size": "1.824088454246521"}},
    ])
    editor.configure_worksheet_style(SHEET, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_table_dividers=True, hide_row_field_labels=True, hide_col_field_labels=True, disable_tooltip=True, hide_sort_controls=True, panes_style={1: {"cell_style": {"text-align": "center", "vertical-align": "center"}, "datalabel_style": {"color-mode": "user", "color": "#ffffff", "font-weight": "bold", "font-family": "Tableau Medium", "font-size": "8"}}}, label_formats=[{"field": "MONTH(Order Date)", "text-format": "iLLL", "text-orientation": "0", "font-size": "8", "font-family": "Tableau Medium"}], axis_style={"render-fold-reversed": "true", "encodings": [{"field": f, "scope": "rows", "type": "space", "attr": "space", "class": "0", "field-type": "quantitative", "range-type": "fixed", "min": 0.9, "max": 4.9, "reverse": "true", **({"fold": "true", "synchronized": "true"} if i else {})} for i, f in enumerate(["Rank Line", "Rank"]) ]})
    def rect(x, y, w, h):
        return {"x": round(x/700*100000), "y": round(y/350*100000), "w": round(w/700*100000), "h": round(h/350*100000)}
    def text_zone(text, x, y, w, h, *, size=8, color="#333333", bold=False, align="center"):
        return {"type": "text", "runs": [{"text": text, "font_size": size, "font_color": color, "bold": bold, "font_alignment": {"left":"0","center":"1","right":"2"}[align]}], "absolute": rect(x,y,w,h)}
    zones = [
        {"type": "text", "runs": [{"text": "WEEK 5 : ", "font_size": 12, "font_color": "#333333", "bold": True}, {"text": "WHERE DO REGIONS RANK MONTH TO MONTH?", "font_size": 12, "font_color": "#333333"}], "absolute": rect(15,16,670,30)},
        {"type": "worksheet", "name": SHEET, "show_title": False, "fit": "entire", "absolute": rect(15,55,670,237)},
        text_zone("DESIGNED BY : LUKE STANKE",15,298,220,24,color="#eb84a9",bold=True,align="left"),
        text_zone("#WOW2020 | WEEK 5",235,298,230,24,color="#eb84a9",bold=True),
        text_zone("RECREATED WITH CWTWB",465,298,220,24,color="#eb84a9",bold=True,align="right"),
        text_zone("http://www.workout-wednesday.com/2020w05/",100,324,500,22,size=8,color="#006080"),
    ]
    editor.add_dashboard(DASHBOARD, width=700, height=350, worksheet_names=[SHEET], layout={"type": "container", "direction": "floating", "children": zones})
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
