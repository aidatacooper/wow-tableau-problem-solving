"""Rebuild native state/city set-action scatter using only locked Hyper data."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_22_WW30_SetAction_DrillDown"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    e.add_set("Selected State", "State", members=[])
    calcs = [
        (
            "Count States Selected",
            "{FIXED: COUNTD(IF [Selected State] THEN [State] END)}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Display Value",
            "IF [Selected State] THEN [City] ELSE [State] END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Records to Show",
            "[Count States Selected]=0 OR [Selected State]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Profit to Plot",
            "IF ATTR([Selected State]) THEN SUM([Profit]) ELSE AVG({FIXED [State]: SUM([Profit])}) END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Sales to Plot",
            "IF ATTR([Selected State]) THEN SUM([Sales]) ELSE AVG({FIXED [State]: SUM([Sales])}) END",
            "real",
            "measure",
            "quantitative",
        ),
        ("-ve Profit?", "[Profit to Plot]<0", "boolean", "measure", "nominal"),
        (
            "Title",
            "IF [Count States Selected]=0 THEN 'Sales vs. Profit by State' ELSE 'Sales vs. Profit for '+[State] END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Subtitle",
            "IF [Count States Selected]=0 THEN 'Select a state to drill down to city level' ELSE 'Double-click a city to drill up to state level' END",
            "string",
            "dimension",
            "nominal",
        ),
    ]
    for name, formula, dt, role, kind in calcs:
        e.add_calculated_field(name, formula, datatype=dt, role=role, field_type=kind)
    e.add_worksheet("Scatter")
    e.configure_layered_chart(
        "Scatter",
        columns=["AGG(Profit to Plot)"],
        rows=["AGG(Sales to Plot)"],
        panes=[
            {
                "mark_type": "Shape",
                "axis": "AGG(Sales to Plot)",
                "color": "AGG(-ve Profit?)",
                "label": "Display Value",
                "detail": "State",
                "detail_extra": ["Display Value", "Title", "Subtitle"],
                "mark_style": {"shape": ":filled/times", "size": "1.2"},
                "color_map": {"true": "#e15759", "false": "#4e79a7"},
            }
        ],
        filters=[{"column": "Records to Show", "values": [True]}],
        fold_axes=False,
    )
    e.set_worksheet_rich_title(
        "Scatter",
        [
            {"text": "<Title>", "fontsize": "12", "bold": True, "fontalignment": "1"},
            {
                "text": "\n<Subtitle>",
                "fontsize": "9",
                "italic": True,
                "fontalignment": "1",
            },
        ],
    )
    e.configure_worksheet_style(
        "Scatter",
        hide_gridlines=False,
        hide_borders=True,
        hide_sort_controls=True,
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        pane_datalabel_style={"font-size": "8"},
        axis_style={
            "per_field": [
                {
                    "field": "AGG(Profit to Plot)",
                    "scope": "cols",
                    "class": "0",
                    "attr": "title",
                    "value": "Profit",
                },
                {
                    "field": "AGG(Sales to Plot)",
                    "scope": "rows",
                    "class": "0",
                    "attr": "title",
                    "value": "Sales",
                },
            ]
        },
    )
    objects = [
        {
            "type": "text",
            "text": "Can you create a drill down using set actions?",
            "x": 8,
            "y": 8,
            "w": 784,
            "h": 42,
            "runs": [
                {
                    "text": "Can you create a drill down using set actions?",
                    "font_size": "18",
                    "bold": True,
                    "font_alignment": "1",
                }
            ],
        },
        {
            "type": "worksheet",
            "name": "Scatter",
            "x": 8,
            "y": 50,
            "w": 784,
            "h": 578,
            "show_title": True,
            "fit": "entire",
        },
    ]
    for x, w, text in [
        (8, 261, "CHALLENGE BY: EMMA WHYTE"),
        (269, 262, "#WOW2020 | WEEK 30"),
        (531, 261, "RECREATED WITH CWTWB"),
    ]:
        objects.append(
            {
                "type": "text",
                "text": text,
                "x": x,
                "y": 628,
                "w": w,
                "h": 32,
                "font_size": 8,
            }
        )
    objects.append(
        {
            "type": "text",
            "text": "https://www.workout-wednesday.com/2020w30/",
            "x": 8,
            "y": 660,
            "w": 784,
            "h": 32,
            "font_size": 8,
        }
    )
    for obj in objects:
        obj["absolute"] = {
            key: round(obj.pop(key) / (800 if key in ["x", "w"] else 700) * 100000)
            for key in ["x", "y", "w", "h"]
        }
    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=700,
        layout={"type": "container", "direction": "floating", "children": objects},
        worksheet_names=["Scatter"],
    )
    e.add_dashboard_set_action(
        DASHBOARD,
        "Scatter",
        "Selected State",
        event_type="on-select",
        caption="Drill Down",
        selection_mode="assign",
        clear_option="exclude-all",
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
