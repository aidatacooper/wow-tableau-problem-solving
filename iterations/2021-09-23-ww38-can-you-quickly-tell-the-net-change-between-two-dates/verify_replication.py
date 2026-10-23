"""Independently verify the WW38 "net change between two dates" workbook.

Reads only the locked Hyper extracts, the written case files and the built
TWBX.  Recomputes, from the raw rows, the 14-day default range, the per-region
first/last trading day inside that range, the min/max sales on those days, the
net change and the percent change; then checks that the workbook encodes the
same chain natively.

Automated acceptance IDs:
  - ww38-parameters
  - ww38-range-calculations
  - ww38-region-range-lod
  - ww38-net-change-oracle
  - ww38-trend-chart
  - ww38-reference-bands
  - ww38-kpi-table
  - ww38-timeframe-selector
  - ww38-dashboard-actions
"""

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
    "ww38-parameters",
    "ww38-range-calculations",
    "ww38-region-range-lod",
    "ww38-net-change-oracle",
    "ww38-trend-chart",
    "ww38-reference-bands",
    "ww38-kpi-table",
    "ww38-timeframe-selector",
    "ww38-dashboard-actions",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD = "2021_09_22_WW38_Daily_Sales_Tracker"
ORDERS_TABLE = TableName("Extract", "Extract")
P_TODAY = datetime.date(2021, 9, 20)
DEFAULT_START = P_TODAY - datetime.timedelta(days=14)
REGION_ORDER = ["South", "West", "Central", "East"]
TIMEFRAMES = ["1 MONTH", "6 MONTHS", "YTD", "1 YEAR", "MAX"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _locked(name: str) -> Path:
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    record = next(item for item in lock["extracted_data"] if name in item["file"])
    path = HERE / record["file"]
    assert digest(path) == record["sha256"], f"locked extract changed: {name}"
    return path


# --- Independent re-implementation of the article's range logic --------------
def timeframe_window(timeframe: str, today: datetime.date) -> tuple[datetime.date, datetime.date]:
    """DATEADD/DATETRUNC bounds of the 'Timeframe to Display' CASE."""
    if timeframe == "1 MONTH":
        year, month = (today.year, today.month - 1) if today.month > 1 else (
            today.year - 1, 12
        )
        import calendar

        day = min(today.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day), today
    if timeframe == "6 MONTHS":
        import calendar

        month_index = today.year * 12 + (today.month - 1) - 6
        year, month = divmod(month_index, 12)
        month += 1
        day = min(today.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day), today
    if timeframe == "YTD":
        return datetime.date(today.year, 1, 1), today
    if timeframe == "1 YEAR":
        import calendar

        day = min(today.day, calendar.monthrange(today.year - 1, today.month)[1])
        return datetime.date(today.year - 1, today.month, day), today
    return datetime.date(1900, 1, 1), today


def oracle(start: datetime.date = DEFAULT_START, end: datetime.date = P_TODAY) -> dict:
    rows = []
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(_locked("Orders (Sample - Superstore).hyper"))) as connection,
    ):
        rows = connection.execute_list_query(
            f'SELECT "Order Date", "Region", "Sales" FROM {ORDERS_TABLE}'
        )
    assert len(rows) == 9994, "row count changed"

    daily: dict[str, dict[datetime.date, float]] = {}
    for order_date, region, sales in rows:
        day = datetime.date(order_date.year, order_date.month, order_date.day)
        daily.setdefault(region, {})
        daily[region][day] = daily[region].get(day, 0.0) + sales

    regions = {}
    for region, days in daily.items():
        inside = sorted(day for day in days if start <= day <= end)
        first, last = inside[0], inside[-1]
        first_sales = round(days[first], 3)
        last_sales = round(days[last], 3)
        difference = round(last_sales - first_sales, 3)
        regions[region] = {
            "first_trading_day": first.isoformat(),
            "last_trading_day": last.isoformat(),
            "first_day_sales": first_sales,
            "last_day_sales": last_sales,
            "net_change": difference,
            "percent_change": round(difference / first_sales, 6),
            "positive": difference >= 0,
        }

    window_start, window_end = timeframe_window("6 MONTHS", P_TODAY)
    window_marks = {
        region: [
            day.isoformat()
            for day in sorted(daily[region])
            if window_start <= day <= window_end
        ]
        for region in daily
    }
    return {
        "today": P_TODAY.isoformat(),
        "default_range": [start.isoformat(), end.isoformat()],
        "default_window": [window_start.isoformat(), window_end.isoformat()],
        "regions": regions,
        "window_mark_counts": {r: len(v) for r, v in window_marks.items()},
        "window_first_last": {
            r: [v[0], v[-1]] for r, v in window_marks.items() if v
        },
        "region_order": REGION_ORDER,
        "row_count": len(rows),
    }


