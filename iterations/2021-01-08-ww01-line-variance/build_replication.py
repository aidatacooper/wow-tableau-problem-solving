"""Rebuild the food insecurity line and comparison circles from locked data."""

from pathlib import Path
import re
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_01_06_WW01_Line_Variance_Table_Calcs"
FOOD = "Food insecurity (includes low and very low food security) Percent of households"
PERCENT = 'n#,##0.0"%";-#,##0.0"%"'


def zone(kind, x, y, w, h, **options):
    return {"type": kind, "absolute": {"x": x, "y": y, "w": w, "h": h}, **options}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/federated_0x2sama1bobbkv1gnvwr91.hyper"))
    e.add_parameter(
        "pComparison",
        datatype="integer",
        default_value="2",
        domain_type="list",
        allowed_values=["0", "1", "2"],
        allowed_aliases={
            "0": "First Year",
            "1": "Most Recent Year",
            "2": "Previous Year",
        },
        internal_name="[Parameter 1]",
        alias="Previous Year",
    )
    e.add_parameter(
        "pSelected Year",
        datatype="integer",
        default_value="2018",
        domain_type="list",
        allowed_values=[str(y) for y in range(1995, 2020)],
        default_format="n0;-0",
        internal_name="[Parameter 2]",
    )
    e.add_calculated_field(
        "Year Axis",
        "[Year]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    e.add_calculated_field(
        "Data Year",
        "[Year]",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    calculations = {
        "First Year": ("WINDOW_MIN(MIN([Year]))", "integer", True),
        "Latest Year": ("WINDOW_MAX(MAX([Year]))", "integer", True),
        "Previous Year": ("[Parameters].[pSelected Year]-1", "integer", False),
        "Selected Year %": (
            f"IF [Year] = [Parameters].[pSelected Year] THEN [{FOOD}] END",
            "real",
            False,
        ),
        "First Year %": (
            f"IF MIN([Year]) = [First Year] THEN MIN([{FOOD}]) END",
            "real",
            True,
        ),
        "Latest Year %": (
            f"IF MIN([Year]) = [Latest Year] THEN MIN([{FOOD}]) END",
            "real",
            True,
        ),
        "Previous Year %": (
            f"IF [Year] = [Previous Year] THEN [{FOOD}] END",
            "real",
            False,
        ),
        "Win Max - Selected Year %": (
            "WINDOW_MAX(MIN([Selected Year %]))",
            "real",
            True,
        ),
        "Selected Comparison %": (
            "CASE [Parameters].[pComparison] WHEN 0 THEN [First Year %] WHEN 1 THEN [Latest Year %] WHEN 2 THEN SUM([Previous Year %]) END",
            "real",
            True,
        ),
        "Win Max - Selected Comparison %": (
            "CASE [Parameters].[pComparison] WHEN 0 THEN WINDOW_MAX([First Year %]) WHEN 1 THEN WINDOW_MAX([Latest Year %]) WHEN 2 THEN WINDOW_MAX(MAX([Previous Year %])) END",
            "real",
            True,
        ),
        "Difference": (
            "[Win Max - Selected Year %]-[Win Max - Selected Comparison %]",
            "real",
            True,
        ),
        "Difference Indicator": (
            "IF [Difference] > 0 THEN '\u25b2' ELSEIF [Difference] < 0 THEN '\u25bc' ELSE 'N/C' END",
            "string",
            True,
        ),
        "DISPLAY: Difference": (
            "IF [Difference] <> 0 THEN ABS([Difference]) END",
            "real",
            True,
        ),
    }
    for name, (formula, datatype, tc) in calculations.items():
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            field_type="nominal" if datatype == "string" else "quantitative",
            table_calc="Rows" if tc else None,
            default_format=PERCENT if datatype == "real" else "",
        )
    e.set_field_format("Win Max - Selected Year %", 'n#,##0"%";-#,##0"%"')
    e.set_field_format(FOOD, PERCENT)
    e.set_field_format("Year", "n0;-0")

    def addressing(names, year):
        def dependencies(name, seen):
            for ref in re.findall(r"\[([^\]]+)\]", calculations[name][0]):
                if ref in calculations and ref not in seen:
                    seen.add(ref)
                    dependencies(ref, seen)
            return seen

        result = {}
        for name in names:
            specs = [
                {
                    "ordering_type": "Field",
                    "order": [{"field": year, "reference": "instance"}],
                }
            ]
            for dep in sorted(dependencies(name, set())):
                if calculations[dep][2]:
                    specs.append(
                        {
                            "field": dep,
                            "ordering_type": "Field",
                            "order": [{"field": year, "reference": "instance"}],
                        }
                    )
            if year == "Data Year":
                specs = [
                    {
                        "ordering_type": "Field",
                        "order": ["Data Year"],
                        **({"field": spec["field"]} if "field" in spec else {}),
                    }
                    for spec in specs
                ]
            result[f"AGG({name})"] = specs
        return result

    data_overrides = addressing(
        [
            "Win Max - Selected Year %",
            "First Year %",
            "Latest Year %",
            "Selected Comparison %",
            "Win Max - Selected Comparison %",
            "Difference",
            "DISPLAY: Difference",
        ],
        "Data Year",
    )
    viz_overrides = addressing(
        [
            "Selected Comparison %",
            "DISPLAY: Difference",
            "Difference Indicator",
            "Win Max - Selected Year %",
        ],
        "[Year Axis]",
    )
    for name in ("Data", "Viz", "Title"):
        e.add_worksheet(name)
    e.configure_layered_chart(
        "Data",
        rows=["Data Year"],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    f"SUM({FOOD})",
                    "SUM(Selected Year %)",
                    "AGG(Win Max - Selected Year %)",
                    "AGG(First Year %)",
                    "AGG(Latest Year %)",
                    "SUM(Previous Year %)",
                    "AGG(Selected Comparison %)",
                    "AGG(Win Max - Selected Comparison %)",
                    "AGG(Difference)",
                    "AGG(DISPLAY: Difference)",
                ],
            }
        ],
        table_calc_overrides=data_overrides,
        table_calc_context=True,
    )
    e.configure_layered_chart(
        "Viz",
        columns=["[Year Axis]"],
        rows=[f"SUM({FOOD})", "Multiple Values"],
        panes=[
            {
                "axis": f"SUM({FOOD})",
                "mark_type": "Line",
                "detail_extra": [
                    "AGG(DISPLAY: Difference)",
                    "AGG(Difference Indicator)",
                    "AGG(Win Max - Selected Year %)",
                ],
                "tooltip": ["ATTR(Year)"],
                "mark_sizing_off": True,
                "mark_style": {
                    "mark-color": "#1b1b1b",
                    "size": "0.0099999997764825821",
                    "mark-labels-show": "false",
                },
            },
            {
                "axis": "Multiple Values",
                "mark_type": "Circle",
                "measure_values": [
                    "AGG(Selected Comparison %)",
                    "SUM(Selected Year %)",
                ],
                "color": "Measure Names",
                "color_map": {
                    "AGG(Selected Comparison %)": "#000000",
                    "SUM(Selected Year %)": "#f0007b",
                },
                "detail_extra": [
                    "AGG(DISPLAY: Difference)",
                    "AGG(Difference Indicator)",
                    "AGG(Win Max - Selected Year %)",
                ],
                "tooltip": [f"SUM({FOOD})", "ATTR(Year)"],
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "1.0214917659759521",
                    "mark-labels-show": "false",
                },
            },
        ],
        table_calc_overrides=viz_overrides,
        table_calc_context=True,
        synchronized=True,
        fold_axes=True,
    )
    for pane in (0, 1):
        e.configure_custom_tooltip(
            "Viz",
            [
                {"field": "ATTR(Year)", "bold": True},
                {"text": " | "},
                {"field": f"SUM({FOOD})", "fontsize": 9},
                {"text": " of U.S Households were food insecure", "fontsize": 9},
            ],
            pane_index=pane,
        )
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        axis_style={
            "encodings": [
                {
                    "field": "[Year Axis]",
                    "scope": "cols",
                    "attr": "space",
                    "type": "space",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": 1994,
                    "max": 2020,
                    "major-origin": 1995,
                    "major-spacing": 2,
                },
                {
                    "field": f"SUM({FOOD})",
                    "scope": "rows",
                    "attr": "space",
                    "type": "space",
                    "field-type": "quantitative",
                    "major-origin": 0,
                    "major-spacing": 5,
                },
            ],
            "per_field": [
                {
                    "field": f"SUM({FOOD})",
                    "scope": "rows",
                    "attr": "title",
                    "value": "",
                },
                {"field": "[Year Axis]", "scope": "cols", "attr": "title", "value": ""},
                {
                    "field": "Multiple Values",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
            ],
        },
        label_formats=[
            {"field": "[Year Axis]", "font-size": 8},
            {"field": f"SUM({FOOD})", "font-size": 8},
        ],
        table_formats=[{"attr": "show-null-value-warning", "value": "false"}],
    )
    header = {
        "Header Selected %": f"{{FIXED : MAX(IF [Year] = [Parameters].[pSelected Year] THEN [{FOOD}] END)}}",
        "Header First %": f"{{FIXED : MAX(IF [Year] = {{FIXED : MIN([Year])}} THEN [{FOOD}] END)}}",
        "Header Latest %": f"{{FIXED : MAX(IF [Year] = {{FIXED : MAX([Year])}} THEN [{FOOD}] END)}}",
        "Header Previous %": f"{{FIXED : MAX(IF [Year] = [Parameters].[pSelected Year]-1 THEN [{FOOD}] END)}}",
        "Header Comparison %": "CASE [Parameters].[pComparison] WHEN 0 THEN [Header First %] WHEN 1 THEN [Header Latest %] WHEN 2 THEN [Header Previous %] END",
        "Header Difference": "[Header Selected %]-[Header Comparison %]",
        "Header Absolute Difference": "IF [Header Difference] <> 0 THEN ABS([Header Difference]) END",
        "Header Indicator": "IF [Header Difference] > 0 THEN '\u25b2' ELSEIF [Header Difference] < 0 THEN '\u25bc' ELSE 'N/C' END",
        "Header Year": "STR([Parameters].[pSelected Year])",
        "Header Comparison Label": "CASE [Parameters].[pComparison] WHEN 0 THEN 'First Year' WHEN 1 THEN 'Most Recent Year' WHEN 2 THEN 'Previous Year' END",
    }
    for name, formula in header.items():
        dtype = (
            "string"
            if name in ("Header Indicator", "Header Year", "Header Comparison Label")
            else "real"
        )
        e.add_calculated_field(
            name,
            formula,
            datatype=dtype,
            default_format=(
                'n#,##0"%";-#,##0"%"' if name == "Header Selected %" else PERCENT
            )
            if dtype == "real"
            else "",
            field_type="nominal" if dtype == "string" else "quantitative",
        )
    e.configure_chart(
        "Title",
        mark_type="Text",
        label="MIN(Header Selected %)",
        label_extra=[
            "ATTR(Header Indicator)",
            "MIN(Header Absolute Difference)",
            "ATTR(Header Year)",
            "ATTR(Header Comparison Label)",
        ],
        label_runs=[
            {
                "field": "MIN(Header Selected %)",
                "fontcolor": "#f0007b",
                "bold": True,
                "fontsize": 18,
            },
            {
                "text": " OF U.S HOUSEHOLDS WERE FOOD INSECURE OR LACKED CONSISTENT ACCESS TO ENOUGH FOOD (               ",
                "fontsize": 12,
            },
            {"field": "ATTR(Header Year)", "fontcolor": "#f0007b", "fontsize": 12},
            {"text": " )\n", "fontsize": 12},
            {"field": "ATTR(Header Indicator)", "fontsize": 12},
            {"text": " ", "fontsize": 12},
            {"field": "MIN(Header Absolute Difference)", "fontsize": 12},
            {"text": " vs.         ", "fontsize": 12},
            {"field": "ATTR(Header Comparison Label)", "fontsize": 12},
        ],
    )
    e.set_field_format("Header Selected %", 'n#,##0"%";-#,##0"%"')
    e.configure_worksheet_style(
        "Title",
        pane_mark_style={"mark-labels-cull": "false", "mark-labels-show": "true"},
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        pane_cell_style={"text-align": "left", "vertical-align": "top"},
    )
    children = [
        zone(
            "worksheet",
            800,
            1000,
            98400,
            10000,
            name="Title",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            800,
            11000,
            98400,
            80000,
            name="Viz",
            show_title=False,
            fit="entire",
        ),
        zone(
            "paramctrl",
            9900,
            7000,
            2500,
            3375,
            parameter="pComparison",
            mode="compact",
            show_title=False,
        ),
        zone(
            "paramctrl",
            80500,
            3500,
            2600,
            3625,
            parameter="pSelected Year",
            mode="compact",
            show_title=False,
        ),
    ]
    for x, text, alignment in (
        (800, "CHALLENGE BY : CANDRA MCRAE", "left"),
        (33600, "#WOW2021  |  WEEK 1", "center"),
        (66400, "RECREATED WITH CWTWB", "right"),
    ):
        children.append(
            zone(
                "text",
                x,
                91000,
                32800,
                4000,
                runs=[
                    {
                        "text": text,
                        "font_size": 8,
                        "font_color": "#f0007b",
                        "font_alignment": {"left": "0", "center": "1", "right": "2"}[
                            alignment
                        ],
                    }
                ],
            )
        )
    children.append(
        zone(
            "text",
            800,
            95000,
            98400,
            4000,
            runs=[
                {
                    "text": "http://www.workout-wednesday.com/wow2021w1tab/",
                    "font_size": 8,
                    "font_color": "#f0007b",
                    "font_alignment": "1",
                }
            ],
        )
    )
    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
    )
    for name in ("Data", "Viz", "Title"):
        e.set_worksheet_title(name, "")
        e.set_window_state(name, hidden=False, zoom_entire_view=True)
    out = HERE / "outputs/replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
