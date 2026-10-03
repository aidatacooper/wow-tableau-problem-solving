"""Rebuild the two-sheet single-click sorting dashboard from extracted data."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_01_01_WW01_One_Click_Sort v2"
CHOICES = [" Sales ", " Sales / Order ", " Profit Ratio "]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    editor.add_parameter("Sort (copy)", "string", " Sales ", domain_type="any")
    calculations = [
        ("Sales / Order", "SUM([Sales])/COUNTD([Order ID])", "real", "measure"),
        ("Profit Ratio", "SUM([Profit])/SUM([Sales])", "real", "measure"),
        ("Negative Profit", "[Profit Ratio] < 0", "boolean", "measure"),
        ("Sort By", "IF [Sort (copy)] = ' Sales ' THEN SUM([Sales]) ELSEIF [Sort (copy)] = ' Sales / Order ' THEN [Sales / Order] ELSEIF [Sort (copy)] = ' Profit Ratio ' THEN [Profit Ratio] END", "real", "measure"),
        ("Text Position", "MIN(0)", "real", "measure"),
        ("Zero", "0", "integer", "measure"),
        ("True", "TRUE", "boolean", "dimension"),
        ("False", "FALSE", "boolean", "dimension"),
    ]
    for name, formula, datatype, role in calculations:
        editor.add_calculated_field(name, formula, datatype=datatype, role=role)
    editor.set_field_format("Sales / Order", 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Profit Ratio", "p0%")
    for name in ["Header v2", "Table v2"]:
        editor.add_worksheet(name)
    header_panes = []
    for index, choice in enumerate(CHOICES):
        editor.add_calculated_field(choice, "MIN(0)", datatype="real")
        editor.add_calculated_field(f"Selected {index}", f"[Sort (copy)] = '{choice}'", datatype="boolean", role="dimension")
        editor.add_calculated_field(f"Arrow {index}", f"IF [Sort (copy)] = '{choice}' THEN '▼' ELSE '' END", datatype="string", role="dimension")
        header_panes.append({"axis": f"[{choice}]", "mark_type": "Text", "color": f"Selected {index}", "color_map": {"true": "#1b1b1b", "false": "#6e6e6e"}, "labels": ["Measure Names", f"Arrow {index}"], "detail_extra": ["True", "False"], "label_runs": [{"text": choice.strip()}, {"text": "\n"}, {"field": f"Arrow {index}"}], "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"}})
    editor.configure_layered_chart("Header v2", columns=[f"[{choice}]" for choice in CHOICES], panes=header_panes, axis_shelf="columns", fold_axes=False)
    colors = {"true": "#d81159", "false": "#cccccc"}
    editor.configure_layered_chart("Table v2", columns=["SUM(Sales)", "Text Position", "Profit Ratio"], rows=["Sub-Category"], axis_shelf="columns", fold_axes=False, sort_descending="Sort By", sort_field="Sub-Category", panes=[
        {"axis": "SUM(Sales)", "mark_type": "Bar", "color": "Negative Profit", "color_map": colors, "label": "SUM(Sales)", "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"}},
        {"axis": "Text Position", "mark_type": "GanttBar", "label": "Sales / Order", "mark_style": {"size": "0.001", "mark-transparency": "0", "mark-labels-show": "true", "mark-labels-cull": "false"}},
        {"axis": "Profit Ratio", "mark_type": "Bar", "color": "Negative Profit", "color_map": colors, "label": "Profit Ratio", "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"}},
    ])
    for sheet in ["Header v2", "Table v2"]:
        editor.configure_worksheet_style(sheet, background_color="#ebebeb", hide_axes=True, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_table_dividers=True, hide_col_field_labels=True, hide_row_field_labels=True, disable_tooltip=True, hide_sort_controls=True, pane_datalabel_style={"font-family": "Tableau Light", "font-size": "10", **({"color": "#1b1b1b"} if sheet == "Table v2" else {})}, label_formats=[{"field": "Sub-Category", "font-size": "10", "font-family": "Tableau Light", "color": "#1b1b1b"}] if sheet == "Table v2" else None)
    editor.configure_worksheet_style("Header v2", pane_cell_style={"text-align": "center", "vertical-align": "center"})
    editor.configure_worksheet_style("Table v2", header_formats=[{"field": "Sub-Category", "width": "110"}], panes_style={"2": {"cell_style": {"text-align": "left", "vertical-align": "center"}}}, axis_style={"encodings": [{"field": "SUM(Sales)", "scope": "cols", "type": "space", "attr": "space", "class": "0", "field-type": "quantitative", "range-type": "fixed", "min": 0, "max": 534651.6722426825}, {"field": "Text Position", "scope": "cols", "type": "space", "attr": "space", "class": "0", "field-type": "quantitative", "range-type": "fixed", "min": -1, "max": 1}]})
    editor.add_reference_line("Table v2", axis_field="Profit Ratio", value_field="MIN(Zero)", label_type="none", tooltip="", pane_index=2)
    editor.configure_reference_line_style("Table v2", "refline0", {"stroke-color": "#6e6e6e", "stroke-size": "1", "line-visibility": "on"})
    def absolute(x, y, w, h):
        return {"x": round(x / 700 * 100000), "y": round(y / 900 * 100000), "w": round(w / 700 * 100000), "h": round(h / 900 * 100000)}
    zones = [
        {"type": "text", "text": "WEEK ONE : CAN YOU SORT DIMENSIONS WITH A SINGLE CLICK?", "runs": [{"text": "WEEK ONE : CAN YOU SORT DIMENSIONS WITH A SINGLE CLICK?", "font_size": "12", "font_color": "#333333"}], "absolute": absolute(8, 8, 684, 42)},
        {"type": "empty", "style": {"background-color": "#d81159", "margin": "0"}, "absolute": absolute(50, 47, 600, 4)},
        {"type": "worksheet", "name": "Header v2", "show_title": False, "fit": "entire", "absolute": absolute(160, 51, 490, 100)},
        {"type": "worksheet", "name": "Table v2", "show_title": False, "fit": "entire", "absolute": absolute(50, 151, 600, 529)},
        {"type": "text", "text": "DESIGNED BY : LUKE STANKE     #WOW2020 | WEEK 1     RECREATED WITH CWTWB", "runs": [{"text": "DESIGNED BY : LUKE STANKE     #WOW2020 | WEEK 1     RECREATED WITH CWTWB", "font_size": "8", "font_color": "#d81159", "font_alignment": "1"}], "absolute": absolute(50, 680, 600, 30)},
        {"type": "text", "text": "https://www.workout-wednesday.com/2020w01/", "absolute": absolute(50, 710, 600, 25)},
    ]
    editor.add_dashboard(DASHBOARD, width=700, height=900, worksheet_names=["Header v2", "Table v2"], layout={"type": "container", "direction": "floating", "style": {"background-color": "#ffffff"}, "children": zones})
    editor.add_dashboard_action(DASHBOARD, "parameter", source_sheet="Header v2", source_field="Measure Names", target_parameter="Sort (copy)", event_type="on-select", caption="Choose sort measure", clear_behavior="keep-current")
    editor.add_dashboard_action(DASHBOARD, "filter", source_sheet="Header v2", target_sheet="Header v2", field_mappings={"True": "False"}, event_type="on-select", caption="Deselect header", clear_behavior="show-all")
    editor.set_active_dashboard(DASHBOARD)
    output_path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    print(build())
