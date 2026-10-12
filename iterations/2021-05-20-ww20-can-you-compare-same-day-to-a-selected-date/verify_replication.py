"""Independently verify the WW20 "same day vs selected date" workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the equivalent-day logic and the per-day sales from the raw rows,
then checks the native workbook contracts that carry the solution chain.

Automated acceptance IDs:
  - ww20-compare-date-logic
  - ww20-selected-compared-sales
  - ww20-percent-difference
  - ww20-ban
  - ww20-line-chart-dates-to-show
  - ww20-parameter-actions
"""

import calendar
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
    "ww20-compare-date-logic",
    "ww20-selected-compared-sales",
    "ww20-percent-difference",
    "ww20-ban",
    "ww20-line-chart-dates-to-show",
    "ww20-parameter-actions",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_05_19_WW20_Date_Compare"
TABLE = TableName("Extract", "Extract")
DEFAULT_SELECTED = datetime.date(2021, 5, 18)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- Independent re-implementation of the article's equivalent-day logic -----
def exact_date_prev_month(selected: datetime.date) -> datetime.date:
    """DATE(DATEADD('month', -1, [pSelectedDate]))."""
    year = selected.year if selected.month > 1 else selected.year - 1
    month = selected.month - 1 if selected.month > 1 else 12
    day = min(selected.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def dow_selected(selected: datetime.date) -> int:
    """DATEPART('weekday', ..., 'Sunday') -> Sunday=1 ... Saturday=7."""
    return (selected.weekday() + 1) % 7 + 1


def datetrunc_week(day: datetime.date, start_weekday: int) -> datetime.date:
    """DATETRUNC('week', day, <start_weekday name>); Sunday=1 naming."""
    current = dow_selected(day)
    offset = (current - start_weekday) % 7
    return day - datetime.timedelta(days=offset)


def equivalent_day_last_month(selected: datetime.date) -> datetime.date:
    exact = exact_date_prev_month(selected)
    prior = datetrunc_week(exact, dow_selected(selected))
    following = prior + datetime.timedelta(days=7)
    return prior if selected.month == following.month else following


def equivalent_day_last_year(selected: datetime.date) -> datetime.date:
    # Tableau's DATEADD('year', -1, ...) clamps 29 Feb onto 28 Feb.
    target_year = selected.year - 1
    day = min(selected.day, calendar.monthrange(target_year, selected.month)[1])
    prev_year = datetime.date(target_year, selected.month, day)
    leap_shift = (
        (selected.month <= 2 and (selected.year - 1) % 4 == 0)
        or (selected.month >= 3 and selected.year % 4 == 0)
    )
    return prev_year + datetime.timedelta(days=2 if leap_shift else 1)


def compare_date(selected: datetime.date, mode: int) -> datetime.date:
    if mode == 1:
        return equivalent_day_last_year(selected)
    if mode == 2:
        return equivalent_day_last_month(selected)
    return selected - datetime.timedelta(days=7)


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
            f'SELECT "Order Date", "Sales" FROM {TABLE}'
        )
    assert len(rows) == 9994, "row count changed"
    daily = {}
    for order_date, sales in rows:
        key = datetime.date(order_date.year, order_date.month, order_date.day).isoformat()
        daily[key] = daily.get(key, 0.0) + sales
    # The probe dates exercise the leap-year and missing-5th-occurrence cases.
    probes = [
        datetime.date(2021, 5, 18),
        datetime.date(2021, 1, 15),
        datetime.date(2020, 3, 31),
        datetime.date(2020, 2, 29),
        datetime.date(2019, 12, 31),
    ]
    logic = {
        probe.isoformat(): {
            "last_year": compare_date(probe, 1).isoformat(),
            "last_month": compare_date(probe, 2).isoformat(),
            "last_week": compare_date(probe, 3).isoformat(),
        }
        for probe in probes
    }
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "distinct_dates": len(daily),
        "default_selected": DEFAULT_SELECTED.isoformat(),
        "default_sales": {
            "selected": round(daily[DEFAULT_SELECTED.isoformat()], 3),
            "last_year": round(daily[compare_date(DEFAULT_SELECTED, 1).isoformat()], 3),
            "last_month": round(daily[compare_date(DEFAULT_SELECTED, 2).isoformat()], 3),
            "last_week": round(daily[compare_date(DEFAULT_SELECTED, 3).isoformat()], 3),
        },
        "logic": logic,
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root):
    result = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is not None:
            result[column.get("caption")] = calc.get("formula") or ""
    return result


