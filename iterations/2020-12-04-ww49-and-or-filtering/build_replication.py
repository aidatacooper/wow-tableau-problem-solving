"""Build dynamic all-members slicers and the selected/omitted sales dashboard."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_12_02_WW49_Toggle_AND_OR_Filtering"
SHEETS = ["Region", "Category", "Segment", "Ship Mode"]
CHOICES = [
    "None",
    "Location",
    "\u255a Region",
    "\u255a State",
    "Product",
    "\u255a Category",
    "\u255a Sub-Category",
    "Customer",
    "\u255a Segment",
    "Shipping",
    "\u255a Ship Mode",
]
FIELDS = ["Region", "State", "Category", "Sub-Category", "Segment", "Ship Mode"]


def zone(kind, x, y, w, h, **options):
    if kind == "text" and "text" in options:
        options["runs"] = [
            {"text": options.pop("text"), "font_size": options.pop("font_size", 8)}
        ]
    return {"type": kind, "absolute": {"x": x, "y": y, "w": w, "h": h}, **options}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    for index in (1, 2, 3):
        param = f"Select a Field for Slicer {index}:"
        e.add_parameter(
            param,
            datatype="string",
            default_value="None",
            domain_type="list",
            allowed_values=CHOICES,
            allowed_aliases={"None": "None Selected"},
            alias="None Selected",
        )
    e.add_parameter(
        "Selected Measure",
        datatype="string",
        default_value="Sales",
        domain_type="list",
        allowed_values=["Sales", "Quantity", "Orders"],
        allowed_aliases={
            "Sales": "Sum of Sales",
            "Quantity": "Quantity Sold",
            "Orders": "Order Count",
        },
    )
    e.add_parameter(
        "pLogic",
        datatype="string",
        default_value="AND",
        domain_type="list",
        allowed_values=["AND", "OR"],
    )
    for index in (1, 2, 3):
        param = f"Select a Field for Slicer {index}:"
        selected = f"Selected Slicer {index}"
        values = f"Selected Slicer {index} Values"
        e.add_calculated_field(
            selected,
            f"IF CONTAINS([Parameters].[{param}], '\u255a ') THEN REPLACE([Parameters].[{param}], '\u255a ', '') ELSE NULL END",
            datatype="string",
            role="dimension",
        )
        formula = (
            "CASE ["
            + selected
            + "] "
            + " ".join(f"WHEN '{field}' THEN [{field}]" for field in FIELDS)
            + " ELSE 'No Selection' END"
        )
        e.add_calculated_field(values, formula, datatype="string", role="dimension")
        e.add_set(f"Select Values for Slicer {index}:", values, use_all=True)
        e.add_calculated_field(
            f"Slicer {index} Is Not Selected?",
            f"[{values}] = 'No Selection'",
            datatype="boolean",
            role="dimension",
        )
    sets = [f"[Select Values for Slicer {i}:]" for i in (1, 2, 3)]
    inactive = [f"[Slicer {i} Is Not Selected?]" for i in (1, 2, 3)]
    formula = f"IF [Parameters].[pLogic]='AND' THEN {' AND '.join(sets)} ELSE "
    formula += f"IF {inactive[1]} AND {inactive[2]} THEN {sets[0]} ELSEIF {inactive[0]} AND {inactive[2]} THEN {sets[1]} ELSEIF {inactive[0]} AND {inactive[1]} THEN {sets[2]} ELSEIF {inactive[2]} THEN {sets[0]} OR {sets[1]} ELSEIF {inactive[1]} THEN {sets[0]} OR {sets[2]} ELSEIF {inactive[0]} THEN {sets[1]} OR {sets[2]} ELSE {' OR '.join(sets)} END END"
    e.add_calculated_field(
        "In Combined Set", formula, datatype="boolean", role="dimension"
    )
    e.add_calculated_field("Order Count", "COUNTD([Order ID])", datatype="integer")
    e.add_calculated_field(
        "Measure to Display",
        "CASE [Parameters].[Selected Measure] WHEN 'Sales' THEN SUM([Sales]) WHEN 'Quantity' THEN SUM([Quantity]) ELSE [Order Count] END",
        default_format="n#,##0",
    )
    e.add_calculated_field(
        "LABEL:Measure to Display Prefix",
        "IF [Parameters].[Selected Measure]='Sales' THEN '$' END",
        datatype="string",
        role="dimension",
    )
    e.add_calculated_field(
        "TOOLTIP:Selected | Omitted",
        "IF [In Combined Set] THEN 'selected' ELSE 'omitted' END",
        datatype="string",
        role="dimension",
    )
    e.add_calculated_field("True", "TRUE", datatype="boolean", role="dimension")
    e.add_calculated_field("False", "FALSE", datatype="boolean", role="dimension")
    e.add_calculated_field(
        "Tooltip Measure",
        "[Parameters].[Selected Measure]",
        datatype="string",
        role="dimension",
    )
    e.add_calculated_field(
        "Ship Mode Rank",
        "CASE [Ship Mode] WHEN 'Same Day' THEN 4 WHEN 'First Class' THEN 3 WHEN 'Second Class' THEN 2 ELSE 1 END",
        datatype="integer",
    )
    for sheet in SHEETS:
        e.add_worksheet(sheet)
        e.set_worksheet_rich_title(
            sheet, [{"text": "By " + sheet, "fontsize": 12, "fontcolor": "#000000"}]
        )
        e.configure_layered_chart(
            sheet,
            columns=["In Combined Set", "AGG(Measure to Display)"],
            rows=[sheet],
            axis_shelf="columns",
            sort_descending="MAX(Ship Mode Rank)" if sheet == "Ship Mode" else None,
            sort_field=sheet if sheet == "Ship Mode" else None,
            sort_mode="computed" if sheet == "Ship Mode" else "auto",
            panes=[
                {
                    "axis": "AGG(Measure to Display)",
                    "mark_type": "Bar",
                    "color": "In Combined Set",
                    "color_map": {True: "#19626b", False: "#dddddd"},
                    "detail": "True",
                    "detail_extra": ["False"],
                    "tooltip": ["ATTR(TOOLTIP:Selected | Omitted)"],
                    "label_runs": [
                        {"field": "LABEL:Measure to Display Prefix"},
                        {"field": "AGG(Measure to Display)"},
                    ],
                    "mark_sizing_off": True,
                    "mark_style": {
                        "size": "1.087458610534668",
                        "mark-labels-show": "true",
                        "mark-labels-cull": "true",
                        "mark-transparency": "206",
                        "has-stroke": "false",
                    },
                }
            ],
        )
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            label_formats=[{"field": "In Combined Set", "display": "false"}],
            header_formats=[{"field": sheet, "width": 144}],
            cell_formats=[{"field": sheet, "height": 35}],
        )
        e.configure_custom_tooltip(
            sheet,
            [
                {"field": sheet, "bold": True, "fontsize": 12},
                {"text": "\nThe "},
                {"field": "ATTR(TOOLTIP:Selected | Omitted)"},
                {"text": " "},
                {"field": "Tooltip Measure"},
                {"text": " for "},
                {"field": sheet},
                {"text": " is "},
                {"field": "LABEL:Measure to Display Prefix"},
                {"field": "AGG(Measure to Display)"},
            ],
        )
        e.configure_custom_label(
            sheet,
            [
                {"field": "LABEL:Measure to Display Prefix"},
                {"field": "AGG(Measure to Display)"},
            ],
        )
        e.set_window_state(sheet, hidden=False, zoom_entire_view=True)
    children = [
        zone(
            "text",
            0,
            0,
            100000,
            4667,
            text="Can you toggle between AND & OR filtering logic?",
            font_size=18,
            bold=True,
        ),
        zone(
            "paramctrl",
            1260,
            6334,
            26050,
            12999,
            parameter="pLogic",
            mode="compact",
            caption="Select which filter logic method to follow:",
        ),
    ]
    for i, (x, width) in enumerate([(27478, 24790), (52436, 23068), (75672, 23068)], 1):
        children += [
            zone(
                "paramctrl",
                x,
                6334,
                width,
                6222,
                parameter=f"Select a Field for Slicer {i}:",
                mode="compact",
            ),
            zone(
                "set_control",
                x,
                12556,
                width,
                6777,
                field=f"Select Values for Slicer {i}:",
                worksheet="Region",
                mode="checkdropdown",
                show_apply=True,
            ),
        ]
    children += [
        zone(
            "paramctrl",
            840,
            22111,
            2941,
            4000,
            parameter="Selected Measure",
            mode="compact",
        ),
        zone(
            "text",
            3781,
            22111,
            48866,
            4000,
            runs=[{"parameter": "Selected Measure", "font_size": 12, "bold": True}],
        ),
        zone(
            "text",
            52647,
            22111,
            46513,
            4000,
            text="Selected | Omitted by Filters",
            font_size=12,
        ),
    ]
    for sheet, y, h in [
        ("Region", 26667, 18889),
        ("Category", 45556, 14332),
        ("Segment", 59888, 14332),
        ("Ship Mode", 74220, 17444),
    ]:
        children.append(
            zone(
                "worksheet",
                1260,
                y,
                97480,
                h,
                name=sheet,
                show_title=True,
                fit="entire",
            )
        )
    children += [
        zone("text", 0, 93334, 35350, 3333, text="DESIGNED BY : SAM EPLEY"),
        zone("text", 35350, 93334, 32325, 3333, text="#WOW2020 | WEEK 49"),
        zone("text", 67675, 93334, 32325, 3333, text="RECREATED WITH CWTWB"),
        zone(
            "text",
            0,
            96667,
            100000,
            3333,
            text="http://www.workout-wednesday.com/2020w49/",
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=1190,
        height=900,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"background-color": "#f5f5f5"},
            "children": children,
        },
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
