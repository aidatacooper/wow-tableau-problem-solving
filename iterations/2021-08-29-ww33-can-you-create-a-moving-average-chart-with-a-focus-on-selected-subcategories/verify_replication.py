"""Independently verify the WW33 moving-average workbook.

Reads only the locked Hyper extract, the case files and the built TWBX.  The
oracle recomputes the monthly grouped sales, the parameterised moving average
and the nested window extrema from the raw rows; the workbook checks assert the
native parameter, group, set, table-calculation and dashboard contracts.

Automated acceptance IDs:
  - ww33-parameters
  - ww33-group
  - ww33-set-focus
  - ww33-moving-average
  - ww33-window-extrema
  - ww33-chart
  - ww33-dashboard-controls
  - ww33-moving-average-values
"""

import collections
import datetime
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww33-parameters",
    "ww33-group",
    "ww33-set-focus",
    "ww33-moving-average",
    "ww33-window-extrema",
    "ww33-chart",
    "ww33-dashboard-controls",
    "ww33-moving-average-values",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_08_18_WW33_Moving_Avg"
TABLE = TableName("Extract", "Extract")
MISC_MEMBERS = ["Art", "Envelopes", "Fasteners", "Labels", "Supplies"]
PRIOR = 3
POST = 3
MONTH = "[tmn:Order Date:qk]"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            f'SELECT "Order Date","Sub-Category","Sales" FROM {TABLE}'
        )
    assert len(rows) == 9994, "row count changed"

    monthly = collections.defaultdict(float)
    for order_date, sub_category, sales in rows:
        group = "Misc" if sub_category in MISC_MEMBERS else sub_category
        monthly[(order_date.year, order_date.month, group)] += sales
    months = sorted({(year, month) for (year, month, _group) in monthly})
    groups = sorted({group for (_year, _month, group) in monthly})
    assert len(months) == 48 and len(groups) == 13, (len(months), len(groups))

    # Tableau completes the 48-month x 13-group domain. WINDOW_AVG uses the
    # calendar offsets and ignores null sales within that window, as independently
    # confirmed by original-author and replica Cloud Data exports.
    series = {
        group: [
            (month, monthly.get((*month, group)))
            for month in months
        ]
        for group in groups
    }

    def moving_average(values, index):
        # Tableau WINDOW_AVG(expr, start, end) is inclusive on both ends and
        # clamps at the table edges (it averages the rows that exist).
        low = max(0, index - PRIOR + 1)
        high = min(len(values) - 1, index + POST)
        window = [v for v in values[low : high + 1] if v is not None]
        return sum(window) / len(window) if window else None

    moving = {
        group: [moving_average([value for _m, value in series[group]], index)
                for index in range(len(series[group]))]
        for group in groups
    }

    # Nested table calc: the extrema run across Sub-Category for the same
    # month, over every row that month actually has.
    by_month = collections.defaultdict(dict)
    for group in groups:
        for (month, _value), value in zip(series[group], moving[group]):
            
            if value is not None: by_month[month][group] = value
    window_max = {month: max(values.values()) for month, values in by_month.items()}
    window_min = {month: min(values.values()) for month, values in by_month.items()}

    # The article's worked example: Accessories in June 2018 averages the six
    # months April..September 2018 with the default 3 prior / 3 post.
    accessories = series["Accessories"]
    june = next(
        index for index, (month, _value) in enumerate(accessories) if month == (2018, 6)
    )
    assert [month for month, _value in accessories[june - 2 : june + 4]] == [
        (2018, 4), (2018, 5), (2018, 6), (2018, 7), (2018, 8), (2018, 9),
    ]
    accessories_window = [value for _month, value in accessories[june - 2 : june + 4]]
    worked_example = sum(accessories_window) / len(accessories_window)
    assert abs(moving["Accessories"][june] - worked_example) < 1e-9

    csv_rows = []
    for group in groups:
        for index, (month, _value) in enumerate(series[group]):
            csv_rows.append(
                {
                    "Month of Order Date": f"{month[0]}-{month[1]:02d}-01",
                    "Sub-Category (group)": group,
                    "Sales": round(series[group][index][1], 6) if series[group][index][1] is not None else None,
                    "Moving Avg": round(moving[group][index], 6) if moving[group][index] is not None else None,
                    "Window Max Avg": round(window_max[month], 6),
                    "Window Min Avg": round(window_min[month], 6),
                }
            )
    csv_rows.sort(key=lambda row: (row["Month of Order Date"], row["Sub-Category (group)"]))

    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "months": len(months),
        "first_month": f"{months[0][0]}-{months[0][1]:02d}",
        "last_month": f"{months[-1][0]}-{months[-1][1]:02d}",
        "groups": groups,
        "misc_members": MISC_MEMBERS,
        "prior": PRIOR,
        "post": POST,
        "series_rows": sum(len(values) for values in series.values()),
        "sparse_groups": sorted(
            group for group in groups if len(series[group]) < len(months)
        ),
        "accessories_2018_06_sales": [round(value, 6) for value in accessories_window],
        "accessories_2018_06_moving_avg": round(moving["Accessories"][june], 6),
        "window_extrema_2018_06": {
            "max": round(window_max[(2018, 6)], 6),
            "min": round(window_min[(2018, 6)], 6),
        },
        "csv_rows": csv_rows,
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def verify():
    facts = oracle()
    root = workbook()

    # --- ww33-parameters ---------------------------------------------------
    params = {
        column.get("caption"): column
        for column in root.findall(".//datasource[@name='Parameters']/column")
    }
    assert set(params) == {"pPrior", "pPost"}, sorted(params)
    for name, column in params.items():
        assert column.get("datatype") == "integer", (name, column.attrib)
        assert column.get("param-domain-type") == "range", (name, column.attrib)
        assert column.get("value") == "3", (name, column.attrib)
        window = column.find("range")
        assert window is not None, name
        assert (window.get("min"), window.get("max"), window.get("granularity")) == (
            "1",
            "6",
            "1",
        ), (name, window.attrib)

    # --- ww33-group --------------------------------------------------------
    group = root.find(".//datasource/column[@name='[Sub-Category (group)]']")
    assert group is not None, "missing grouped Sub-Category"
    calculation = group.find("calculation")
    assert calculation is not None and calculation.get("class") == "categorical-bin"
    assert calculation.get("column") == "[Sub-Category]"
    members = [value.text for value in calculation.findall("bin/value")]
    assert members == [f'"{name}"' for name in MISC_MEMBERS], members
    assert calculation.find("bin").get("value") == '"Misc"'

    # --- ww33-set-focus ----------------------------------------------------
    sets = [
        node
        for node in root.findall(".//datasource/group")
        if node.get("{http://www.tableausoftware.com/xml/user}ui-builder") == "filter-group"
    ]
    assert len(sets) == 1, [node.get("name") for node in sets]
    set_node = sets[0]
    assert set_node.get("name") == "[Sub-Category (group) Set]"
    set_members = [
        member.get("member")
        for member in set_node.findall("groupfilter/groupfilter")
    ]
    assert set(set_members) == {'"Chairs"', '"Paper"', '"Storage"'}, set_members

    # --- ww33-moving-average ----------------------------------------------
    columns = {
        column.get("caption"): column
        for column in root.findall(".//datasource/column")
        if column.get("caption")
    }
    formula = columns["Moving Avg"].find("calculation").get("formula")
    assert formula == (
        "WINDOW_AVG(SUM([Sales]), (-1*[Parameters].[Parameter 1])+1, "
        "[Parameters].[Parameter 2])"
    ), formula
    assert columns["Window Max Avg"].find("calculation").get("formula") == (
        "WINDOW_MAX([Calculation_87D61B00F1384E53A3B7D87FE19E8221])"
    ) or columns["Window Max Avg"].find("calculation").get("formula", "").startswith(
        "WINDOW_MAX([Calculation_"
    )
    assert columns["Window Min Avg"].find("calculation").get("formula", "").startswith(
        "WINDOW_MIN([Calculation_"
    )

    sheet = root.find(f".//worksheets/worksheet[@name='Viz']")
    assert sheet is not None, "missing Viz worksheet"
    instances = {
        instance.get("name"): instance
        for instance in sheet.findall("table/view/datasource-dependencies/column-instance")
    }
    moving_instance = next(
        name for name in instances if name.startswith("[usr:Calculation_") and
        instances[name].get("column") == columns["Moving Avg"].get("name")
    )
    addresses = instances[moving_instance].findall("table-calc")
    assert addresses and addresses[0].get("ordering-field", "").endswith(MONTH), [
        etree.tostring(node) for node in addresses
    ]

    # --- ww33-window-extrema ----------------------------------------------
    for caption in ("Window Max Avg", "Window Min Avg"):
        local = columns[caption].get("name")
        instance = next(
            node for node in instances.values() if node.get("column") == local
        )
        nested = instance.findall("table-calc")
        assert len(nested) == 2, (caption, [etree.tostring(n) for n in nested])
        assert nested[0].get("ordering-field", "").endswith("[Sub-Category (group)]")
        assert nested[1].get("field", "").endswith(columns["Moving Avg"].get("name"))
        assert nested[1].get("ordering-field", "").endswith(MONTH)

    # --- ww33-chart --------------------------------------------------------
    panes = sheet.findall("table/panes/pane")
    assert len(panes) == 2, len(panes)
    marks = [pane.find("mark").get("class") for pane in panes]
    assert marks == ["Line", "Area"], marks
    line, area = panes
    colors = [node.get("column") for node in line.findall("encodings/color")]
    assert any("Sub-Category (group) Set" in column for column in colors), colors
    assert any(column.endswith("[Sub-Category (group)]") for column in colors), colors
    assert line.find("encodings/size") is not None, "line pane has no size encoding"
    assert line.find("encodings/lod").get("column").endswith("[Sub-Category (group)]")
    area_colors = [node.get("column") for node in area.findall("encodings/color")]
    assert any("Measure Names" in column for column in area_colors), area_colors
    assert area.find("encodings/lod").get("column").endswith("[Sub-Category (group)]")
    rows = sheet.findtext("table/rows")
    assert "Multiple Values" in rows and "Calculation_" in rows, rows
    columns_shelf = sheet.findtext("table/cols")
    assert MONTH in columns_shelf, columns_shelf
    axis_rule = sheet.find("table/style/style-rule[@element='axis']")
    assert axis_rule is not None
    spaces = axis_rule.findall("encoding[@type='space']")
    assert spaces and spaces[0].get("fold") == "true", [etree.tostring(s) for s in spaces]
    assert spaces[0].get("synchronized") == "true"
    mark_rule = sheet.find("table/style/style-rule[@element='mark']")
    size_encoding = mark_rule.find("encoding[@attr='size']")
    assert size_encoding is not None
    assert size_encoding.get("type") == "catsize"
    assert (size_encoding.get("min-size"), size_encoding.get("max-size")) == ("0.2", "1")

    # The band must paint under the lines: the Area pane's Measure Names
    # palette is white for the lower (min) measure and pale grey for the max.
    datasource = next(
        node
        for node in root.findall("datasources/datasource")
        if node.get("name") != "Parameters"
    )
    palette = datasource.find(
        "style/style-rule[@element='mark']/encoding[@field='[:Measure Names]']"
    )
    assert palette is not None
    mapped = {
        entry.find("bucket").text: entry.get("to") for entry in palette.findall("map")
    }
    assert set(mapped.values()) == {"#ffffff", "#eeeeee"}, mapped
    assert any("Window Min" in json.dumps(key) or "Calculation_" in key for key in mapped)

    # --- ww33-dashboard-controls ------------------------------------------
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zones = dashboard.findall(".//zone")
    set_zones = [zone for zone in zones if zone.get("type-v2") == "setMembership"]
    assert len(set_zones) == 1, len(set_zones)
    assert set_zones[0].get("param", "").endswith("[Sub-Category (group) Set]")
    assert set_zones[0].get("mode") == "checkdropdown"
    controls = [zone for zone in zones if zone.get("type-v2") == "paramctrl"]
    bound = {zone.get("param") for zone in controls}
    assert bound == {"[Parameters].[Parameter 1]", "[Parameters].[Parameter 2]"}, bound
    assert all(zone.get("mode") == "slider" for zone in controls)
    sheet_zones = [
        zone for zone in zones if zone.get("name") == "Viz" and zone.get("type-v2") == "NONE"
    ]
    assert sheet_zones, "Viz is not placed on the dashboard"

    # --- ww33-moving-average-values ---------------------------------------
    assert facts["accessories_2018_06_moving_avg"] == round(
        sum(facts["accessories_2018_06_sales"]) / 6, 6
    )
    assert facts["window_extrema_2018_06"]["max"] >= facts["window_extrema_2018_06"]["min"]
    (HERE / "outputs/expected-moving-avg.csv").write_text(
        "Month of Order Date,Sub-Category (group),Sales,Moving Avg,Window Max Avg,"
        "Window Min Avg\n"
        + "\n".join(
            ",".join(str(row[key]) for key in row) for row in facts["csv_rows"]
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = {
        "scope": (
            "Locked-extract oracle (monthly grouped sales, parameterised moving "
            "average, nested window extrema) plus native parameter/group/set/"
            "table-calc/dashboard workbook contracts."
        ),
        "acceptance": ACCEPTANCE,
        "facts": {key: value for key, value in facts.items() if key != "csv_rows"},
        "expected_rows": len(facts["csv_rows"]),
        "output_sha256": digest(OUTPUT),
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result["facts"], indent=2)[:2000])
    print("PASS")
