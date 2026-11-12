"""Verify the WW52 one-measure table against the locked Hyper and the built XML.

Two independent layers, because either one alone can pass on a broken workbook:

* the built workbook is inspected for the native construction the challenge
  depends on (one measure, SIZE()-driven split, subtotal/grand-total labels,
  diverging palette, totals on top, 1000x600 dashboard);
* every exported value is recomputed from the extracted facts and compared
  with the captured Tableau exports, so a wrong table-calculation partition
  cannot pass on structure alone.
"""

from pathlib import Path
import csv
import re
import zipfile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
AUTHOR_CSV = HERE / "outputs" / "cloud-author-table.csv"
REPLICA_CSV = HERE / "outputs" / "cloud-replica-table.csv"
SHEET = "Table"
DASHBOARD = "2021 Week 52 - Single Table One Measure"
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
NS = "{http://www.tableau.com/xml/user}"


def workbook_root() -> etree._Element:
    with zipfile.ZipFile(OUTPUT) as archive:
        entry = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(entry))


def worksheet(root: etree._Element) -> etree._Element:
    for sheet in root.iterfind("worksheets/worksheet"):
        if sheet.get("name") == SHEET:
            return sheet
    raise AssertionError(f"Missing worksheet {SHEET}")


def strip_reference(text: str) -> str:
    """Drop the ``[datasource].`` prefix Tableau puts in front of a field."""
    match = re.fullmatch(r"\[[^\]]+\]\.(\[.*\])", text or "")
    return match.group(1) if match else (text or "")


def oracle() -> dict[tuple[str, str, str], float]:
    """Recompute every cell of the table from the extracted facts alone."""
    data = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(data)) as connection:
            facts = connection.execute_list_query(
                'SELECT "Category", "Sub-Category", EXTRACT(MONTH FROM "Order Date"), '
                'SUM("Sales") FROM "Extract"."Extract" '
                'GROUP BY "Category", "Sub-Category", EXTRACT(MONTH FROM "Order Date")'
            )
    detail: dict[tuple[str, str, int], float] = {}
    for category, sub_category, month, sales in facts:
        detail[(category, sub_category, int(month))] = float(sales)

    cells: dict[tuple[str, str, str], float] = {}
    for (category, sub_category, month), sales in detail.items():
        cells[(category, MONTHS[month - 1], sub_category)] = sales
    for month in range(1, 13):
        month_total = sum(v for (*_, m), v in detail.items() if m == month)
        for category in {c for (c, _, m) in detail if m == month}:
            category_total = sum(
                v for (c, _, m), v in detail.items() if c == category and m == month
            )
            cells[(category, MONTHS[month - 1], "All")] = -category_total / month_total
        cells[("All", MONTHS[month - 1], "All")] = month_total
    return cells


def exported_cells(path: Path) -> dict[tuple[str, str, str], float]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row["Category"], row["Month of Order Date"], row["Sub-Category"]):
            float(row["Custom Measure"].replace(",", ""))
            for row in csv.DictReader(handle)
        }


