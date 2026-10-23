"""Independently verify the WW30 "Let's go streaking!" workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
The streak chain is recomputed in Python from the extract so the workbook
contracts are checked against a real oracle, not against the builder's own
formulas.

Automated acceptance IDs:
  - ww30-month-bucket
  - ww30-streak-chain
  - ww30-longest-streak
  - ww30-peak-sales
  - ww30-sort-order
  - ww30-viz-shape
  - ww30-legend
  - ww30-data-sheet
"""

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww30-month-bucket",
    "ww30-streak-chain",
    "ww30-longest-streak",
    "ww30-peak-sales",
    "ww30-sort-order",
    "ww30-viz-shape",
    "ww30-legend",
    "ww30-data-sheet",
]
OUTPUT = HERE / "outputs/replicated-workbook.twbx"
DASHBOARD = "2021_07_28_WW30_LetsGoStreaking"
TABLE = 'Extract"."Extract'

# The article's own screenshots: the four leading Sub-Categories and their
# Longest Streak values (image-58.png / image-72.png in the post).
ARTICLE_HEAD = [("Appliances", 5), ("Bookcases", 5), ("Phones", 5), ("Art", 4)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle() -> dict:
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT DATE_TRUNC(\'month\', "Order Date"), "Sub-Category", SUM("Sales") '
            f'FROM "{TABLE}" GROUP BY 1, 2 ORDER BY 2, 1'
        )
    series: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for month, sub_category, sales in rows:
        series[sub_category].append((f"{month.year:04d}-{month.month:02d}", float(sales)))

    # Full calendar domain: absent monthly SUM remains null; ZN in Sales Diff
    # turns it into zero and breaks a streak. Recompute without builder helpers.
    all_months=sorted({f"{month.year:04d}-{month.month:02d}" for month,_,_ in rows})
    series={g:[(m,dict(points).get(m)) for m in all_months] for g,points in series.items()}
    result = {}
    for sub_category, points in series.items():
        sales = [value for _, value in points]
        months = [month for month, _ in points]
        # Reproduce the author's table calculation chain row by row.
        positive: list[int] = []
        streaks: list[int | None] = []
        for index, value in enumerate(sales):
            diff = None if index == 0 else (value or 0) - (sales[index - 1] or 0)
            is_positive = 1 if (diff is not None and diff > 0) else 0
            matches_previous = index > 0 and positive[-1] == is_positive
            if (not matches_previous) and is_positive == 1:
                streak = 1
            elif is_positive == 1:
                streak = is_positive + (streaks[-1] or 0)
            else:
                streak = None
            positive.append(is_positive)
            streaks.append(streak)
        longest = max((streak or 0) for streak in streaks)
        peaks = [
            {"month": months[index], "sales": round(sales[index], 4)}
            for index, streak in enumerate(streaks)
            if (streak or 0) == longest and longest > 0
        ]
        result[sub_category] = {
            "months": len(months),
            "longest_streak": longest,
            "peaks": peaks,
        }

    order = sorted(result, key=lambda name: (-result[name]["longest_streak"], name))
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "sub_categories": result,
        "sorted": order,
    }


def workbook() -> etree._Element:
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root: etree._Element) -> dict[str, str]:
    """Map every calculated field caption to a caption-based formula."""

    raw = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is not None:
            raw[column.get("name")] = (column.get("caption"), calc.get("formula") or "")
    names = {name.strip("[]"): name for name in raw}

    def resolve(formula: str) -> str:
        def replace(match):
            token = match.group(1)
            if token in names and names[token] in raw:
                caption = raw[names[token]][0]
                return f"[{caption}]" if caption else match.group(0)
            return match.group(0)

        return re.sub(r"\[([^\]]+)\]", replace, formula)

    return {
        caption: resolve(formula).replace("\r\n", "\n").replace("\r", "\n")
        for caption, formula in raw.values()
        if caption
    }


def norm(text: str) -> str:
    """Collapse all whitespace so formulas compare on structure, not layout."""
    return re.sub(r"\s+", "", text)


def worksheet(root: etree._Element, name: str) -> etree._Element:
    for element in root.findall(".//worksheets/worksheet"):
        if element.get("name") == name:
            return element
    raise AssertionError(f"missing worksheet {name}")


def pane_mark(pane: etree._Element) -> str | None:
    mark = pane.find("mark")
    return mark.get("class") if mark is not None else None


