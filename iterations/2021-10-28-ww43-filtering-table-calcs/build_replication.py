"""Independent WW43 construction from packaged data and public cwtwb APIs."""
from pathlib import Path

import cwtwb
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/replicated-workbook.twbx"


def build() -> Path:
    if cwtwb.__version__ != "0.29.0a1":
        raise RuntimeError(f"Baseline requires cwtwb 0.29.0a1; got {cwtwb.__version__}")
    OUTPUT.parent.mkdir(exist_ok=True)
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/federated_0dg8n3q1ypgh2719qo5qk1.hyper"))
    for name in ("pMinDate", "pMaxDate"):
        e.add_parameter(name, datatype="date", default_value="#1900-01-01#", domain_type="any")
    e.add_calculated_field("Order Date Month", "DATE(DATETRUNC('month',[Order Date]))",
                           datatype="date", role="dimension", field_type="quantitative")
    for prefix, aggregate in (("Min", "MIN"), ("Max", "MAX")):
        e.add_calculated_field(f"{prefix} Date Selected",
            f"IF [p{prefix}Date]=#1900-01-01# THEN {{FIXED : {aggregate}([Order Date Month])}} "
            f"ELSE [p{prefix}Date] END", datatype="date", role="dimension", field_type="ordinal")
    e.add_calculated_field("Is Month Selected?",
        "[Order Date Month]>=[Min Date Selected] AND [Order Date Month]<=[Max Date Selected]",
        datatype="boolean", role="dimension", field_type="nominal")
    e.add_calculated_field("Visible Month", "LOOKUP(MIN([Is Month Selected?]),0)",
        datatype="boolean", role="measure", field_type="nominal", table_calc="Rows")
    e.add_calculated_field("Rolling Average", "WINDOW_AVG(SUM([Sales]),-2,0)", table_calc="Rows")
    e.add_calculated_field("No. Months", "DATEDIFF('month',[Min Date Selected],[Max Date Selected])+1",
        datatype="integer", role="dimension", field_type="ordinal")
    e.add_calculated_field("Avg Monthly Sales", "SUM([Sales])/MIN([No. Months])")
    for field in ("Sales", "Rolling Average", "Avg Monthly Sales"):
        e.set_field_format(field, 'c"$"#,##0.00')

    e.add_worksheet("Trend")
    # One chronological partition: only month is on the view. Sub-category is
    # an ordinary action filter, never a partitioning dimension or date filter.
    addressing = [{"ordering_type": "Field", "order": ["EXACTDATE(Order Date Month)"]}]
    e.configure_dual_axis("Trend", mark_type_1="Area", mark_type_2="Line",
        columns=["EXACTDATE(Order Date Month)"], rows=["SUM(Sales)", "Rolling Average"],
        synchronized=True, show_labels=False, mark_color_1="#82b3d3", mark_color_2="#184e77",
        filters=[{"column": "Visible Month", "values": [True]}],
        table_calc_overrides={"Rolling Average": addressing, "Visible Month": addressing})
    e.configure_custom_tooltip("Trend", [{"text": "Month: "}, {"field": "EXACTDATE(Order Date Month)"},
        {"text": "\nSales: "}, {"field": "SUM(Sales)"},
        {"text": "\n3-month rolling average: "}, {"field": "Rolling Average"}])
    e.configure_worksheet_style("Trend", hide_gridlines=True, hide_zeroline=True,
        panes_style={"1": {"mark_style": {"mark-color": "#82b3d3", "mark-transparency": "50"}}})
    e.set_worksheet_title("Trend", "Monthly sales and 3-month rolling average")

    e.add_worksheet("Bars")
    e.configure_layered_chart("Bars", rows=["Sub-Category"],
        columns=["SUM(Sales)", "Avg Monthly Sales"], axis_shelf="columns",
        fold_axes=False, synchronized=False, sort_descending="SUM(Sales)", sort_field="Sub-Category",
        filters=[{"column": "Is Month Selected?", "values": [True]}],
        panes=[{"axis": "SUM(Sales)", "mark_type": "Bar", "mark_color": "#82b3d3",
                "label": "SUM(Sales)", "tooltip": ["Sub-Category", "SUM(Sales)"]},
               {"axis": "Avg Monthly Sales", "mark_type": "Bar", "mark_color": "#184e77",
                "label": "Avg Monthly Sales", "tooltip": ["Sub-Category", "Avg Monthly Sales"]}])
    e.configure_worksheet_style("Bars", hide_gridlines=True, hide_zeroline=True)
    e.set_worksheet_title("Bars", "Sales and average monthly sales by sub-category")
    dashboard = "Filtering Table Calcs"
    e.add_dashboard(dashboard, width=800, height=1000, worksheet_names=["Trend", "Bars"],
        layout={"type": "container", "direction": "vertical", "children": [
            {"type": "text", "text": "FILTERING TABLE CALCS", "font_size": "24", "bold": True, "fixed_size": 55},
            {"type": "text", "text": "Drag across months to zoom. Select a sub-category to filter the trend.\nClear selections to reset.", "fixed_size": 55},
            {"type": "worksheet", "name": "Trend", "weight": 4},
            {"type": "worksheet", "name": "Bars", "weight": 6},
            {"type": "text", "text": "Workout Wednesday 2021 · Week 43 | Sean Miller · Donna Coles", "fixed_size": 25}]})
    e.add_dashboard_action(dashboard, "filter", source_sheet="Bars", target_sheet="Trend",
        fields=["Sub-Category"], event_type="on-select", caption="Filter trend by sub-category")
    for prefix, aggregate in (("Min", "MIN"), ("Max", "MAX")):
        e.add_dashboard_action(dashboard, "parameter", source_sheet="Trend",
            source_field="EXACTDATE(Order Date Month)", target_parameter=f"p{prefix}Date", aggregation=aggregate.lower(),
            clear_behavior="set-value", clear_value="d:1900-01-01", caption=f"Select {prefix.lower()} month")
    e.set_active_dashboard(dashboard)
    e.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
