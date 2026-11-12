"""Smallest runnable check that fails when the required behavior breaks.

The case is about one thing: comparing *weeks* across three years on one axis.
So the verifier recomputes the whole weekly series straight from the packaged
Hyper extract with the Hyper API — independently of the workbook the builder
produced — and then checks that the artifact's calculations and encodings carry
that behavior.

acceptance: week-buckets
acceptance: complete-weeks-only
acceptance: year-group-offset
acceptance: baseline-date-axis
acceptance: yoy-percent-change
acceptance: author-colour-key
acceptance: tooltip-yoy-label
"""

from __future__ import annotations

import datetime as dt
import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs" / "Sales Growth (2022_01_12_WW01_Superstore Sales Growth).hyper"
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"

# The challenge fixes "today" at 1 Dec 2021 so the last, still-running week is
# excluded instead of being plotted as a drop.
TODAY = dt.date(2021, 12, 1)

# Author palettes, keyed by year-group offset.
COLOURS = {"0": "#9cbe30", "1": "#a0cbe8", "2": "#bfbfbf"}

WORKSHEET = "Line Chart"
DASHBOARD = "2022_01_11_WW02_YoY_By_Week"


def _week_start(day: dt.date) -> dt.date:
    """Monday of the week containing ``day`` (the datasource's start-of-week)."""
    return day - dt.timedelta(days=day.weekday())


def _plot_week(week_start: dt.date) -> dt.date:
    """The 2021 week the author plots a week start at.

    MAKEDATE keeps the month and day but not the weekday, so the three years
    land on different weekdays; truncating back to Monday puts them on one
    shared x position.
    """
    rebased = dt.date(2021, week_start.month, week_start.day)
    return _week_start(rebased)


def _hyper_series():
    """Return the weekly series straight from the extract.

    Three views of the same aggregate are needed:

    * ``groups``: week start -> {year-group offset: sales}
    * ``positions``: plotted 2021 week -> {year-group offset: sales}, which is
      what the continuous axis actually carries
    * ``week_end`` / ``all_weeks``: the unfiltered weeks, so the verifier can
      show what the Core Data to Include filter removes
    """
    from tableauhyperapi import Connection, HyperProcess, Telemetry

    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as connection:
            rows = connection.execute_list_query(
                'SELECT "Sales", "Order Date" FROM "Extract"."Extract"'
            )

    sales: dict[dt.date, float] = defaultdict(float)
    week_end: dict[dt.date, dt.date] = {}
    all_weeks: set[dt.date] = set()
    for value, raw in rows:
        day = dt.date(raw.year, raw.month, raw.day)
        start = _week_start(day)
        end = start + dt.timedelta(days=6)
        week_end[start] = end
        all_weeks.add(start)
        # acceptance: complete-weeks-only — the author's filter, restated.
        if end < TODAY and start.year >= TODAY.year - 2:
            sales[start] += float(value)

    groups: dict[dt.date, dict[int, float]] = defaultdict(dict)
    positions: dict[dt.date, dict[int, float]] = defaultdict(dict)
    for start, value in sales.items():
        offset = TODAY.year - start.year
        groups[start][offset] = value
        # Two weeks of the same year can only collide if the calendar shifts by
        # more than a week, so summing is the safe general form.
        position = _plot_week(start)
        positions[position][offset] = positions[position].get(offset, 0.0) + value
    return groups, positions, week_end, all_weeks


def _by_offset(groups: dict[dt.date, dict[int, float]]) -> dict[int, dict[dt.date, float]]:
    out: dict[int, dict[dt.date, float]] = defaultdict(dict)
    for start, series in groups.items():
        for offset, value in series.items():
            out[offset][start] = value
    return out


def _twb() -> str:
    return zipfile.ZipFile(OUTPUT).read("replicated-workbook.twb").decode("utf-8")


