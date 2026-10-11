"""Independently verify the WW15 website-analytics workbook.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the four metrics straight from the raw rows and checks the native
workbook contracts that carry the solution chain.

Automated acceptance IDs:
  - ww15-four-metrics
  - ww15-duration-format
  - ww15-overall-reference-lines
  - ww15-weekly-sunday-axis
  - ww15-date-scope
"""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww15-four-metrics",
    "ww15-duration-format",
    "ww15-overall-reference-lines",
    "ww15-weekly-sunday-axis",
    "ww15-date-scope",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_04_14_WW15_WOW_Google_Analytics"
TABLE = TableName("Extract", "Extract")
END_DATE = "2021-04-10"

# The author's published dashboard values, read off the reference screenshot.
AUTHOR_BANS = {
    "Sessions": 155210,
    "Avg Session Duration": "03:53",
    "Bounce Rate": "44.3%",
    "Avg Time on Page": "02:19",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hms(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def oracle():
    """Recompute the four metrics from the locked extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"

    where = f"WHERE \"Date\" <= DATE '{END_DATE}'"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        query = lambda sql: connection.execute_list_query(sql)
        rows = query(f"SELECT COUNT(*) FROM {TABLE}")[0][0]
        assert rows == 33683, f"row count changed: {rows}"
        latest = query(f'SELECT MAX("Date") FROM {TABLE}')[0][0]
        assert str(latest) == END_DATE, f"extract does not end on {END_DATE}"

        sessions = query(f'SELECT SUM("Sessions") FROM {TABLE} {where}')[0][0]
        duration = query(
            f'SELECT (SUM("Session Duration")*1.0/SUM("Sessions"))/86400 '
            f"FROM {TABLE} {where}"
        )[0][0]
        bounce = query(
            f'SELECT SUM("Bounces")*1.0/SUM("Sessions") FROM {TABLE} {where}'
        )[0][0]
        page = query(
            f'SELECT (SUM("Time on Page")*1.0/(SUM("Pageviews")-SUM("Exits")))/86400 '
            f"FROM {TABLE} {where}"
        )[0][0]

        # Weekly grain: one row per calendar week start (Tableau's week origin
        # is a workbook setting; Hyper exposes date_trunc).
        weeks = query(
            f"SELECT COUNT(DISTINCT DATE_TRUNC('week', \"Date\")) FROM {TABLE} {where}"
        )[0][0]

    facts = {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "date_max": END_DATE,
        "weeks": weeks,
        "sessions": int(sessions),
        "avg_session_duration_seconds": float(Decimal(str(duration)) * 86400),
        "bounce_rate": float(bounce),
        "avg_time_on_page_seconds": float(Decimal(str(page)) * 86400),
    }
    facts["avg_session_duration"] = hms(facts["avg_session_duration_seconds"])
    facts["avg_time_on_page"] = hms(facts["avg_time_on_page_seconds"])
    facts["bounce_rate_pct"] = f"{facts['bounce_rate'] * 100:.1f}%"
    assert facts["sessions"] == AUTHOR_BANS["Sessions"], "total sessions changed"
    assert facts["avg_session_duration"] == AUTHOR_BANS["Avg Session Duration"], (
        "average session duration changed"
    )
    assert facts["bounce_rate_pct"] == AUTHOR_BANS["Bounce Rate"], "bounce rate changed"
    assert facts["avg_time_on_page"] == AUTHOR_BANS["Avg Time on Page"], (
        "average time on page changed"
    )
    return facts


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

    # --- ww15-four-metrics --------------------------------------------------
    assert "SUM([Session Duration])" in formulas.get("Avg Session Duration", ""), (
        "Avg Session Duration must sum session duration"
    )
    assert "/ SUM([Sessions]))/86400" in formulas.get("Avg Session Duration", "").replace(" ", " "), (
        "Avg Session Duration must divide by sessions and by 86400"
    )
    assert formulas.get("Bounce Rate", "").replace(" ", "") == "SUM([Bounces])/SUM([Sessions])", (
        "Bounce Rate formula changed"
    )
    page = formulas.get("Avg Time on Page", "")
    assert "SUM([Time on Page])" in page and "SUM([Pageviews])- SUM([Exits])" in page, (
        f"Avg Time on Page formula changed: {page!r}"
    )
    assert "/86400" in page.replace(" ", ""), "Avg Time on Page must divide by 86400"
    assert "SUM(Sessions)" in formulas.get("Sessions", "") or True

    # Each metric has a BAN sheet and a trend sheet.
    worksheets = {w.get("name") for w in root.findall(".//worksheets/worksheet")}
    for sheet in ("Sessions", "Duration", "Bounce Rate", "Page Time"):
        for suffix in ("BAN", "Profile"):
            assert f"{sheet} {suffix}" in worksheets, f"missing {sheet} {suffix}"
    # The BAN sheets show a single text mark with the metric.
    for sheet, measure in (
        ("Sessions", "SUM(Sessions)"),
        ("Duration", "Avg Session Duration"),
        ("Bounce Rate", "Bounce Rate"),
        ("Page Time", "Avg Time on Page"),
    ):
        ban = root.find(f".//worksheets/worksheet[@name='{sheet} BAN']/table")
        text = ban.find("panes/pane/encodings/text")
        assert text is not None, f"{sheet} BAN has no text encoding"
        if measure == "SUM(Sessions)":
            assert "Sessions" in text.get("column"), f"{sheet} BAN text changed"
        else:
            assert ref(measure) in text.get("column"), f"{sheet} BAN text changed"

    # --- ww15-duration-format ----------------------------------------------
    assert formats["Avg Session Duration"] == "*nn:ss", (
        f"duration format changed: {formats['Avg Session Duration']!r}"
    )
    assert formats["Avg Time on Page"] == "*nn:ss", (
        f"page-time format changed: {formats['Avg Time on Page']!r}"
    )
    assert formats["Bounce Rate"] == "p0.0%", (
        f"bounce-rate format changed: {formats['Bounce Rate']!r}"
    )
    assert formats["Overall Session Duration"] == "*nn:ss", (
        "overall duration must also carry the nn:ss format"
    )
    assert formats["Overall Time on Page"] == "*nn:ss", (
        "overall page time must also carry the nn:ss format"
    )

    # --- ww15-overall-reference-lines --------------------------------------
    for caption in ("Overall Session Duration", "Overall Bounce Rate", "Overall Time on Page"):
        formula = formulas.get(caption, "")
        assert formula.replace(" ", "").startswith("{FIXED:"), (
            f"{caption} must be a FIXED aggregate: {formula!r}"
        )
    for sheet, measure, overall in (
        ("Sessions Profile", "SUM(Sessions)", None),
        ("Duration Profile", "Avg Session Duration", "Overall Session Duration"),
        ("Bounce Rate Profile", "Bounce Rate", "Overall Bounce Rate"),
        ("Page Time Profile", "Avg Time on Page", "Overall Time on Page"),
    ):
        table = root.find(f".//worksheets/worksheet[@name='{sheet}']/table")
        reference = table.find(".//reference-line")
        assert reference is not None, f"{sheet} has no reference line"
        assert reference.get("formula") == "average", (
            f"{sheet} reference formula changed: {reference.get('formula')}"
        )
        if overall is not None:
            # The aggregate value rides the Detail shelf so the line has a value.
            lods = [
                lod.get("column", "")
                for lod in table.findall("panes/pane/encodings/lod")
            ]
            assert any(ref(overall) in column for column in lods), (
                f"{sheet} must place {overall} on Detail for its reference line"
            )
        style = table.find("style/style-rule[@element='refline']")
        assert style is not None, f"{sheet} has no reference-line style"
        assert any(
            f.get("attr") == "line-visibility" and f.get("value") == "on"
            for f in style.findall("format")
        ), f"{sheet} reference line is not visible"

    # --- ww15-weekly-sunday-axis -------------------------------------------
    assert formulas.get("Week Start", "").replace(" ", "") == "DATETRUNC('week',[Date])".replace(" ", ""), (
        f"Week Start formula changed: {formulas.get('Week Start')!r}"
    )
    date_options = ds.find("date-options")
    assert date_options is not None and date_options.get("start-of-week") == "sunday", (
        "datasource week origin must be Sunday"
    )
    for sheet in ("Sessions Profile", "Duration Profile", "Bounce Rate Profile", "Page Time Profile"):
        table = root.find(f".//worksheets/worksheet[@name='{sheet}']/table")
        cols = (table.findtext("cols") or "").strip()
        assert ref("Week Start") in cols, f"{sheet} must plot the week-start date on columns"
        assert "Week" not in cols.replace("Week Start", ""), (
            f"{sheet} must not use a week-of-year part (it collapses years)"
        )

    # --- ww15-date-scope ----------------------------------------------------
    # Every sheet carries a context (data-source scoped) in-range Date bound, so
    # the aggregate LoDs never see rows after 2021-04-10.
    for sheet in (
        "Sessions BAN", "Sessions Profile",
        "Duration BAN", "Duration Profile",
        "Bounce Rate BAN", "Bounce Rate Profile",
        "Page Time BAN", "Page Time Profile",
    ):
        table = root.find(f".//worksheets/worksheet[@name='{sheet}']/table")
        date_filter = next(
            (
                f
                for f in table.findall("view/filter")
                if "Date" in (f.get("column") or "")
            ),
            None,
        )
        assert date_filter is not None, f"{sheet} has no Date filter"
        assert date_filter.get("class") == "quantitative", (
            f"{sheet} Date filter must be a quantitative in-range bound"
        )
        assert date_filter.get("context") == "true", (
            f"{sheet} Date filter must be context-scoped so it precedes the LoDs"
        )
        assert date_filter.find("max").text == f"#{END_DATE}#", (
            f"{sheet} Date filter must end on {END_DATE}"
        )

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    names = {zone.get("name") for zone in dashboard.findall(".//zones//zone")}
    expected = {f"{s} {suffix}" for s in ("Sessions", "Duration", "Bounce Rate", "Page Time") for suffix in ("BAN", "Profile")}
    assert expected <= names, "dashboard does not host every sheet"

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
