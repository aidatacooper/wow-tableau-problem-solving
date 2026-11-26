"""Build WW2024/13 from extracted Hyper and public cwtwb APIs only."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent

def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/federated_1l2jyeb12pijk613twqta1.hyper"))
    e.add_calculated_field("Year", "YEAR([Order Date])", datatype="integer", role="dimension", field_type="ordinal")
    e.add_calculated_field("Total Row", "MIN(1.5)")
    e.add_calculated_field("Segment Row", "MIN(0.5)")
    e.add_calculated_field("Cumulative Sales", "RUNNING_SUM(SUM([Sales]))", table_calc="Rows")
    e.add_calculated_field("Year Share", "SUM([Sales])/WINDOW_SUM(SUM([Sales]))", table_calc="Rows")
    e.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Cumulative Sales", 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Year Share", "p0.0%")
    e.set_field_format("Year", "0")
    e.add_worksheet("Segmented Sales")
    common = {
        "mark_type": "Bar", "size": "SUM(Sales)",
        "mark_sizing": {"mark-sizing-setting": "marks-scaling-on", "mark-alignment": "mark-alignment-right", "use-custom-mark-size": False, "custom-mark-size-in-axis-units": 1.0},
        "mark_style": {"size": "0.94", "mark-color": "#dec7b6", "mark-transparency": "255", "has-stroke": "true", "stroke-color": "#ffffff"},
    }
    e.configure_layered_chart("Segmented Sales", rows=["Sub-Category", "AGG(Total Row)", "AGG(Segment Row)"],
        columns=["AGG(Cumulative Sales)"], axis_shelf="rows", synchronized=True, fold_axes=True, hide_axes=True,
        sort_descending="SUM(Sales)", panes=[
            dict(common, axis="AGG(Total Row)", tooltip=["SUM(Sales)"]),
            dict(common, axis="AGG(Segment Row)", detail="Year", tooltip=["SUM(Sales)", "AGG(Year Share)"]),
        ], table_calc_overrides={"AGG(" + name + ")": [{"ordering_type": "Field", "order": ["Year"]}] for name in ("Cumulative Sales", "Year Share")})
    e.configure_custom_tooltip("Segmented Sales", [
        {"field": "Sub-Category", "bold": True, "fontcolor": "#9d7660"},
        {"text": "\nTotal Sales: "}, {"field": "SUM(Sales)", "bold": True},
    ], pane_index=0)
    e.configure_custom_tooltip("Segmented Sales", [
        {"field": "Sub-Category", "bold": True}, {"text": " | "}, {"field": "Year", "bold": True},
        {"text": "\nSales: "}, {"field": "SUM(Sales)", "bold": True}, {"text": " ("}, {"field": "AGG(Year Share)"}, {"text": ")"},
    ], pane_index=1)
    e.configure_worksheet_style("Segmented Sales", background_color="#fefaf1", hide_gridlines=True, hide_zeroline=True,
        hide_borders=True, hide_table_dividers=True, hide_col_field_labels=True, hide_row_field_labels=True,
        label_formats=[{"field": "Sub-Category", "text-align": "right", "vertical-align": "top", "color": "#9d7660", "font-weight": "bold"}],
        header_formats=[{"field": "Sub-Category", "attr": "width", "value": "150"}],
        axis_style={"encodings": [{"field": "AGG(Total Row)", "attr": "space", "class": "0", "field-type": "quantitative", "min": -0.3, "max": 1.5, "range-type": "fixed", "scope": "rows", "type": "space"}],
                    "per_field": [{"field": "AGG(Cumulative Sales)", "attr": "display", "scope": "cols", "value": "false"}]})
    e.add_dashboard("Segmented Bar Chart", width=1000, height=800, layout={
        "type": "container", "direction": "vertical", "children": [
            {"type": "text", "text": "Sales by Sub-Category", "fixed_size": 45, "style": {"background-color": "#fefaf1"}},
            {"type": "worksheet", "name": "Segmented Sales", "fit": "entire", "show_title": False, "style": {"margin": "0"}},
            {"type": "text", "text": "Total sales above | yearly segments below | #WOW2024 Week 13", "fixed_size": 28, "style": {"background-color": "#fefaf1"}},
        ]})
    e.set_active_dashboard("Segmented Bar Chart")
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output), validate=False)
    return output
if __name__ == "__main__": print(build())
