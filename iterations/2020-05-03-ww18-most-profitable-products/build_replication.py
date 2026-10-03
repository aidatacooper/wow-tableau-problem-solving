"""Native nested Top N table and one parameter action for expansion/collapse."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_04_28_TopN_Nested_Table_Blogged_Version"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    for name, value in [("SUB-CATEGORIES TO SHOW", "3"), ("PRODUCTS TO SHOW", "5")]:
        editor.add_parameter(name, "integer", value, min_value="1", max_value="10")
    editor.add_parameter("Selected SubCat Group", "string", "", domain_type="any")
    editor.add_set(
        "Top N SubCats by Profit",
        "Sub-Category",
        basis_field="Profit",
        top_n="SUB-CATEGORIES TO SHOW",
    )
    editor.add_calculated_field(
        "SubCat Group",
        "IF [Top N SubCats by Profit] THEN [Sub-Category] ELSE 'All Others' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field("Margin", "SUM([Profit])/SUM([Sales])")
    expanded = "[Margin Rank]<=MIN([PRODUCTS TO SHOW]) OR [Selected SubCat Group]=MIN([SubCat Group])"
    formulas = {
        "Margin Rank": ("RANK_UNIQUE([Margin])", "integer", "ordinal"),
        "Sales For Others": (
            "WINDOW_SUM(IF [Margin Rank]>[PRODUCTS TO SHOW] THEN SUM([Sales]) END)",
            "real",
            "quantitative",
        ),
        "Profit For Others": (
            "WINDOW_SUM(IF [Margin Rank]>[PRODUCTS TO SHOW] THEN SUM([Profit]) END)",
            "real",
            "quantitative",
        ),
        "Margin For Others": (
            "IF [Margin Rank]>[PRODUCTS TO SHOW] THEN [Profit For Others]/[Sales For Others] END",
            "real",
            "quantitative",
        ),
        "Product Name Group": (
            f"IF {expanded} THEN ATTR([Product Name]) ELSE 'All Others' END",
            "string",
            "nominal",
        ),
        "Product Group Header": (
            "IF [Margin Rank]<=[PRODUCTS TO SHOW] THEN '' ELSEIF [Selected SubCat Group]=MIN([SubCat Group]) THEN '▼' ELSE '►' END",
            "string",
            "nominal",
        ),
        "Show?": (
            "[Margin Rank]<=MIN([PRODUCTS TO SHOW])+1 OR MIN([SubCat Group])=[Selected SubCat Group]",
            "boolean",
            "nominal",
        ),
        "Grouped Sales": (
            f"IF {expanded} THEN SUM([Sales]) ELSE [Sales For Others] END",
            "real",
            "quantitative",
        ),
        "Grouped Profit": (
            f"IF {expanded} THEN SUM([Profit]) ELSE [Profit For Others] END",
            "real",
            "quantitative",
        ),
        "Grouped Margin": (
            f"IF {expanded} THEN [Margin] ELSE [Margin For Others] END",
            "real",
            "quantitative",
        ),
    }
    for name, (formula, datatype, kind) in formulas.items():
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role="measure",
            field_type=kind,
            table_calc="Rows",
        )
    editor.add_calculated_field(
        "SubCat Group for Reset",
        "IF [Selected SubCat Group]=MIN([SubCat Group]) THEN '' ELSE MIN([SubCat Group]) END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    for name in ["Grouped Sales", "Grouped Profit"]:
        editor.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Grouped Margin", "p0%")
    editor.add_worksheet("Viz")
    address = {"ordering_type": "Field", "ordering_field": "Product Name"}
    nested = [
        "Margin Rank",
        "Sales For Others",
        "Profit For Others",
        "Margin For Others",
        "Grouped Sales",
        "Grouped Profit",
        "Grouped Margin",
    ]
    overrides = {
        ("[" + name + "]" if name != name.strip() else name): [address]
        + [{**address, "field": dep} for dep in nested if dep != name]
        for name in formulas
    }
    editor.configure_layered_chart(
        "Viz",
        rows=[
            "Top N SubCats by Profit",
            "SubCat Group",
            "Product Group Header",
            "Margin Rank",
            "Product Name",
            "Product Name Group",
        ],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Automatic",
                "label": "Multiple Values",
                "measure_values": ["Grouped Margin", "Grouped Profit", "Grouped Sales"],
                "detail": "SubCat Group for Reset",
                "tooltip": nested + ["Show?"],
                "selection_relaxation": "disallow",
            }
        ],
        fold_axes=False,
        sort_descending="SUM(Profit)",
        sort_field="SubCat Group",
        filters=[{"column": "Show?", "values": [True]}],
        table_calc_overrides=overrides,
    )
    editor.set_measure_name_aliases(
        "Viz",
        {
            "Grouped Margin": " Margin ",
            "Grouped Profit": " Profit ",
            "Grouped Sales": " Sales ",
        },
    )
    editor.configure_subtotals(
        "Viz",
        measure_fields=["Grouped Margin", "Grouped Profit", "Grouped Sales"],
        aggregation="Automatic",
        subtotal_fields=["SubCat Group"],
        label="Total",
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        show_row_totals=True,
        hide_band_color=True,
        pane_cell_style={
            "font-size": "10",
            "text-align": "center",
            "color": "#000000",
        },
        label_formats=[
            {"field": name, "display": "false"}
            for name in ["Top N SubCats by Profit", "Margin Rank", "Product Name"]
        ]
        + [
            {
                "field": "SubCat Group",
                "text-orientation": "-90",
                "font-size": "14",
                "color": "#5500ff",
                "font-family": "Tableau Medium",
            }
        ],
        table_formats=[{"attr": "band-size", "scope": "rows", "value": "0"}],
        header_formats=[
            {"scope": "rows", "band-color": "#00000000"},
            {"field": "Product Name Group", "width": "280"},
            {"field": "SubCat Group", "width": "52"},
            {"field": "Product Group Header", "width": "52"},
            {"field": "Measure Names", "height": "32"},
        ],
        cell_formats=[
            {"field": "Product Name Group", "height": "30"},
        ],
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        worksheet_names=["Viz"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "WHICH PRODUCTS WERE MOST PROFITABLE?",
                    "font_size": 14,
                    "fixed_size": 40,
                },
                {
                    "type": "horizontal",
                    "fixed_size": 65,
                    "children": [
                        {"type": "empty"},
                        {
                            "type": "paramctrl",
                            "parameter": "SUB-CATEGORIES TO SHOW",
                            "mode": "slider",
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "PRODUCTS TO SHOW",
                            "mode": "slider",
                        },
                        {"type": "empty"},
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": False,
                    "fit": "width",
                },
                {
                    "type": "text",
                    "text": "DESIGNED BY: LUKE STANKE | #WOW2020 WEEK 18 | RECREATED WITH CWTWB\nhttps://www.workout-wednesday.com/2020w18/",
                    "font_size": 8,
                    "font_color": "#285179",
                    "fixed_size": 55,
                },
            ],
        },
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Viz",
        source_field="SubCat Group for Reset",
        target_parameter="Selected SubCat Group",
        caption="Expand Collapse Products",
        clear_behavior="keep-current",
    )
    editor.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(path, validate=False)
    return path


if __name__ == "__main__":
    print(build())
