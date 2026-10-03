"""Customer-grain dot distribution, built from an empty workbook."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_01_WW27_OrdersByCustomerDistribution"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/TEMP_1hl4av000gzffz18luq09058fa8f.hyper")
    )
    editor.add_parameter(
        "pMarkIndicator", datatype="integer", default_value="5", domain_type="any"
    )
    editor.add_calculated_field(
        "# Orders Per Customer",
        "{FIXED [Segment],[Customer ID]: COUNTD([Order ID])}",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    calculations = {
        "# Customers": "COUNTD([Customer ID])",
        "# Customers per Order Count": "WINDOW_SUM([# Customers])",
        "Index": "INDEX()",
        "Marks to Plot": "INT([# Customers per Order Count]/[pMarkIndicator])",
        "Cols": "[Index]%[Marks to Plot]",
        "Cols Shifted": (
            "IF [Marks to Plot]%2=0 THEN [Cols]-[Marks to Plot]/2+0.5 "
            "ELSE [Cols]-([Marks to Plot]-1)/2 END"
        ),
    }
    for name, formula in calculations.items():
        editor.add_calculated_field(
            name,
            formula,
            datatype="real" if name == "Cols Shifted" else "integer",
            table_calc=None if name == "# Customers" else "Rows",
        )
    overrides = {
        name: [{"ordering_type": "Field", "ordering_field": "Customer ID"}]
        + [
            {"field": nested, "ordering_type": "Field", "ordering_field": "Customer ID"}
            for nested in [
                "# Customers per Order Count",
                "Index",
                "Marks to Plot",
                "Cols",
            ]
            if nested != name
        ]
        for name in calculations
        if name != "# Customers"
    }
    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        columns=["Segment", "Cols Shifted"],
        rows=["# Orders Per Customer"],
        panes=[
            {
                "mark_type": "Circle",
                "detail": "Customer ID",
                "detail_extra": [
                    "# Customers per Order Count",
                    "Marks to Plot",
                    "Index",
                    "Cols",
                ],
                "mark_sizing_off": True,
                "mark_style": {"mark-color": "#183236", "size": "0.9335359335"},
            }
        ],
        table_calc_overrides=overrides,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_col_field_labels=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_band_color=True,
        hide_zeroline=True,
        disable_tooltip=True,
        axis_style={
            "per_field": [
                {
                    "field": "# Orders Per Customer",
                    "scope": "rows",
                    "attr": "title",
                    "value": "Total Orders",
                },
                {
                    "field": "Cols Shifted",
                    "scope": "cols",
                    "attr": "display",
                    "value": "false",
                },
            ]
        },
        label_formats=[
            {
                "field": "Segment",
                "font-weight": "bold",
                "font-size": "12",
                "color": "#898989",
            }
        ],
        gridline_style={
            "rows": {"stroke-color": "#d4d4d4"},
            "cols": {"line-visibility": "off"},
        },
    )
    editor.add_dashboard(
        DASHBOARD,
        width=900,
        height=500,
        worksheet_names=["Viz"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "WHAT IS THE DISTRIBUTION OF TOTAL ORDERS BY CUSTOMER?",
                    "font_size": 16,
                    "font_color": "#183236",
                    "bold": True,
                    "fixed_size": 32,
                },
                {
                    "type": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {"type": "empty", "weight": 1},
                        {
                            "type": "text",
                            "text": "● =",
                            "font_size": 12,
                            "fixed_size": 36,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "pMarkIndicator",
                            "mode": "type_in",
                            "show_title": False,
                            "fixed_size": 58,
                        },
                        {
                            "type": "text",
                            "text": "customers",
                            "font_size": 12,
                            "fixed_size": 90,
                        },
                        {"type": "empty", "weight": 1},
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": False,
                    "fit": "entire",
                },
                {
                    "type": "text",
                    "text": "DESIGNED BY LUKE STANKE | #WOW2020 WEEK 27 | RECREATED WITH CWTWB",
                    "font_size": 9,
                    "fixed_size": 28,
                },
                {
                    "type": "text",
                    "text": "https://www.workout-wednesday.com/2020w27/",
                    "font_size": 9,
                    "fixed_size": 24,
                },
            ],
        },
    )
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
