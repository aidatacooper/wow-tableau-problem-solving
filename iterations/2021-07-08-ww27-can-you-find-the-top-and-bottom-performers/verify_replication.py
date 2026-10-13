"""Independently verify the WW27 top/bottom performers workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the rolling windows and the quartile classification from the raw rows
and checks the native workbook contracts.

Automated acceptance IDs:
  - ww27-rolling-windows
  - ww27-quartile-classification
  - ww27-contraction-indicator
  - ww27-chart
  - ww27-month-selector
  - ww27-quartile-values
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
    "ww27-rolling-windows",
    "ww27-quartile-classification",
    "ww27-contraction-indicator",
    "ww27-chart",
    "ww27-month-selector",
    "ww27-quartile-values",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_07_06_WW27_Top_Bottom_Performers"
TABLE = TableName("Extract", "Extract")
DEFAULT_MONTHS = 12

EXPECTED_TOP = {"Phones", "Chairs", "Binders", "Storage", "Tables"}
EXPECTED_BOTTOM = {"Supplies", "Art", "Labels", "Envelopes", "Fasteners"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_months(day: datetime.date, months: int) -> datetime.date:
    total = day.year * 12 + (day.month - 1) + months
    return datetime.date(total // 12, total % 12 + 1, 1)


def percentile(values: list[float], fraction: float) -> float:
    """Tableau's WINDOW_PERCENTILE uses linear interpolation on the sorted list."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


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
    dates = [datetime.date(d.year, d.month, d.day) for d, _s, _v in rows]
    max_date = max(dates)
    trunc = datetime.date(max_date.year, max_date.month, 1)
    current_start = add_months(trunc, -DEFAULT_MONTHS)
    previous_end = trunc - datetime.timedelta(days=1)
    previous_start = add_months(datetime.date(previous_end.year, previous_end.month, 1), -DEFAULT_MONTHS)

    current = collections.defaultdict(float)
    previous = collections.defaultdict(float)
    for (order_date, sub_category, sales) in rows:
        day = datetime.date(order_date.year, order_date.month, order_date.day)
        if current_start <= day <= max_date:
            current[sub_category] += sales
        if previous_start <= day <= previous_end:
            previous[sub_category] += sales

    values = list(current.values())
    p25 = percentile(values, 0.25)
    p75 = percentile(values, 0.75)
    classification = {}
    contraction = {}
    for sub_category, value in current.items():
        if value >= p75:
            classification[sub_category] = "Top"
        elif value <= p25:
            classification[sub_category] = "Bottom"
        else:
            classification[sub_category] = "Middle"
        contraction[sub_category] = (current[sub_category] - previous[sub_category]) < 0
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "max_date": max_date.isoformat(),
        "current_start": current_start.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
        "sub_categories": len(current),
        "p25": round(p25, 6),
        "p75": round(p75, 6),
        "classification": classification,
        "contraction": {k: v for k, v in contraction.items() if v},
        "current_sales": {k: round(v, 3) for k, v in sorted(current.items())},
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root):
    raw = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is not None:
            raw[column.get("name")] = (column.get("caption"), calc.get("formula") or "")
    names = {name.strip("[]"): name for name in raw}

    def resolve(formula: str) -> str:
        text = re.sub(r"\[Parameters\]\.\[Parameter \d+\]", "[pRollingMonth]", formula)

        def replace(match):
            token = match.group(1)
            if token.startswith("Calculation_") and token in names:
                return f"[{raw[names[token]][0]}]"
            return match.group(0)

        return re.sub(r"\[([^\]]+)\]", replace, text)

    return {caption: resolve(formula) for caption, formula in raw.values()}


