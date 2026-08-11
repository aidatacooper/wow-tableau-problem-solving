"""Build WW39 BCG growth-share matrix from locked Hyper data."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor

HYPER = next((HERE / "inputs").glob("*.hyper"))
OUT = HERE / "outputs"


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(HYPER), table_name="Extract")
    e.add_parameter(
        "No of Years",
        datatype="integer",
        default_value="2",
        domain_type="range",
        min_value="1",
        max_value="4",
        granularity="1",
    )
    e.add_parameter(
        "Sort",
        datatype="string",
        default_value="Order",
        domain_type="list",
        allowed_values=["Order", "Sales"],
    )
    e.add_calculated_field(
        "Max Year in Dataset", "{ FIXED : MAX(YEAR([Order Date])) }", datatype="integer"
    )
    e.add_calculated_field(
        "Dates to Include",
        "YEAR([Order Date]) >= [Max Year in Dataset] - ([Parameters].[No of Years] - 1)",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Sales Current Years",
        "IF YEAR([Order Date]) = [Max Year in Dataset] THEN [Sales] END",
        datatype="real",
    )
    e.add_calculated_field(
        "Sales Previous Years",
        "IF YEAR([Order Date]) <> [Max Year in Dataset] THEN [Sales] END",
        datatype="real",
    )
    e.add_calculated_field(
        "Average Sales Previous Years",
        "SUM([Sales Previous Years])/([Parameters].[No of Years]-1)",
        datatype="real",
    )
    e.add_calculated_field(
        "Sales Growth",
        "(SUM([Sales Current Years])-[Average Sales Previous Years])/[Average Sales Previous Years]",
        datatype="real",
    )
    e.add_calculated_field(
        "Market Share",
        "SUM([Sales])/TOTAL(SUM([Sales]))",
        datatype="real",
        table_calc="Rows",
    )
    e.add_calculated_field(
        "Orders Current Years",
        "COUNTD(IF YEAR([Order Date]) = [Max Year in Dataset] THEN [Order ID] END)",
        datatype="real",
    )
    e.add_calculated_field(
        "Orders Previous Years",
        "COUNTD(IF YEAR([Order Date]) <> [Max Year in Dataset] THEN [Order ID] END)",
        datatype="real",
    )
    e.add_calculated_field(
        "Average Orders Previous Years",
        "[Orders Previous Years]/([Parameters].[No of Years]-1)",
        datatype="real",
    )
    e.add_calculated_field(
        "Orders Growth",
        "([Orders Current Years]-[Average Orders Previous Years])/[Average Orders Previous Years]",
        datatype="real",
    )
    e.add_calculated_field(
        "Orders Market Share",
        "COUNTD([Order ID])/TOTAL(COUNTD([Order ID]))",
        datatype="real",
        table_calc="Rows",
    )
    e.add_calculated_field("Mid Market Share Constant", "0.07", datatype="real")
    e.add_calculated_field(
        "Mid Sales Growth Constant",
        "0.30",
        datatype="real",
    )
    e.add_calculated_field(
        "Mid Orders Growth Constant",
        "0.25",
        datatype="real",
    )
    e.add_calculated_field(
        "BCG Quadrant",
        "IF [Sales Growth] <= 0.30 AND [Market Share] <= 0.07 THEN 'Dog' ELSEIF [Market Share] <= 0.07 THEN 'Question Mark' ELSEIF [Sales Growth] > 0.30 THEN 'Star' ELSE 'Cash Cow' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "BCG Quadrant Orders",
        "IF [Orders Growth] <= 0.25 AND [Orders Market Share] <= 0.07 THEN 'Dog' ELSEIF [Orders Market Share] <= 0.07 THEN 'Question Mark' ELSEIF [Orders Growth] > 0.25 THEN 'Star' ELSE 'Cash Cow' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Manufacturer-SubCat",
        "[Manufacturer] + ' (' + [Sub-Category] + ')'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "BCG Icon",
        "IF [BCG Quadrant] = 'Star' THEN '☆' ELSEIF [BCG Quadrant] = 'Question Mark' THEN '?' ELSEIF [BCG Quadrant] = 'Cash Cow' THEN '♉' ELSE '♢' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    e.add_calculated_field(
        "BCG Icon Orders",
        "IF [BCG Quadrant Orders] = 'Star' THEN '☆' ELSEIF [BCG Quadrant Orders] = 'Question Mark' THEN '?' ELSEIF [BCG Quadrant Orders] = 'Cash Cow' THEN '♉' ELSE '♢' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    palette = {
        "Star": "#ffc000",
        "Question Mark": "#a69f9b",
        "Cash Cow": "#d3a4b3",
        "Dog": "#d5c3b8",
    }
    date_filter = [{"column": "Dates to Include", "values": ["true"]}]
    e.add_worksheet("Scatter:Orders")
    e.configure_chart(
        "Scatter:Orders",
        mark_type="Text",
        columns=["Orders Market Share"],
        rows=["Orders Growth"],
        detail="Sub-Category",
        color="BCG Quadrant Orders",
        size="Orders Current Years",
        label="BCG Icon Orders",
        tooltip=["Sub-Category", "Orders Growth", "Orders Market Share"],
        filters=date_filter,
        color_map=palette,
    )
    e.add_reference_line(
        "Scatter:Orders",
        axis_field="Orders Market Share",
        value_field="MIN(Mid Market Share Constant)",
        formula="average",
        scope="per-pane",
        label_type="none",
        probability=None,
    )
    e.add_reference_line(
        "Scatter:Orders",
        axis_field="Orders Growth",
        value_field="MIN(Mid Orders Growth Constant)",
        formula="average",
        scope="per-pane",
        label_type="none",
        probability=None,
    )
    e.add_worksheet("Scatter:Sales")
    e.configure_chart(
        "Scatter:Sales",
        mark_type="Text",
        columns=["Market Share"],
        rows=["Sales Growth"],
        detail="Sub-Category",
        color="BCG Quadrant",
        size="SUM(Sales Current Years)",
        label="BCG Icon",
        tooltip=["Sub-Category", "Sales Growth", "Market Share"],
        filters=date_filter,
        color_map=palette,
    )
    e.add_reference_line(
        "Scatter:Sales",
        axis_field="Market Share",
        value_field="MIN(Mid Market Share Constant)",
        formula="average",
        scope="per-pane",
        label_type="none",
        probability=None,
    )
    e.add_reference_line(
        "Scatter:Sales",
        axis_field="Sales Growth",
        value_field="MIN(Mid Sales Growth Constant)",
        formula="average",
        scope="per-pane",
        label_type="none",
        probability=None,
    )
    e.add_worksheet("Top 20 Orders")
    e.configure_chart(
        "Top 20 Orders",
        mark_type="Bar",
        columns=["Orders Current Years"],
        rows=["Manufacturer-SubCat"],
        color="BCG Quadrant Orders",
        label="Orders Current Years",
        sort_descending="Orders Current Years",
        filters=[
            {
                "column": "Manufacturer-SubCat",
                "top": 20,
                "by": "SUM(Sales Current Years)",
            }
        ],
        color_map=palette,
    )
    e.add_worksheet("Top 20 Bars")
    e.configure_chart(
        "Top 20 Bars",
        mark_type="Bar",
        columns=["SUM(Sales Current Years)"],
        rows=["Manufacturer-SubCat"],
        color="BCG Quadrant",
        label="SUM(Sales Current Years)",
        sort_descending="SUM(Sales Current Years)",
        filters=[
            {
                "column": "Manufacturer-SubCat",
                "top": 20,
                "by": "SUM(Sales Current Years)",
            }
        ],
        color_map=palette,
    )
    e.add_worksheet("Legend")
    e.configure_chart(
        "Legend",
        mark_type="Text",
        columns=["BCG Quadrant"],
        label="BCG Icon",
        color="BCG Quadrant",
        color_map=palette,
    )
    for s in (
        "Scatter:Orders",
        "Scatter:Sales",
        "Top 20 Orders",
        "Top 20 Bars",
        "Legend",
    ):
        e.configure_worksheet_style(
            s, hide_gridlines=True, hide_zeroline=False, hide_table_dividers=True
        )
    for s in ("Scatter:Orders", "Scatter:Sales"):
        e.configure_worksheet_style(
            s, pane_datalabel_style={"font-family": "Tableau Book", "font-size": "22"}
        )
    high_band = {
        "type": "container",
        "direction": "horizontal",
        "fixed_size": 42,
        "children": [
            {
                "type": "text",
                "text": "HIGH GROWTH LOW\nMARKET SHARE",
                "font_size": "8",
                "bold": True,
                "font_color": "#ffffff",
                "style": {"background_color": "#a69f9b"},
                "weight": 1,
            },
            {
                "type": "text",
                "text": "HIGH GROWTH HIGH MARKET SHARE",
                "font_size": "8",
                "bold": True,
                "style": {"background_color": "#ffd447"},
                "weight": 3,
            },
        ],
    }
    low_band = {
        "type": "container",
        "direction": "horizontal",
        "fixed_size": 42,
        "children": [
            {
                "type": "text",
                "text": "LOW GROWTH LOW\nMARKET SHARE",
                "font_size": "8",
                "bold": True,
                "style": {"background_color": "#d5c3b8"},
                "weight": 1,
            },
            {
                "type": "text",
                "text": "LOW GROWTH HIGH MARKET SHARE",
                "font_size": "8",
                "bold": True,
                "style": {"background_color": "#d3a4b3"},
                "weight": 3,
            },
        ],
    }
    legend_zone = {
        "type": "container",
        "direction": "horizontal",
        "children": [
            {
                "type": "text",
                "text": "♉\nCash Cows",
                "font_size": "10",
                "color": "#d3a4b3",
                "weight": 1,
            },
            {
                "type": "text",
                "text": "♢\nDogs",
                "font_size": "10",
                "color": "#d5c3b8",
                "weight": 1,
            },
            {
                "type": "text",
                "text": "?\nQuestion Marks",
                "font_size": "10",
                "color": "#a69f9b",
                "weight": 1,
            },
            {
                "type": "text",
                "text": "☆\nStars",
                "font_size": "10",
                "color": "#ffc000",
                "weight": 1,
            },
        ],
    }
    e.add_dashboard(
        "WW39 BCG Growth Share Matrix",
        width=1200,
        height=900,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 140,
                    "children": [
                        {
                            "type": "text",
                            "text": "BCG GROWTH SHARE MATRIX\nSUBCATEGORY PORTFOLIO",
                            "font_size": "18",
                            "fixed_size": 430,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "No of Years",
                            "show_title": True,
                            "mode": "compact",
                            "fixed_size": 190,
                        },
                        legend_zone,
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        {
                            "type": "container",
                            "direction": "vertical",
                            "children": [
                                {
                                    "type": "text",
                                    "text": "ORDERS",
                                    "font_size": "12",
                                    "bold": True,
                                    "fixed_size": 30,
                                },
                                high_band,
                                {
                                    "type": "worksheet",
                                    "name": "Scatter:Orders",
                                    "fit": "entire",
                                    "show_title": False,
                                    "weight": 1,
                                },
                                low_band,
                                {
                                    "type": "text",
                                    "text": "SALES",
                                    "font_size": "12",
                                    "bold": True,
                                    "fixed_size": 30,
                                },
                                high_band,
                                {
                                    "type": "worksheet",
                                    "name": "Scatter:Sales",
                                    "fit": "entire",
                                    "show_title": False,
                                    "weight": 1,
                                },
                                low_band,
                            ],
                        },
                        {
                            "type": "container",
                            "direction": "vertical",
                            "children": [
                                {
                                    "type": "text",
                                    "text": "TOP 20 MANUFACTURERS",
                                    "font_size": "12",
                                    "bold": True,
                                    "fixed_size": 30,
                                },
                                {
                                    "type": "container",
                                    "direction": "horizontal",
                                    "children": [
                                        {
                                            "type": "worksheet",
                                            "name": "Top 20 Orders",
                                            "fit": "entire",
                                            "show_title": False,
                                            "weight": 1,
                                        },
                                        {
                                            "type": "worksheet",
                                            "name": "Top 20 Bars",
                                            "fit": "entire",
                                            "show_title": False,
                                            "weight": 1,
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "CWTWB SDK REBUILD                         #WORKOUTWEDNESDAY  |  2019  |  WEEK 39                         BUILT FROM CASE CONTRACT",
                    "font_size": "8",
                    "fixed_size": 28,
                },
            ],
        },
        worksheet_names=[
            "Scatter:Orders",
            "Scatter:Sales",
            "Top 20 Orders",
            "Top 20 Bars",
        ],
    )
    OUT.mkdir(exist_ok=True)
    e.save(p, validate=False)
    return p


if __name__ == "__main__":
    stem = f"{HERE.name}-replicated-workbook"
    for suffix in (".twb", ".twbx"):
        print(build(OUT / f"{stem}{suffix}"))