def verify() -> None:
    facts = oracle()
    root = workbook()
    calc = formulas(root)
    chart = worksheet(root, "Chart")
    legend = worksheet(root, "Legend")
    data_sheet = worksheet(root, "Data")

    # --- ww30-month-bucket ---------------------------------------------------
    assert "Order Date Month" in calc, sorted(calc)
    assert norm(calc["Order Date Month"]) == norm("DATE(DATETRUNC('month',[Order Date]))"), calc[
        "Order Date Month"
    ]
    cols = (chart.findtext("table/cols") or "").strip()
    # The month axis is the native Month-Trunc instance of the raw date, which
    # is exactly what the author's workbook uses ([tmn:Order Date:qk]).
    assert "[tmn:Order Date:qk]" in cols, cols
    # A continuous month-truncated date keeps 48 distinct points on the axis,
    # unlike the discrete MONTH() part which would bucket across years.
    assert ":qk]" in cols, cols

    # --- ww30-streak-chain ---------------------------------------------------
    expected_chain = {
        "Sales Diff": "ZN(SUM([Sales]))-LOOKUP(ZN(SUM([Sales])),-1)",
        "Diff Is +ve": "IF[Sales Diff]>0THEN1ELSE0END",
        "Match Prev Value": "LOOKUP([Diff Is +ve],-1)=[Diff Is +ve]",
        "Increase Streak": (
            "IF(NOT([Match Prev Value]))AND([Diff Is +ve]=1)THEN1"
            "ELSEIF[Diff Is +ve]=1THEN([Diff Is +ve]+PREVIOUS_VALUE([Diff Is +ve]))"
            "END"
        ),
    }
    for caption, expected in expected_chain.items():
        assert caption in calc, f"missing calculated field {caption}"
        actual = calc[caption].replace(" ", "").replace("\n", "")
        assert actual == norm(expected), (caption, actual)
        assert "PREVIOUS_VALUE" in calc["Increase Streak"] or caption != "Increase Streak"

    # Every table calculation must be addressed by the month bucket only, which
    # is what restarts the streak for each Sub-Category row.
    for column in root.findall(".//datasource/column"):
        table_calc = column.find("calculation/table-calc")
        if table_calc is None:
            continue
        if column.get("caption") in {"Sales Diff", "Diff Is +ve", "Match Prev Value",
                                     "Increase Streak", "Longest Streak",
                                     "Sales of Month with Longest Streak", "Sort"}:
            assert table_calc.get("ordering-type") == "Field", column.get("caption")
            ordering = table_calc.get("ordering-field") or ""
            # Field-level metadata names the month bucket; chart-level
            # overrides resolve it to the exact-date column instance.
            assert "Calculation_" in ordering or ordering == "[Order Date]", (
                column.get("caption"),
                ordering,
            )

    for sheet in ("Chart", "Data"):
        for tc in worksheet(root, sheet).findall(".//column-instance/table-calc"):
            assert "[tmn:Order Date:qk]" in tc.get("ordering-field", "") or tc.get("ordering-field") == "[Order Date]", etree.tostring(tc)

    # --- ww30-longest-streak -------------------------------------------------
    assert norm("WINDOW_MAX([Increase Streak])") in norm(calc.get("Longest Streak", "")), calc.get(
        "Longest Streak"
    )
    oracle_longest = {name: value["longest_streak"] for name, value in facts["sub_categories"].items()}
    assert oracle_longest["Appliances"] == 5, oracle_longest["Appliances"]
    assert oracle_longest["Binders"] == 2, oracle_longest["Binders"]
    assert oracle_longest["Storage"] == 2, oracle_longest["Storage"]
    # Longest Streak must be colour-encoded and also carried as a discrete pill.
    colour_fields = [
        encoding.get("field", "")
        for encoding in chart.findall("table/style/style-rule[@element='mark']/encoding")
        if encoding.get("attr") == "color"
    ]
    assert colour_fields, "Longest Streak is not on the colour shelf"
    rows = chart.findtext("table/rows") or ""
    assert ":ok]" in rows, rows
    # The colour ramp is the author's five stepped greens pinned to 0..5.
    colour = chart.find("table/style/style-rule[@element='mark']/encoding[@attr='color']")
    assert colour.get("min") == "0" and colour.get("max") == "5", etree.tostring(colour)[:200]
    assert colour.get("num-steps") == "5", etree.tostring(colour)[:200]
    swatches = [node.text for node in colour.findall("color-palette/color")]
    assert len(swatches) == 5, swatches

    # --- ww30-peak-sales -----------------------------------------------------
    assert (
        norm(calc.get("Sales of Month with Longest Streak", ""))
        == norm("IF [Longest Streak] = [Increase Streak] THEN SUM([Sales]) END")
    ), calc.get("Sales of Month with Longest Streak")
    # The article's own screenshots mark exactly these peak months.
    expected_peaks = {
        "Appliances": ["2017-11"],
        "Bookcases": ["2019-06"],
        "Phones": ["2019-09"],
        "Art": ["2019-06"],
    }
    for name, months in expected_peaks.items():
        assert [peak["month"] for peak in facts["sub_categories"][name]["peaks"]] == months, (
            name,
            facts["sub_categories"][name]["peaks"],
        )

    # --- ww30-sort-order -----------------------------------------------------
    assert norm(calc.get("Sort", "")) == norm("[Longest Streak]*-1"), calc.get("Sort")
    # A leading discrete negative-streak pill sorts ascending, hence longest first.
    # A computed sort over a table calculation is not valid at query-sort time.
    sort_column=chart.find('.//datasource-dependencies/column[@caption="Sort"]')
    sort_instance=chart.find('.//column-instance[@column="'+sort_column.get("name")+'"]')
    shelf=chart.findtext("table/rows")
    assert sort_instance.get("type")=="ordinal"
    assert shelf.index(sort_instance.get("name")) < shelf.index("Sub-Category")
    # Sorting by -Longest Streak puts the 5-streak rows first, matching the
    # article's leading four rows.
    for name, streak in ARTICLE_HEAD:
        assert facts["sub_categories"][name]["longest_streak"] == streak, (name, streak)
    assert facts["sorted"][0] in {"Appliances", "Bookcases", "Phones"}, facts["sorted"][:4]

    # --- ww30-viz-shape ------------------------------------------------------
    panes = chart.findall("table/panes/pane")
    assert len(panes) == 2, len(panes)
    marks = [pane_mark(pane) for pane in panes]
    assert marks == ["Line", "Circle"], marks
    for pane in panes:
        style = pane.find("style/style-rule[@element='mark']")
        values = {f.get("attr"): f.get("value") for f in style.findall("format")} if style is not None else {}
        assert values.get("line-interpolation") == "step", (pane.get("id"), values)
    line_style = panes[0].find("style/style-rule[@element='mark']")
    line_values = {f.get("attr"): f.get("value") for f in line_style.findall("format")}
    assert line_values.get("mark-color", "").lower() == "#898989", line_values
    axis_encoding = chart.find("table/style/style-rule[@element='axis']/encoding[@attr='space'][@fold='true']")
    assert axis_encoding is not None, "the two panes are not folded onto one axis"
    assert axis_encoding.get("fold") == "true" and axis_encoding.get("synchronized") == "true", (
        etree.tostring(axis_encoding)[:300]
    )
    assert [pane.get("y-axis-name") for pane in panes] != [None, None], panes

    # --- ww30-legend ---------------------------------------------------------
    assert (
        calc.get("Legend", "").replace(" ", "").replace("\n", "")
        == "CASE[Sub-Category]WHEN'Art'THEN0WHEN'Chairs'THEN1WHEN'Labels'THEN2"
        "WHEN'Paper'THEN3WHEN'Phones'THEN4ELSE5END"
    ), calc.get("Legend")
    legend_marks = [pane_mark(pane) for pane in legend.findall("table/panes/pane")]
    assert legend_marks and legend_marks[0] in {"Square", "Shape"}, legend_marks
    legend_colour = legend.find("table/style/style-rule[@element='mark']/encoding[@attr='color']")
    assert legend_colour is not None, "the Legend sheet has no colour ramp"
    assert legend_colour.get("min") == "0" and legend_colour.get("max") == "5", etree.tostring(
        legend_colour
    )[:200]

    # The audit sheet exposes every link of the chain as its own column, which
    # is what makes the streak numbers exportable and checkable row by row.
    data_cols = data_sheet.findtext("table/cols") or ""
    assert ":Measure Names]" in data_cols, data_cols
    data_rows = data_sheet.findtext("table/rows") or ""
    assert "[none:Sub-Category:nk]" in data_rows, data_rows
    assert "[tmn:Order Date:qk]" in data_rows, data_rows
    data_measures = {
        column.get("caption")
        for column in data_sheet.findall(".//datasource-dependencies/column")
    }
    for caption in ("Sales Diff", "Diff Is +ve", "Increase Streak", "Longest Streak",
                    "Sales of Month with Longest Streak"):
        assert caption in data_measures, (caption, sorted(m for m in data_measures if m))

    dashboards = [element for element in root.findall(".//dashboards/dashboard")]
    assert any(d.get("name") == DASHBOARD for d in dashboards), [d.get("name") for d in dashboards]
    dashboard = next(d for d in dashboards if d.get("name") == DASHBOARD)
    zone_sheets = {
        zone.get("name") for zone in dashboard.iter("zone") if zone.get("name")
    }
    assert {"Chart", "Legend"} <= zone_sheets, zone_sheets


if __name__ == "__main__":
    verify()
    print("PASS")
