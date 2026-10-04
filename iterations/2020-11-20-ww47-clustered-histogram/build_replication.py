"""Create the clustered histogram from locked order facts and public SDK calls."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_11_18_WW47_Clustered_Histogram"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / "Orders (Sample - Superstore).hyper"))
    calculations = [
        ("# ORDERS", "COUNTD([Order ID])", "integer", "measure", "quantitative"),
        (
            "Order Value",
            "{FIXED [Order ID]: SUM([Sales])}",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Round Up to 100",
            "CEILING([Order Value]/100)*100",
            "integer",
            "dimension",
            "ordinal",
        ),
        (
            "Sales Bin",
            "IF [Round Up to 100]>2100 THEN 2100 ELSE [Round Up to 100] END",
            "integer",
            "dimension",
            "quantitative",
        ),
        (
            "SALE AMOUNT",
            "CASE [Segment] WHEN 'Consumer' THEN [Sales Bin]-75 WHEN 'Corporate' THEN [Sales Bin]-50 ELSE [Sales Bin]-25 END",
            "integer",
            "dimension",
            "quantitative",
        ),
        ("Segment UPPER", "UPPER([Segment])", "string", "dimension", "nominal"),
        (
            "TOOLTIP Lower",
            "IF [SALE AMOUNT]<2000 THEN [Round Up to 100]-100 END",
            "integer",
            "dimension",
            "ordinal",
        ),
        (
            "TOOLTIP Upper",
            "IF [SALE AMOUNT]<2000 THEN [Round Up to 100] END",
            "integer",
            "dimension",
            "ordinal",
        ),
        (
            "TOOLTIP between",
            "IF [SALE AMOUNT]<2000 THEN ' between' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "TOOLTIP symbol",
            "IF [SALE AMOUNT]<2000 THEN ' - ' ELSE '$2000+' END",
            "string",
            "dimension",
            "nominal",
        ),
    ]
    for name, formula, datatype, role, field_type in calculations:
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format='c"$"#,##0'
            if name in {"SALE AMOUNT", "TOOLTIP Lower", "TOOLTIP Upper"}
            else "",
        )
    e.add_worksheet("Chart")
    e.configure_layered_chart(
        "Chart",
        columns=["SALE AMOUNT"],
        rows=["# ORDERS"],
        panes=[
            {
                "mark_type": "Bar",
                "color": "Segment UPPER",
                "mark_sizing_off": True,
                "mark_style": {"size": "1.4282872676849365"},
            }
        ],
    )
    e.configure_custom_tooltip(
        "Chart",
        [
            {"field": "ATTR(Segment)", "bold": True, "fontsize": 12},
            {"text": "\n"},
            {"field": "# ORDERS", "bold": True},
            {"text": " orders"},
            {"field": "ATTR(TOOLTIP between)"},
            {"text": " "},
            {"field": "ATTR(TOOLTIP Lower)", "bold": True},
            {"field": "ATTR(TOOLTIP symbol)", "bold": True},
            {"field": "ATTR(TOOLTIP Upper)", "bold": True},
        ],
    )
    e.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        axis_style={
            "encodings": [
                {
                    "field": "SALE AMOUNT",
                    "scope": "cols",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": 12,
                    "max": 2099,
                }
            ]
        },
    )
    e.add_reference_band(
        "Chart",
        axis_field="SALE AMOUNT",
        lower_value=2000,
        upper_value=2100,
        fill_color="#f5f5f5",
        upper_label="$2000+",
    )

    e.configure_reference_line_style(
        "Chart",
        "refline0",
        {
            "vertical-align": "top",
            "color": "#000000",
            "font-weight": "bold",
            "background-color": "#ffffff00",
        },
    )

    def zone(kind, x, y, width, height, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x * 100000 / 1400),
                "y": round(y * 125),
                "w": round(width * 100000 / 1400),
                "h": round(height * 125),
            },
            "style": {"margin": 4, "padding": 0},
            **kwargs,
        }

    e.add_dashboard(
        DASHBOARD,
        width=1400,
        height=800,
        worksheet_names=["Chart"],
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    8,
                    1384,
                    75,
                    runs=[
                        {
                            "text": "# ORDERS BY SALE AMOUNT & SEGMENT ",
                            "font_size": 18,
                            "font_color": "#1b1b1b",
                            "font_alignment": "0",
                            "bold": True,
                        },
                        {
                            "text": "(2020)\nORDERS OVER $2000 GROUPED TOGETHER",
                            "font_size": 9,
                            "font_color": "#1b1b1b",
                            "font_alignment": "0",
                            "bold": True,
                        },
                    ],
                ),
                zone(
                    "worksheet",
                    8,
                    83,
                    1384,
                    658,
                    name="Chart",
                    show_title=False,
                    fit="entire",
                ),
                zone(
                    "color",
                    78,
                    710,
                    435,
                    26,
                    worksheet="Chart",
                    field="Segment UPPER",
                    show_title=False,
                    mode="horz",
                ),
                zone(
                    "text",
                    8,
                    741,
                    461,
                    32,
                    runs=[
                        {
                            "text": "DESIGNED BY : ANN JACKSON",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "0",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    469,
                    741,
                    462,
                    32,
                    runs=[
                        {
                            "text": "#WOW2020 | WEEK 47",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "1",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    931,
                    741,
                    461,
                    32,
                    runs=[
                        {
                            "text": "RECREATED WITH CWTWB",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "2",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    8,
                    773,
                    1384,
                    19,
                    runs=[
                        {
                            "text": "http://www.workout-wednesday.com/2020w47/",
                            "font_size": 8,
                            "font_alignment": "1",
                            "hyperlink": "http://www.workout-wednesday.com/2020w47/",
                        }
                    ],
                ),
            ],
        },
    )
    out = HERE / "outputs" / "replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
