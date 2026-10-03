"""Build fiscal October reporting and dynamic budget controls from Hyper data."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_06_24_WW26_FY_Reporting"
COLORS = {
    "Difference < -5%": "#d81159",
    "Difference > 5%": "#008682",
    "-5% <= Difference <= 5%": "#ffe00a",
}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Week 26 (2020_06_24_WW26).hyper"))
    e.set_field_fiscal_year_start("Accounting Date", 10)
    for name, value in [("Budget Sales (M)", "2300"), ("Budget OPP (M)", "3000")]:
        e.add_parameter(
            name, datatype="integer", default_value=value, domain_type="any"
        )
    e.add_parameter(
        "Compare Filter",
        datatype="integer",
        default_value="0",
        domain_type="list",
        allowed_values=["0", "1"],
        allowed_aliases={"0": "FYTD vs Budget FYTD", "1": "FYTD vs Prior FYTD"},
        alias="FYTD vs Budget FYTD",
    )

    def calc(name, formula, datatype="real", role="measure", kind="quantitative"):
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )

    calc("Sales", "IF STARTSWITH([Account Number],'5') THEN [Value] END")
    calc(
        "OPP",
        "IF STARTSWITH([Account Number],'5') OR STARTSWITH([Account Number],'696') THEN [Value] END",
    )
    calc(
        "Current Month",
        "DATE(DATETRUNC('month',{FIXED:MAX([Accounting Date])}))",
        "date",
        "dimension",
        "ordinal",
    )
    calc(
        "Current Month Prev FY",
        "DATE(DATEADD('year',-1,[Current Month]))",
        "date",
        "dimension",
        "ordinal",
    )
    calc(
        "FY Start Current Year",
        "DATE(DATEADD('month',9,DATETRUNC('year',DATEADD('month',-9,[Current Month]))))",
        "date",
        "dimension",
        "ordinal",
    )
    calc(
        "Budget Visible",
        "[Parameters].[Parameter 3]=0",
        "boolean",
        "dimension",
        "nominal",
    )
    calc(
        "Fiscal Year",
        "'FY ' + STR(YEAR(DATEADD('month',3,[Accounting Date])))",
        "string",
        "dimension",
        "nominal",
    )
    calc(
        "Latest Month",
        "IF DATETRUNC('month',[Accounting Date])=[Current Month] THEN [Accounting Date] END",
        "date",
        "dimension",
        "ordinal",
    )
    calc(
        "Legend Label",
        "CASE [Account Number] WHEN '69Z99999' THEN 'Difference > 5%' WHEN '95U19440' THEN 'Difference < -5%' ELSE '-5% <= Difference <= 5%' END",
        "string",
        "dimension",
        "nominal",
    )
    calc("Zero", "0.0")
    calc("Legend Point", "MIN(0.5)")
    calc(
        "Legend Sort",
        "CASE [Legend Label] WHEN 'Difference > 5%' THEN 3 WHEN 'Difference < -5%' THEN 1 ELSE 2 END",
    )
    metrics = []
    for metric, param in [("Sales", "1"), ("OPP", "2")]:
        calc(
            f"Current FYTD {metric}",
            f"IF DATETRUNC('month',[Accounting Date])>=[FY Start Current Year] AND DATETRUNC('month',[Accounting Date])<=[Current Month] THEN [{metric}] END",
        )
        calc(
            f"Prev FYTD {metric}",
            f"IF DATETRUNC('month',[Accounting Date])<DATEADD('month',1,[Current Month Prev FY]) THEN [{metric}] END",
        )
        calc(f"Budget {metric} Ref Line", f"[Parameters].[Parameter {param}]*1000000")
        calc(
            f"{metric} Ref Line",
            f"IF [Parameters].[Parameter 3]=0 THEN MIN([Budget {metric} Ref Line]) ELSE SUM([Prev FYTD {metric}]) END",
        )
        calc(f"{metric} Diff", f"SUM([Current FYTD {metric}])-[{metric} Ref Line]")
        calc(f"{metric} Diff %", f"[{metric} Diff]/[{metric} Ref Line]")
        calc(
            f"COLOUR:{metric} Diff",
            f"IF [{metric} Diff %]<-0.05 THEN 'Difference < -5%' ELSEIF [{metric} Diff %]>0.05 THEN 'Difference > 5%' ELSE '-5% <= Difference <= 5%' END",
            "string",
            "measure",
            "nominal",
        )
        calc(
            f"Current Month {metric}",
            f"IF DATETRUNC('month',[Accounting Date])=[Current Month] THEN [{metric}] END",
        )
        for field in [
            metric,
            f"Current FYTD {metric}",
            f"Prev FYTD {metric}",
            f"Budget {metric} Ref Line",
            f"{metric} Ref Line",
            f"{metric} Diff",
        ]:
            e.set_field_format(field, 'c"$"#,##0,,M;-"$"#,##0,,M')
        e.set_field_format(f"{metric} Diff", '*\u25b2"$"#,##0,,M;\u25bc"$"#,##0,,M')
        e.set_field_format(f"{metric} Diff %", "p0.0%")
        e.set_datasource_color_palette(f"COLOUR:{metric} Diff", COLORS)
        metrics += [
            f"SUM(Current FYTD {metric})",
            f"SUM(Prev FYTD {metric})",
            f"{metric} Ref Line",
            f"{metric} Diff",
            f"{metric} Diff %",
        ]
    e.set_datasource_color_palette(
        "Fiscal Year", {"FY 2019": "#6c6c6c", "FY 2020": "#5557eb"}
    )
    e.set_datasource_color_palette("Legend Label", COLORS)
    names = [
        "Data",
        "Diff Legend",
        "OPP Bar",
        "OPP KPI",
        "OPP Trend",
        "Param Pop",
        "Sales Bar",
        "Sales KPI",
        "Sales Trend",
        "Year Legend",
    ]
    for sheet in names:
        e.add_worksheet(sheet)
    e.configure_layered_chart(
        "Data",
        rows=["Measure Names"],
        panes=[
            {"mark_type": "Text", "label": "Multiple Values", "measure_values": metrics}
        ],
    )
    for metric in ["Sales", "OPP"]:
        e.configure_chart(
            f"{metric} Bar",
            mark_type="Bar",
            columns=[f"SUM(Current FYTD {metric})"],
            color=f"COLOUR:{metric} Diff",
            tooltip=[f"{metric} Ref Line", f"{metric} Diff", f"{metric} Diff %"],
            mark_sizing_off=True,
        )
        e.add_reference_line(
            f"{metric} Bar",
            axis_field=f"SUM(Current FYTD {metric})",
            value_field=f"{metric} Ref Line",
            label_type="value",
            tooltip="Reference = <Value>",
        )
        e.configure_reference_line_style(
            f"{metric} Bar",
            "refline0",
            {
                "fill-above": "#00000000",
                "fill-below": "#00000000",
                "stroke-color": "#1b1b1b",
                "font-size": 8,
                "vertical-align": "top",
                "text-align": "left",
                "background-color": "#ffffff7f",
            },
        )
        e.configure_chart(
            f"{metric} KPI",
            mark_type="Text",
            label_runs=[
                {
                    "field": f"{metric} Diff",
                    "fontsize": 9,
                    "fontcolor": "#333333",
                    "fontalignment": "2",
                },
                {"text": "\n", "fontsize": 9, "fontalignment": "2"},
                {
                    "field": f"{metric} Diff %",
                    "fontsize": 9,
                    "fontcolor": "#333333",
                    "fontalignment": "2",
                },
            ],
            label_extra=[f"{metric} Diff", f"{metric} Diff %"],
            tooltip=[f"SUM(Current FYTD {metric})", f"{metric} Ref Line"],
        )
        e.configure_layered_chart(
            f"{metric} Trend",
            columns=["MONTH(Accounting Date)"],
            rows=[f"SUM({metric})", f"SUM(Current Month {metric})"],
            panes=[
                {
                    "axis": f"SUM({metric})",
                    "mark_type": "Line",
                    "color": "Fiscal Year",
                    "labels": [f"SUM(Current Month {metric})"],
                    "mark_sizing_off": True,
                    "mark_style": {
                        "size": "0.42779004573822021"
                        if metric == "Sales"
                        else "0.44977900385856628",
                        "mark-labels-mode": "all",
                        "mark-labels-show": "true",
                        "font-size": "8",
                    },
                },
                {
                    "axis": f"SUM(Current Month {metric})",
                    "mark_type": "Circle",
                    "mark_sizing_off": True,
                    "mark_style": {
                        "size": "0.85",
                        "mark-color": "#000000",
                        "mark-labels-show": "false",
                    },
                },
            ],
            axis_shelf="rows",
            fold_axes=True,
            synchronized=True,
        )
        e.add_reference_line(
            f"{metric} Trend",
            axis_field=f"SUM({metric})",
            value_field=f"SUM({metric})",
            formula="average",
            scope="per-table",
            label_type="custom",
            label="Avg",
            tooltip="Average = <Value>",
        )
        e.configure_reference_line_style(
            f"{metric} Trend",
            "refline0",
            {
                "fill-above": "#00000000",
                "fill-below": "#00000000",
                "line-visibility": "on",
                "line-pattern-only": "dotted",
                "stroke-size": 2,
                "font-size": 8,
            },
        )
        e.configure_worksheet_style(
            f"{metric} Trend",
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
            axis_style={
                "per_field": [
                    {
                        "field": field,
                        "scope": "rows",
                        "class": 0,
                        "attr": "display",
                        "value": "false",
                    }
                    for field in (f"SUM({metric})", f"SUM(Current Month {metric})")
                ]
            },
            label_formats=[
                {
                    "field": "MONTH(Accounting Date)",
                    "text-format": "iLLL",
                    "text-orientation": "-90",
                    "font-size": 8,
                }
            ],
            cell_formats=[
                {
                    "field": f"SUM(Current Month {metric})",
                    "text-format": 'c"$"#,##0,,M;-"$"#,##0,,M',
                }
            ],
            pane_datalabel_style={"font-size": 8, "color-mode": "auto"},
        )
        e.configure_worksheet_style(
            f"{metric} Bar",
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            pane_cell_style={"text-align": "left"},
            pane_datalabel_style={
                "color-mode": "auto",
                "font-size": 9,
                "font-weight": "bold",
            },
            pane_mark_style={"size": "0.74662983417510986", "mark-labels-show": "true"},
        )
        e.set_worksheet_title(f"{metric} Trend", f"{metric} Trend")
    e.configure_chart(
        "Year Legend",
        mark_type="Circle",
        rows=["Fiscal Year"],
        columns=["Legend Point"],
        label="Fiscal Year",
        color="Fiscal Year",
        axis_fixed_range={"min": 0.45, "max": 1.0},
    )
    e.configure_chart(
        "Diff Legend",
        mark_type="Square",
        rows=["Legend Label"],
        columns=["Legend Point"],
        label="Legend Label",
        color="Legend Label",
        filters=[
            {"column": "Account Number", "values": ["69Z99999", "95U19440", "95U19210"]}
        ],
        sort_field="Legend Label",
        sort_descending="MAX(Legend Sort)",
        axis_fixed_range={"min": 0.45, "max": 1.0},
    )
    e.configure_chart(
        "Param Pop",
        mark_type="Text",
        label="Budget Visible",
        filters=[{"column": "Budget Visible", "values": [False]}],
    )
    for sheet in ["Year Legend", "Diff Legend", "OPP KPI", "Sales KPI", "Param Pop"]:
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=not sheet.endswith("KPI"),
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
        )
    for sheet, dimension in [
        ("Year Legend", "Fiscal Year"),
        ("Diff Legend", "Legend Label"),
    ]:
        e.configure_worksheet_style(
            sheet,
            hide_row_label=dimension,
            pane_cell_style={"text-align": "right", "vertical-align": "center"},
            pane_datalabel_style={"font-size": 8, "color-mode": "auto"},
            pane_mark_style={"mark-labels-show": "true"},
        )
    for metric in ("Sales", "OPP"):
        e.configure_worksheet_style(
            f"{metric} KPI",
            cell_formats=[{"height": 61, "width": 85}],
            table_dividers=[
                {
                    "scope": scope,
                    "line-visibility": "on",
                    "line-pattern-only": "solid",
                    "stroke-color": "#000000",
                }
                for scope in ("rows", "cols")
            ],
        )

    def zone(kind, x, y, w, h, **options):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 800 * 100000),
                "y": round(y / 500 * 100000),
                "w": round(w / 800 * 100000),
                "h": round(h / 500 * 100000),
            },
            "style": {"margin": 4},
            **options,
        }

    def text(content, x, y, w, h, *, size=8, color="#333333", bold=False, align="0"):
        return zone(
            "text",
            x,
            y,
            w,
            h,
            runs=[
                {
                    "text": content,
                    "font_size": size,
                    "font_color": color,
                    "bold": bold,
                    "font_alignment": align,
                }
            ],
        )

    zones = [
        zone(
            "text",
            8,
            8,
            784,
            68.53,
            runs=[
                {
                    "text": "Financial Report\n",
                    "font_size": 15,
                    "font_color": "#333333",
                    "font_alignment": "0",
                },
                {
                    "parameter": "Compare Filter",
                    "font_size": 12,
                    "bold": True,
                    "font_alignment": "0",
                },
                {
                    "text": " Performance",
                    "font_size": 12,
                    "bold": True,
                    "font_alignment": "0",
                },
            ],
        ),
        zone(
            "empty",
            8,
            76.53,
            784,
            1,
            style={"margin": 0, "background-color": "#b4b4b4"},
        ),
        zone(
            "container",
            19,
            85,
            563,
            28,
            direction="horizontal",
            visibility={"field": "Budget Visible"},
            style={"margin": 0},
            children=[
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "Budget Sales (M)",
                            "font_size": 9,
                            "font_alignment": "0",
                        }
                    ],
                    "fixed_size": 152,
                    "style": {"margin": 0, "background-color": "#f5f5f5"},
                },
                {
                    "type": "paramctrl",
                    "parameter": "Budget Sales (M)",
                    "mode": "type_in",
                    "show_title": False,
                    "fixed_size": 120,
                    "style": {"margin": 0, "background-color": "#f5f5f5"},
                },
                {"type": "empty", "fixed_size": 20},
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "Budget OPP (M)",
                            "font_size": 9,
                            "font_alignment": "0",
                        }
                    ],
                    "fixed_size": 144,
                    "style": {"margin": 0, "background-color": "#f5f5f5"},
                },
                {
                    "type": "paramctrl",
                    "parameter": "Budget OPP (M)",
                    "mode": "type_in",
                    "show_title": False,
                    "fixed_size": 127,
                    "style": {"margin": 0, "background-color": "#f5f5f5"},
                },
            ],
        ),
        zone(
            "empty",
            18.5,
            120.03,
            273.5,
            297.47,
            style={
                "margin": 0,
                "border-style": "solid",
                "border-width": 1,
                "border-color": "#898989",
            },
        ),
        zone(
            "empty",
            312.5,
            120.03,
            277.5,
            297.47,
            style={
                "margin": 0,
                "border-style": "solid",
                "border-width": 1,
                "border-color": "#898989",
            },
        ),
    ]
    for metric, x, bar_width, kpi_width, trend_width in [
        ("Sales", 29, 158, 94, 252),
        ("OPP", 323, 161, 95, 256),
    ]:
        zones.extend(
            [
                zone(
                    "worksheet",
                    x,
                    130.53,
                    bar_width,
                    72,
                    name=f"{metric} Bar",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "worksheet",
                    x + bar_width,
                    130.53,
                    kpi_width,
                    72,
                    name=f"{metric} KPI",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "worksheet",
                    x,
                    202.53,
                    trend_width,
                    204.47,
                    name=f"{metric} Trend",
                    fit="entire",
                    show_title=False,
                ),
            ]
        )
    zones.extend(
        [
            zone(
                "text",
                600,
                109.53,
                192,
                29,
                runs=[
                    {
                        "text": "FILTERS",
                        "font_size": 9,
                        "bold": True,
                        "font_alignment": "0",
                    }
                ],
                style={"margin": 4, "background-color": "#f5f5f5"},
            ),
            zone(
                "paramctrl",
                600,
                138.53,
                192,
                34,
                parameter="Compare Filter",
                mode="compact",
                show_title=False,
            ),
            zone(
                "text",
                600,
                172.53,
                192,
                29,
                runs=[
                    {
                        "text": "LEGENDS",
                        "font_size": 9,
                        "bold": True,
                        "font_alignment": "0",
                    }
                ],
                style={"margin": 4, "background-color": "#f5f5f5"},
            ),
            zone(
                "worksheet",
                600,
                201.53,
                192,
                92,
                name="Diff Legend",
                fit="entire",
                show_title=False,
            ),
            zone(
                "empty",
                600,
                293.53,
                192,
                1,
                style={"margin": 0, "background-color": "#b4b4b4"},
            ),
            zone(
                "worksheet",
                600,
                294.53,
                192,
                48,
                name="Year Legend",
                fit="entire",
                show_title=False,
            ),
            text(
                "DESIGNED BY : @IVETTALEXA",
                8,
                428,
                261.33,
                32,
                color="#f90857",
                bold=True,
            ),
            text(
                "#WOW2020  |  WEEK 26",
                269.33,
                428,
                261.34,
                32,
                color="#f90857",
                bold=True,
                align="1",
            ),
            text(
                "RECREATED BY : @DONNACOLES30",
                530.67,
                428,
                261.33,
                32,
                color="#f90857",
                bold=True,
                align="2",
            ),
            text(
                "http://www.workout-wednesday.com/2020w26/",
                8,
                460,
                784,
                32,
                color="#0077aa",
                align="1",
            ),
        ]
    )
    # Foreground edge zones preserve the author card outlines in both the
    # visible-budget and hidden-budget native container states.
    for x, width in ((18.5, 273.5), (312.5, 277.5)):
        for edge_x, edge_y, edge_w, edge_h in (
            (x, 120.03, width, 1),
            (x, 416.5, width, 1),
            (x, 120.03, 1, 297.47),
            (x + width - 1, 120.03, 1, 297.47),
        ):
            zones.append(
                zone(
                    "empty",
                    edge_x,
                    edge_y,
                    edge_w,
                    edge_h,
                    style={"margin": 0, "background-color": "#898989"},
                )
            )
    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=500,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": zones,
        },
    )
    e.set_field_fiscal_year_start("Accounting Date", 10)
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
