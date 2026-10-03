from pathlib import Path
import calendar
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor
from lxml import etree

H = next((HERE / "inputs").glob("*.hyper"))
O = HERE / "outputs"


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(H), table_name="Extract")
    e.add_parameter(
        "Date", datatype="date", default_value="#2019-10-01#", domain_type="any"
    )
    e.add_parameter(
        "Time Range",
        datatype="string",
        default_value="LAST 9 MONTHS",
        domain_type="any",
    )
    e.add_calculated_field(
        "Pick Time Range",
        "IF MONTH([Order Date])=1 THEN 'LAST 3 MONTHS' ELSEIF MONTH([Order Date])=2 THEN 'LAST 6 MONTHS' ELSEIF MONTH([Order Date])=3 THEN 'LAST 9 MONTHS' ELSEIF MONTH([Order Date])=4 THEN 'LAST 12 MONTHS' ELSE 'YEAR TO DATE' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Order Date Month",
        "DATE(DATETRUNC('month',[Order Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Month Label",
        "DATENAME('month',[Order Date]) + ' ' + STR(YEAR([Order Date]))",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Time Value",
        "CASE [Parameters].[Time Range] WHEN 'LAST 3 MONTHS' THEN 3 WHEN 'LAST 6 MONTHS' THEN 6 WHEN 'LAST 9 MONTHS' THEN 9 WHEN 'LAST 12 MONTHS' THEN 12 ELSE 0 END",
        datatype="integer",
    )
    e.add_calculated_field(
        "End Date Current Period",
        "DATEADD('day',-1,DATEADD('month',1,DATETRUNC('month',[Parameters].[Date])))",
        datatype="date",
    )
    e.add_calculated_field(
        "Start Date Current Period",
        "IF [Time Value]=0 THEN DATETRUNC('year',[Parameters].[Date]) ELSE DATEADD('month',1-[Time Value],DATETRUNC('month',[Parameters].[Date])) END",
        datatype="date",
    )
    e.add_calculated_field(
        "Start Date Prior Period",
        "IF [Time Value]=0 THEN DATEADD('year',-1,DATETRUNC('year',[Parameters].[Date])) ELSE DATEADD('month',-[Time Value],[Start Date Current Period]) END",
        datatype="date",
    )
    e.add_calculated_field(
        "Current Period Sales",
        "IF [Order Date] >= [Start Date Current Period] AND [Order Date] <= [End Date Current Period] THEN [Sales] END",
        datatype="real",
    )
    e.add_calculated_field(
        "Prior Period Sales",
        "IF [Order Date] >= [Start Date Prior Period] AND [Order Date] < [Start Date Current Period] THEN [Sales] END",
        datatype="real",
    )
    e.add_calculated_field(
        "End Date Prior Period",
        "IF [Time Value]=0 THEN DATEADD('year',-1,[End Date Current Period]) ELSE DATEADD('month',-[Time Value],[End Date Current Period]) END",
        datatype="date",
    )
    e.add_calculated_field(
        "Dates To Include",
        "([Order Date] >= [Start Date Current Period] AND [Order Date] <= [End Date Current Period]) OR ([Order Date] >= [Start Date Prior Period] AND [Order Date] <= [End Date Prior Period])",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Period",
        "IF [Order Date] >= [Start Date Current Period] THEN 'CURRENT PERIOD' ELSE 'PRIOR PERIOD' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field("Index", "INDEX()", datatype="integer", table_calc="Rows")
    e.add_calculated_field(
        "Date Selector Colour",
        "IF [Order Date Month] >= [Start Date Current Period] AND [Order Date Month] <= [End Date Current Period] THEN 'CURRENT PERIOD' ELSEIF [Order Date Month] >= [Start Date Prior Period] AND [Order Date Month] <= [End Date Prior Period] THEN 'PRIOR PERIOD' ELSE 'OTHER' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Time Selector Colour",
        "IF [Pick Time Range] = [Parameters].[Time Range] THEN 'SELECTED' ELSE 'OTHER' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Dashboard Title",
        "'SALES COMPARISON | ' + [Parameters].[Time Range] + CHAR(10) + 'CURRENT PERIOD (' + DATENAME('month',[Start Date Current Period]) + ' ' + STR(YEAR([Start Date Current Period])) + ' - ' + DATENAME('month',[End Date Current Period]) + ' ' + STR(YEAR([End Date Current Period])) + ')   |   PRIOR PERIOD (' + DATENAME('month',[Start Date Prior Period]) + ' ' + STR(YEAR([Start Date Prior Period])) + ' - ' + DATENAME('month',[End Date Prior Period]) + ' ' + STR(YEAR([End Date Prior Period])) + ')'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Comparison Sales",
        "IF [Order Date] >= [Start Date Current Period] AND [Order Date] <= [End Date Current Period] THEN [Sales] ELSEIF [Order Date] >= [Start Date Prior Period] AND [Order Date] <= [End Date Prior Period] THEN [Sales] END",
        datatype="real",
    )
    e.add_calculated_field(
        "Relative Month",
        "IF [Order Date] >= [Start Date Current Period] AND [Order Date] <= [End Date Current Period] THEN DATEDIFF('month',[Start Date Current Period],DATETRUNC('month',[Order Date])) ELSEIF [Order Date] >= [Start Date Prior Period] AND [Order Date] <= [End Date Prior Period] THEN DATEDIFF('month',[Start Date Prior Period],DATETRUNC('month',[Order Date])) END",
        datatype="integer",
    )
    e.add_calculated_field(
        "Line End Label",
        "IF DATETRUNC('month',[Order Date]) = DATETRUNC('month',[Start Date Current Period]) OR DATETRUNC('month',[Order Date]) = DATETRUNC('month',[End Date Current Period]) OR DATETRUNC('month',[Order Date]) = DATETRUNC('month',[Start Date Prior Period]) OR DATETRUNC('month',[Order Date]) = DATETRUNC('month',[End Date Prior Period]) THEN DATENAME('month',[Order Date]) + ' ' + STR(YEAR([Order Date])) END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    for n in ("Viz", "Date Selector", "Pick Time Selector", "Title"):
        e.add_worksheet(n)
    e.configure_chart(
        "Viz",
        mark_type="Line",
        columns=["MIN(Relative Month)"],
        rows=["SUM(Sales)"],
        color="Date Selector Colour",
        label="Order Date Month",
        filters=[{"column": "Dates To Include", "values": ["true"]}],
        tooltip=["SUM(Sales)"],
        color_map={
            "CURRENT PERIOD": "#23a4c7",
            "PRIOR PERIOD": "#55585d",
            "OTHER": "#cfcfcf",
        },
        text_format={"font-size": "9", "font-family": "Tableau Book"},
    )
    e.configure_chart(
        "Date Selector",
        mark_type="Circle",
        rows=["Month Label"],
        color="Date Selector Colour",
        sort_descending="Order Date Month",
        color_map={
            "CURRENT PERIOD": "#23a4c7",
            "PRIOR PERIOD": "#55585d",
            "OTHER": "#d3d3d3",
        },
    )
    e.configure_chart(
        "Pick Time Selector",
        mark_type="Circle",
        rows=["Pick Time Range"],
        color="Time Selector Colour",
        color_map={"SELECTED": "#fc719e", "OTHER": "#d3d3d3"},
    )
    e.configure_chart("Title", mark_type="Text", label="Dashboard Title")
    selector = e._find_worksheet("Date Selector")
    selector_view = selector.find("table/view")
    shelf_sorts = selector_view.find("shelf-sorts")
    if shelf_sorts is not None:
        selector_view.remove(shelf_sorts)
    month_ci = e.field_registry.parse_expression("Month Label")
    month_ref = e.field_registry.resolve_full_reference(month_ci.instance_name)
    manual_sort = etree.Element(
        "sort", column=month_ref, direction="ASC", **{"class": "manual"}
    )
    dictionary = etree.SubElement(manual_sort, "dictionary")
    for year in range(2019, 2015, -1):
        for month in range(12, 0, -1):
            etree.SubElement(
                dictionary, "bucket"
            ).text = f'"{calendar.month_name[month]} {year}"'
    aggregation = selector_view.find("aggregation")
    if aggregation is None:
        selector_view.append(manual_sort)
    else:
        aggregation.addprevious(manual_sort)
    for s in ("Viz", "Date Selector", "Pick Time Selector"):
        e.configure_worksheet_style(
            s,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            pane_datalabel_style={"font-size": "8"},
        )
    e.add_dashboard(
        "WW42 Sales Comparison",
        width=1100,
        height=1000,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        {
                            "type": "container",
                            "direction": "vertical",
                            "children": [
                                {
                                    "type": "worksheet",
                                    "name": "Title",
                                    "fit": "entire",
                                    "show_title": False,
                                    "fixed_size": 70,
                                },
                                {
                                    "type": "worksheet",
                                    "name": "Viz",
                                    "fit": "entire",
                                    "show_title": False,
                                    "weight": 1,
                                },
                            ],
                        },
                        {
                            "type": "container",
                            "direction": "vertical",
                            "fixed_size": 265,
                            "children": [
                                {
                                    "type": "text",
                                    "text": "PICK TIME RANGE",
                                    "font_size": "10",
                                    "bold": True,
                                    "fixed_size": 30,
                                },
                                {
                                    "type": "worksheet",
                                    "name": "Pick Time Selector",
                                    "show_title": False,
                                    "fixed_size": 150,
                                },
                                {
                                    "type": "text",
                                    "text": "PICK END MONTH",
                                    "font_size": "10",
                                    "bold": True,
                                    "fixed_size": 30,
                                },
                                {
                                    "type": "worksheet",
                                    "name": "Date Selector",
                                    "show_title": False,
                                    "weight": 1,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "DESIGNED BY : ANN JACKSON                  #WORKOUTWEDNESDAY  |  2019  |  WEEK 42                  RECREATED BY : DONNA COLES",
                    "font_size": "8",
                    "bold": True,
                    "color": "#fc719e",
                    "fixed_size": 35,
                },
            ],
        },
        worksheet_names=["Title", "Date Selector", "Pick Time Selector", "Viz"],
    )
    e.add_dashboard_action(
        "WW42 Sales Comparison",
        "parameter",
        "Date Selector",
        source_field="Order Date Month",
        target_parameter="Date",
        aggregation="attr",
        caption="Set Date",
    )
    e.add_dashboard_action(
        "WW42 Sales Comparison",
        "parameter",
        "Pick Time Selector",
        source_field="Pick Time Range",
        target_parameter="Time Range",
        aggregation="attr",
        caption="Pick Time Range",
    )
    O.mkdir(exist_ok=True)
    e.save(p, validate=False)
    return p


if __name__ == "__main__":
    for n in (
        "2019-10-19-ww42-comparative-line-dynamic-inputs-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(O / n))
