"""Rebuild set-controlled connected scatter and dynamic insight panel."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_08_12_WW34_Connected_Scatter"
COLORS = {"Furniture": "#a26dc2", "Office Supplies": "#a2b627", "Technology": "#30bcad"}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    e.add_set("Selected Category", "Category", members=[])
    specs = [
        (
            "Month Year",
            "DATE(DATETRUNC('month',[Order Date]))",
            "date",
            "dimension",
            "quantitative",
            None,
        ),
        (
            "Profit Ratio",
            "SUM([Profit])/SUM([Sales])",
            "real",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Selected PR",
            "IF ATTR([Selected Category]) THEN [Profit Ratio] END",
            "real",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Max PR per Category",
            "WINDOW_MAX([Profit Ratio])",
            "real",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Min PR per Category",
            "WINDOW_MIN([Profit Ratio])",
            "real",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Max Qty per Category",
            "WINDOW_MAX(SUM([Quantity]))",
            "integer",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Min Qty per Category",
            "WINDOW_MIN(SUM([Quantity]))",
            "integer",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Max PR Month",
            "WINDOW_MAX(IF ATTR([Selected Category]) AND [Profit Ratio]=[Max PR per Category] THEN MIN([Month Year]) END)",
            "date",
            "measure",
            "ordinal",
            "Columns",
        ),
        (
            "Min PR Month",
            "WINDOW_MAX(IF ATTR([Selected Category]) AND [Profit Ratio]=[Min PR per Category] THEN MIN([Month Year]) END)",
            "date",
            "measure",
            "ordinal",
            "Columns",
        ),
        (
            "Max Qty Month",
            "WINDOW_MAX(IF ATTR([Selected Category]) AND SUM([Quantity])=[Max Qty per Category] THEN MIN([Month Year]) END)",
            "date",
            "measure",
            "ordinal",
            "Columns",
        ),
        (
            "Min Qty Month",
            "WINDOW_MAX(IF ATTR([Selected Category]) AND SUM([Quantity])=[Min Qty per Category] THEN MIN([Month Year]) END)",
            "date",
            "measure",
            "ordinal",
            "Columns",
        ),
        ("Index=Size", "INDEX()=SIZE()", "boolean", "dimension", "nominal", "Columns"),
    ]
    for name, f, dt, role, kind, tc in specs:
        e.add_calculated_field(
            name, f, datatype=dt, role=role, field_type=kind, table_calc=tc
        )
    for name in [
        "Month Year",
        "Max PR Month",
        "Min PR Month",
        "Max Qty Month",
        "Min Qty Month",
    ]:
        e.set_field_format(name, "*mmmm yyyy")
    for name in [
        "Profit Ratio",
        "Selected PR",
        "Max PR per Category",
        "Min PR per Category",
    ]:
        e.set_field_format(name, "p0%")
    filters = [{"column": "YEAR(Order Date)", "values": [2018, 2019]}]
    e.add_worksheet("Scatter")
    e.configure_layered_chart(
        "Scatter",
        columns=["SUM(Quantity)"],
        rows=["AGG(Profit Ratio)", "AGG(Selected PR)"],
        panes=[
            {
                "axis": "AGG(Profit Ratio)",
                "mark_type": "Circle",
                "color": "Category",
                "color_map": COLORS,
                "detail": "EXACTDATE(Month Year)",
                "tooltip": [
                    "EXACTDATE(Month Year)",
                    "SUM(Quantity)",
                    "AGG(Profit Ratio)",
                ],
                "mark_style": {"size": "1"},
            },
            {
                "axis": "AGG(Selected PR)",
                "mark_type": "Line",
                "path": "EXACTDATE(Month Year)",
                "color": "Category",
                "color_map": COLORS,
                "label": "EXACTDATE(Month Year)",
                "tooltip": ["SUM(Quantity)", "AGG(Profit Ratio)"],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "true"},
                "label_runs": [
                    {"field": "EXACTDATE(Month Year)", "fontsize": "6", "bold": True}
                ],
            },
        ],
        filters=filters,
    )
    e.configure_worksheet_style(
        "Scatter",
        hide_gridlines=True,
        hide_sort_controls=True,
        pane_datalabel_style={"color-mode": "match"},
        axis_style={
            "per_field": [
                {
                    "field": "AGG(Profit Ratio)",
                    "scope": "rows",
                    "class": "0",
                    "attr": "title",
                    "value": "PROFIT RATIO",
                },
                {
                    "field": "SUM(Quantity)",
                    "scope": "cols",
                    "class": "0",
                    "attr": "title",
                    "value": "QUANTITY",
                },
                {
                    "field": "AGG(Selected PR)",
                    "scope": "rows",
                    "class": "0",
                    "attr": "display",
                    "value": "false",
                },
            ]
        },
    )
    e.set_worksheet_rich_title(
        "Scatter",
        [
            {
                "text": "QUANTITY VS. PROFIT RATIO BY CATEGORY AND MONTH",
                "fontsize": "10",
                "bold": True, "fontalignment": "0",
            }
        ],
    )
    e.add_worksheet("Insights")
    fields = [
        "AGG(Max PR per Category)",
        "AGG(Min PR per Category)",
        "AGG(Max Qty per Category)",
        "AGG(Min Qty per Category)",
        "AGG(Max PR Month)",
        "AGG(Min PR Month)",
        "AGG(Max Qty Month)",
        "AGG(Min Qty Month)",
    ]
    calc = [{"ordering_type": "Field", "ordering_field": "EXACTDATE(Month Year)"}]
    overrides = {x: calc for x in fields}
    overrides["Index=Size"] = calc
    for name, nested in [
        ("Max PR Month", "Max PR per Category"),
        ("Min PR Month", "Min PR per Category"),
        ("Max Qty Month", "Max Qty per Category"),
        ("Min Qty Month", "Min Qty per Category"),
    ]:
        overrides["AGG(" + name + ")"] = [
            *calc,
            {
                "field": nested,
                "ordering_type": "Field",
                "ordering_field": "EXACTDATE(Month Year)",
            },
        ]
    runs = [{"text": "INSIGHTS\n", "bold": True, "fontsize": "10"}]
    for date, value, text in [
        (
            "Max PR Month",
            "Max PR per Category",
            "best performing month by Profit Ratio",
        ),
        ("Max Qty Month", "Max Qty per Category", "best performing month by Quantity"),
        (
            "Min PR Month",
            "Min PR per Category",
            "worst performing month by Profit Ratio",
        ),
        ("Min Qty Month", "Min Qty per Category", "worst performing month by Quantity"),
    ]:
        runs += [
            {"text": "- ", "fontsize": "8"},
            {"field": "AGG(" + date + ")", "bold": True, "fontsize": "8"},
            {"text": " was the " + text + " (", "fontsize": "8"},
            {"field": "AGG(" + value + ")", "bold": True, "fontsize": "8"},
            {"text": ")\n", "fontsize": "8"},
        ]
    e.configure_layered_chart(
        "Insights",
        columns=[],
        rows=[],
        panes=[
            {
                "mark_type": "Text",
                "color": "Category",
                "color_map": COLORS,
                "detail": "EXACTDATE(Month Year)",
                "detail_extra": ["Index=Size"],
                "labels": fields,
                "label_runs": runs,
                "mark_style": {"mark-labels-show": "true"},
            }
        ],
        filters=[
            *filters,
            {"column": "Selected Category", "values": [True]},
            {"column": "Index=Size", "values": [True]},
        ],
        table_calc_overrides=overrides,
        fold_axes=False,
    )
    e.configure_worksheet_style(
        "Insights",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_sort_controls=True,
        pane_cell_style={"text-align": "left", "vertical-align": "top"},
    )

    def zone(kind, x, y, w, h, **kw):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1200 * 100000),
                "y": round(y / 1000 * 100000),
                "w": round(w / 1200 * 100000),
                "h": round(h / 1000 * 100000),
            },
            **kw,
        }

    children = [
        zone(
            "text",
            8,
            8,
            1184,
            43,
            text="IS PROFIT RATIO INFLUENCED BY QUANTITY?  CLICK FOR INSIGHTS",
            font_size=16,
        ),
        zone("empty", 8, 51, 1184, 4, style={"background-color": "#000000"}),
        zone(
            "worksheet",
            8,
            63,
            1184,
            885,
            name="Scatter",
            fit="entire",
            show_title=True,
        ),
        zone(
            "worksheet",
            668,
            704,
            500,
            170,
            name="Insights",
            fit="entire",
            show_title=False,
        ),
        zone("text", 8, 948, 395, 44, text="DESIGNED BY: ANN JACKSON", font_size=8),
        zone("text", 403, 948, 394, 44, text="#WOW2020 | WEEK 33", font_size=8),
        zone("text", 797, 948, 395, 44, text="RECREATED WITH CWTWB", font_size=8),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=1200,
        height=1000,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Scatter", "Insights"],
    )
    e.add_dashboard_set_action(
        DASHBOARD,
        "Scatter",
        "Selected Category",
        event_type="on-select",
        caption="Select Category",
        single_select=True,
        selection_mode="assign",
        clear_option="exclude-all",
    )
    e.add_dashboard_action(
        DASHBOARD,
        "highlight",
        source_sheet="Scatter",
        target_sheet="Scatter",
        fields=["Category"],
        event_type="on-select",
        caption="Highlight Category",
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
