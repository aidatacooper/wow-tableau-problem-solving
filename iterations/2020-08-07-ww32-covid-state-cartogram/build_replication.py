"""Native text/area cartogram from locked county-level COVID data."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_08_05_WW32_Covid_State_Small_Multiple"
ROWS_FORMULA = "CASE [PROVINCE_STATE_NAME]\r\nWHEN 'Alabama' THEN 7\r\nWHEN 'Alaska' THEN 1\r\nWHEN 'Arizona' THEN 6\r\nWHEN 'Arkansas' THEN 6\r\nWHEN 'California' THEN 5\r\nWHEN 'Colorado' THEN 5\r\nWHEN 'Connecticut' THEN 4\r\nWHEN 'Delaware' THEN 5\r\nWHEN 'District of Columbia' THEN 6\r\nWHEN 'Florida' THEN 8\r\nWHEN 'Georgia' THEN 7\r\nWHEN 'Hawaii' THEN 8\r\nWHEN 'Idaho' THEN 3\r\nWHEN 'Illinois' THEN 3\r\nWHEN 'Indiana' THEN 4\r\nWHEN 'Iowa' THEN 4\r\nWHEN 'Kansas' THEN 6\r\nWHEN 'Kentucky' THEN 5\r\nWHEN 'Louisiana' THEN 7\r\nWHEN 'Maine' THEN 1\r\nWHEN 'Maryland' THEN 5\r\nWHEN 'Massachusetts' THEN 3\r\nWHEN 'Michigan' THEN 3\r\nWHEN 'Minnesota' THEN 3\r\nWHEN 'Mississippi' THEN 7\r\nWHEN 'Missouri' THEN 5\r\nWHEN 'Montana' THEN 3\r\nWHEN 'Nebraska' THEN 5\r\nWHEN 'Nevada' THEN 4\r\nWHEN 'New Hampshire' THEN 2\r\nWHEN 'New Jersey' THEN 4\r\nWHEN 'New Mexico' THEN 6\r\nWHEN 'New York' THEN 3\r\nWHEN 'North Carolina' THEN 6\r\nWHEN 'North Dakota' THEN 3\r\nWHEN 'Ohio' THEN 4\r\nWHEN 'Oklahoma' THEN 7\r\nWHEN 'Oregon' THEN 4\r\nWHEN 'Pennsylvania' THEN 4\r\nWHEN 'Rhode Island' THEN 3\r\nWHEN 'South Carolina' THEN 6\r\nWHEN 'South Dakota' THEN 4\r\nWHEN 'Tennessee' THEN 6\r\nWHEN 'Texas' THEN 8\r\nWHEN 'Utah' THEN 5\r\nWHEN 'Vermont' THEN 2\r\nWHEN 'Virginia' THEN 5\r\nWHEN 'Washington' THEN 3\r\nWHEN 'West Virginia' THEN 5\r\nWHEN 'Wisconsin' THEN 3\r\nWHEN 'Wyoming' THEN 4\r\nEND"
COLS_FORMULA = "CASE [PROVINCE_STATE_NAME]\r\nWHEN 'Alabama' THEN 8\r\nWHEN 'Alaska' THEN 1\r\nWHEN 'Arizona' THEN 3\r\nWHEN 'Arkansas' THEN 6\r\nWHEN 'California' THEN 2\r\nWHEN 'Colorado' THEN 4\r\nWHEN 'Connecticut' THEN 11\r\nWHEN 'Delaware' THEN 11\r\nWHEN 'District of Columbia' THEN 10\r\nWHEN 'Florida' THEN 10\r\nWHEN 'Georgia' THEN 9\r\nWHEN 'Hawaii' THEN 1\r\nWHEN 'Idaho' THEN 3\r\nWHEN 'Illinois' THEN 7\r\nWHEN 'Indiana' THEN 7\r\nWHEN 'Iowa' THEN 6\r\nWHEN 'Kansas' THEN 5\r\nWHEN 'Kentucky' THEN 7\r\nWHEN 'Louisiana' THEN 6\r\nWHEN 'Maine' THEN 12\r\nWHEN 'Maryland' THEN 10\r\nWHEN 'Massachusetts' THEN 12\r\nWHEN 'Michigan' THEN 9\r\nWHEN 'Minnesota' THEN 6\r\nWHEN 'Mississippi' THEN 7\r\nWHEN 'Missouri' THEN 6\r\nWHEN 'Montana' THEN 4\r\nWHEN 'Nebraska' THEN 5\r\nWHEN 'Nevada' THEN 3\r\nWHEN 'New Hampshire' THEN 12\r\nWHEN 'New Jersey' THEN 10\r\nWHEN 'New Mexico' THEN 4\r\nWHEN 'New York' THEN 10\r\nWHEN 'North Carolina' THEN 8\r\nWHEN 'North Dakota' THEN 5\r\nWHEN 'Ohio' THEN 8\r\nWHEN 'Oklahoma' THEN 5\r\nWHEN 'Oregon' THEN 2\r\nWHEN 'Pennsylvania' THEN 9\r\nWHEN 'Rhode Island' THEN 11\r\nWHEN 'South Carolina' THEN 9\r\nWHEN 'South Dakota' THEN 5\r\nWHEN 'Tennessee' THEN 7\r\nWHEN 'Texas' THEN 5\r\nWHEN 'Utah' THEN 3\r\nWHEN 'Vermont' THEN 11\r\nWHEN 'Virginia' THEN 9\r\nWHEN 'Washington' THEN 2\r\nWHEN 'West Virginia' THEN 8\r\nWHEN 'Wisconsin' THEN 8\r\nWHEN 'Wyoming' THEN 4\r\nEND"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/COVID-19 Activity (1) Extract.hyper"))
    specs = [
        ("Rows", ROWS_FORMULA, "integer", "dimension", "ordinal", None),
        ("Columns", COLS_FORMULA, "integer", "dimension", "ordinal", None),
        (
            "Report Date",
            "DATE([REPORT_DATE])",
            "date",
            "dimension",
            "quantitative",
            None,
        ),
        (
            "7 day moving Avg",
            "WINDOW_AVG(SUM([PEOPLE_POSITIVE_NEW_CASES_COUNT]),-6,0)",
            "real",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Max Avg Per State",
            "WINDOW_MAX([7 day moving Avg])",
            "real",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Normalised Value",
            "[7 day moving Avg]/[Max Avg Per State]",
            "real",
            "measure",
            "quantitative",
            "Columns",
        ),
        (
            "Plot State",
            "IF DATE([REPORT_DATE])=#2020-05-16# THEN 1.75 END",
            "real",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Display State",
            "IF [PROVINCE_STATE_NAME]='District of Columbia' THEN 'District of'+CHAR(10)+'Columbia' ELSE [PROVINCE_STATE_NAME] END",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        ("Valid State", "NOT ISNULL([Rows])", "boolean", "dimension", "nominal", None),
    ]
    for name, f, dt, role, kind, tc in specs:
        e.add_calculated_field(
            name, f, datatype=dt, role=role, field_type=kind, table_calc=tc
        )
    e.set_field_format("7 day moving Avg", "n#,##0")
    e.add_worksheet("Map")
    moving = [
        {
            "field": "7 day moving Avg",
            "ordering_type": "Field",
            "ordering_field": "EXACTDATE(Report Date)",
            "tc_options": "NullIfIncomplete",
        }
    ]
    nested = [
        {"ordering_type": "Rows"},
        *moving,
        {
            "field": "Max Avg Per State",
            "ordering_type": "Field",
            "ordering_field": "EXACTDATE(Report Date)",
        },
    ]
    filters = [
        {"column": "Valid State", "values": [True]},
        {
            "column": "EXACTDATE(Report Date)",
            "type": "quantitative",
            "min": "#2020-03-01#",
            "max": "#2020-07-31#",
        },
    ]
    e.configure_layered_chart(
        "Map",
        columns=["Columns", "EXACTDATE(Report Date)"],
        rows=["Rows", "MIN(Plot State)", "AGG(Normalised Value)"],
        panes=[
            {
                "axis": "MIN(Plot State)",
                "mark_type": "Text",
                "label": "ATTR(Display State)",
                "label_runs": [{"field": "ATTR(Display State)", "fontsize": "7"}],
                "detail": "PROVINCE_STATE_NAME",
                "mark_style": {"mark-labels-show": "true"},
                "datalabel_style": {"font-size": "8"},
            },
            {
                "axis": "AGG(Normalised Value)",
                "mark_type": "Area",
                "detail": "PROVINCE_STATE_NAME",
                "label": "AGG(7 day moving Avg)",
                "tooltip": [
                    "AGG(7 day moving Avg)",
                    "SUM(PEOPLE_POSITIVE_NEW_CASES_COUNT)",
                ],
                "mark_style": {
                    "mark-color": "#4e79a7",
                    "mark-labels-show": "true",
                    "mark-labels-mode": "range",
                    "mark-labels-range-min": "false",
                    "mark-labels-cull": "false",
                },
                "datalabel_style": {"font-size": "7"},
            },
        ],
        filters=filters,
        table_calc_overrides={
            "AGG(Normalised Value)": nested,
            "AGG(7 day moving Avg)": [
                {
                    "ordering_type": "Field",
                    "ordering_field": "EXACTDATE(Report Date)",
                    "tc_options": "NullIfIncomplete",
                }
            ],
        },
        hide_axes=True,
    )
    e.configure_worksheet_style(
        "Map",
        hide_axes=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_zeroline=False,
        hide_borders=True,
        hide_sort_controls=True,
        hide_row_label="Rows",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        label_formats=[
            {"field": "Rows", "display": "false"},
            {"field": "Columns", "display": "false"},
        ],
        panes_style={
            "1": {"datalabel_style": {"font-size": "8"}},
            "2": {"datalabel_style": {"font-size": "7"}},
        },
        axis_style={
            "encodings": [
                {
                    "field": "MIN(Plot State)",
                    "scope": "rows",
                    "class": "0",
                    "range_type": "fixed",
                    "min": "0",
                    "max": "2",
                },
                {
                    "field": "AGG(Normalised Value)",
                    "scope": "rows",
                    "class": "0",
                    "fold": True,
                    "synchronized": True,
                },
                {
                    "field": "EXACTDATE(Report Date)",
                    "scope": "cols",
                    "min": "#2020-03-01#",
                    "max": "#2020-08-01#",
                    "range_type": "fixed",
                },
            ]
        },
    )

    def zone(kind, x, y, w, h, **kw):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 900 * 100000),
                "y": round(y / 730 * 100000),
                "w": round(w / 900 * 100000),
                "h": round(h / 730 * 100000),
            },
            **kw,
        }

    children = [
        zone(
            "text",
            8,
            8,
            884,
            86,
            runs=[
                {
                    "text": "COVID-19 NEW CASE TRENDS\n",
                    "bold": True,
                    "font_size": "12",
                    "font_alignment": "1",
                },
                {
                    "text": "Values Represent Seven-Day Moving Average from March, 1 to July, 31\nAxis normalized for each visualization.",
                    "font_size": "10",
                    "font_alignment": "1",
                },
            ],
        ),
        zone("worksheet", 8, 95, 884, 549, name="Map", fit="entire", show_title=False),
        zone("text", 8, 644, 295, 32, text="CREATED BY: LUKE STANKE", font_size=8),
        zone("text", 303, 644, 294, 32, text="#WOW2020 | WEEK 32", font_size=8),
        zone("text", 597, 644, 295, 32, text="RECREATED WITH CWTWB", font_size=8),
        zone(
            "text",
            8,
            676,
            442,
            46,
            text="https://www.workout-wednesday.com/wow2020w32/",
            font_size=8,
        ),
        zone(
            "text",
            450,
            676,
            442,
            46,
            text="DATA: TABLEAU COVID-19 DATA HUB",
            font_size=8,
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=900,
        height=730,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Map"],
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
