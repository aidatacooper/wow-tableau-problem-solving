from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor

H = HERE / "inputs" / "Orders (Sample - Superstore).hyper"
O = HERE / "outputs"


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(H), table_name="Extract")
    date_options = e._datasource.find("date-options")
    if date_options is not None:
        date_options.set("start-of-week", "sunday")
    e.add_parameter(
        "SELECT YEAR",
        datatype="string",
        default_value="2019",
        domain_type="list",
        allowed_values=["2016", "2017", "2018", "2019"],
    )
    e.add_parameter(
        "HIGHLIGHT TOP 3",
        datatype="string",
        default_value="WEEKS",
        domain_type="list",
        allowed_values=["MONTHS", "WEEKS", "DAYS"],
    )
    e.add_calculated_field(
        "FILTER - Year",
        "STR(YEAR([Order Date])) = [Parameters].[SELECT YEAR]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Week Index",
        "FLOAT(DATEPART('week',[Order Date]) - { FIXED MONTH([Order Date]) : MIN(DATEPART('week',[Order Date])) })",
        datatype="real",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Column Number",
        "CASE MONTH([Order Date]) WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 3 THEN 3 WHEN 4 THEN 1 WHEN 5 THEN 2 WHEN 6 THEN 3 WHEN 7 THEN 1 WHEN 8 THEN 2 WHEN 9 THEN 3 WHEN 10 THEN 1 WHEN 11 THEN 2 ELSE 3 END",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Short Weekday",
        "LEFT(DATENAME('weekday',[Order Date]),1)",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Day Month Label",
        "RIGHT('0'+STR(DAY([Order Date])),2)+'/'+RIGHT('0'+STR(MONTH([Order Date])),2)",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Total Monthly Sales",
        "{ FIXED YEAR([Order Date]), MONTH([Order Date]) : SUM([Sales]) }",
        datatype="real",
    )
    e.add_calculated_field(
        "Total Weekly Sales",
        "{ FIXED YEAR([Order Date]), WEEK([Order Date]) : SUM([Sales]) }",
        datatype="real",
    )
    e.add_calculated_field(
        "Group By Date",
        "IF [Parameters].[HIGHLIGHT TOP 3] = 'MONTHS' THEN DATETRUNC('month',[Order Date]) ELSEIF [Parameters].[HIGHLIGHT TOP 3] = 'WEEKS' THEN DATETRUNC('week',[Order Date]) ELSE [Order Date] END",
        datatype="datetime",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Value",
        "IF [Parameters].[HIGHLIGHT TOP 3] = 'MONTHS' THEN SUM([Total Monthly Sales]) ELSEIF [Parameters].[HIGHLIGHT TOP 3] = 'WEEKS' THEN SUM([Total Weekly Sales]) ELSE SUM([Sales]) END",
        datatype="real",
    )
    e.add_set(
        "In top 3",
        "Group By Date",
        basis_field="Value",
        aggregation="None",
        top_n=3,
        internal_name="[Set 1]",
    )
    e.add_calculated_field(
        "Calendar Title",
        "[Parameters].[SELECT YEAR] + ' SALES CALENDAR'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_worksheet("Title")
    e.configure_chart(
        "Title",
        mark_type="Text",
        label="Calendar Title",
        text_format={
            "font-size": "20",
            "font-family": "Tableau Medium",
            "color": "#333333",
        },
    )
    e.add_worksheet("Front")
    e.configure_chart(
        "Front",
        mark_type="Circle",
        columns=["Column Number", "WEEKDAY(Order Date)"],
        rows=["QUARTER(Order Date)", "Week Index"],
        color="In top 3",
        label="Day Month Label",
        size="SUM(Sales)",
        filters=[{"column": "FILTER - Year", "values": ["true"], "context": True}],
        tooltip=["Day Month Label", "SUM(Sales)", "Total Monthly Sales"],
        color_map={"true": "#edc948", "false": "#cfcfcf"},
    )
    e.configure_worksheet_style(
        "Front",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        label_formats=[
            {"field": "Column Number", "display": "false"},
            {"field": "Week Index", "display": "false"},
            {"field": "QUARTER(Order Date)", "display": "false"},
        ],
        pane_datalabel_style={"font-size": "6", "font-family": "Tableau Book"},
        pane_mark_style={"size": "1.263370156288147"},
    )
    quarters = {
        "type": "container",
        "direction": "vertical",
        "fixed_size": 62,
        "children": [
            {"type": "text", "text": "Q1", "font_size": "14", "fixed_size": 292},
            {
                "type": "text",
                "text": "Q2",
                "font_size": "14",
                "style": {"background_color": "#f4f4f4"},
                "fixed_size": 292,
            },
            {"type": "text", "text": "Q3", "font_size": "14", "fixed_size": 292},
            {
                "type": "text",
                "text": "Q4",
                "font_size": "14",
                "style": {"background_color": "#f4f4f4"},
                "fixed_size": 292,
            },
        ],
    }
    e.add_dashboard(
        "WW44 Sales Calendar",
        width=1600,
        height=1300,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 100,
                    "children": [
                        {
                            "type": "worksheet",
                            "name": "Title",
                            "fit": "entire",
                            "show_title": False,
                            "weight": 1,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "SELECT YEAR",
                            "mode": "compact",
                            "fixed_size": 220,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "HIGHLIGHT TOP 3",
                            "mode": "compact",
                            "fixed_size": 240,
                        },
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        quarters,
                        {
                            "type": "worksheet",
                            "name": "Front",
                            "fit": "entire",
                            "show_title": False,
                            "weight": 1,
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 44",
                    "font_size": "8",
                    "bold": True,
                    "fixed_size": 32,
                },
            ],
        },
        worksheet_names=["Title", "Front"],
    )
    O.mkdir(exist_ok=True)
    e.save(p, validate=False)
    return p


if __name__ == "__main__":
    for n in (
        "2019-11-01-ww44-sales-calendar-top3-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(O / n))