def workbook() -> etree._ElementTree:
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def data_sources(root):
    """Workbook-level data sources (worksheet views carry ``<datasource>`` stubs).

    ``lxml``'s limited ElementPath does not support ``!=`` predicates, so the
    parameter source is filtered in Python.
    """
    return [
        source
        for source in root.findall("datasources/datasource")
        if source.get("name") != "Parameters"
    ]


def formula_map(root) -> dict[str, str]:
    """Return every calculation keyed by caption, with internal names expanded.

    Tableau stores a calculation's dependencies as generated local names, so a
    naive text comparison would never see the article's field references. This
    rewrites each internal name back to the caption a reader would recognise.
    """
    raw = {}
    names = {}
    for source in data_sources(root):
        for column in source.findall("column"):
            if column.get("caption"):
                names[column.get("name")] = column.get("caption")
            calc = column.find("calculation")
            if calc is not None and column.get("caption"):
                raw[column.get("caption")] = calc.get("formula") or ""
    resolved = {}
    for caption, formula in raw.items():
        for internal, other in sorted(names.items(), key=lambda kv: -len(kv[0])):
            formula = formula.replace(internal, f"[{other}]")
        resolved[caption] = formula
    return resolved


def formulas(root) -> dict[str, str]:
    """Captions/formulas of the workbook-level data sources only.

    Worksheet views carry their own ``<datasource>`` stubs, so every lookup
    stays on ``datasources/datasource``.
    """
    result = {}
    for source in data_sources(root):
        for column in source.findall("column"):
            calc = column.find("calculation")
            if calc is not None and column.get("caption"):
                result[column.get("caption")] = calc.get("formula") or ""
    return result


def parameter(root, caption):
    for column in root.findall("datasources/datasource/column"):
        if column.get("caption") == caption:
            return column
    return None


def sheet(root, name):
    worksheet = root.find(f".//worksheets/worksheet[@name='{name}']")
    assert worksheet is not None, f"missing worksheet: {name}"
    return worksheet


def pane_columns(worksheet):
    return [
        node.get("column", "")
        for node in worksheet.findall("table/panes/pane/encodings/*")
    ]


