"""Independently verify the WW16 Quick LoDs dual-axis chart.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the per-Sub-Category and per-Category averages straight from the raw
rows and checks the native workbook contracts that carry the Quick LoD chain.

Automated acceptance IDs:
  - ww16-subcategory-lod
  - ww16-category-average-lod
  - ww16-difference-formula
  - ww16-colour-split
  - ww16-dual-axis
"""

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww16-subcategory-lod",
    "ww16-category-average-lod",
    "ww16-difference-formula",
    "ww16-colour-split",
    "ww16-dual-axis",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_04_21_WW16_Quick_LODs"
TABLE = TableName("Extract", "Extract")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute the Quick LoD values from the locked extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"

    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        query = lambda sql: connection.execute_list_query(sql)
        rows = query(f"SELECT COUNT(*) FROM {TABLE}")[0][0]
        assert rows == 9994, f"row count changed: {rows}"

        subcategory = {
            sub: Decimal(str(value))
            for sub, value in query(
                f'SELECT "Sub-Category", SUM("Sales") FROM {TABLE} GROUP BY 1'
            )
        }
        categories = {
            sub: cat
            for sub, cat in query(
                f'SELECT DISTINCT "Sub-Category", "Category" FROM {TABLE}'
            )
        }

    assert len(subcategory) == 17, "Sub-Category domain changed"
    assert len(set(categories.values())) == 3, "Category domain changed"

    # The Category average is the mean of its Sub-Category totals, not the mean
    # of raw rows: the two differ for every Category.
    category_average = {}
    for cat in set(categories.values()):
        members = [value for sub, value in subcategory.items() if categories[sub] == cat]
        category_average[cat] = sum(members) / len(members)

    raw_average = {}
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        for cat, value in connection.execute_list_query(
            f'SELECT "Category", AVG("Sales") FROM {TABLE} GROUP BY 1'
        ):
            raw_average[cat] = Decimal(str(value))
    for cat in category_average:
        assert abs(category_average[cat] - raw_average[cat]) > Decimal("100"), (
            f"Category average for {cat} collapsed to the raw row grain"
        )

    difference = {
        sub: (value - category_average[categories[sub]]) / category_average[categories[sub]]
        for sub, value in subcategory.items()
    }

    # The author's published screenshot shows these rounded percentages.
    expected = {
        "Chairs": "77%", "Tables": "12%", "Bookcases": "-38%", "Furnishings": "-51%",
        "Storage": "180%", "Binders": "155%", "Appliances": "35%", "Paper": "-2%",
        "Supplies": "-42%", "Art": "-66%", "Envelopes": "-79%", "Labels": "-84%",
        "Fasteners": "-96%", "Phones": "58%", "Machines": "-9%",
        "Accessories": "-20%", "Copiers": "-28%",
    }
    for sub, want in expected.items():
        value = round(difference[sub] * 100)
        got = f"{value}%"
        assert got == want, f"{sub} difference changed: {got} != {want}"

    return {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "subcategories": len(subcategory),
        "categories": sorted(set(categories.values())),
        "category_average": {cat: float(value) for cat, value in category_average.items()},
        "difference": {sub: float(value) for sub, value in difference.items()},
        "above": sorted(sub for sub, value in difference.items() if value > 0),
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        root = etree.fromstring(archive.read(name))
    return root


def verify():
    facts = oracle()
    root = workbook()
    ds = next(
        node
        for node in root.findall("datasources/datasource")
        if node.get("name") != "Parameters"
    )

    formulas = {}
    internal = {}
    formats = {}
    for column in ds.findall("column"):
        caption = column.get("caption") or column.get("name", "").strip("[]")
        internal[caption] = column.get("name")
        formats[caption] = column.get("default-format") or ""
        calculation = column.find("calculation")
        if calculation is not None:
            formulas[caption] = calculation.get("formula") or ""

    def local(name):
        return str(name).strip("[]")

    def ref(name):
        return local(internal[name])

    def compact(text):
        return re.sub(r"\s+", "", text).upper()

    # --- ww16-subcategory-lod ----------------------------------------------
    subcategory = compact(formulas.get("Sales (Sub-Category)", ""))
    assert subcategory == "{FIXED[SUB-CATEGORY]:SUM([SALES])}", (
        f"Sales (Sub-Category) LoD changed: {formulas.get('Sales (Sub-Category)')!r}"
    )

    # --- ww16-category-average-lod -----------------------------------------
    category = compact(formulas.get("Sales (Sub-Category) (Category)", ""))
    assert category.startswith("{FIXED[CATEGORY]:AVG("), (
        f"Category average must be a FIXED AVG: {formulas.get('Sales (Sub-Category) (Category)')!r}"
    )
    assert ref("Sales (Sub-Category)") in formulas.get("Sales (Sub-Category) (Category)", ""), (
        "the Category average must average the Sub-Category LoD"
    )

    # --- ww16-difference-formula -------------------------------------------
    difference = compact(formulas.get("Difference", ""))
    assert difference.startswith("(SUM([SALES])-SUM("), (
        f"Difference formula changed: {formulas.get('Difference')!r}"
    )
    assert difference.endswith(")/SUM(") or "/SUM(" in difference, (
        "Difference must divide by the Category average"
    )
    assert ref("Sales (Sub-Category) (Category)") in formulas.get("Difference", ""), (
        "Difference must reference the Category average"
    )
    assert formats["Difference"] == "*▲0%;▼0%", (
        f"Difference custom format changed: {formats['Difference']!r}"
    )
    assert formats["Sales (Sub-Category) (Category)"] == 'c"$"#,##0;-"$"#,##0', (
        "the Category average currency format changed"
    )

    # --- ww16-colour-split --------------------------------------------------
    difference_ref = compact(ref("Difference"))
    assert compact(formulas.get("Colour", "")) == f"[{difference_ref}]>0", (
        f"Colour formula changed: {formulas.get('Colour')!r}"
    )
    label = compact(formulas.get("Above | Below", ""))
    assert label == f"IF[{difference_ref}]>0THEN'ABOVE'ELSE'BELOW'END", (
        f"Above | Below formula changed: {formulas.get('Above | Below')!r}"
    )
    palette = next(
        (
            encoding
            for encoding in ds.findall("style/style-rule[@element='mark']/encoding")
            if ref("Colour") in (encoding.get("field") or "")
        ),
        None,
    )
    assert palette is not None, "boolean colour palette missing"
    buckets = {b.text for b in palette.findall("map/bucket")}
    assert buckets == {"true", "false"}, f"palette buckets changed: {buckets}"
    colors = {m.get("to") for m in palette.findall("map")}
    assert len(colors) == 2, "above/below colours must differ"
    above_true = palette.find("map[bucket='true']").get("to")

    # --- ww16-dual-axis -----------------------------------------------------
    viz = root.find(".//worksheets/worksheet[@name='Viz']")
    assert viz is not None, "missing Viz worksheet"
    table = viz.find("table")
    rows = (table.findtext("rows") or "").strip()
    cols = (table.findtext("cols") or "").strip()
    assert ref("Category") in rows and ref("Sub-Category") in rows, (
        "Category and Sub-Category must both be on Rows"
    )
    assert "Sales" in cols, "Sales must be on Columns"
    assert ref("Sales (Sub-Category) (Category)") in cols, (
        "the Category average must be on Columns for the dual axis"
    )
    panes = table.findall("panes/pane")
    bar = next((p for p in panes if p.find("mark").get("class") == "Bar"), None)
    gantt = next((p for p in panes if p.find("mark").get("class") == "GanttBar"), None)
    assert bar is not None, "the Sales pane must be a Bar"
    assert gantt is not None, "the Category average pane must be a GanttBar"
    # The Bar pane is coloured by Colour and labelled with Difference.
    color = bar.find("encodings/color")
    assert color is not None and ref("Colour") in color.get("column"), (
        "the Sales bar must colour by Colour"
    )
    text = bar.find("encodings/text")
    assert text is not None and ref("Difference") in text.get("column"), (
        "the Sales bar must label with Difference"
    )
    # The Gantt pane carries no colour encoding (the grey is a mark colour).
    assert gantt.find("encodings/color") is None, (
        "the Category-average pane must not carry its own colour encoding"
    )
    gantt_style = gantt.find("style/style-rule[@element='mark']")
    assert gantt_style is not None and any(
        f.get("attr") == "mark-color" for f in gantt_style.findall("format")
    ), "the Category-average pane must set a flat mark colour"
    # The axis is synchronised so both measures share one scale.
    axis_rule = table.find("style/style-rule[@element='axis']")
    assert axis_rule is not None, "axis rule missing"
    assert any(
        encoding.get("synchronized") == "true"
        for encoding in axis_rule.findall("encoding")
    ), "the dual axis must be synchronised"

    # The authored tooltip names the Above | Below field and the Category average.
    tooltip = table.find(".//customized-tooltip")
    assert tooltip is not None, "authored tooltip missing"
    tooltip_text = etree.tostring(tooltip).decode()
    assert ref("Above | Below") in tooltip_text, (
        "the tooltip must include the Above | Below field"
    )
    assert ref("Difference") in tooltip_text, "the tooltip must include Difference"

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    assert any(
        zone.get("name") == "Viz" for zone in dashboard.findall(".//zones//zone")
    ), "dashboard does not host Viz"

    evidence = {
        "scope": "Locked-extract oracle plus native workbook contracts.",
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
