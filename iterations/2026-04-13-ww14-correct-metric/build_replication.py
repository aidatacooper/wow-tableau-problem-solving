"""Build WW14 (2026) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate).
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "federated_1nm7djf14r2b931axjuel0.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2026_04_13_WW14_Correct_Metric"

# The author restricts the report to the last three months of the extract
# (Oct/Nov/Dec 2025) and keeps marks whose difference is inside [0, 1/6].
WINDOW_MONTHS = ["202510", "202511", "202512"]
MAX_DIFFERENCE = "0.16666666666666663"

WEIGHTED_AVG = "SUM([Discount] * [Quantity]) / SUM([Quantity])"
DIFFERENCE = "ABS([Weighted Avg] - AVG([Discount]))"
IS_DIFFERENCE = "ROUND([Difference from correct metric], 3) <> 0"


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    editor.set_date_options(start_of_week="sunday")

    for name, formula, datatype, role, field_type in [
        ("Weighted Avg", WEIGHTED_AVG, "real", "measure", "quantitative"),
        ("Difference from correct metric", DIFFERENCE, "real", "measure", "quantitative"),
        ("Is difference?", IS_DIFFERENCE, "boolean", "measure", "nominal"),
    ]:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format="p0.0%" if datatype == "real" else "",
        )

    common_filters = [
        {
            "column": "MY(Order Date)",
            "type": "categorical",
            "values": WINDOW_MONTHS,
        },
        {
            "column": "Difference from correct metric",
            "type": "quantitative",
            "min": "0",
            "max": MAX_DIFFERENCE,
        },
    ]

    editor.add_worksheet("Simple Avg")
    editor.configure_chart(
        "Simple Avg",
        mark_type="Circle",
        columns=["AVG(Discount)"],
        rows=["AVG(Quantity)"],
        detail="Order ID",
        color="Is difference?",
        label="AVG(Discount)",
        tooltip=["Difference from correct metric"],
        filters=common_filters,
        color_map={"true": "#E15759", "false": "#4E79A7"},
    )

    editor.add_worksheet("Weighted Avg")
    editor.configure_chart(
        "Weighted Avg",
        mark_type="Circle",
        columns=["Weighted Avg"],
        rows=["AVG(Quantity)"],
        detail="Order ID",
        color="Is difference?",
        label="Weighted Avg",
        tooltip=["Difference from correct metric"],
        filters=common_filters,
        color_map={"true": "#E15759", "false": "#4E79A7"},
    )

    editor.add_worksheet("Order Details")
    editor.configure_chart(
        "Order Details",
        mark_type="Automatic",
        rows=["Order ID", "Category"],
        measure_values=["AVG(Quantity)", "AVG(Discount)"],
        filters=common_filters,
    )

    editor.configure_custom_tooltip(
        "Simple Avg",
        runs=[
            {"text": "Order "},
            {"field": "Order ID"},
            {"text": "\nSimple average discount: "},
            {"field": "AVG(Discount)"},
            {"text": "\nWeighted average discount: "},
            {"field": "Weighted Avg"},
            {"text": "\nDifference: "},
            {"field": "Difference from correct metric"},
            {"text": "\n"},
            {
                "sheet": {
                    "name": "Order Details",
                    "maxwidth": 400,
                    "maxheight": 300,
                    "filter_fields": ["Order ID"],
                }
            },
        ],
    )
    editor.configure_custom_tooltip(
        "Weighted Avg",
        runs=[
            {"text": "Order "},
            {"field": "Order ID"},
            {"text": "\nSimple average discount: "},
            {"field": "AVG(Discount)"},
            {"text": "\nWeighted average discount: "},
            {"field": "Weighted Avg"},
            {"text": "\nDifference: "},
            {"field": "Difference from correct metric"},
            {"text": "\n"},
            {
                "sheet": {
                    "name": "Order Details",
                    "maxwidth": 400,
                    "maxheight": 300,
                    "filter_fields": ["Order ID"],
                }
            },
        ],
    )

    for sheet in ("Simple Avg", "Weighted Avg", "Order Details"):
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_borders=True,
            hide_zeroline=True,
            hide_row_field_labels=(sheet == "Order Details"),
            hide_col_field_labels=(sheet == "Order Details"),
            hide_table_dividers=(sheet == "Order Details"),
        )

    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"background-color": "#f5f5f5"},
        "children": [
            {
                "type": "text",
                "text": "#WOW2026  W14 | Can you calculate the correct metric?",
                "runs": [
                    {
                        "text": "#WOW2026  W14 | ",
                        "font_size": "20",
                        "bold": True,
                        "font_color": "#000000",
                    },
                    {
                        "text": "Can you calculate the correct metric?",
                        "font_size": "20",
                        "font_color": "#000000",
                    },
                ],
                "absolute": {"x": 0, "y": 0, "w": 100000, "h": 9177},
            },
            {
                "type": "text",
                "text": "Simple average (AVG of Discount)",
                "runs": [
                    {
                        "text": "Simple average (AVG of Discount)",
                        "font_size": "14",
                        "font_color": "#1b1b1b",
                    }
                ],
                "absolute": {"x": 1538, "y": 11530, "w": 46000, "h": 4000},
            },
            {
                "type": "worksheet",
                "name": "Simple Avg",
                "show_title": False,
                "fit": "entire",
                "style": {"background-color": "#ffffff", "padding": 10},
                "absolute": {"x": 1538, "y": 15530, "w": 46000, "h": 35764},
            },
            {
                "type": "text",
                "text": "Weighted average (SUM(Discount*Quantity)/SUM(Quantity))",
                "runs": [
                    {
                        "text": "Weighted average (SUM(Discount*Quantity)/SUM(Quantity))",
                        "font_size": "14",
                        "font_color": "#1b1b1b",
                    }
                ],
                "absolute": {"x": 48460, "y": 11530, "w": 49940, "h": 4000},
            },
            {
                "type": "worksheet",
                "name": "Weighted Avg",
                "show_title": False,
                "fit": "entire",
                "style": {"background-color": "#ffffff", "padding": 10},
                "absolute": {"x": 48460, "y": 15530, "w": 49940, "h": 35764},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1300,
        height=850,
        layout=layout,
        worksheet_names=["Simple Avg", "Weighted Avg"],
    )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="highlight",
        source_sheet="Simple Avg",
        target_sheet="Simple Avg",
        caption="Highlight order",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2026-04-13-ww14-correct-metric-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
