"""Build WW40 selectable area/bar/line views from locked Hyper data."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor

HYPER = next((HERE / "inputs").glob("*.hyper"))
OUT = HERE / "outputs"


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(HYPER), table_name="Extract")
    e.add_parameter(
        "Choose Display Type",
        datatype="string",
        default_value="Bar",
        domain_type="list",
        allowed_values=["Area", "Bar", "Line"],
    )
    e.add_calculated_field(
        "FILTER:Display",
        "CASE [Parameters].[Choose Display Type] WHEN 'Line' THEN 'Line' WHEN 'Bar' THEN 'Bar' ELSE 'Area' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Order Month",
        "DATE(DATETRUNC('month',[Order Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    for n, m in [("Area", "Area"), ("Bar", "Bar"), ("Line", "Line")]:
        e.add_calculated_field(
            "Preview Choice " + n,
            "'" + n + "'",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        group = {"Area": 3, "Bar": 4, "Line": 5}[n]
        e.add_worksheet(n)
        e.configure_chart(
            n,
            mark_type=m,
            columns=["EXACTDATE(Order Month)"],
            rows=["SUM(Sales)"],
            filters=[
                {"column": "FILTER:Display", "values": [n], "filter_group": group}
            ],
        )
        e.add_worksheet("Preview:" + n)
        e.configure_chart(
            "Preview:" + n,
            mark_type=m,
            columns=["EXACTDATE(Order Month)"],
            rows=["SUM(Sales)"],
            filters=[
                {"column": "FILTER:Display", "values": [n], "filter_group": group}
            ],
        )
        e.configure_worksheet_style(
            n, hide_gridlines=True, hide_zeroline=True, hide_axes=False
        )
        e.configure_worksheet_style(
            "Preview:" + n, hide_gridlines=True, hide_zeroline=True, hide_axes=True
        )
    main = [
        {
            "type": "worksheet",
            "name": n,
            "fit": "entire",
            "show_title": False,
            "absolute": {"x": 0, "y": 9286, "w": 100000, "h": 50000},
        }
        for n in ("Area", "Bar", "Line")
    ]
    preview = [
        {
            "type": "worksheet",
            "name": "Preview:" + n,
            "fit": "entire",
            "show_title": False,
            "absolute": {"x": 19000, "y": 64000, "w": 81000, "h": 30000},
        }
        for n in ("Area", "Bar", "Line")
    ]
    e.add_dashboard(
        "WW40 Show Hide Charts",
        width=1000,
        height=700,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 65,
                    "children": [
                        {
                            "type": "text",
                            "text": "Sales by Month",
                            "font_size": "15",
                            "weight": 1,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "Choose Display Type",
                            "mode": "compact",
                            "fixed_size": 205,
                        },
                    ],
                },
                {"type": "container", "direction": "vertical", "children": main},
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 220,
                    "children": [
                        {
                            "type": "text",
                            "text": "Display Preview\nChoose display above",
                            "bold": True,
                            "fixed_size": 190,
                        }
                    ]
                    + preview,
                },
                {
                    "type": "text",
                    "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 40",
                    "font_size": "8",
                    "fixed_size": 32,
                },
            ],
        },
        worksheet_names=[
            "Area",
            "Bar",
            "Line",
            "Preview:Area",
            "Preview:Bar",
            "Preview:Line",
        ],
    )
    OUT.mkdir(exist_ok=True)
    e.save(p, validate=False)
    return p


if __name__ == "__main__":
    for n in (
        "2019-10-07-ww40-show-hide-sheets-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUT / n))
