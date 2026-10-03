"""Build WW34 independently from extracted Hyper using public cwtwb APIs."""

from pathlib import Path
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs/TEMP_1aj3wwv0bifaq61233rve10455iy.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"
DASHBOARD_NAME = "2019_08_21_WW34_TopN_Single_Sheet"


def addressing():
    rank = {
        "ordering_type": "Field",
        "level_break": "Manfacturer Category",
        "order": ["Region", "Manfacturer Category"],
        "sort": {"direction": "DESC", "using": "SUM(Quantity)"},
    }
    return {
        "Index": [rank],
        "FILTER Index": [{"ordering_type": "Columns"}, {"field": "Index", **rank}],
        "LABEL:Manufacturer": [
            {"ordering_type": "Columns"},
            {"field": "Manufacturer + Rank", "ordering_type": "Columns"},
            {"field": "Index Rank", "ordering_type": "Columns"},
            {"field": "Index", **rank},
        ],
    }


def build(output_twb: Path, output_twbx: Path) -> Path:
    # From-scratch entry: keep original Hyper, drop all author views.
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Parameters -------------------------------------------------------
    editor.add_parameter(
        "Top n Manufacturers",
        datatype="integer",
        default_value="15",
        domain_type="range",
        min_value="1",
        max_value="100",
        granularity="1",
    )
    editor.add_parameter(
        "Include Other",
        datatype="boolean",
        default_value="false",
        alias="NO",
        domain_type="list",
        allowed_values=["true", "false"],
        allowed_aliases={"true": "YES", "false": "NO"},
    )

    # --- Calculated fields (dependencies first) ---------------------------
    editor.add_calculated_field(
        "Manufacturer",
        "MID([Product Name],1, FINDNTH([Product Name],' ',1)-1)",
        datatype="string",
    )
    for region in ("Central", "East", "South", "West"):
        editor.add_calculated_field(
            f"{region} - Qty",
            f"IF [Region] = '{region}' THEN [Quantity] END",
            datatype="integer",
        )

    # Manfacturer Category: references the four top-N sets by name.  The sets
    # are created below; unresolved references stay as their clean bracket
    # names, which is exactly the sets' internal name, so they resolve.
    editor.add_calculated_field(
        "Manfacturer Category",
        "IF [Region]='Central' AND [Top Central] THEN [Manufacturer] "
        "ELSEIF [Region]='East' AND [Top East] THEN [Manufacturer] "
        "ELSEIF [Region]='South' AND [Top South] THEN [Manufacturer] "
        "ELSEIF [Region]='West' AND [Top West] THEN [Manufacturer] "
        "ELSE 'Other' END",
        datatype="string",
    )

    # Index is ordinal so the rows shelf renders discrete 1..N row headers.
    editor.add_calculated_field(
        "Index",
        "INDEX()",
        datatype="integer",
        field_type="ordinal",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Index Rank",
        "'(#' + STR([Index]) + ')'",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Manufacturer + Rank",
        "ATTR([Manfacturer Category]) + ' ' + [Index Rank]",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "FILTER Index",
        "[Index] <= [Top n Manufacturers]",
        datatype="boolean",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "FILTER - Other",
        "NOT([Include Other]) AND [Manfacturer Category] = 'Other'",
        datatype="boolean",
        role="dimension",
    )
    editor.add_calculated_field(
        "LABEL:Manufacturer",
        "IF ATTR([Highlighted Manufacturer]) THEN [Manufacturer + Rank] "
        "ELSE ATTR([Manfacturer Category]) END",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field("MIN(0)", "MIN(0)", datatype="integer")

    # --- Sets -------------------------------------------------------------
    editor.add_set(
        "Top Central",
        "Manufacturer",
        basis_field="Central - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top East",
        "Manufacturer",
        basis_field="East - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top South",
        "Manufacturer",
        basis_field="South - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top West",
        "Manufacturer",
        basis_field="West - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Highlighted Manufacturer",
        "Manfacturer Category",
    )

    # --- Worksheet: dual axis on columns ----------------------------------
    editor.add_worksheet("Viz")
    editor.configure_dual_axis(
        "Viz",
        mark_type_1="GanttBar",
        mark_type_2="Bar",
        # Region partitions the overlaid MIN(0) labels and SUM(Quantity) bars.
        columns=["Region", "[MIN(0)]", "SUM(Quantity)"],
        rows=["Index"],
        dual_axis_shelf="columns",
        synchronized=True,
        color_1="Region",
        label_1="LABEL:Manufacturer",
        hide_axes=True,
        detail_1="Manfacturer Category",
        color_2="Region",
        detail_2="Manfacturer Category",
        label_2="SUM(Quantity)",
        filters=[
            {"column": "FILTER - Other", "values": [False]},
            {"column": "FILTER Index", "values": [True]},
        ],
        table_calc_overrides=addressing(),
        color_map_1={
            "South": "#027b8e",
            "East": "#6fb899",
            "Central": "#8175aa",
            "West": "#9f8f12",
        },
    )

    editor.set_worksheet_rich_title(
        "Viz",
        runs=[
            {
                "text": "Top <[Parameters].[Top n Manufacturers]> Manufacturers by Region using a Single Worksheet",
                "fontsize": 16,
                "fontcolor": "#666666",
                "fontalignment": "1",
            },
            {
                "text": "\nhover to highlight rank",
                "fontsize": 12,
                "italic": True,
                "fontcolor": "#666666",
                "fontalignment": "1",
            },
        ],
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=False,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        cell_formats=[{"field": "Index", "height": 34}],
        header_formats=[{"height_header": 24}, {"field": "Region", "height": 40}],
        label_formats=[
            {"field": "Index", "display": False},
            {"field": "Region", "font-size": 14},
        ],
        axis_style={
            "per_field": [
                {
                    "field": field,
                    "attr": "display",
                    "scope": "cols",
                    "class": cls,
                    "value": "false",
                }
                for field in ["SUM(Quantity)", "[MIN(0)]"]
                for cls in ["0", "1"]
            ]
        },
        pane_datalabel_style={"color-mode": "match", "font-size": 10},
        panes_style={
            "1": {
                "cell_style": {"text_align": "left", "vertical_align": "center"},
                "datalabel_style": {"color-mode": "match", "font-size": 10},
            },
            "2": {"datalabel_style": {"color-mode": "match", "font-size": 10}},
        },
    )
    # --- Dashboard --------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "worksheet",
                "name": "Viz",
                "fit": "standard",
                "absolute": {"x": 800, "y": 1000, "w": 80000, "h": 90250},
            },
            {
                "type": "paramctrl",
                "parameter": "Include Other",
                "mode": "compact",
                "absolute": {"x": 80800, "y": 1000, "w": 18400, "h": 7500},
            },
            {
                "type": "paramctrl",
                "parameter": "Top n Manufacturers",
                "mode": "type_in",
                "absolute": {"x": 80800, "y": 8500, "w": 18400, "h": 7500},
            },
            {
                "type": "text",
                "text": "DESIGNED BY : Jeffrey A. Schaffer",
                "font_size": "8",
                "absolute": {"x": 800, "y": 91250, "w": 22700, "h": 4055},
            },
            {
                "type": "text",
                "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 34",
                "font_size": "8",
                "absolute": {"x": 23500, "y": 91250, "w": 55900, "h": 4055},
            },
            {
                "type": "text",
                "text": "RECREATED BY : Donna Coles",
                "font_size": "8",
                "absolute": {"x": 79400, "y": 91250, "w": 19800, "h": 4055},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "http://www.workout-wednesday.com/week-34-can-you-build-a-top-n-bar-chart-on-a-single-worksheet/",
                        "font_size": "8",
                        "font_color": "#3093bb",
                        "hyperlink": "http://www.workout-wednesday.com/week-34-can-you-build-a-top-n-bar-chart-on-a-single-worksheet/",
                    }
                ],
                "absolute": {"x": 15600, "y": 95305, "w": 67600, "h": 3695},
            },
            {
                "type": "text",
                "text": "DATA : Superstore Sales",
                "font_size": "8",
                "absolute": {"x": 83200, "y": 95305, "w": 16000, "h": 3695},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD_NAME,
        width=1000,
        height=800,
        layout=layout,
        worksheet_names=["Viz"],
    )

    # --- Set Action (on-hover fills Highlighted Manufacturer) --------------
    editor.add_dashboard_set_action(
        DASHBOARD_NAME,
        source_sheet="Viz",
        target_set="Highlighted Manufacturer",
        event_type="on-hover",
        caption="Highlight Rank",
        clear_option="exclude-all",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_twb, validate=False)
    editor.save(output_twbx, validate=False)

    return output_twb


if __name__ == "__main__":
    print(
        build(
            OUTPUT_DIR
            / "2019-09-02-ww34-top-n-single-worksheet-replicated-workbook.twb",
            OUTPUT_DIR / "replicated-workbook.twbx",
        )
    )