def verify():
    facts = oracle()
    root = workbook()
    calc = formulas(root)

    # --- ww20-compare-date-logic -------------------------------------------
    # The workbook's chain must encode the leap-year branch and the
    # weekday-truncation fallback that the oracle re-implements above.
    assert "DATEADD('month', -1, [Parameters].[Parameter 1])" in calc["Exact Date Prev Month"]
    assert "DATEPART('weekday',[Parameters].[Parameter 1],'Sunday')" in calc["DoW Selected Date"]
    prior = calc["Prior DoW Prev Mth"]
    for weekday in ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"):
        assert f"DATETRUNC('week', " in prior and f"'{weekday}')" in prior, weekday
    assert "MONTH([Parameters].[Parameter 1]) = MONTH(" in calc["Equivalent Day Last Month"]
    last_year = calc["Equivalent Day Last Year"]
    assert "(YEAR([Parameters].[Parameter 1])-1)%4=0" in last_year
    assert "YEAR([Parameters].[Parameter 1])%4=0" in last_year
    assert "DATEADD('day',2,DATEADD('year',-1," in last_year
    assert "DATEADD('day',1,DATEADD('year',-1," in last_year
    compare = calc["Compare Date"]
    assert "THEN [Calculation_" in compare and "= 1" in compare and "= 2" in compare
    assert "DATEADD('week', -1, [Parameters].[Parameter 1])" in compare
    assert "pComparison" in {c.get("caption") for c in root.findall(".//datasource/column")}
    comparison = next(
        c for c in root.findall(".//datasource[@name='Parameters']/column")
        if c.get("caption") == "pComparison"
    )
    aliases = {a.get("key"): a.get("value") for a in comparison.findall("aliases/alias")}
    assert aliases == {
        "1": "Same Day Last Year",
        "2": "Same Day Last Month",
        "3": "Last Week",
    }, aliases

    # --- ww20-selected-compared-sales --------------------------------------
    assert calc["Selected Date Sales"] == (
        "IF [Order Date] = [Parameters].[Parameter 1] THEN [Sales] END"
    )
    assert "IF [Order Date] = [Calculation_" in calc["Compared Date Sales"]
    assert calc["Compared Date Sales"].endswith("THEN [Sales] END")
    # The oracle's per-day sums for the default selection must be non-null.
    assert all(value > 0 for value in facts["default_sales"].values()), facts["default_sales"]

    # --- ww20-percent-difference -------------------------------------------
    difference = calc["% Difference"]
    assert "SUM(" in difference and ") - SUM(" in difference and "/ SUM(" in difference
    difference_column = next(
        c for c in root.findall(".//datasource/column") if c.get("caption") == "% Difference"
    )
    assert difference_column.get("default-format") == "*▲0.0%;▼0.0%"

    # --- ww20-ban -----------------------------------------------------------
    ban = root.find(".//worksheets/worksheet[@name='BAN']")
    assert ban is not None, "missing BAN worksheet"
    axis = ban.find(".//style/style-rule[@element='axis']/encoding")
    assert axis is not None and axis.get("min") == "0" and axis.get("max") == "1"
    assert axis.get("range-type") == "fixed"
    pane = ban.find("table/panes/pane")
    assert pane.find("mark").get("class") == "Bar"
    color = pane.find("encodings/color")
    assert color is not None and "Calculation_" in (color.get("column") or "")
    label = pane.find("customized-label")
    assert label is not None, "BAN has no customized label"
    runs = "".join(node.text or "" for node in label.findall("formatted-text/run"))
    assert "Selected" not in runs and "vs." in runs
    assert re.search(r"\(<\[Parameters\]\.\[Parameter 2\]>", runs), runs
    assert "Compare Date" not in runs
    text_columns = [node.get("column", "") for node in pane.findall("encodings/text")]
    assert any("Selected Date" not in c and "Calculation_" in c for c in text_columns)
    # The BAN colour legend uses the author's 24-swatch diverging palette.
    palette = ban.findall(".//style-rule[@element='mark']//color-palette/color")
    assert [c.text for c in palette] == [
        "#0b8376", "#178a7e", "#249286", "#339a8f", "#43a298", "#55aaa0",
        "#67b1a9", "#7bb9b3", "#91c1bc", "#a7c9c5", "#bfd1cf", "#d9d9d9",
        "#c5c5c5", "#b1b1b1", "#9d9d9d", "#8a8a8a", "#767676", "#626262",
        "#4e4e4e", "#3b3b3b", "#272727", "#131313", "#000000", "#000000",
    ], [c.text for c in palette]

    # --- ww20-line-chart-dates-to-show -------------------------------------
    chart = root.find(".//worksheets/worksheet[@name='Chart']")
    assert chart is not None, "missing Chart worksheet"
    filters = chart.findall(".//view/filter")
    assert any(
        "Calculation_" in (f.get("column") or "")
        and f.find("groupfilter").get("member") == "true"
        for f in filters
    ), "Dates To Show filter missing"
    panes = chart.findall("table/panes/pane")
    assert len(panes) == 2, f"expected the dual-layer chart, got {len(panes)}"
    assert panes[0].find("mark").get("class") == "Line"
    circle = panes[1]
    assert circle.find("mark").get("class") == "Circle"
    measure_filter = next(
        f for f in filters if (f.get("column") or "").endswith("[:Measure Names]")
    )
    members = measure_filter.findall(".//groupfilter[@function='member']")
    assert len(members) == 3, f"expected three shared measures, got {len(members)}"
    assert "Selected | Compared Sales Value" in calc
    assert "THEN -500 END" in calc["Minus 500"]
    cols = chart.findtext("table/cols")
    assert "Order Date" in cols, cols
    rows = chart.findtext("table/rows")
    assert "Sales" in rows and "Multiple Values" in rows, rows

    # --- ww20-parameter-actions --------------------------------------------
    actions = root.findall(".//actions/edit-parameter-action")
    assert len(actions) == 2, f"expected two parameter actions, got {len(actions)}"
    targets = {
        a.find("params/param[@name='target-parameter']").get("value") for a in actions
    }
    assert targets == {"[Parameters].[Parameter 1]"}, targets
    sources = {
        a.find("params/param[@name='source-field']").get("value") for a in actions
    }
    assert any("Order Date" in s for s in sources), sources
    assert any("Calculation_" in s for s in sources), sources
    assert "DATE(#2021-05-18#)" in calc["Default Date"]
    filter_actions = root.findall(".//actions/action")
    assert any(
        (a.find("link") is not None and "~s0=<" in (a.find("link").get("expression") or ""))
        for a in filter_actions
    ), "True->False 'Don't highlight' action missing"
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    evidence = {
        "scope": "Locked-extract oracle plus native compare-date workbook contracts.",
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
    print(json.dumps(result["facts"], indent=2))
    print("PASS")