def _formula(xml: str, internal_name: str) -> str:
    match = re.search(
        r'<column [^>]*name="' + re.escape(internal_name) + r'"[^>]*>.*?</column>',
        xml,
        re.S,
    )
    if match is None:
        raise AssertionError(f"Missing calculated field {internal_name}")
    formula = re.search(r'formula="([^"]*)"', match.group(0))
    if formula is None:
        raise AssertionError(f"{internal_name} has no formula")
    return (
        formula.group(1)
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&#10;", "\n")
        .replace("&amp;", "&")
    )


def _check_structure(xml: str) -> None:
    """Assert the artifact carries the behavior described in analysis.md."""
    # acceptance: week-buckets
    if 'start-of-week="monday"' not in xml:
        raise AssertionError("Datasource does not start weeks on Monday")
    if "DATETRUNC('week'" not in _formula(xml, "[Calculation_WeekStart]"):
        raise AssertionError("Order Date Week Start is not a week truncation")
    if "DATEADD('day', 6" not in _formula(xml, "[Calculation_WeekEnd]"):
        raise AssertionError("Order Date Week End is not week start + 6 days")

    # acceptance: complete-weeks-only
    core = _formula(xml, "[Calculation_CoreData]")
    if "[Calculation_WeekEnd] < [Parameters].[Parameter 1]" not in core:
        raise AssertionError(f"Core Data to Include lost its completeness test: {core}")
    if "YEAR([Calculation_WeekStart]) >= YEAR([Parameters].[Parameter 1]) - 2" not in core:
        raise AssertionError("Core Data to Include lost its three-year window")
    if 'member="true"' not in xml:
        raise AssertionError("The Core Data to Include = true filter is missing")

    # acceptance: year-group-offset
    year_group = _formula(xml, "[Calculation_YearGroup]")
    if "YEAR([Parameters].[Parameter 1]) - YEAR([Calculation_WeekStart])" not in year_group:
        raise AssertionError(f"Year Group is not a signed offset from Today: {year_group}")

    # acceptance: baseline-date-axis
    date_to_plot = _formula(xml, "[Calculation_DateToPlot]")
    if "MAKEDATE(2021" not in date_to_plot or "DATETRUNC('week'" not in date_to_plot:
        raise AssertionError(f"Date to Plot is not a rebased week start: {date_to_plot}")
    if not re.search(r"<cols>\[[^\]]+\]\.\[none:Calculation_DateToPlot:qk\]</cols>", xml):
        raise AssertionError("Date to Plot is not bound as a continuous exact-date axis")
    if not re.search(r"<rows>\[[^\]]+\]\.\[sum:Sales:qk\]</rows>", xml):
        raise AssertionError("Sales is not aggregated on Rows")
    if "none:Calculation_YearGroup:ok" not in xml:
        raise AssertionError("Year Group is not the colour encoding")

    # acceptance: yoy-percent-change — the baked percentage difference must be
    # addressed along Year Group, otherwise LOOKUP reads the previous *week*.
    diff = _formula(xml, "[Calculation_SalesDiff]")
    if "LOOKUP(ZN(SUM([Sales])), 1)" not in diff:
        raise AssertionError(f"% Sales Diff is not a percentage difference: {diff}")
    addressing = re.search(
        r'<column-instance[^>]*column="\[Calculation_SalesDiffPos\]"[^>]*>(.*?)</column-instance>',
        xml,
        re.S,
    )
    if addressing is None:
        raise AssertionError("% Sales Diff +ve is not on the tooltip shelf")
    if 'ordering-type="Field"' not in addressing.group(1):
        raise AssertionError("The percentage difference addressing is not field-based")
    if addressing.group(1).count("Calculation_YearGroup") < 2:
        raise AssertionError("The percentage difference is not addressed by Year Group")

    # acceptance: author-colour-key
    palette = re.search(
        r'<encoding attr="color" field="\[none:Calculation_YearGroup:ok\]"[^>]*>(.*?)</encoding>',
        xml,
        re.S,
    )
    if palette is None:
        raise AssertionError("Year Group has no datasource colour palette")
    mapped = {
        bucket: colour
        for colour, bucket in re.findall(
            r'<map to="(#[0-9a-f]{6})"><bucket>(-?\d+)</bucket></map>', palette.group(1)
        )
    }
    if mapped != COLOURS:
        raise AssertionError(f"Year Group palette is {mapped}, expected {COLOURS}")
    for colour in COLOURS.values():
        if f'fontcolor="{colour}"' not in xml:
            raise AssertionError(f"The title colour key is missing {colour}")

    # acceptance: tooltip-yoy-label
    tooltip = re.search(r"<customized-tooltip>(.*?)</customized-tooltip>", xml, re.S)
    if tooltip is None:
        raise AssertionError("The worksheet has no custom tooltip")
    for fragment, label in (
        ("attr:Calculation_WeekEnd:ok", "week ending"),
        ("attr:Calculation_PeriodLabel:nk", "period label"),
        ("sum:Sales:qk", "sales"),
        ("usr:Calculation_YoYLabel:nk", "YoY% label"),
        ("usr:Calculation_SalesDiffPos:qk", "positive YoY%"),
        ("usr:Calculation_SalesDiffNeg:qk", "negative YoY%"),
    ):
        if fragment not in tooltip.group(1):
            raise AssertionError(f"The tooltip is missing the {label}")
    if "ISNULL" not in _formula(xml, "[Calculation_YoYLabel]"):
        raise AssertionError("The YoY% label is not suppressed when there is no value")
    if 'fontcolor="#9cbe30"' not in tooltip.group(1) or 'fontcolor="#e15759"' not in tooltip.group(1):
        raise AssertionError("The tooltip percentage is not split into positive/negative colours")


