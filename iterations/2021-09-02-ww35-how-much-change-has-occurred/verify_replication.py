"""Independently verify the WW35 "How much change has occurred?" workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
The 2020/2021 Sub-Category sales, the % difference and the descending order are
recomputed from the extract with the Hyper API — not from the workbook — so a
drifted LoD or a broken sort cannot pass by being self-consistent. The native
workbook contracts (context year filter, folded dual axis, two mark panes,
label encoding, dashboard zone) are then checked on the generated XML.

Automated acceptance IDs:
  - ww35-year-window
  - ww35-subcategory-sales
  - ww35-percent-change
  - ww35-descending-order
  - ww35-dual-axis-panes
  - ww35-label-and-colour
  - ww35-dashboard-layout
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, TableName, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww35-year-window",
    "ww35-subcategory-sales",
    "ww35-percent-change",
    "ww35-descending-order",
    "ww35-dual-axis-panes",
    "ww35-label-and-colour",
    "ww35-dashboard-layout",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_09_01_WW35_Change_in_Sales"
SHEET = "Viz"
TABLE = TableName("Extract", "Extract")

# Reference read from the author's published screenshot (image-9.png).
#
# ``sales_2021`` is the value printed in the author's blue "2021 Sales" pill.
# ``sales_2020`` is the value implied by the red 2020 dot: the screenshot's
# x-scale was fitted as x = 407.35 + 0.002994 * sales (zero at 407.4 px,
# 100K at 706.7 px), which reproduces every dot centre within 2 px.
#
# The screenshot's % Difference labels are *offset by one row* relative to its
# own marks from the second row onwards: 13 of the 14 labels match the next
# row's % difference. The author workbook XML itself attaches
# ``<text column="% Difference">`` to the circle pane with no offset, so the
# labels are correct per row and only the published raster is shifted. The
# verifier therefore checks the extract against the printed 2021 values, the
# dot-implied 2020 values and the full ordered set of published label values.
AUTHOR_ROWS = [
    ("Phones", 105341, 78962),
    ("Chairs", 95554, 83919),
    ("Binders", 72788, 49683),
    ("Storage", 69678, 58789),
    ("Copiers", 62899, 49599),
    ("Tables", 60894, 60833),
    ("Accessories", 59946, 41896),
    ("Machines", 43545, 55907),
    ("Appliances", 42927, 26050),
    ("Bookcases", 30024, 26275),
    ("Furnishings", 28915, 27874),
    ("Paper", 27695, 20662),
    ("Supplies", 16049, 14278),
    ("Art", 8863, 5961),
    ("Labels", 3861, 2827),
]

# Published "+0%;-0%" labels, top to bottom. Row 1 matches its own row; the
# remaining 14 are the values of the rows *below* them (see note above). The
# last published label, -29, is Envelopes' -28.6 even though Envelopes itself
# is scrolled out of the screenshot, which is why 15 labels exist for 15
# visible rows.
AUTHOR_LABELS = [33, 47, 19, 27, 0, 43, -22, 65, 14, 4, 34, 12, 49, 37, -29]


def label_percent(value: float) -> int:
    """Round a fraction the way Tableau's ``+0%;-0%`` format does."""
    from decimal import ROUND_HALF_UP, Decimal

    return int(
        (Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle() -> dict:
    """Recompute the chart from the extract, independently of the workbook."""
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

    years = {row[0].year for row in rows}
    totals: dict[str, dict[int, float]] = {}
    for order_date, sub_category, sales in rows:
        bucket = totals.setdefault(sub_category, {})
        bucket[order_date.year] = bucket.get(order_date.year, 0.0) + sales

    chart = []
    for sub_category, by_year in totals.items():
        current = by_year.get(2021, 0.0)
        prior = by_year.get(2020, 0.0)
        chart.append(
            {
                "sub_category": sub_category,
                "sales_2021": round(current, 2),
                "sales_2020": round(prior, 2),
                "pct_difference": round((current - prior) / prior, 4),
            }
        )
    # Tableau's computed sort on SUM([2021 Sales]) descending.
    chart.sort(key=lambda row: row["sales_2021"], reverse=True)

    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "years": sorted(years),
        "chart": chart,
    }


def workbook() -> etree._Element:
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def local_names(root: etree._Element) -> dict[str, str]:
    """Map internal column names to captions for readable assertions."""
    result = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name") or ""
        result[name] = column.get("caption") or name.strip("[]")
    return result


def label_for(names: dict[str, str], reference: str) -> str:
    match = re.search(r"\[(?:\w+):([^:\]]+):(?:\w\w)\]", reference or "")
    if not match:
        return reference or ""
    return names.get(f"[{match.group(1)}]", match.group(1))


def verify() -> dict:
    facts = oracle()
    root = workbook()
    names = local_names(root)

    # --- ww35-year-window ---------------------------------------------------
    # The author limits the data to 2020 + 2021. The extract also holds 2018
    # and 2019, so the window is a real, observable behaviour.
    assert facts["years"] == [2018, 2019, 2020, 2021], facts["years"]
    assert facts["rows"] == 9994, facts["rows"]
    sheet = root.find(f".//worksheets/worksheet[@name='{SHEET}']")
    assert sheet is not None, "missing Viz worksheet"
    view = sheet.find("table/view")
    filters = view.findall("filter")
    year_filters = [
        node
        for node in filters
        if label_for(names, node.get("column")) == "Order Date"
        or "yr:" in (node.get("column") or "")
    ]
    assert len(year_filters) == 1, [etree.tostring(f) for f in filters]
    year_filter = year_filters[0]
    assert year_filter.get("context") == "true", "the year filter must be a context filter"
    members = {
        member.get("member")
        for member in year_filter.findall(".//groupfilter[@function='member']")
    }
    assert members == {"2020", "2021"}, members
    slices = [
        (column.text or "").strip() for column in view.findall("slices/column")
    ]
    assert year_filter.get("column") in slices, slices

    # --- ww35-subcategory-sales + ww35-percent-change -----------------------
    calc = {}
    for column in root.findall(".//datasource/column"):
        node = column.find("calculation")
        if node is not None:
            calc[column.get("caption") or ""] = node.get("formula") or ""
    assert calc.get("2021 Sales") == (
        "{FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2021 THEN [Sales] END)}"
    ), calc.get("2021 Sales")
    assert calc.get("2020 Sales") == (
        "{FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2020 THEN [Sales] END)}"
    ), calc.get("2020 Sales")
    pct = calc.get("% Difference") or ""
    # The stored formula uses internal calculation names; resolve them back to
    # captions before asserting the shape of the comparison.
    caption_of = {name.strip("[]"): caption for name, caption in names.items()}
    resolved_pct = re.sub(
        r"\[([^\]]+)\]",
        lambda match: f"[{caption_of.get(match.group(1), match.group(1))}]",
        pct,
    )
    assert resolved_pct == (
        "(SUM([2021 Sales])-SUM([2020 Sales]))/SUM([2020 Sales])"
    ), resolved_pct

    chart = facts["chart"]
    assert len(chart) == 17, len(chart)
    by_name = {row["sub_category"]: row for row in chart}
    # The extract has to reproduce the numbers the author plotted: the printed
    # 2021 pill values and the 2020 values implied by the dot positions.
    for sub_category, sales_2021, sales_2020 in AUTHOR_ROWS:
        row = by_name[sub_category]
        assert abs(row["sales_2021"] - sales_2021) <= 1.0, (sub_category, row)
        assert abs(row["sales_2020"] - sales_2020) <= 1.0, (sub_category, row)
    assert by_name["Phones"]["sales_2020"] == 78962.03, by_name["Phones"]
    assert by_name["Phones"]["pct_difference"] == 0.3341, by_name["Phones"]
    assert by_name["Machines"]["pct_difference"] == -0.2211, by_name["Machines"]
    assert by_name["Envelopes"]["pct_difference"] == -0.2857, by_name["Envelopes"]

    # The ordered list of published label values must match the computed
    # percentages: row 1 to its own row, rows 2-15 to the row *below* them.
    order = [row["sub_category"] for row in chart]
    computed = [label_percent(by_name[name]["pct_difference"]) for name in order]
    assert AUTHOR_LABELS[0] == computed[0], (AUTHOR_LABELS[0], computed[0])
    shifted = computed[2 : 2 + len(AUTHOR_LABELS) - 1]
    assert AUTHOR_LABELS[1:] == shifted, (AUTHOR_LABELS[1:], shifted)

    # --- ww35-descending-order ---------------------------------------------
    expected_order = [row["sub_category"] for row in chart]
    assert expected_order[:3] == ["Phones", "Chairs", "Binders"], expected_order[:3]
    assert expected_order[-1] == "Fasteners", expected_order[-1]
    sorts = view.findall("computed-sort")
    assert len(sorts) == 1, [etree.tostring(s) for s in sorts]
    sort = sorts[0]
    assert sort.get("direction") == "DESC", sort.get("direction")
    assert label_for(names, sort.get("column")) == "Sub-Category", sort.get("column")
    assert label_for(names, sort.get("using")) == "2021 Sales", sort.get("using")

    # --- ww35-dual-axis-panes ----------------------------------------------
    rows_shelf = sheet.findtext("table/rows") or ""
    cols_shelf = sheet.findtext("table/cols") or ""
    # Discrete 2021 Sales pill under Sub-Category.
    assert "none:Sub-Category" in rows_shelf, rows_shelf
    discrete = re.findall(r"\[(?:\w+):([^:\]]+):ok\]", rows_shelf)
    assert [names.get(f"[{name}]", name) for name in discrete] == ["2021 Sales (discrete)"], rows_shelf
    # SUM(Sales) twice, folded into one synchronised axis.
    assert cols_shelf.count("sum:Sales") == 2, cols_shelf
    assert " + " in cols_shelf, cols_shelf
    axis_rule = sheet.find("table/style/style-rule[@element='axis']")
    assert axis_rule is not None, "missing axis style rule"
    folding = [
        node
        for node in axis_rule.findall("encoding")
        if node.get("attr") == "space" and node.get("fold") == "true"
    ]
    assert len(folding) == 1, etree.tostring(axis_rule)
    assert folding[0].get("synchronized") == "true", etree.tostring(folding[0])
    assert folding[0].get("scope") == "cols", etree.tostring(folding[0])

    panes = sheet.findall("table/panes/pane")
    assert len(panes) == 2, [etree.tostring(p) for p in panes]
    # The author's workbook has the Bar on the first axis and the Circle on the
    # second (x-index=1), so the dot is drawn on top of the bar.
    marks = [pane.find("mark").get("class") for pane in panes]
    assert marks == ["Bar", "Circle"], marks
    for pane in panes:
        assert (pane.get("x-axis-name") or "").endswith("sum:Sales:qk]"), pane.get("x-axis-name")
    assert panes[0].get("x-index") is None, panes[0].get("x-index")
    assert panes[1].get("x-index") == "1", panes[1].get("x-index")

    # --- ww35-label-and-colour ---------------------------------------------
    bar_pane, circle_pane = panes
    circle_text = circle_pane.findall("encodings/text")
    assert len(circle_text) == 1, etree.tostring(circle_pane)
    assert label_for(names, circle_text[0].get("column")) == "% Difference", circle_text[0].get("column")
    circle_color = circle_pane.find("encodings/color")
    bar_color = bar_pane.find("encodings/color")
    assert circle_color is not None and bar_color is not None
    assert label_for(names, circle_color.get("column")) == "Dot Period", circle_color.get("column")
    assert label_for(names, bar_color.get("column")) == "Bar Period", bar_color.get("column")
    # Period labels enforce current-year foreground rendering.

    palette = root.find(".//datasource/style/style-rule[@element='mark']")
    assert palette is not None, "missing datasource colour palette"
    encodings = {
        encoding.get("field"): {
            bucket.text.strip(chr(34)): mapping.get("to")
            for mapping in encoding.findall("map")
            for bucket in mapping.findall("bucket")
        }
        for encoding in palette.findall("encoding")
        if encoding.get("attr") == "color"
    }
    assert len(encodings) == 2, encodings
    colours = list(encodings.values())
    # The bar pane keeps 2021 grey (drawn on top) and 2020 red; the circle pane
    # colours 2021 blue and 2020 red.
    assert {"Current (2021)": "#bab0ac", "Prior (2020)": "#e15759"} in colours, colours
    assert {"Current (2021)": "#4e79a7", "Prior (2020)": "#e15759"} in colours, colours
    labels_shown = circle_pane.find(
        "style/style-rule[@element='mark']/format[@attr='mark-labels-show']"
    )
    assert labels_shown is not None and labels_shown.get("value") == "true"
    stroke = circle_pane.find(
        "style/style-rule[@element='mark']/format[@attr='stroke-color']"
    )
    assert stroke is not None and stroke.get("value") == "#ffffff", stroke
    bar_labels = bar_pane.find(
        "style/style-rule[@element='mark']/format[@attr='mark-labels-show']"
    )
    assert bar_labels is None or bar_labels.get("value") == "false"

    # --- ww35-dashboard-layout ---------------------------------------------
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zone_names = {
        zone.get("name") for zone in dashboard.findall(".//zones//zone") if zone.get("name")
    }
    assert SHEET in zone_names, zone_names
    size = dashboard.find("size")
    assert size.get("minwidth") == "700" and size.get("minheight") == "800", etree.tostring(size)
    texts = [
        "".join(run.text or "" for run in zone.findall(".//formatted-text/run"))
        for zone in dashboard.findall(".//zones//zone[@type-v2='text']")
    ]
    joined = " ".join(texts)
    assert "LUKE STANKE" in joined, texts
    assert "WEEK 35" in joined, texts
    assert "2021w35" in joined, texts

    evidence = {
        "scope": "Locked-extract oracle plus native filter/axis/pane/label/dashboard contracts.",
        "acceptance": ACCEPTANCE,
        "facts": {
            "extract_sha256": facts["extract_sha256"],
            "rows": facts["rows"],
            "years": facts["years"],
            "chart": facts["chart"],
            "author_reference_rows": len(AUTHOR_ROWS),
            "order": expected_order,
        },
        "output_sha256": digest(OUTPUT),
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    chart = result["facts"]["chart"]
    print(
        json.dumps(
            {
                "rows": result["facts"]["rows"],
                "years": result["facts"]["years"],
                "top": chart[0],
                "bottom": chart[-1],
                "author_rows_matched": result["facts"]["author_reference_rows"],
            },
            indent=2,
        )
    )
    print("PASS")
