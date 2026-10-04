"""Build Gaussian-process predictions and a native measure selector from raw data."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_02_03_WW05_Predicting_The_Future"
INPUT = (
    "Digest 2019 Table 313.20 (2021_02_03_WW05_HBCU Fall Enrollment 1976-2018).hyper"
)
MEASURES = ["Total Enrollment", "% Black Students", "% Non-Black Students"]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / INPUT))
    e.add_parameter(
        "pSelect_Measure",
        datatype="string",
        default_value="Total Enrollment",
        domain_type="all",
    )
    definitions = {
        "Total Enrollment": ("[Total enrollment 2 All students]", "integer", False),
        "% Black Students": (
            "SUM([Total enrollment 2 Black students]) / SUM([Total Enrollment])",
            "real",
            False,
        ),
        "% Non-Black Students": ("1-[% Black Students]", "real", False),
        "Actual Value": (
            "CASE [pSelect_Measure] WHEN 'Total Enrollment' THEN SUM([Total Enrollment]) WHEN '% Black Students' THEN [% Black Students] ELSE [% Non-Black Students] END",
            "real",
            False,
        ),
        "Predicted Value": (
            "MODEL_QUANTILE('model=gp',0.5,[Actual Value],ATTR(DATETRUNC('year',[Year])))",
            "real",
            True,
        ),
        "Prediction Residual": ("[Actual Value]-[Predicted Value]", "real", True),
        "Tooltip - Actual Value": (
            "IF [pSelect_Measure]='Total Enrollment' THEN [Actual Value]/1000 ELSE [Actual Value]*100 END",
            "real",
            False,
        ),
        "Tooltip - Predicted Value": (
            "IF [pSelect_Measure]='Total Enrollment' THEN [Predicted Value]/1000 ELSE [Predicted Value]*100 END",
            "real",
            True,
        ),
        "Tooltip - Residual": (
            "[Tooltip - Actual Value]-[Tooltip - Predicted Value]",
            "real",
            True,
        ),
        "Latest Year - Actual": (
            "WINDOW_MAX(IF MIN([Year])=MIN([Latest Year]) THEN [Tooltip - Actual Value] END)",
            "real",
            True,
        ),
        "Latest Year +5 - Predicted": (
            "WINDOW_MAX(IF LAST()=0 THEN [Tooltip - Predicted Value] END)",
            "real",
            True,
        ),
        "Increase | Decrease": (
            "IF [Latest Year - Actual]-[Latest Year +5 - Predicted]>0 THEN 'decrease' ELSE 'increase' END",
            "string",
            True,
        ),
        "Title Latest Year": ("ATTR(DATEPART('year',[Latest Year]))", "integer", False),
        "Title Future Year": (
            "ATTR(DATEPART('year',[Latest Year + 5]))",
            "integer",
            False,
        ),
    }
    e.add_calculated_field(
        "Year",
        "MAKEDATE([Year 1],1,1)",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Latest Year",
        "{MAX([Year])}",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Latest Year + 5",
        "DATE(DATEADD('year',5,[Latest Year]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Tooltip - Value Suffix",
        "IF [pSelect_Measure]='Total Enrollment' THEN 'K' ELSE '%' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    for name, (formula, datatype, tc) in definitions.items():
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role="measure",
            field_type="nominal" if datatype == "string" else "quantitative",
            table_calc="Rows" if tc else None,
        )
    for field in [
        "Tooltip - Actual Value",
        "Tooltip - Predicted Value",
        "Latest Year - Actual",
        "Latest Year +5 - Predicted",
    ]:
        e.set_field_format(field, "n#,##0.0;-#,##0.0")
    e.set_field_format("Tooltip - Residual", "*+#,##0.0;-#,##0.0")
    e.set_field_format("Year", "*yyyy")
    for field in ["Title Latest Year", "Title Future Year"]:
        e.set_field_format(field, "n0;-0")
    for field in ["% Black Students", "% Non-Black Students"]:
        e.set_field_format(field, "p0.0%")
    e.add_worksheet("Chart")
    detail = [
        "Title Latest Year",
        "Title Future Year",
        "Latest Year - Actual",
        "Latest Year +5 - Predicted",
        "Increase | Decrease",
    ]
    tooltip = [
        "YEARTRUNC(Year)",
        "Tooltip - Actual Value",
        "Tooltip - Predicted Value",
        "Tooltip - Residual",
        "ATTR(Tooltip - Value Suffix)",
    ]
    addressed = {
        name: [
            {
                "ordering_type": "Field",
                "order": [{"field": "YEARTRUNC(Year)", "reference": "instance"}],
            }
        ]
        for name, (_, _, tc) in definitions.items()
        if tc and name != "Prediction Residual"
    }
    nested = {
        "Tooltip - Predicted Value": ["Predicted Value"],
        "Tooltip - Residual": ["Tooltip - Predicted Value", "Predicted Value"],
        "Latest Year +5 - Predicted": ["Tooltip - Predicted Value", "Predicted Value"],
        "Increase | Decrease": [
            "Latest Year - Actual",
            "Latest Year +5 - Predicted",
            "Tooltip - Predicted Value",
            "Predicted Value",
        ],
    }
    for name, deps in nested.items():
        addressed[name].extend(
            {
                "field": dep,
                "ordering_type": "Field",
                "order": [{"field": "YEARTRUNC(Year)", "reference": "instance"}],
            }
            for dep in deps
        )
    e.configure_layered_chart(
        "Chart",
        columns=["YEARTRUNC(Year)"],
        rows=["Actual Value", "Predicted Value"],
        panes=[
            {
                "axis": "Actual Value",
                "mark_type": "Area",
                "detail_extra": detail,
                "tooltip": tooltip,
                "mark_style": {"mark-color": "#00a2b3", "mark-transparency": "65"},
                "selection_relaxation": "selection-relaxation-disallow",
            },
            {
                "axis": "Predicted Value",
                "mark_type": "Line",
                "detail_extra": detail,
                "tooltip": tooltip,
                "mark_style": {"mark-color": "#5c6068"},
                "selection_relaxation": "selection-relaxation-disallow",
            },
        ],
        filters=[{"column": "[Year 1]", "type": "quantitative", "min": "1993"}],
        table_calc_overrides=addressed,
    )
    e.configure_worksheet_time_series(
        "Chart",
        "YEARTRUNC(Year)",
        periods=5,
        period_type="year",
        calculations_on_densified_marks=True,
    )
    for pane in [0, 1]:
        e.configure_custom_tooltip(
            "Chart",
            [
                {"field": "YEARTRUNC(Year)", "bold": True},
                {"text": "\nActual: "},
                {"field": "Tooltip - Actual Value"},
                {"field": "ATTR(Tooltip - Value Suffix)"},
                {"text": "\nPredicted: "},
                {"field": "Tooltip - Predicted Value"},
                {"field": "ATTR(Tooltip - Value Suffix)"},
                {"text": "\nResidual: "},
                {"field": "Tooltip - Residual"},
                {"field": "ATTR(Tooltip - Value Suffix)"},
            ],
            pane_index=pane,
        )
    e.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        table_formats=[{"attr": "show-null-value-warning", "value": "false"}],
        cell_formats=[
            {"field": field, "text-format": "n0;-0"}
            for field in ["Title Latest Year", "Title Future Year"]
        ],
        axis_style={
            "per_field": [
                {
                    "field": "YEARTRUNC(Year)",
                    "scope": "cols",
                    "class": "0",
                    "attr": "title",
                    "value": "",
                }
            ]
            + [
                {
                    "field": field,
                    "scope": "rows",
                    "class": "0",
                    "attr": "display",
                    "value": "false",
                }
                for field in ["Actual Value", "Predicted Value"]
            ],
            "encodings": [
                {
                    "field": field,
                    "scope": "rows",
                    "attr": "space",
                    "class": "0",
                    "type": "space",
                    "field-type": "quantitative",
                    **(
                        {"domain-expand": "false"}
                        if i == 0
                        else {"fold": "true", "synchronized": "true"}
                    ),
                }
                for i, field in enumerate(["Actual Value", "Predicted Value"])
            ],
        },
    )
    e.set_worksheet_rich_title(
        "Chart",
        [
            {
                "text": "By <Title Future Year>, <[Parameters].[pSelect_Measure]> at HBCUs is expected to <Increase | Decrease> to <Latest Year +5 - Predicted><ATTR(Tooltip - Value Suffix)>",
                "fontsize": 16,
                "fontcolor": "#027b8e",
                "bold": True,
            },
            {
                "text": " (vs <Latest Year - Actual><ATTR(Tooltip - Value Suffix)> in <Title Latest Year>)\nActual | ",
                "fontsize": 10,
                "fontcolor": "#027b8e",
            },
            {"text": "Predicted", "fontsize": 10, "fontcolor": "#5c6068"},
        ],
    )
    e.add_worksheet("Measure Select")
    e.add_calculated_field("Selector Axis", "MIN(1)", datatype="integer")
    e.configure_layered_chart(
        "Measure Select",
        rows=["Measure Names"],
        columns=["Selector Axis"],
        axis_shelf="cols",
        panes=[
            {
                "axis": "Selector Axis",
                "mark_type": "Bar",
                "labels": ["Measure Names"],
                "measure_values": MEASURES,
                "detail_extra": ["Multiple Values"],
                "mark_style": {
                    "mark-color": "#027b8e",
                    "size": "1.9890055656433105",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
                "datalabel_style": {
                    "color": "#ffffff",
                    "font-size": "12",
                    "font-weight": "bold",
                },
                "selection_relaxation": "selection-relaxation-disallow",
            }
        ],
        filters=[{"column": "[Year 1]", "type": "quantitative", "min": "1993"}],
    )
    e.configure_worksheet_style(
        "Measure Select",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_label="Measure Names",
        hide_row_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center"},
        pane_datalabel_style={
            "color": "#ffffff",
            "text-align": "center",
            "font-weight": "bold",
            "font-size": "12",
        },
        cell_formats=[
            {"field": "Measure Names", "height": "74", "width": "111"},
            {"width": "193"},
        ],
        header_formats=[{"height": "40"}],
        axis_style={
            "encodings": [
                {
                    "field": "Selector Axis",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "max": "1",
                    "min": "0",
                    "range-type": "fixed",
                    "scope": "cols",
                    "type": "space",
                }
            ]
        },
    )
    e.set_worksheet_rich_title(
        "Measure Select",
        [{"text": "Select Measure", "fontsize": 9, "fontalignment": "1"}],
    )
    e.add_dashboard(
        DASHBOARD,
        width=1200,
        height=600,
        layout={
            "type": "container",
            "style": {"margin": 8},
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        {
                            "type": "worksheet",
                            "name": "Chart",
                            "show_title": True,
                            "fit": "entire",
                        },
                        {
                            "type": "worksheet",
                            "name": "Measure Select",
                            "fixed_size": 217,
                            "show_title": True,
                            "fit": "standard",
                        },
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "CHALLENGE BY : CANDRA MCRAE",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                    "font_alignment": 0,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "#WOW2021  |  WEEK 05",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                    "font_alignment": 1,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "RECREATED WITH CWTWB",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                    "font_alignment": 2,
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "fixed_size": 32,
                    "runs": [
                        {
                            "text": "http://www.workout-wednesday.com/2021w05tab/",
                            "font_size": 8,
                            "font_color": "#027b8e",
                            "font_alignment": 1,
                        }
                    ],
                },
            ],
        },
    )
    e.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Measure Select",
        source_field="Measure Names",
        target_parameter="pSelect_Measure",
        aggregation="attr",
        clear_behavior="keep-current",
        clear_value="s:LROOT:",
        caption="Select Measure",
    )
    e.set_window_state("Chart", hidden=False, zoom_entire_view=True)
    e.set_window_state("Measure Select", hidden=False)
    e.set_window_state(DASHBOARD, maximized=True)
    path = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    e.save(str(path))
    return path


if __name__ == "__main__":
    print(build())
