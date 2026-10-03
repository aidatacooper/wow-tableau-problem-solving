"""Three native ranked lists with window statistics and a shared date parameter."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_03_11_WW11_Smart_Ranking"


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/federated_08xa5gt11f4gl80zj8uk20.hyper"))
    e.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    e.add_parameter("Order Date Parameter", "date", "#2019-05-08#", domain_type="any")
    for name, formula, datatype, role, kind in [
        (
            "Dates to Include",
            "[Order Date]>=DATEADD('day',-84,[Order Date Parameter]) AND [Order Date]<=[Order Date Parameter]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Day of Week",
            "UPPER(DATENAME('weekday',[Order Date Parameter],'Monday'))",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Weekdays to Include",
            "[Day of Week]=UPPER(DATENAME('weekday',[Order Date],'Monday'))",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Selected Date",
            "IF [Order Date]=[Order Date Parameter] THEN '►' ELSE '' END",
            "string",
            "dimension",
            "nominal",
        ),
        ("Order Date Copy", "[Order Date]", "date", "dimension", "ordinal"),
        (
            "Question",
            "'HOW DOES '+[Day of Week]+' '+STR(MONTH([Order Date Parameter]))+'/'+STR(DAY([Order Date Parameter]))+'/'+STR(YEAR([Order Date Parameter]))+' COMPARE TO THE PRIOR 12 '+[Day of Week]+'S?'",
            "string",
            "dimension",
            "nominal",
        ),
        ("# Orders", "COUNTD([Order ID])", "integer", "measure", "quantitative"),
    ]:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    for metric, measure in [
        ("Sales", "SUM(Sales)"),
        ("Orders", "# Orders"),
        ("Qty", "SUM(Quantity)"),
    ]:
        formula_measure = {
            "Sales": "SUM([Sales])",
            "Orders": "[# Orders]",
            "Qty": "SUM([Quantity])",
        }[metric]
        color, header, rank = (
            "COLOUR:" + metric,
            metric + " Header",
            "Selected Date " + metric + " Rank",
        )
        e.add_calculated_field(
            color,
            f"IF {formula_measure}=WINDOW_MAX({formula_measure}) THEN 1 ELSEIF {formula_measure}=WINDOW_MIN({formula_measure}) THEN 4 ELSEIF {formula_measure}>=WINDOW_AVG({formula_measure}) THEN 2 ELSE 3 END",
            datatype="integer",
            role="measure",
            field_type="quantitative",
        )
        e.add_calculated_field(
            header,
            f"IF [{color}]<=2 THEN 'ABOVE\nAVERAGE' ELSE 'BELOW\nAVERAGE' END",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        e.add_calculated_field(
            rank,
            f"IF ATTR([Order Date])=[Order Date Parameter] THEN RANK_UNIQUE({formula_measure}) END",
            datatype="integer",
            role="measure",
            field_type="quantitative",
        )
        addressing = {
            "ordering_type": "Field",
            "order": ["[Order Date Copy]", "Selected Date", "[Order Date]"],
        }
        sheet = metric + " Rank"
        e.add_worksheet(sheet)
        e.configure_layered_chart(
            sheet,
            rows=[header, "[Order Date Copy]", "Selected Date", "[Order Date]"],
            panes=[
                {
                    "mark_type": "Square",
                    "color": color,
                    "label": measure,
                    "detail": rank,
                    "mark_style": {
                        "size": "14.547999382019043",
                        "mark-labels-show": "true",
                    },
                    "tooltip": ["[Order Date]", measure],
                }
            ],
            filters=[
                {"column": "Dates to Include", "values": [True]},
                {"column": "Weekdays to Include", "values": [True]},
            ],
            sort_field="[Order Date Copy]",
            sort_descending=measure,
            table_calc_overrides={
                color: [addressing],
                header: [addressing, dict(addressing, field=color)],
                rank: [addressing],
            },
        )
        e.configure_worksheet_style(
            sheet,
            table_formats=[
                {"attr": "band-level", "scope": "rows", "value": "3"},
                {"attr": "band-size", "scope": "rows", "value": "1"},
            ],
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            cell_formats=[
                {
                    "field": "[Order Date]",
                    "height": "22",
                    "font-family": "Tableau Medium",
                    "font-size": "8",
                }
            ],
            header_formats=[
                {"field": "Selected Date", "width": "16"},
                {"field": "[Order Date]", "width": "80"},
                {"field": header, "width": "40"},
                {"scope": "rows", "band-color": "#d4d4d4"},
            ],
            label_formats=[
                {"field": "[Order Date Copy]", "display": "false"},
                {
                    "field": "[Order Date]",
                    "text-format": "mm/dd/yyyy",
                    "font-size": "8",
                    "font-family": "Tableau Medium",
                    "font-weight": "bold",
                    "color": "#333333",
                },
                {"scope": "rows", "text-align": "right"},
                {"field": header, "text-orientation": "-90", "font-size": "8"},
                {"field": "Selected Date", "font-size": "8"},
            ],
            color_style={"field": color, "palette": "tableau-map-temperatur"},
            pane_datalabel_style={"font-family": "Tableau Book", "font-size": "8"},
        )
        e.set_worksheet_rich_title(
            sheet,
            [
                {
                    "text": "#<"
                    + rank
                    + "> IN "
                    + ("QUANTITY" if metric == "Qty" else metric.upper()),
                    "bold": True,
                    "fontsize": 10,
                    "fontalignment": 1,
                }
            ],
        )
    e.add_worksheet("Title")
    e.configure_layered_chart(
        "Title",
        panes=[
            {
                "mark_type": "Text",
                "label": "Question",
                "mark_style": {"mark-labels-show": "true"},
                "label_runs": [
                    {
                        "field": "Question",
                        "fontsize": 10,
                        "fontname": "Tableau Medium",
                        "fontcolor": "#333333",
                        "fontalignment": 1,
                    }
                ],
            }
        ],
    )
    layout = {
        "type": "container",
        "direction": "vertical",
        "style": {"padding": 10, "background-color": "#eeeeee"},
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 55,
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Title",
                        "show_title": False,
                        "fit": "entire",
                    },
                    {
                        "type": "paramctrl",
                        "parameter": "Order Date Parameter",
                        "mode": "datetime",
                        "show_title": False,
                        "fixed_size": 100,
                    },
                ],
            },
            {
                "type": "container",
                "direction": "horizontal",
                "children": [
                    {
                        "type": "worksheet",
                        "name": metric + " Rank",
                        "fit": "entire",
                        "show_title": True,
                        "style": {
                            "margin": 6,
                            "background-color": "#ffffff",
                            "padding": 4,
                        },
                    }
                    for metric in ["Sales", "Orders", "Qty"]
                ],
            },
            {
                "type": "text",
                "text": "#WOW2020 WEEK 11 | Ann Jackson | Recreated with cwtwb",
                "font_size": 8,
                "fixed_size": 25,
            },
        ],
    }
    e.add_dashboard(
        DASHBOARD,
        width=700,
        height=450,
        worksheet_names=["Title", "Sales Rank", "Orders Rank", "Qty Rank"],
        layout=layout,
    )
    e.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    path.parent.mkdir(parents=True, exist_ok=True)
    e.save(path, validate=False)
    return path


if __name__ == "__main__":
    print(build())
