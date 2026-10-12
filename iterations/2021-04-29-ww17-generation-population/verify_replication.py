"""Independently verify the WW17 Generation Populations chart.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the generation buckets, totals, percentages and ranks straight from
the raw rows and checks the native workbook contracts that carry the solution
chain.

Automated acceptance IDs:
  - ww17-generation-buckets
  - ww17-generation-totals
  - ww17-rank
  - ww17-year-sort
  - ww17-pane-shading
  - ww17-year-labels
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
    "ww17-generation-buckets",
    "ww17-generation-totals",
    "ww17-rank",
    "ww17-year-sort",
    "ww17-pane-shading",
    "ww17-year-labels",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_04_28_WW17_Generation_Population"
TABLE = TableName("Extract", "Extract")

BUCKETS = [
    (1927, "Greatest \nGeneration"),
    (1945, "Silent Generation"),
    (1964, "Baby Boomer"),
    (1980, "Generation X"),
    (1996, "Millennials"),
    (2012, "Generation Z"),
    (9999, "Gen \nAlpha"),
]

# The author's published header values.
AUTHOR_HEADERS = {
    "Greatest \nGeneration": ("1.7M", "0.5%", 7, 1919),
    "Silent Generation": ("23.2M", "7.1%", 6, 1928),
    "Baby Boomer": ("71.6M", "21.8%", 2, 1946),
    "Generation X": ("65.2M", "19.9%", 4, 1965),
    "Millennials": ("72.1M", "22.0%", 1, 1981),
    "Generation Z": ("66.9M", "20.4%", 3, 1997),
    "Gen \nAlpha": ("27.6M", "8.4%", 5, 2013),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generation(year: int) -> str:
    for limit, name in BUCKETS:
        if year <= limit:
            return name
    raise AssertionError("unreachable")


def oracle():
    """Recompute the generation populations from the locked extract."""
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
        assert rows == 303, f"row count changed: {rows}"

        years = {
            year: Decimal(str(value))
            for year, value in query(
                f'SELECT 2019-"AGE", SUM("2019 Population") FROM {TABLE} '
                f"WHERE \"SEX\"='Total' GROUP BY 1"
            )
        }

    assert len(years) == 101, "year domain changed"
    assert min(years) == 1919 and max(years) == 2019, "year range changed"

    totals = {}
    for year, value in years.items():
        name = generation(year)
        totals.setdefault(name, {"pop": Decimal(0), "min_year": year})
        totals[name]["pop"] += value
        totals[name]["min_year"] = min(totals[name]["min_year"], year)

    grand_total = sum(entry["pop"] for entry in totals.values())
    assert len(totals) == 7, "generation count changed"

    ranked = sorted(totals, key=lambda name: -totals[name]["pop"])
    for position, name in enumerate(ranked, start=1):
        totals[name]["rank"] = position

    for name, (want_pop, want_pct, want_rank, want_year) in AUTHOR_HEADERS.items():
        entry = totals[name]
        assert f"{entry['pop'] / 1000000:.1f}M" == want_pop, f"{name} total changed"
        assert f"{entry['pop'] / grand_total * 100:.1f}%" == want_pct, (
            f"{name} percent changed"
        )
        assert entry["rank"] == want_rank, f"{name} rank changed"
        assert entry["min_year"] == want_year, f"{name} first year changed"

    return {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "years": len(years),
        "year_min": min(years),
        "year_max": max(years),
        "grand_total": int(grand_total),
        "generations": {
            name: {
                "pop": int(totals[name]["pop"]),
                "pct": float(totals[name]["pop"] / grand_total),
                "rank": totals[name]["rank"],
                "min_year": totals[name]["min_year"],
            }
            for name in AUTHOR_HEADERS
        },
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

    def resolve(text):
        """Rewrite internal [Calculation_...] references back to their captions."""
        for caption, name in internal.items():
            if not name:
                continue
            text = text.replace(name, f"[{caption}]")
        return text

    # --- ww17-generation-buckets -------------------------------------------
    assert compact(formulas.get("Year", "")) == "2019-[AGE]", (
        f"Year formula changed: {formulas.get('Year')!r}"
    )
    gen = resolve(formulas.get("Generation", ""))
    for token in ("1927", "1945", "1964", "1980", "1996", "2012"):
        assert token in gen, f"Generation is missing the {token} boundary"
    assert "'Greatest \\nGeneration'" in gen or "Greatest" in gen, "missing Greatest Generation"
    assert "Gen \\nAlpha" in gen or "Gen" in gen, "missing Gen Alpha"
    assert gen.count("Generation") >= 3, "generation names changed"

    # --- ww17-generation-totals --------------------------------------------
    total_lod = compact(resolve(formulas.get("Total Population Per Generation", "")))
    assert total_lod.startswith("{FIXED["), (
        f"Total Population Per Generation must be a FIXED LoD: {formulas.get('Total Population Per Generation')!r}"
    )
    assert "SUM([2019POPULATION])" in total_lod, "the LoD must sum the 2019 population"
    assert "[GENERATION]" in total_lod and "[SEX]" in total_lod, (
        "the LoD must be fixed at Generation and SEX"
    )
    percent = compact(resolve(formulas.get("% of Total Population", "")))
    assert "TOTAL(SUM(" in percent, "the percent must use a TOTAL table calculation"
    assert formats["% of Total Population"] == "p0.0%", "percent format changed"
    header = compact(resolve(formulas.get("Total | Percent", "")))
    assert "ROUND(SUM(" in header and "'M'" in header and "'%'" in header, (
        f"Total | Percent header text changed: {formulas.get('Total | Percent')!r}"
    )

    # --- ww17-rank ----------------------------------------------------------
    assert compact(resolve(formulas.get("Rank", ""))) == (
        "RANK_DENSE(SUM([TOTALPOPULATIONPERGENERATION]))"
    ), (
        f"Rank formula changed: {formulas.get('Rank')!r}"
    )
    assert formats["Rank"] == 'n"#"#,##0;-"#"#,##0', (
        f"Rank custom format changed: {formats['Rank']!r}"
    )

    # --- ww17-year-sort -----------------------------------------------------
    min_year = compact(resolve(formulas.get("Min Year per Generation", "")))
    assert min_year.startswith("{FIXED["), "Min Year per Generation must be a FIXED LoD"
    assert "MIN([YEAR])" in min_year, "the sort key must take the minimum Year"

    viz = root.find(".//worksheets/worksheet[@name='Chart']")
    assert viz is not None, "missing Chart worksheet"
    table = viz.find("table")
    cols = (table.findtext("cols") or "").strip()
    rows = (table.findtext("rows") or "").strip()
    # The pane order runs through the generation's first year.
    for caption in ("Min Year per Generation", "Rank", "Generation", "Total | Percent", "Year"):
        assert ref(caption) in cols, f"{caption} is missing from the column axis"
    assert ref("Min Year per Generation") in cols.split("/")[0], (
        "Min Year per Generation must be the outer column so panes run chronologically"
    )
    assert "2019 Population" in rows, "the population measure must be on Rows"
    assert ref("Point to Plot Year Label") in rows, (
        "the year-label measure must share the row axis"
    )

    # --- ww17-pane-shading --------------------------------------------------
    assert compact(resolve(formulas.get("Sort Position", ""))).startswith("RANK_DENSE(MIN("), (
        f"Sort Position formula changed: {formulas.get('Sort Position')!r}"
    )
    assert compact(resolve(formulas.get("Sort Position is +ve number", ""))) == (
        "[SORTPOSITION]%2=0"
    ), f"Sort Position is +ve number changed: {formulas.get('Sort Position is +ve number')!r}"
    palette = next(
        (
            encoding
            for encoding in ds.findall("style/style-rule[@element='mark']/encoding")
            if ref("Sort Position is +ve number") in (encoding.get("field") or "")
        ),
        None,
    )
    assert palette is not None, "pane shading palette missing"
    buckets = {b.text for b in palette.findall("map/bucket")}
    assert buckets == {"true", "false"}, f"shading buckets changed: {buckets}"
    colors = {m.get("to") for m in palette.findall("map")}
    assert colors == {"#00c3a9", "#00ad90"}, f"teal shades changed: {colors}"

    # --- ww17-year-labels ---------------------------------------------------
    point = compact(resolve(formulas.get("Point to Plot Year Label", "")))
    assert "THEN4700000" in point, "Point to Plot Year Label must plot at 4.7M"
    assert "1919" in formulas.get("Point to Plot Year Label", ""), (
        "the 1919 label must be suppressed"
    )
    panes = table.findall("panes/pane")
    bar = next((p for p in panes if p.find("mark").get("class") == "Bar"), None)
    circle = next((p for p in panes if p.find("mark").get("class") == "Circle"), None)
    assert bar is not None, "the population pane must be a Bar"
    assert circle is not None, "the year-label pane must be a Circle"
    color = bar.find("encodings/color")
    assert color is not None and ref("Sort Position is +ve number") in color.get("column"), (
        "the bar pane must colour by the pane shading field"
    )
    label = circle.find("encodings/text")
    assert label is not None and ref("Min Year per Generation") in label.get("column"), (
        "the circle pane must label the generation's first year"
    )
    # Dashed pane dividers.
    divider = table.find("style/style-rule[@element='table-div']")
    assert divider is not None, "pane divider style missing"
    assert any(
        f.get("attr") == "line-pattern-only" and f.get("value") == "dashed"
        for f in divider.findall("format")
    ), "the pane dividers must be dashed"
    # Background colour.
    table_style = table.find("style/style-rule[@element='table']")
    assert table_style is not None and any(
        f.get("attr") == "background-color" and f.get("value") == "#dcd2c4"
        for f in table_style.findall("format")
    ), "the worksheet background must be #dcd2c4"
    # Only the Total sex is plotted.
    sex_filter = next(
        (
            f
            for f in table.findall("view/filter")
            if "SEX" in (f.get("column") or "")
        ),
        None,
    )
    assert sex_filter is not None, "SEX filter missing"
    assert "Total" in etree.tostring(sex_filter).decode(), "the chart must plot SEX = Total"

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    assert any(
        zone.get("name") == "Chart" for zone in dashboard.findall(".//zones//zone")
    ), "dashboard does not host Chart"

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
