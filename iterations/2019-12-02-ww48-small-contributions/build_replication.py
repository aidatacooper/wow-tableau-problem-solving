"""Independent WW48 reconstruction; extracted data and public SDK only."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
DASHBOARD = "2019_11_27_WW48_Sales_by_State"

def build(output_path):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_parameter("Threshold Percent", datatype="real", default_value="0.03", domain_type="any", default_format="p0.00%")
    calculations = [
        ("Total Sales", "{FIXED:SUM([Sales])}", "real", "measure", "quantitative"),
        ("State Contribution", "{FIXED [State]:SUM([Sales])} / [Total Sales]", "real", "measure", "quantitative"),
        ("% Sales Per State", "[Sales] / [Total Sales]", "real", "measure", "quantitative"),
        ("State Grouping", "IF [State Contribution] >= [Threshold Percent] THEN [State] ELSE 'All Other States' END", "string", "dimension", "nominal"),
        ("State Order", "IF [State Grouping] = 'All Other States' THEN 1 ELSE 0 END", "integer", "dimension", "ordinal"),
        ("Label: State", "IF [State Order] = 0 THEN [State] END", "string", "dimension", "nominal"),
        ("Label: Other States", "IF [State Order] = 1 THEN 'All Other States' END", "string", "dimension", "nominal"),
        ("Zero", "0", "real", "measure", "quantitative"),
        ("Threshold Line", "[Threshold Percent]", "real", "measure", "quantitative"),
    ]
    for name, formula, dtype, role, kind in calculations:
        editor.add_calculated_field(name, formula, datatype=dtype, role=role, field_type=kind, default_format="p0.00%" if dtype == "real" else "")
    for name, condition in [("Count States Listed", 0), ("Count States Grouped", 1)]:
        editor.add_calculated_field(name, f"WINDOW_SUM(IF ATTR([State Order]) = {condition} THEN COUNTD([State]) ELSE 0 END)", datatype="integer", table_calc="Rows")
    editor.add_worksheet("Viz")
    editor.configure_layered_chart("Viz", columns=["SUM(% Sales Per State)", "MIN(Zero)"], rows=["State Order", "State Grouping"], axis_shelf="columns", synchronized=True, hide_axes=False, sort_descending="SUM(% Sales Per State)", table_calc_overrides={f"AGG({name})": [{"ordering_type": "Field", "order": ["State Order", "State Grouping"]}] for name in ["Count States Listed", "Count States Grouped"]},
        panes=[
            {"axis": "SUM(% Sales Per State)", "mark_type": "Bar", "color": "State Order", "color_map": {"0": "#28a1a7", "1": "#bab0ac"}, "detail": "AGG(Count States Listed)", "tooltip": ["Label: State", "Label: Other States", "SUM(% Sales Per State)"], "mark_style": {"size": "0.43878454", "mark-labels-show": "false"}},
            {"axis": "MIN(Zero)", "mark_type": "GanttBar", "color": "State Order", "color_map": {"0": "#28a1a7", "1": "#bab0ac"}, "detail": "AGG(Count States Grouped)", "labels": ["State Grouping", "SUM(% Sales Per State)"], "label_runs": [{"field": "State Grouping", "fontsize": 8}, {"field": "SUM(% Sales Per State)", "prefix": " ", "fontsize": 8, "bold": True}], "mark_style": {"mark-transparency": "0", "mark-labels-show": "true"}},
        ])
    editor.configure_worksheet_style("Viz", hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_table_dividers=True, hide_row_field_labels=True, label_formats=[{"field": "State Order", "display": "false"}, {"field": "State Grouping", "display": "false"}], axis_style={"per_field": [{"field": "SUM(% Sales Per State)", "attr": "display", "scope": "cols", "class": "0", "value": "true"}, {"field": "MIN(Zero)", "attr": "display", "scope": "cols", "class": "0", "value": "false"}, {"field": "SUM(% Sales Per State)", "attr": "title", "scope": "cols", "class": "0", "value": "PERCENT OF SALES"}]}, cell_formats=[{"field": "State Grouping", "height": 58}], panes_style={"2": {"cell_style": {"vertical-align": "top", "text-align": "right"}, "datalabel_style": {"color-mode": "match", "font-weight": "bold"}}})
    editor.add_reference_line("Viz", axis_field="SUM(% Sales Per State)", value_field="AVG(Threshold Line)", scope="per-table", label_type="value", pane_index=0)
    editor.set_worksheet_rich_title("Viz", runs=[{"text": "Contribution of Sales By State\n", "fontsize": 15}, {"text": "<AGG(Count States Listed)> states contribute to <[Parameters].[Threshold Percent]> or more of Total Sales", "fontsize": 9, "bold": True, "fontcolor": "#28a1a7"}, {"text": " | "}, {"text": "<AGG(Count States Grouped)> contribute less", "fontsize": 9, "bold": True, "fontcolor": "#bab0ac"}])
    editor.add_dashboard(DASHBOARD, width=1100, height=900, worksheet_names=["Viz"], layout={"type": "container", "direction": "floating", "children": [
        {"type": "worksheet", "name": "Viz", "show_title": True, "fit": "entire", "absolute": {"x": 727, "y": 889, "w": 75546, "h": 90111}},
        {"type": "paramctrl", "parameter": "Threshold Percent", "caption": "Group States Contributing Less Than", "mode": "type_in", "absolute": {"x": 76273, "y": 889, "w": 23000, "h": 6222}},
        {"type": "text", "text": "DESIGNED BY : ANN JACKSON     #WORKOUTWEDNESDAY | 2019 | WEEK 48     RECREATED BY : DONNA COLES", "runs": [{"text": "DESIGNED BY : ANN JACKSON     #WORKOUTWEDNESDAY | 2019 | WEEK 48     RECREATED BY : DONNA COLES", "font_size": "8", "font_color": "#28a1a7"}], "absolute": {"x": 727, "y": 91000, "w": 98546, "h": 3778}},
        {"type": "text", "text": "workout-wednesday.com | Week 48: Automatically combine small contributions", "absolute": {"x": 727, "y": 94778, "w": 98546, "h": 4333}},
    ]})
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return Path(output_path)

if __name__ == "__main__":
    print(build(HERE / "outputs/replicated-workbook.twbx"))