def _check_numbers() -> None:
    """Assert the weekly series the workbook must draw, from the extract only."""
    groups, positions, week_end, all_weeks = _hyper_series()
    by_offset = _by_offset(groups)

    # acceptance: week-buckets
    for start in groups:
        if start.weekday() != 0:
            raise AssertionError(f"{start} is not a Monday")
    firsts = {offset: min(series) for offset, series in by_offset.items()}
    lasts = {offset: max(series) for offset, series in by_offset.items()}
    expected_firsts = {2: dt.date(2019, 1, 7), 1: dt.date(2020, 1, 6), 0: dt.date(2021, 1, 4)}
    expected_lasts = {2: dt.date(2019, 12, 30), 1: dt.date(2020, 12, 28), 0: dt.date(2021, 11, 22)}
    if firsts != expected_firsts or lasts != expected_lasts:
        raise AssertionError(
            f"Week range is {firsts}..{lasts}, expected {expected_firsts}..{expected_lasts}"
        )

    # acceptance: complete-weeks-only — no plotted week may run into "today".
    # The extract itself stops on 2021-11-28, so the author's filter is a guard
    # rather than a data change here; both facts are asserted so a changed
    # dataset cannot silently start plotting a partial week.
    for start in groups:
        if week_end[start] >= TODAY:
            raise AssertionError(f"Plotted week {start} runs into {TODAY}")
    if max(all_weeks) != dt.date(2021, 11, 22):
        raise AssertionError(
            f"Extract now contains weeks after 2021-11-22 ({max(all_weeks)}); "
            "the incomplete-week guard is no longer a no-op"
        )
    if set(groups) != all_weeks:
        raise AssertionError("The filter dropped weeks it should have kept")

    # acceptance: baseline-date-axis — every plotted week lands on a Monday and
    # the three years share x positions.
    for position in positions:
        if position.weekday() != 0:
            raise AssertionError(f"Plotted position {position} is not a Monday")
    if _plot_week(dt.date(2019, 1, 7)) != _plot_week(dt.date(2021, 1, 4)):
        raise AssertionError("The 2019 and 2021 first weeks do not share an x position")
    if max(len(offsets) for offsets in positions.values()) > 3:
        raise AssertionError("An axis position carries more than three year groups")
    # Every current-year week must share its position with the previous year,
    # otherwise there is nothing to compare against. The older years run five
    # weeks further, so those trailing positions hold only two groups.
    with_three = sum(1 for offsets in positions.values() if len(offsets) == 3)
    if with_three != len(by_offset[0]):
        raise AssertionError(
            f"{with_three} positions carry three year groups, expected "
            f"{len(by_offset[0])} (one per current-year week)"
        )

    # acceptance: yoy-percent-change — exactly one year-over-year value per
    # current-year week, computed against the previous year at the same
    # position, and none for the oldest year.
    compared = 0
    for position, series in sorted(positions.items()):
        if 0 in series and 1 in series:
            if series[0] == series[1]:
                raise AssertionError(f"{position}: current and previous years are identical")
            if series[1] <= 0:
                raise AssertionError(f"{position}: previous year is not positive")
            change = (series[0] - series[1]) / abs(series[1])
            if change < -1:
                raise AssertionError(f"{position}: percentage difference is out of range")
            compared += 1
        elif 0 in series:
            raise AssertionError(f"{position}: current year has nothing to compare against")
        elif 2 in series and 1 not in series:
            raise AssertionError(f"{position}: the oldest year is missing its prior year")
    if compared != len(by_offset[0]):
        raise AssertionError("Not every current-year week has a year-over-year value")
    if compared < 40:
        raise AssertionError(f"Only {compared} weeks have a year-over-year value")

    # acceptance: year-group-offset — the 2019/2020 boundary week proves Year
    # Group is an offset, not the calendar year: it stays in one group.
    straddle = dt.date(2019, 12, 30)
    if set(groups[straddle]) != {2}:
        raise AssertionError("The week of 2019-12-30 was split across year groups")
    # The calendar-year split really would have produced two groups: the week
    # runs from 30 Dec 2019 into 5 Jan 2020.
    if (straddle + dt.timedelta(days=6)).year == straddle.year:
        raise AssertionError("The 2019-12-30 week does not cross a year boundary")

    print(
        f"weeks={len(groups)} positions={len(positions)} yoy_weeks={compared} "
        f"first={firsts[0]} last={lasts[0]} straddle={straddle}"
    )