def verify():
    facts = oracle()
    july = oracle(datetime.date(2021, 7, 1), datetime.date(2021, 7, 31))
    single = oracle(datetime.date(2021, 9, 7), datetime.date(2021, 9, 7))
    assert all(x["net_change"] == 0 for x in single["regions"].values())
    assert all(x["first_trading_day"].startswith("2021-07") and x["last_trading_day"].startswith("2021-07") for x in july["regions"].values())
    assert timeframe_window("1 MONTH", P_TODAY)[0] == datetime.date(2021, 8, 20)
    assert timeframe_window("1 YEAR", P_TODAY)[0] == datetime.date(2020, 9, 20)
    assert timeframe_window("YTD", P_TODAY)[0] == datetime.date(2021, 1, 1)
    states = {"default": facts, "july-range": july, "single-day": single}
    (HERE / "outputs/expected-range-states.json").write_text(json.dumps(states, indent=2) + "\n", encoding="utf-8")
    with ZipFile(OUTPUT) as archive:
        for name in ("Orders (Sample - Superstore).hyper", "Date Range.hyper"):
            locked = _locked(name)
            packaged_hashes = {hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.endswith(".hyper")}
            assert digest(locked) in packaged_hashes, f"Locked input not packaged unchanged: {name}"
    root = workbook()
    calc = formula_map(root)

    # --- ww38-parameters ----------------------------------------------------
    today = parameter(root, "pToday")
    start = parameter(root, "pStartRange")
    end = parameter(root, "pEndRange")
    timeframe = parameter(root, "pTimeframe")
    assert today is not None and today.get("datatype") == "date"
    assert today.get("value") == "#2021-09-20#", today.get("value")
    assert start.get("value") == "#1900-01-01#"
    assert end.get("value") == "#1900-01-01#"
    assert timeframe.get("datatype") == "string"
    assert timeframe.get("value") == '"6 MONTHS"', timeframe.get("value")
    members = [m.get("value") for m in timeframe.findall("members/member")]
    assert members == [f'"{value}"' for value in TIMEFRAMES], members

    # --- ww38-range-calculations -------------------------------------------
    assert calc["Selected Range Start Date"] == (
        "IF [Parameters].[Parameter 2] = #1900-01-01# THEN "
        "DATE(DATEADD('day',-14,[Parameters].[Parameter 1]))\n"
        "ELSE DATE([Parameters].[Parameter 2])\nEND"
    )
    assert calc["Selected Range End Date"] == (
        "IF [Parameters].[Parameter 3] = #1900-01-01# THEN "
        "DATE([Parameters].[Parameter 1])\n"
        "ELSE DATE([Parameters].[Parameter 3])\nEND"
    )
    assert calc["Order Date Day"] == "DATE(DATETRUNC('day',[Order Date]))"
    display = calc["Timeframe to Display"]
    for branch in (
        "WHEN '1 MONTH' THEN",
        "WHEN '6 MONTHS' THEN",
        "WHEN 'YTD' THEN",
        "WHEN '1 YEAR' THEN",
        "ELSE ",
    ):
        assert branch in display, branch
    assert "DATEADD('month', -6," in display
    assert "DATETRUNC('year'," in display
    assert "DATEADD('year',-1," in display
    assert "THEN [Order Date Day] END" in calc["Selected Dates to Plot"]
    assert "[Selected Range Start Date]" in calc["Selected Dates to Plot"]
    assert "[Selected Range End Date]" in calc["Selected Dates to Plot"]

    # --- ww38-region-range-lod ---------------------------------------------
    assert calc["Min Selected Date Per Region"] == (
        "{FIXED [Region]: MIN([Selected Dates to Plot])}"
    )
    assert calc["Max Selected Date Per Region"] == (
        "{FIXED [Region]: MAX([Selected Dates to Plot])}"
    )
    assert calc["Min Date Sales"].startswith("{FIXED [Region]: SUM(IF [Order Date Day]=")
    assert calc["Max Date Sales"].startswith("{FIXED [Region]: SUM(IF [Order Date Day]=")
    assert "[Min Selected Date Per Region]" in calc["Min Date Sales"]
    assert "[Max Selected Date Per Region]" in calc["Max Date Sales"]
    assert "THEN [Sales] END)}" in calc["Min Date Sales"]
    assert "THEN [Sales] END)}" in calc["Max Date Sales"]

    # --- ww38-net-change-oracle --------------------------------------------
    assert calc["Range Sales Diff"] == "SUM([Max Date Sales])-SUM([Min Date Sales])"
    assert calc["Range Sales % Diff"] == (
        "[Range Sales Diff]/SUM([Min Date Sales])"
    )
    assert calc["Colour - KPI"] == "[Range Sales Diff]>=0"
    trend_colour = calc["Colour - Trend"]
    assert "IF MIN([Order Date Day]) >= [Selected Range Start Date]" in trend_colour
    assert "THEN 1" in trend_colour and "ELSE -1" in trend_colour and "ELSE 0" in trend_colour
    for caption, sign in (
        ("Ref Line Start Date -ve", "<0"),
        ("Ref Line End Date -ve", "<0"),
        ("Ref Line Start Date +ve", ">=0"),
        ("Ref Line End Date +ve", ">=0"),
    ):
        assert calc[caption] == (
            f"IF [Range Sales Diff]{sign} THEN "
            + ("[Selected Range Start Date]" if "Start" in caption
               else "[Selected Range End Date]")
            + " END"
        ), calc[caption]
    columns = {
        column.get("caption"): column
        for source in data_sources(root)
        for column in source.findall("column")
    }
    assert columns["Range Sales Diff"].get("default-format") == (
        '*+"$"#,##0.00;-"$"#,##0.00'
    )
    assert columns["Range Sales % Diff"].get("default-format") == "*▲0.0%;▼0.0%"

    # The oracle's numbers are the ones the workbook must reproduce: four
    # regions, one net change per region, and at least one loss and one gain so
    # both band halves are exercised.
    assert set(facts["regions"]) == {"Central", "East", "South", "West"}
    assert facts["default_range"] == ["2021-09-06", "2021-09-20"]
    assert sum(1 for r in facts["regions"].values() if not r["positive"]) == 1
    assert sum(1 for r in facts["regions"].values() if r["positive"]) == 3
    # Region boundaries are the trading days, not the calendar range ends.
    assert facts["regions"]["Central"]["last_trading_day"] == "2021-09-18"
    assert facts["regions"]["East"]["last_trading_day"] == "2021-09-20"
    assert facts["regions"]["Central"]["net_change"] < 0
    assert facts["regions"]["East"]["net_change"] > 0

    # --- ww38-trend-chart ---------------------------------------------------
    trend = sheet(root, "Trend")
    panes = trend.findall("table/panes/pane")
    assert len(panes) == 2, f"expected a folded dual axis, got {len(panes)}"
    assert panes[0].find("mark").get("class") == "Line"
    assert panes[1].find("mark").get("class") == "Area"
    cols = trend.findtext("table/cols")
    assert cols.count(" + ") == 1, cols
    assert cols.count("[none:") == 2 and cols.count(":qk]") == 2, cols
    assert all(p.find("view/breakdown").get("value") == "off" for p in panes)
    for p in panes:
        tooltip = "".join(p.itertext())
        assert "EXACTDATE(" not in tooltip
    rows = trend.findtext("table/rows")
    assert "Region" in rows and "Sales" in rows, rows
    fold = trend.find("table/style/style-rule[@element='axis']/encoding")
    assert fold is not None and fold.get("fold") == "true"
    assert fold.get("synchronized") == "true"
    timeframe_filter = [
        f for f in trend.findall("table/view/filter")
        if f.find("groupfilter") is not None
        and f.find("groupfilter").get("member") == "true"
    ]
    assert timeframe_filter, "Timeframe to Display = True filter missing"
    colours = pane_columns(trend)
    assert sum(1 for column in colours if ":ok]" in column) == 2, colours

    # --- ww38-reference-bands ----------------------------------------------
    palette = {}
    for encoding in [
        node
        for source in data_sources(root)
        for node in source.findall("style/style-rule/encoding")
    ]:
        if encoding.get("attr") != "color":
            continue
        palette[encoding.get("field")] = {
            (m.findtext("bucket") or ""): m.get("to")
            for m in encoding.findall("map")
        }
    trend_palettes = [v for k, v in palette.items() if ":ok]" in k]
    assert any(
        v == {"1": "#57c4ad", "-1": "#eb4325", "0": "#ffffff"} for v in palette.values()
    ), palette
    assert any(
        v == {"true": "#59a14f", "false": "#e15759"} for v in palette.values()
    ), palette
    assert any(
        v == {"true": "#ffffff", "false": "#d5d5d5"} for v in palette.values()
    ), palette

    bands = []
    assert not panes[0].findall("reference-line"), "Earlier pane background would cover the band"
    for pane in panes[1:]:
        lines = pane.findall("reference-line")
        assert len(lines) == 4, f"Final pane needs both conditional bands, got {len(lines)}"
        ids = {line.get("id") for line in lines}
        assert all(line.get("paired-id") in ids for line in lines)
        assert all(line.get("scope") == "per-cell" for line in lines)
        assert {line.get("formula") for line in lines} == {"min", "max"}
        axis = {line.get("axis-column") for line in lines}
        assert len(axis) == 1
        bands.append((axis.pop(), {line.get("value-column") for line in lines}))
    band_fields = [field for _, fields in bands for field in fields]
    assert any("Calculation_" in field for field in band_fields)
    detail_columns = [
        node.get("column")
        for node in trend.findall("table/panes/pane/encodings/lod")
    ]
    # Every band endpoint must also be on Detail, otherwise a per-cell band
    # resolves to null and the sheet renders blank.
    assert len(detail_columns) >= 8, detail_columns
    fills = {
        node.get("id"): node.get("value")
        for node in trend.findall("table/style/style-rule[@element='refband']/format")
        if node.get("attr") == "fill-color"
    }
    assert "#e8a09a" in fills.values() and "#f1f5e2" in fills.values(), fills

    # --- ww38-kpi-table -----------------------------------------------------
    kpi = sheet(root, "KPI")
    kpi_pane = kpi.find("table/panes/pane")
    assert kpi_pane.find("mark").get("class") == "Text"
    assert kpi.findtext("table/rows").count("Region") == 1
    kpi_texts = [
        node.get("column") for node in kpi_pane.findall("encodings/text")
    ]
    assert len(kpi_texts) == 2, kpi_texts
    label = "".join(
        node.text or ""
        for node in kpi_pane.findall("customized-label/formatted-text/run")
    )
    assert label.count("<") == 2 and label.count(">") == 2, label
    region_sort = kpi.find("table/view/shelf-sorts/shelf-sort-v2")
    assert region_sort is not None and region_sort.get("direction") == "DESC"
    assert "Region" in region_sort.get("dimension-to-sort", "")

    # --- ww38-timeframe-selector -------------------------------------------
    selector = sheet(root, "Timeframe Selector")
    assert selector.findtext("table/cols").count("Date Range") == 1
    selector_text = selector.find("table/panes/pane/encodings/text")
    assert selector_text is not None and "Date Range" in selector_text.get("column")
    selector_size = selector.find(
        "table/style/style-rule[@element='mark']/encoding[@attr='size']"
    )
    assert selector_size is not None and selector_size.get("type") == "catsize"
    list_source = [
        ds for ds in root.findall("datasources/datasource")
        if ds.get("caption") == "Date Range"
    ]
    assert len(list_source) == 1, "the five-row Date Range list source is missing"

    # --- ww38-dashboard-actions --------------------------------------------
    actions = root.findall(".//actions/edit-parameter-action")
    targets = {
        action.find("params/param[@name='target-parameter']").get("value"): action
        for action in actions
    }
    assert set(targets) == {
        "[Parameters].[Parameter 2]",
        "[Parameters].[Parameter 3]",
        "[Parameters].[Parameter 4]",
    }, sorted(targets)
    assert targets["[Parameters].[Parameter 4]"].find("source").get("worksheet") == (
        "Timeframe Selector"
    )
    assert targets["[Parameters].[Parameter 4]"].find("agg-type").get("type") == "attr"
    assert targets["[Parameters].[Parameter 2]"].find("agg-type").get("type") == "min"
    assert targets["[Parameters].[Parameter 3]"].find("agg-type").get("type") == "max"
    filter_actions = [
        action for action in root.findall(".//actions/action")
        if action.find("command") is not None
        and action.find("command").get("command") == "tsc:tsl-filter"
    ]
    assert len(filter_actions) == 2, filter_actions
    for action in filter_actions:
        expression = action.find("link").get("expression")
        assert "~s0=<" in expression, expression
        target = action.find("command/param[@name='target']").get("value")
        assert target in {"Trend", "Timeframe Selector"}
        filtered = sheet(root, target)
        action_filter = [
            f for f in filtered.findall("table/view/filter")
            if "Action (False)" in (f.get("column") or "")
        ]
        assert action_filter, f"{target} has no action filter"
        assert action_filter[0].find("groupfilter").get("member") == "false"
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD}']")
    assert dashboard is not None, "dashboard missing"
    size = dashboard.find("size")
    assert (size.get("maxwidth"), size.get("maxheight")) == ("700", "500")
    zone_names = {
        zone.get("name") for zone in dashboard.findall(".//zone") if zone.get("name")
    }
    assert {"Trend", "KPI", "Subtitle", "Timeframe Selector"} <= zone_names, zone_names
    hidden = {
        window.get("name")
        for window in root.findall(".//windows/window")
        if window.get("hidden") == "true"
    }
    assert not ({"Trend", "KPI", "Subtitle", "Timeframe Selector"} & hidden), "Replica sheets stay exposed for original/replica CSV verification"

    evidence = {
        "scope": (
            "Locked-extract oracle plus native workbook contracts for the "
            "timeframe/date-range net-change dashboard."
        ),
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
        "additional_states": ["july-range", "single-day"],
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result["facts"]["regions"], indent=2))
    print("PASS")
