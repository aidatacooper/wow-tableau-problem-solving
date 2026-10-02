"""Build the WW05 KPI period-comparison replication with cwtwb."""

from pathlib import Path
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    editor.add_parameter("pToday", datatype="date", default_value="#2025-02-04#", domain_type="any")
    editor.add_calculated_field("Today Last Month", "DATE(DATEADD('month', -1, [pToday]))", datatype="date")
    editor.add_calculated_field("Today Last Year", "DATE(DATEADD('year', -1, [pToday]))", datatype="date")
    editor.add_calculated_field(
        "Recent | Prior  Mth | Prior Yr",
        "IF [Order Date] >= DATEADD('day', -14, [pToday]) AND [Order Date] <= [pToday] THEN 'Recent' "
        "ELSEIF [Order Date] >= DATEADD('day', -14, [Today Last Month]) AND [Order Date] <= DATEADD('day', 14, [Today Last Month]) THEN 'Prior Month' "
        "ELSEIF [Order Date] >= DATEADD('day', -14, [Today Last Year]) AND [Order Date] <= DATEADD('day', 14, [Today Last Year]) THEN 'Prior Year' END",
        datatype="string", role="dimension",
    )
    editor.add_calculated_field("Profit Ratio", "SUM([Profit]) / SUM([Sales])", default_format="p0.0%")
    editor.add_calculated_field("PR - Recent", "IF MIN([Recent | Prior  Mth | Prior Yr]) = 'Recent' THEN [Profit Ratio] END")
    editor.add_calculated_field("PR - Not Recent", "IF MIN([Recent | Prior  Mth | Prior Yr]) <> 'Recent' THEN [Profit Ratio] END")
    editor.add_calculated_field(
        "X-Axis", "CASE [Recent | Prior  Mth | Prior Yr] WHEN 'Recent' THEN DATEDIFF('day',[pToday],[Order Date]) "
        "WHEN 'Prior Month' THEN DATEDIFF('day',[Today Last Month],[Order Date]) "
        "WHEN 'Prior Year' THEN DATEDIFF('day',[Today Last Year],[Order Date]) END",
        datatype="integer", role="dimension", field_type="quantitative",
    )
    editor.add_calculated_field("PR - Today", "{FIXED:SUM(IF [Order Date]=[pToday] THEN [Profit] END)}/{FIXED:SUM(IF [Order Date]=[pToday] THEN [Sales] END)}", default_format="p0.0%")
    editor.add_calculated_field("PR - Yesterday", "{FIXED:SUM(IF [Order Date]=DATEADD('day', -1,[pToday]) THEN [Profit] END)}/{FIXED:SUM(IF [Order Date]=DATEADD('day', -1,[pToday]) THEN [Sales] END)}")
    editor.add_calculated_field("PR Difference", "[PR - Today] - [PR - Yesterday]", default_format="p0.0%")
    editor.add_calculated_field("PR Direction Up", "IF [PR Difference]>=0 THEN 'Up' END", datatype="string", role="dimension")
    editor.add_calculated_field("PR Direction Down", "IF [PR Difference]<0 THEN 'Down' END", datatype="string", role="dimension")

    period_filter = [
        {
            "column": "Recent | Prior  Mth | Prior Yr",
            "values": ["Recent", "Prior Month", "Prior Year"],
        }
    ]
    editor.add_worksheet("Period Trend")
    editor.configure_dual_axis(
        "Period Trend",
        mark_type_1="Line",
        mark_type_2="Line",
        columns=["X-Axis"],
        rows=["PR - Not Recent", "PR - Recent"],
        color_1="Recent | Prior  Mth | Prior Yr",
        color_2="Recent | Prior  Mth | Prior Yr",
        synchronized=True,
        filters=period_filter,
        show_labels=False,
        color_map_1={
            "Recent": "#8e6391",
            "Prior Month": "#76b7b2",
            "Prior Year": "#D0D0D0",
        },
    )
    editor.set_worksheet_caption(
        "Period Trend",
        "Profit ratio aligned by relative day for recent, prior month, and prior year",
    )
    editor.configure_worksheet_style(
        "Period Trend",
        hide_borders=True,
        hide_table_dividers=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_gridlines=False,
        gridline_style={"rows": {"line_visibility": "on"}, "cols": {"line_visibility": "off"}},
        axis_style={"per_field": [{"field": field, "attr": "title", "class": "0", "scope": "rows", "value": ""} for field in ["PR - Recent", "PR - Not Recent"]] + [{"field": "X-Axis", "attr": "display", "class": "0", "scope": "cols", "value": "false"}, {"field": "PR - Recent", "attr": "display", "class": "0", "scope": "rows", "value": "false"}]},
        label_formats=[{"field": "PR - Not Recent", "text-format": "p0.0%"}],
        panes_style={"1": {"mark_style": {"mark-line-pattern": "dashed"}}, "2": {"mark_style": {"mark-markers-mode": "all"}}},
    )

    editor.add_worksheet("KPI Summary")
    editor.configure_chart(
        "KPI Summary",
        mark_type="Text",
        label="AVG(PR - Today)",
        label_extra=[
            "AVG(PR Difference)",
            "PR Direction Up",
            "PR Direction Down",
        ],
        label_runs=[
            {"field": "AVG(PR - Today)", "fontsize": 18, "bold": True, "fontcolor": "#000000"},
            {"text": "\n"},
            {"field": "PR Direction Up", "fontsize": 12, "fontcolor": "#499a9a"},
            {"field": "PR Direction Down", "fontsize": 12, "fontcolor": "#e15759"},
            {"text": " by ", "fontsize": 12},
            {"field": "AVG(PR Difference)", "fontsize": 12},
            {"text": " vs. Prior Day", "fontsize": 12},
        ],
    )
    editor.set_worksheet_caption(
        "KPI Summary",
        "Latest profit ratio and change from the previous day",
    )
    editor.configure_worksheet_style(
        "KPI Summary",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        hide_table_dividers=True,
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
    )

    editor.set_worksheet_rich_title("KPI Summary", runs=[{"text": "Profit Ratio", "fontsize": 12, "bold": True, "fontcolor": "#000000"}, {"text": " on <[Parameters].[pToday]>", "fontsize": 10}])
    def text(text, x, y, w, h, size=8, color="#000000", alignment="0", bold=False, hyperlink=None):
        run={"text": text, "font_size": str(size), "font_color": color, "font_alignment": alignment, "bold": bold}
        if hyperlink: run["hyperlink"]=hyperlink
        return {"type": "text", "runs": [run], "absolute": {"x": x, "y": y, "w": w, "h": h}}
    layout={"type": "container", "direction": "floating", "children": [
        text("KPI Trend Monitor With Period\nComparison", 2000, 1333, 96000, 13000, 14, bold=True),
        {"type": "worksheet", "name": "KPI Summary", "show_title": True, "fit": "entire", "absolute": {"x": 2000, "y": 14333, "w": 96000, "h": 24000}},
        {"type": "worksheet", "name": "Period Trend", "show_title": False, "fit": "entire", "absolute": {"x": 2000, "y": 38333, "w": 96000, "h": 44834}},
        {"type": "color", "mode": "horz", "worksheet": "Period Trend", "field": "Recent | Prior  Mth | Prior Yr", "show_title": False, "absolute": {"x": 2000, "y": 83167, "w": 96000, "h": 5333}},
        text("CHALLENGE BY:\nYoshi Arakawa", 2000, 88500, 32000, 5834, color="#8175aa"),
        text("#WOW2026\nWEEK 5", 34000, 88500, 32000, 5834, color="#8175aa", alignment="1"),
        text("RECREATED BY:\nDonna Coles", 66000, 88500, 32000, 5834, color="#8175aa", alignment="2"),
        text("https://www.workout-wednesday.com/2026w5tab/", 2000, 94334, 96000, 4333, alignment="1", hyperlink="https://www.workout-wednesday.com/2026w5tab/"),
    ]}
    editor.add_dashboard(
        "KPI Trend Monitor",
        width=400,
        height=600,
        layout=layout,
        worksheet_names=["KPI Summary", "Period Trend"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("2026-02-09-ww05-kpi-period-comparison-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
