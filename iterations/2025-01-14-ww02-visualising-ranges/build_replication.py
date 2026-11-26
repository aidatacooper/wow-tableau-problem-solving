"""Build the single-sheet hourly glucose ranges from extracted Hyper inputs."""
import json
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
RANGES = ["Minimum", "5th Percentile", "25th Percentile", "75th Percentile", "95th Percentile", "Maximum"]
COLORS = ["#ffffff", "#d2e1f3", "#a9c1df", "#7a93b9", "#a9c1df", "#d2e1f3"]

def build():
    OUTPUT.parent.mkdir(exist_ok=True)
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / "WoW2024Wk49.hyper"))
    for name, formula in [("Minimum", "MIN([Glucose mg/dL])"), ("Maximum", "MAX([Glucose mg/dL])"), ("Median", "PERCENTILE([Glucose mg/dL],0.5)")] + [(f"{n}th Percentile", f"PERCENTILE([Glucose mg/dL],{n/100})") for n in [5,25,75,95]]:
        e.add_calculated_field(name, formula, datatype="real", role="measure", field_type="quantitative", default_format="n0.0")
    e.add_calculated_field("Hour", "DATEPART('hour',[Device Timestamp])", datatype="integer", role="dimension", field_type="quantitative")
    for n in [80,180]:
        e.add_calculated_field(f"Normal {n}", str(n), datatype="integer", role="measure", field_type="quantitative")
    e.add_worksheet("Glucose ranges")
    e.configure_layered_chart("Glucose ranges", columns=["Hour"], rows=["Median", "Multiple Values"], panes=[
        {"axis":"Median", "mark_type":"Line", "breakdown":"off", "tooltip":["Median"], "mark_style":{"mark-color":"#000000", "mark-line-pattern":"dashed", "size":"0.5"}},
        {"axis":"Multiple Values", "mark_type":"Area", "breakdown":"off", "color":"Measure Names", "label":"Measure Names", "measure_values":RANGES, "mark_style":{"mark-transparency":"255", "has-stroke":"false", "mark-labels-show":"true", "mark-labels-cull":"false"}}
    ], synchronized=True)
    e.set_datasource_color_palette("Measure Names", {json.dumps(e.field_registry.resolve_full_reference(e.field_registry.parse_expression(n).instance_name)):c for n,c in zip(RANGES,COLORS)}, is_measure_names=True)
    e.configure_worksheet_style("Glucose ranges", hide_gridlines=True, hide_zeroline=True, hide_table_dividers=True,
        axis_style={"render-fold-reversed":"true", "encodings":[{"field":"Hour", "scope":"cols", "class":"0", "min":"0", "max":"26", "range-type":"fixed", "major-origin":"0", "major-spacing":"3"}], "per_field":[
            {"field":"Hour", "attr":"title", "value":"Hour of day", "scope":"cols", "class":"0"},
            {"field":"Median", "attr":"title", "value":"mg/dL", "scope":"rows", "class":"0"},
            {"field":"Multiple Values", "attr":"display", "value":"false", "scope":"rows", "class":"0"}]},
        pane_cell_style={"text-align":"right", "vertical-align":"center"}, pane_datalabel_style={"font-size":"9"})
    for n in [80,180]:
        msg=e.add_reference_line("Glucose ranges", axis_field="Median", value_field=f"AVG(Normal {n})", formula="average", scope="per-table", label_type="value", probability=None, pane_index=0)
        e.configure_reference_line_style("Glucose ranges",msg.split("'")[1],{"line-visibility":"on", "line-pattern-only":"dotted", "stroke-size":"3", "stroke-color":"#f28e2b", "fill-above":"#00000000", "fill-below":"#00000000"})
    e.set_worksheet_title("Glucose ranges", "14-day Glucose Trends\nHourly median and percentile ranges | Normal range: 80–180 mg/dL")
    e.add_dashboard("Visualizing Ranges",width=1300,height=600,worksheet_names=["Glucose ranges"],layout={"type":"container","direction":"vertical","children":[{"type":"worksheet","name":"Glucose ranges"},{"type":"text","text":"#WOW2025 Week 2 | Sean Miller | workout-wednesday.com/2025w2tab/ | Recreated from extracted glucose data","height":26}]})
    e.set_active_dashboard("Visualizing Ranges")
    e.save(str(OUTPUT))
    return OUTPUT

if __name__ == "__main__":
    print(build())
