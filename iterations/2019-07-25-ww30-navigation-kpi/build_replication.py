"""Build the complete 2019 WW30 navigating-KPI replication with cwtwb."""

from pathlib import Path
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

KPI_SHEETS = {
    "Customers": ("COUNTD(Customer ID)", "#57A337"),
    "Products": ("COUNTD(Product Name)", "#FC719E"),
    "Orders": ("COUNTD(Order ID)", "#8076ba"),
    "Cities": ("COUNTD(City State UPPER)", "#1BA3C6"),
}
DETAIL_SHEETS = {
    "by Customer": ("Cust Name UPPER", "Customer Sales", "#57A337"),
    "by Product": ("Product Name UPPER", "Product Sales", "#FC719E"),
    "by Order": ("Order ID", "Order Sales", "#8076BA"),
    "by City": ("City State UPPER", "City Sales", "#1BA3C6"),
}
NAVIGATION = {
    "Customers": "Customer Sales",
    "Products": "Product Sales",
    "Orders": "Order Sales",
    "Cities": "City Sales",
}


def detail_layout(title: str, sheet: str, color: str) -> dict:
    return {"type": "container", "direction": "floating", "style": {"margin": 8}, "children": [
        {"type": "worksheet", "name": sheet, "fit": "width", "style": {"margin": 0}, "absolute": {"x": 1333, "y": 1333, "w": 97334, "h": 97334}},
        {"type": "navigation_button", "target_dashboard": "4 Box KPI", "caption": "GO BACK", "bold": True, "font_color": "#ffffff", "background_color": color.lower(), "absolute": {"x": 71333, "y": 1167, "w": 27333, "h": 8667}},
    ]}


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    editor.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    for name, formula in {
        "City State UPPER": "UPPER([City]) + ', ' + UPPER([State])",
        "Cust Name UPPER": "UPPER([Customer Name])",
        "Product Name UPPER": "UPPER([Product Name])",
    }.items():
        editor.add_calculated_field(name, formula, datatype="string", role="dimension")
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
                "mark-color": color,
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
            label_extra=[dimension],
            label_runs=[{"field": dimension, "bold": True}, {"text": "\u00a0"}, {"field": "SUM(Sales)", "fontsize": "8"}],
            tooltip=[dimension, "SUM(Sales)"],
            sort_descending="SUM(Sales)",
        )
        editor.set_worksheet_rich_title(sheet, [{"text": "SALES BY " + _dashboard.removesuffix(" Sales").upper(), "bold": sheet != "by Order", "fontname": "Tableau Medium", "fontsize": "20", "fontcolor": color}])
        editor.configure_worksheet_style(
            sheet, hide_axes=True, hide_row_label=dimension, hide_col_field_labels=True, hide_row_field_labels=True,
            hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_table_dividers=True,
            cell_formats=[{"field": dimension, "height": 30 if sheet in ("by Order", "by Product") else 33}, {"field": "SUM(Sales)", "format": 'c"$"#,##0;-"$"#,##0'}],
            pane_cell_style={"text-align": "left"},
            pane_datalabel_style={"color-mode": "match", "font-weight": "bold"},
            pane_mark_style={"mark-color": color, "mark-labels-show": "true", "mark-labels-cull": "true"},
        )

    main_layout = {"type": "container", "direction": "floating", "style": {"margin": 8}, "children": [
        {"type": "worksheet", "name": sheet, "show_title": False, "fit": "entire", "style": {"margin": 0}, "absolute": {"x": x, "y": y, "w": 47000, "h": 40000}}
        for sheet, x, y in [("Customers", 2000, 2000), ("Products", 50500, 2000), ("Cities", 2000, 43500), ("Orders", 50500, 43500)]
    ] + [
        {"type": "text", "text": "#WORKOUTWEDNESDAY | 2019 | WEEK 30", "font_size": "9", "font_color": "#8076ba", "absolute": {"x": 5000, "y": 82000, "w": 90000, "h": 5000}},
        {"type": "text", "text": "DESIGNED BY: ANN JACKSON", "font_size": "8", "font_color": "#8076ba", "absolute": {"x": 2000, "y": 87000, "w": 40000, "h": 5000}},
        {"type": "text", "text": "RECREATED BY: DONNA COLES", "font_size": "8", "font_color": "#8076ba", "absolute": {"x": 68000, "y": 87000, "w": 32000, "h": 5000}},
        {"type": "text", "runs": [{"text": "http://www.workout-wednesday.com/week-30-creating-a-navigating-kpi-block/", "font_size": "8", "font_color": "#006b9e", "hyperlink": "http://www.workout-wednesday.com/week-30-creating-a-navigating-kpi-block/"}], "absolute": {"x": 5000, "y": 94000, "w": 90000, "h": 5000}},
    ]}
    editor.add_dashboard(
        "4 Box KPI",
        width=600,
        height=600,
        layout=main_layout,
        worksheet_names=list(KPI_SHEETS),
    )

    for sheet, (_dimension, dashboard, _color) in DETAIL_SHEETS.items():
        editor.add_dashboard(
            dashboard,
            width=600,
            height=600,
            layout=detail_layout(dashboard, sheet, _color),
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
    for filename in ("2019-07-25-ww30-navigation-kpi-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