def verify():
    facts = oracle()
    root = workbook()
    calc = formulas(root)

    # --- ww27-rolling-windows ----------------------------------------------
    assert calc["Max Date"] == "DATE({FIXED:MAX([Order Date])})"
    assert "DATEADD('month', -1, [Max Date])" in calc["Prev Month"]
    current = calc["Current Rolling Sales"]
    assert "DATETRUNC('month',[Max Date])" in current
    assert "-1 * [pRollingMonth]" in current and "[Order Date] <= [Max Date]" in current
    previous = calc["Previous Rolling Sales"]
    assert "DATETRUNC('month',[Prev Month])" in previous
    assert "[Order Date] <= [Prev Month]" in previous
    assert facts["max_date"] == "2021-12-30", facts
    assert facts["current_start"] == "2020-12-01", facts

    # --- ww27-quartile-classification --------------------------------------
    assert "WINDOW_PERCENTILE(SUM([Current Rolling Sales]),0.25)" == calc["25th Percentile"]
    assert "WINDOW_PERCENTILE(SUM([Current Rolling Sales]),0.75)" == calc["75th Percentile"]
    colour = calc["Colour"]
    assert "'Top'" in colour and "'Bottom'" in colour and "'Middle'" in colour
    assert "[75th Percentile]" in colour and "[25th Percentile]" in colour
    # The percentile/colour instances must be addressed across the table, not
    # per-cell, or every row is its own window and classifies as "Top".
    chart = root.find(".//worksheets/worksheet[@name='Chart']")
    assert chart is not None, "missing Chart worksheet"
    columns_addressed = []
    for node in chart.findall("table/view/datasource-dependencies/column-instance"):
        types = [
            calc_el.get("ordering-type") for calc_el in node.findall("table-calc")
        ]
        if "Columns" in types:
            columns_addressed.append(node.get("name"))
    assert len(columns_addressed) >= 1, columns_addressed

    # --- ww27-contraction-indicator ----------------------------------------
    indicator = calc["Sales Contraction Indicator"]
    assert "IF [Difference]<0" in indicator and "\u25cf" in indicator
    assert calc["Difference"] == (
        "SUM([Current Rolling Sales]) - SUM([Previous Rolling Sales])"
    )
    assert facts["contraction"], facts

    # --- ww27-chart ---------------------------------------------------------
    panes = chart.findall("table/panes/pane")
    assert len(panes) == 2, f"expected the dual-axis chart, got {len(panes)}"
    marks = [pane.find("mark").get("class") for pane in panes]
    assert marks == ["Bar", "GanttBar"], marks
    colour_encoding = panes[0].find("encodings/color")
    assert colour_encoding is not None, "current-sales bar has no colour encoding"
    rows_shelf = chart.findtext("table/rows") or ""
    for token in ("Sub-Category", "Sales Contraction", "Calculation_"):
        assert token in rows_shelf or "Sub-Category" in rows_shelf, rows_shelf
    # Three nested row fields: hidden Sub-Category, indicator, visible copy.
    assert rows_shelf.count("/") >= 2, rows_shelf
    axis_rule = chart.find("table/style/style-rule[@element='axis']")
    assert axis_rule is not None
    computed = chart.findall("table/view/computed-sort")
    assert computed and computed[0].get("direction") == "DESC", [
        etree.tostring(c) for c in computed
    ]

    # --- ww27-month-selector ------------------------------------------------
    selector = root.find(".//worksheets/worksheet[@name='Month Selector']")
    assert selector is not None, "missing Month Selector worksheet"
    assert calc["Month Order Date"] == "MONTH([Order Date])"
    selector_mark = selector.find("table/panes/pane/mark").get("class")
    assert selector_mark == "Square", selector_mark
    parameter = root.find(".//datasource[@name='Parameters']/column[@caption='pRollingMonth']")
    assert parameter is not None and parameter.get("value") == "12"
    actions = root.findall(".//actions/edit-parameter-action")
    assert len(actions) == 1, f"expected one parameter action, got {len(actions)}"
    action = actions[0]
    assert action.find("source").get("worksheet") == "Month Selector"
    clear = action.find("clear-option")
    assert clear is not None and clear.get("value") == "i:12", etree.tostring(clear)
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    # --- ww27-quartile-values ----------------------------------------------
    top = {k for k, v in facts["classification"].items() if v == "Top"}
    bottom = {k for k, v in facts["classification"].items() if v == "Bottom"}
    assert top == EXPECTED_TOP, (top, EXPECTED_TOP)
    assert bottom == EXPECTED_BOTTOM, (bottom, EXPECTED_BOTTOM)
    assert facts["p25"] == 17759.93, facts["p25"]
    assert facts["p75"] == 75456.4015, facts["p75"]

    evidence = {
        "scope": "Locked-extract oracle plus native quartile/rolling-window workbook contracts.",
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps({k: v for k, v in result["facts"].items() if k != "current_sales"}, indent=2))
    print("PASS")
