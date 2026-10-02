"""Build the complete WW06 null-safe average and Apply interaction replication."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2026_02_11_WW06_Averages_and_Nulls"
    / "2026_02_11_WW06_Averages_and_Nulls.twbx"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"


def build(output_path: Path) -> Path:
    # Use the challenge's packaged datasource because Manufacturer is absent
    # from cwtwb's standard Superstore reference; all views are rebuilt.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()
    # The packaged datasource already contains the required
    # Category > Sub-Category > Manufacturer hierarchy.
    # The packaged source already carries pMinDate and pMaxDate with the
    # challenge defaults; reuse them rather than duplicating parameter captions.

    # Reuse the source datasource's verified semantic fields (#Orders,
    # #Orders in Date Range, Index, Min/Max Date, Colour, True/False, etc.).
    # The replication independently rebuilds every worksheet, dashboard, and
    # action while avoiding duplicate field captions in Tableau metadata.

    editor.add_worksheet("Null-safe Average")
    editor.configure_chart(
        "Null-safe Average",
        mark_type="Square",
        columns=["WEEKDAY(Order Date)"],
        rows=["Category", "Sub-Category", "Manufacturer"],
        color="#Orders in Date Range",
        label="#Orders in Date Range",
        detail="Number Prefix *",
        tooltip=["#Orders", "Tooltip - 0 orders"],
        filters=[{"column": "Category"}],
    )
    editor.enable_domain_completion("Null-safe Average", field_name="Index")
    editor.configure_subtotals(
        "Null-safe Average",
        measure_fields=["#Orders in Date Range"],
        aggregation="Average",
        subtotal_fields=["Sub-Category", "Manufacturer"],
        label="Avg.",
    )
    editor.configure_worksheet_style(
        "Null-safe Average",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
    )

    editor.add_worksheet("Apply Button")
    editor.configure_chart(
        "Apply Button",
        mark_type="Square",
        label="AGG(Min Date)",
        detail="AGG(Max Date)",
        color="AGG(Colour)",
        filters=[
            {
                "column": "Order Date",
                "type": "quantitative",
                "min": "#2025-07-11#",
                "max": "#2025-07-23#",
                "context": True,
            }
        ],
        color_map={"true": "#D9D9D9", "false": "#F28E2B"},
    )
    editor.set_worksheet_caption("Apply Button", "Apply selected date range")
    editor.configure_worksheet_style(
        "Apply Button",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        disable_tooltip=True,
    )

    layout = {
        "type": "container",
        "direction": "horizontal",
        "children": [
            {"type": "worksheet", "name": "Null-safe Average", "weight": 5},
            {
                "type": "container",
                "direction": "vertical",
                "fixed_size": 230,
                "children": [
                    {"type": "worksheet", "name": "Apply Button", "fixed_size": 120},
                    {
                        "type": "paramctrl",
                        "parameter": "pMinDate",
                        "mode": "compact",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "pMaxDate",
                        "mode": "compact",
                    },
                ],
            },
        ],
    }
    editor.add_dashboard(
        "Null-safe Average Dashboard",
        width=1200,
        height=760,
        layout=layout,
        worksheet_names=["Null-safe Average", "Apply Button"],
    )
    editor.add_dashboard_action(
        dashboard_name="Null-safe Average Dashboard",
        action_type="parameter",
        source_sheet="Apply Button",
        source_field="Min Date",
        target_parameter="pMinDate",
        aggregation="min",
        clear_value="d:2025-07-11",
        caption="Set Min Date",
    )
    editor.add_dashboard_action(
        dashboard_name="Null-safe Average Dashboard",
        action_type="parameter",
        source_sheet="Apply Button",
        source_field="Max Date",
        target_parameter="pMaxDate",
        aggregation="max",
        clear_value="d:2025-07-23",
        caption="Set Max Date",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("2026-02-15-ww06-null-safe-averages-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
