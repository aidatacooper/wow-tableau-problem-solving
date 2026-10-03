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
    editor.add_dashboard(DASHBOARD, width=700, height=350, worksheet_names=[SHEET], layout={"type": "container", "direction": "floating", "children": [
        {"type": "text", "text": "WEEK 5: WHERE DO REGIONS RANK MONTH TO MONTH?", "runs": [{"text": "WEEK 5: WHERE DO REGIONS RANK MONTH TO MONTH?", "font_size": "12", "font_color": "#333333"}], "absolute": {"x": 1143, "y": 2286, "w": 97714, "h": 11429}},
        {"type": "worksheet", "name": SHEET, "show_title": False, "fit": "entire", "absolute": {"x": 1143, "y": 15143, "w": 97714, "h": 68000}},
        {"type": "text", "text": "DESIGNED BY: LUKE STANKE      #WOW2020 WEEK 5      RECREATED WITH CWTWB", "runs": [{"text": "DESIGNED BY: LUKE STANKE      #WOW2020 WEEK 5      RECREATED WITH CWTWB", "font_size": "8", "font_color": "#eb84a9"}], "absolute": {"x": 1143, "y": 85714, "w": 97714, "h": 6286}},
        {"type": "text", "text": "https://www.workout-wednesday.com/2020w05/", "absolute": {"x": 1143, "y": 94286, "w": 97714, "h": 5000}},
    ]})
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
