"""Build WW42 from raw extracted Hyper using public cwtwb APIs only."""
from datetime import date
from pathlib import Path

import cwtwb
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "Reference Date Range"


def build() -> Path:
    if cwtwb.__version__ not in {"0.29.0a1", "0.29.0a2"}:
        raise RuntimeError("Use an explicitly recorded a1 baseline or a2 candidate SDK source")
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_0vk99460mvko1c1383vmf0pl4zzq.hyper"))
    e.add_calculated_field("Month", "DATE(DATETRUNC('month', [Order Date]))",
                           datatype="date", role="dimension", field_type="quantitative",
                           default_format="*mmm yyyy")
    initial = [date(2020, m, 1) for m in (10, 11, 12)] + [date(2021, m, 1) for m in range(1, 7)]
    e.add_set("Selected Months", "Month", members=initial)
    calculations = [
        ("In Selection", "[Selected Months]", "boolean", "dimension", "nominal"),
        ("Selected Sales", "IF [Selected Months] THEN [Sales] END", "real", "measure", "quantitative"),
        ("Overall Sales", "{FIXED : SUM([Sales])}", "real", "measure", "quantitative"),
        ("Overall Months", "{FIXED : COUNTD([Month])}", "integer", "measure", "quantitative"),
        ("Overall Monthly Average", "[Overall Sales] / [Overall Months]", "real", "measure", "quantitative"),
        ("Selected Total", "{FIXED : SUM([Selected Sales])}", "real", "measure", "quantitative"),
        ("Selected Count", "{FIXED : COUNTD(IF [Selected Months] THEN [Month] END)}", "integer", "measure", "quantitative"),
        ("Selected Monthly Average", "IF [Selected Count] > 0 THEN [Selected Total] / [Selected Count] END", "real", "measure", "quantitative"),
        ("First Month", "{FIXED : MIN(IF [Selected Months] THEN [Month] END)}", "date", "dimension", "quantitative"),
        ("Last Month", "{FIXED : MAX(IF [Selected Months] THEN [Month] END)}", "date", "dimension", "quantitative"),
        ("First Sales", "{FIXED : SUM(IF [Month] = [First Month] THEN [Sales] END)}", "real", "measure", "quantitative"),
        ("Last Sales", "{FIXED : SUM(IF [Month] = [Last Month] THEN [Sales] END)}", "real", "measure", "quantitative"),
        ("Endpoint Change", "IF [First Sales] <> 0 THEN ([Last Sales] - [First Sales]) / [First Sales] END", "real", "measure", "quantitative"),
        ("Zero", "0.0", "real", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, kind in calculations:
        e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=kind)
    for name, formula, direction in [
        ("State Rank", "RANK(SUM([Sales]), 'desc')", "Rows"),
        ("State Share", "SUM([Sales]) / WINDOW_SUM(SUM([Sales]))", "Rows"),
        ("Rank Color", "STR(IF RANK(SUM([Sales]), 'desc') <= 3 THEN RANK(SUM([Sales]), 'desc') ELSE 10 END)", "Rows"),
        ("Selected Peak", "IF SUM([Selected Sales]) = WINDOW_MAX(SUM([Selected Sales])) THEN SUM([Selected Sales]) END", "Columns"),
    ]:
        e.add_calculated_field(name, formula, table_calc=direction,
                               datatype="string" if name == "Rank Color" else "real",
                               field_type="nominal" if name == "Rank Color" else "quantitative")
    e.set_field_geographic_role("State", "state")
    e.set_geocoding_context(country="United States")
    for name in ["Sales", "Selected Sales", "Overall Sales", "Overall Monthly Average", "Selected Total", "Selected Monthly Average", "First Sales", "Last Sales", "Selected Peak"]:
        e.set_field_format(name, 'c"$"#,##0.00')
    for name in ["Endpoint Change", "State Share"]:
        e.set_field_format(name, "p0.0%")
    for name in ["First Month", "Last Month"]:
        e.set_field_format(name, "*mmmm yyyy")

    sheets = ["Overall Summary", "Selected Summary", "Trend", "State Donut", "Top States", "State Map"]
    for sheet in sheets:
        e.add_worksheet(sheet)
    e.configure_chart("Overall Summary", mark_type="Text", columns=[], rows=[],
                      label="MIN(Overall Sales)", label_extra=["MIN(Overall Monthly Average)"],
                      label_runs=[{"text": "ALL MONTHS\n"}, {"field": "MIN(Overall Sales)", "bold": True, "fontsize": 22},
                                  {"text": " total sales\n"}, {"field": "MIN(Overall Monthly Average)", "bold": True}, {"text": " per month"}])
    e.configure_chart("Selected Summary", mark_type="Text", columns=[], rows=[],
                      label="MIN(Selected Total)",
                      label_extra=["MIN(Selected Monthly Average)", "MIN(Endpoint Change)", "MIN(Selected Count)", "MIN(First Month)", "MIN(Last Month)"],
                      label_runs=[{"field": "MIN(Selected Count)", "bold": True}, {"text": " selected months: "},
                                  {"field": "MIN(First Month)"}, {"text": " – "}, {"field": "MIN(Last Month)"},
                                  {"text": "\n"}, {"field": "MIN(Selected Total)", "bold": True, "fontsize": 22},
                                  {"text": " total sales\n"}, {"field": "MIN(Selected Monthly Average)"}, {"text": " per month  |  "},
                                  {"field": "MIN(Endpoint Change)"}, {"text": " first-to-last change"}])
    e.configure_layered_chart("Trend", columns=["EXACTDATE(Month)"],
                         rows=["SUM(Sales)", "SUM(Selected Sales)"], axis_shelf="rows",
                         panes=[
                             {"axis": "SUM(Sales)", "mark_type": "Line", "mark_style": {"mark-color": "#c8c8ce"},
                              "detail_extra": ["EXACTDATE(First Month)", "EXACTDATE(Last Month)"]},
                             {"axis": "SUM(Selected Sales)", "mark_type": "Line", "mark_style": {"mark-color": "#8074a8"},
                              "detail_extra": ["EXACTDATE(First Month)", "EXACTDATE(Last Month)"],
                              "label": "Selected Peak"},
                         ], synchronized=True, fold_axes=True,
                         table_calc_overrides={"Selected Peak": [{"ordering_type": "Field", "order": ["EXACTDATE(Month)"]}]})
    e.add_reference_band("Trend", axis_field="EXACTDATE(Month)",
                         lower_field="EXACTDATE(First Month)", upper_field="EXACTDATE(Last Month)", fill_color="#eeeaf5", pane_index=0)
    for rid in ("refline0", "refline1"):
        e.configure_reference_line_style("Trend", rid, {"line-pattern": "dotted", "stroke-color": "#8074a8"})
    for pane in (0, 1):
        e.configure_custom_tooltip("Trend", [{"field": "Month", "bold": True},
                                            {"text": "\nSales: "}, {"field": "SUM(Sales)"}], pane_index=pane)
    selected = [{"column": "In Selection", "values": [True]}]
    rank_address = {name: [{"ordering_type": "Field", "order": ["State"]}] for name in ["State Rank", "State Share", "Rank Color"]}
    e.configure_layered_chart("State Donut", columns=[], rows=["MIN(Zero)", "MIN(Zero)"],
                         axis_shelf="rows", synchronized=True, fold_axes=True,
                         panes=[
                             {"axis": "MIN(Zero)", "mark_type": "Pie", "detail": "State",
                              "color": "Rank Color", "wedge_size": "SUM(Sales)",
                              "color_map": {"1": "#4b416d", "2": "#8074a8", "3": "#b4a9d0", "10": "#dedbe5"},
                              "mark_style": {"size": "2.0"}},
                             {"axis": "MIN(Zero)", "mark_type": "Circle", "label": "SUM(Sales)",
                              "mark_style": {"size": "1.25", "mark-color": "#ffffff"}},
                         ], filters=selected, table_calc_overrides={"Rank Color": rank_address["Rank Color"]}, hide_axes=True)
    e.configure_chart("Top States", mark_type="Text", columns=[], rows=["State"],
                      label="SUM(Sales)", label_extra=["State Share", "State Rank"],
                      label_runs=[{"field": "State", "bold": True}, {"text": "  "}, {"field": "SUM(Sales)"},
                                  {"text": "  ("}, {"field": "State Share"}, {"text": " of selected total)"}],
                      sort_field="State", sort_descending="SUM(Sales)",
                      filters=selected + [{"column": "State Rank", "min": "1", "max": "3"}],
                      table_calc_overrides={name: rank_address[name] for name in ["State Rank", "State Share"]})
    e.configure_chart("State Map", mark_type="Map", columns=["Longitude (generated)"],
                      rows=["Latitude (generated)"], geographic_field="State", detail="State", color="SUM(Sales)",
                      filters=selected, tooltip=["State", "SUM(Sales)"])
    for sheet in sheets:
        e.configure_worksheet_style(sheet, hide_gridlines=True, hide_zeroline=True,
                                    hide_borders=True, hide_row_field_labels=True, hide_col_field_labels=True,
                                    pane_datalabel_style={"font-family": "Arial", "font-size": "11"})
    e.configure_worksheet_style("Selected Summary", background_color="#eeeaf5")
    e.set_worksheet_title("Trend", "Monthly sales — select marks to replace the reference months")
    e.configure_custom_label("Trend", [{"text": ""}], pane_index=0)
    e.configure_custom_label("Trend", [{"field": "Selected Peak"}], pane_index=1)
    e.configure_worksheet_style("Trend", panes_style={1: {"mark_style": {"mark-labels-show": "false"}}})
    e.configure_custom_label("State Donut", [{"text": ""}], pane_index=0)
    e.configure_custom_label("State Donut", [{"field": "SUM(Sales)", "fontsize": 13}], pane_index=1)
    e.configure_worksheet_style("State Donut", panes_style={2: {"datalabel_style": {"text-align": "center", "vertical-align": "center"}}})
    e.set_worksheet_title("State Donut", "Selected sales by state")
    e.set_worksheet_title("Top States", "Top 3 states • share of all selected sales")
    e.set_worksheet_title("State Map", "Selected months • sales by state")

    def zone(kind, x, y, w, h, **kwargs):
        return {"type": kind, "absolute": {"x": x * 100, "y": y * 125, "w": w * 100, "h": h * 125},
                "style": {"margin": "4", "padding": "2"}, **kwargs}

    e.add_dashboard(DASHBOARD, width=1000, height=800, worksheet_names=sheets,
                    layout={"type": "container", "direction": "floating", "children": [
                        zone("text", 10, 5, 980, 42, text="SUPERSTORE | A reference date range", font_size=23, font_color="#4b416d", bold=True),
                        zone("worksheet", 10, 50, 330, 155, name="Overall Summary", fit="entire", show_title=False),
                        zone("worksheet", 345, 50, 645, 155, name="Selected Summary", fit="entire", show_title=False),
                        zone("worksheet", 10, 210, 980, 265, name="Trend", fit="entire"),
                        zone("worksheet", 10, 480, 270, 265, name="State Donut", fit="entire"),
                        zone("worksheet", 285, 480, 340, 265, name="Top States", fit="entire"),
                        zone("worksheet", 630, 480, 360, 265, name="State Map", fit="entire"),
                        zone("text", 10, 750, 980, 40, text="Drag over monthly marks, or Ctrl-click months. Clearing the selection keeps the reference months.\nWorkout Wednesday 2021 W42 • Lorna Brown & Erica Hughes • Donna Coles analysis", font_size=10),
                    ]})
    e.add_dashboard_set_action(DASHBOARD, "Trend", "Selected Months", event_type="on-select",
                               caption="Replace reference months", clear_option="do-nothing",
                               single_select=False, selection_mode="assign")
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
