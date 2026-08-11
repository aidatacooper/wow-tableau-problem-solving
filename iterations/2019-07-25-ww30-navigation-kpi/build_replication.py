"""Build the complete 2019 WW30 navigating-KPI replication with cwtwb."""

from pathlib import Path
import sys


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


SOURCE_TWBX = (
    ITERATION_DIR.parents[1]
    / "dashboards"
    / "2019_07_24_WW30_Navigation_KPI"
    / "2019_07_24_WW30_Navigation_KPI.twbx"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"

KPI_SHEETS = {
    "Customers": ("COUNTD(Customer ID)", "#57A337"),
    "Products": ("COUNTD(Product Name)", "#FC719E"),
    "Orders": ("COUNTD(Order ID)", "#F5A623"),
    "Cities": ("COUNTD(City State UPPER)", "#1BA3C6"),
}
DETAIL_SHEETS = {
    "by Customer": ("Cust Name UPPER", "Customer Sales", "#4E79A7"),
    "by Product": ("Product Name UPPER", "Product Sales", "#F28E2B"),
    "by Order": ("Order ID", "Order Sales", "#59A14F"),
    "by City": ("City State UPPER", "City Sales", "#E15759"),
}
NAVIGATION = {
    "Customers": "Customer Sales",
    "Products": "Product Sales",
    "Orders": "Order Sales",
    "Cities": "City Sales",
}


def detail_layout(title: str, sheet: str) -> dict:
    return {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 66,
                "children": [
                    {
                        "type": "text",
                        "text": title,
                        "font_size": "20",
                        "bold": True,
                        "weight": 1,
                    },
                    {
                        "type": "navigation_button",
                        "target_dashboard": "4 Box KPI",
                        "caption": "GO BACK",
                        "background_color": "#253746",
                        "fixed_size": 150,
                    },
                ],
            },
            {"type": "worksheet", "name": sheet, "fit": "entire", "weight": 1},
        ],
    }


def build(output_path: Path) -> Path:
    # Preserve the original datasource, calculations, connection metadata, and
    # bundled Orders Hyper extract. Only the view layer is rebuilt.
    editor = TWBEditor(SOURCE_TWBX)
    editor.clear_worksheets()
    editor.add_calculated_field(
        "KPI Color",
        '"KPI"',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    for sheet, (measure, color) in KPI_SHEETS.items():
        editor.add_worksheet(sheet)
        editor.configure_chart(
            sheet,
            mark_type="Square",
            color="KPI Color",
            label=measure,
            tooltip=[measure],
            mark_sizing_off=True,
            color_map={"KPI": color},
            label_runs=[
                {
                    "field": measure,
                    "bold": True,
                    "fontsize": "26",
                    "fontcolor": "#FFFFFF",
                },
                {"text": "\u00c6\n"},
                {
                    "text": sheet.upper(),
                    "fontsize": "15",
                    "fontcolor": "#FFFFFF",
                },
            ],
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            pane_cell_style={
                "vertical-align": "center",
                "text-align": "center",
            },
            pane_datalabel_style={"color-mode": "match"},
            pane_mark_style={
                "mark-labels-show": "true",
                "size": "14.547999382019043",
            },
        )
        editor.set_worksheet_caption(sheet, f"Select to open {sheet.lower()} sales")

    for sheet, (dimension, _dashboard, color) in DETAIL_SHEETS.items():
        editor.add_worksheet(sheet)
        editor.configure_chart(
            sheet,
            mark_type="Bar",
            rows=[dimension],
            columns=["SUM(Sales)"],
            label="SUM(Sales)",
            tooltip=[dimension, "SUM(Sales)"],
            sort_descending="SUM(Sales)",
            color_map={"blue": color},
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
        )

    main_layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "text": "NAVIGATING KPI BLOCK",
                "font_size": "22",
                "bold": True,
                "fixed_size": 68,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "weight": 1,
                "children": [
                    {
                        "type": "container",
                        "direction": "vertical",
                        "weight": 1,
                        "children": [
                            {
                                "type": "worksheet",
                                "name": "Customers",
                                "fit": "entire",
                                "weight": 1,
                            },
                            {
                                "type": "worksheet",
                                "name": "Orders",
                                "fit": "entire",
                                "weight": 1,
                            },
                        ],
                    },
                    {
                        "type": "container",
                        "direction": "vertical",
                        "weight": 1,
                        "children": [
                            {
                                "type": "worksheet",
                                "name": "Products",
                                "fit": "entire",
                                "weight": 1,
                            },
                            {
                                "type": "worksheet",
                                "name": "Cities",
                                "fit": "entire",
                                "weight": 1,
                            },
                        ],
                    },
                ],
            },
            {
                "type": "text",
                "text": "Select a KPI to open its ranked sales detail",
                "font_size": "10",
                "fixed_size": 38,
            },
        ],
    }
    editor.add_dashboard(
        "4 Box KPI",
        width=1000,
        height=720,
        layout=main_layout,
        worksheet_names=list(KPI_SHEETS),
    )

    for sheet, (_dimension, dashboard, _color) in DETAIL_SHEETS.items():
        editor.add_dashboard(
            dashboard,
            width=1000,
            height=720,
            layout=detail_layout(dashboard, sheet),
            worksheet_names=[sheet],
        )

    for source, target in NAVIGATION.items():
        editor.add_dashboard_action(
            dashboard_name="4 Box KPI",
            action_type="go-to-sheet",
            source_sheet=source,
            target_sheet=target,
            caption=f"Open {target}",
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in ("2019-07-25-ww30-navigation-kpi-replicated-workbook.twb", "2019-07-25-ww30-navigation-kpi-replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