def assert_close(expected: dict, actual: dict, label: str) -> None:
    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))[:5]
        extra = sorted(set(actual) - set(expected))[:5]
        raise AssertionError(f"{label}: cell set differs (missing {missing}, extra {extra})")
    worst = 0.0
    worst_key = None
    for key, value in expected.items():
        got = actual[key]
        scale = max(abs(value), 1.0)
        error = abs(got - value) / scale
        if error > worst:
            worst, worst_key = error, key
    if worst > 1e-6:
        raise AssertionError(f"{label}: {worst_key} differs by {worst:.2e}")


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")
    TWBEditor.open_existing(OUTPUT)
    root = workbook_root()
    sheet = worksheet(root)
    table = sheet.find("table")

    # acceptance: single-measure-encoding
    pane = table.find("panes/pane")
    encodings = pane.find("encodings")
    text_columns = [e.get("column") for e in encodings.findall("text")]
    color_columns = [e.get("column") for e in encodings.findall("color")]
    if len(text_columns) != 1 or text_columns != color_columns:
        raise AssertionError(
            "Text and Color must both bind exactly the same single measure: "
            f"{text_columns} / {color_columns}"
        )
    if "Sales" in text_columns[0]:
        raise AssertionError("The raw Sales measure must not be on the Text shelf")
    if pane.find("mark").get("class") != "Square":
        raise AssertionError("Mark class must be Square")

    # acceptance: size-driven-subtotal-split
    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.iterfind(".//datasource/column")
        if column.find("calculation") is not None
    }
    if formulas.get("Size", "").strip() != "SIZE()":
        raise AssertionError(f"Size must be SIZE(): {formulas.get('Size')!r}")
    custom = formulas.get("Custom Measure", "")
    compact = custom.replace(" ", "")
    if "=1THENSUM([Sales])ELSE-SUM([Sales])/TOTAL(SUM([Sales]))END" not in compact:
        raise AssertionError(f"Custom Measure is not the SIZE() branch: {custom!r}")
    size_local = next(
        column.get("name")
        for column in root.iterfind(".//datasource/column")
        if column.get("caption") == "Size"
    )
    if size_local not in custom:
        raise AssertionError("Custom Measure must branch on the Size field")

    # Both table calculations are addressed by Category.
    encoded_instance = strip_reference(text_columns[0])
    instance = None
    for candidate in table.iterfind("view/datasource-dependencies/column-instance"):
        if candidate.get("name") == encoded_instance:
            instance = candidate
    if instance is None:
        raise AssertionError("The encoded measure has no column instance")
    addressing = instance.findall("table-calc")
    if len(addressing) != 2 or any(
        t.get("ordering-type") != "Field"
        or not re.fullmatch(
            r"\[[^\]]+\]\.\[(?:none:)?Category(?::nk)?\]",
            t.get("ordering-field", ""),
        )
        for t in addressing
    ):
        raise AssertionError(
            "Both table calculations must compute using Category: "
            f"{[t.attrib for t in addressing]}"
        )

    # acceptance: totals-above-groups
    rows = table.find("rows")
    if rows.get("total") != "true" or rows.get("onTop") != "true":
        raise AssertionError(f"Row totals must be shown above the groups: {rows.attrib}")
    if not (rows.text or "").count("/") == 1:
        raise AssertionError("Rows shelf must nest Category over Sub-Category")
    if not table.find("subtotals/column") is not None:
        raise AssertionError("Category subtotals are missing")
    if "none:Category" not in (table.find("subtotals/column").text or ""):
        raise AssertionError("Subtotals must be added for Category")
    if "mn:Order Date" not in (table.find("cols").text or ""):
        raise AssertionError("Columns shelf must use the month of Order Date")

    # acceptance: subtotal-labels-and-formats
    header = table.find("style/style-rule[@element='header']")
    labels = {
        (strip_reference(f.get("field")), f.get("data-class")): f.get("value")
        for f in header.findall("format")
        if f.get("attr") == "total-label"
    }
    if labels.get(("[none:Category:nk]", "total")) != "Total":
        raise AssertionError(f"Grand total label must be 'Total': {labels}")
    if labels.get(("[none:Sub-Category:nk]", "subtotal")) != "% of Total":
        raise AssertionError(f"Subtotal label must be '% of Total': {labels}")

    cell = table.find("style/style-rule[@element='cell']")
    formats = {
        f.get("data-class") or "default": f.get("value")
        for f in cell.findall("format")
        if f.get("attr") == "text-format"
    }
    if formats.get("default") != 'c"$"#,##0;-"$"#,##0':
        raise AssertionError(f"Detail cells must be whole-dollar currency: {formats}")
    if formats.get("total") != 'c"$"#,##0;-"$"#,##0':
        raise AssertionError(f"Grand totals must be whole-dollar currency: {formats}")
    if formats.get("subtotal") != "*0%;0%":
        raise AssertionError(f"Subtotals must hide the sign: {formats}")

    # acceptance: diverging-colour-scale
    encoding = table.find("style/style-rule[@element='mark']/encoding")
    if encoding is None or encoding.get("attr") != "color":
        raise AssertionError("Missing continuous colour encoding")
    if encoding.get("palette") != "green_blue_white_diverging_10_0":
        raise AssertionError(f"Wrong palette: {encoding.get('palette')}")
    if encoding.get("type") != "interpolated":
        raise AssertionError("Colour encoding must be interpolated")
    if float(encoding.get("center")) != 0.0:
        raise AssertionError(f"Colour centre must be 0: {encoding.get('center')}")
    if encoding.get("include-totals") != "true":
        raise AssertionError("Colour range must include totals")
    if encoding.get("symmetric") != "false":
        raise AssertionError("Percent shares and currency need independent colour ranges")
    if strip_reference(encoding.get("field")) != strip_reference(text_columns[0]):
        raise AssertionError("Colour must encode the same single measure")

    # acceptance: dashboard-fixed-size
    dashboard = next(
        d for d in root.iterfind("dashboards/dashboard") if d.get("name") == DASHBOARD
    )
    size = dashboard.find("size")
    if (size.get("minwidth"), size.get("minheight")) != ("1000", "600"):
        raise AssertionError(f"Dashboard must be 1000x600: {size.attrib}")
    if size.get("sizing-mode") != "fixed":
        raise AssertionError("Dashboard must be fixed size")
    zones = dashboard.iterfind("zones/zone/zone")
    if not any(z.get("name") == SHEET for z in zones):
        raise AssertionError("Dashboard must place the table worksheet")
    if len([z for z in zones if z.get("type-v2") == "text"]) != 4:
        raise AssertionError("Dashboard must carry the four footer text zones")

    # acceptance: subtotal-share-oracle
    expected = oracle()
    assert_close(expected, exported_cells(AUTHOR_CSV), "author export")
    # acceptance: replica-export-parity
    replica = exported_cells(REPLICA_CSV)
    assert_close(expected, replica, "replica export")
    assert_close(exported_cells(AUTHOR_CSV), replica, "author versus replica")
    # A detail cell with no facts is NULL and Tableau leaves it blank, so the
    # exported row count is the oracle's cell count rather than 21 x 12.
    if len(replica) != len(expected):
        raise AssertionError(
            f"Expected {len(expected)} exported cells, got {len(replica)}"
        )
    months = {key[1] for key in replica}
    if months != set(MONTHS):
        raise AssertionError(f"Missing months: {sorted(set(MONTHS) - months)}")
    if {(c, s) for c, _, s in replica} != {(c, s) for c, _, s in expected}:
        raise AssertionError("Row labels differ from the oracle")


if __name__ == "__main__":
    verify()
    print("PASS")