def check_cloud_marks() -> None:
    """Compare every exported mark after normalizing dates and group aliases."""
    # acceptance: cloud-mark-parity
    results = []
    for role in ("author", "replica"):
        path = HERE / "outputs" / f"cloud-{role}-dashboard.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        marks = {}
        for row in rows:
            date = (
                dt.datetime.strptime(row["Week of Date to Plot"], "%B %d, %Y")
                if role == "author"
                else dt.datetime.strptime(row["Date to Plot"], "%m/%d/%Y")
            ).date()
            label = row["Year Group"] if role == "author" else row["Period Label"]
            key = (date, label)
            if key in marks:
                raise AssertionError(f"Duplicate Cloud mark: {key}")
            marks[key] = tuple(
                row[field] for field in (
                    "Sales", "Order Date Week End", "% Sales Diff +ve",
                    "% Sales Diff -ve", "TOOLTIP: Label YoY%"
                )
            )
        if len(marks) != 151:
            raise AssertionError(f"{role}: expected 151 exported marks")
        results.append(marks)
    if results[0] != results[1]:
        raise AssertionError("Cloud weekly sales, week end or YoY display differs")
    print("Cloud parity: all 151 weekly marks match")


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")
    xml = _twb()

    editor = TWBEditor.open_existing(OUTPUT)
    if WORKSHEET not in set(editor.list_worksheets()):
        raise AssertionError(f"Missing worksheet: {WORKSHEET}")
    if DASHBOARD not in {item["name"] for item in editor.list_dashboards()}:
        raise AssertionError(f"Missing dashboard: {DASHBOARD}")

    _check_structure(xml)
    _check_numbers()
    check_cloud_marks()


if __name__ == "__main__":
    verify()
    print("PASS")
