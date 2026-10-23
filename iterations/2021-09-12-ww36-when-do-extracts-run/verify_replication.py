"""Independent behavioural checks for the WW36 extract-Gantt replica.

The verifier never trusts the built workbook for numbers.  It recomputes the
business behaviour straight from the locked Hyper extract with the Hyper API and
compares those results with the *declared* workbook contract (formulas, shelves,
filters, encodings, dashboard controls).  If the builder drifts, the workbook
would still be self-consistent; only an independent aggregate catches it.

acceptance: extract-status-classification
acceptance: waiting-and-processing-durations
acceptance: baseline-same-day-normalisation
acceptance: over-wait-threshold-flag
acceptance: days-to-show-filter
acceptance: gantt-dual-axis-encoding
acceptance: key-legend-pairing
acceptance: dashboard-controls-and-legends
acceptance: locked-input-and-round-trip
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json
import zipfile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs" / "TEMP_0za05zv08wbboi1164y2i07f3q8l.hyper"
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"

NOW = datetime(2021, 2, 5, 16, 30, 0)
BASELINE = datetime(2021, 1, 1, 0, 0, 0)
WAIT_THRESHOLD = 0.007
SECONDS_PER_DAY = 86400.0

GANTT = "Gantt"
KEY = "Key"
DASHBOARD = "When Do Extracts Run During The Day?"


def _workbook() -> etree._Element:
    with zipfile.ZipFile(OUTPUT) as archive:
        return etree.fromstring(archive.read("replicated-workbook.twb"))


def _rows() -> list[dict]:
    """Read the locked extract once, without any workbook involvement."""
    table = '"Extract"."Extract"'
    query = (
        f'SELECT "id", "Site", "title", "created_at", "started_at", '
        f'"completed_at", "finish_code", "progress" FROM {table}'
    )
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as connection:
            raw = connection.execute_list_query(query)
    return [
        {
            "id": row[0],
            "site": row[1],
            "title": row[2],
            "created_at": row[3].to_datetime(),
            "started_at": row[4].to_datetime() if row[4] is not None else None,
            "completed_at": row[5].to_datetime() if row[5] is not None else None,
            "finish_code": row[6],
            "progress": row[7],
        }
        for row in raw
    ]


def _status(row: dict) -> str:
    """Author's Extract Status definition, evaluated independently."""
    if row["finish_code"] == 1 and row["progress"] != 100:
        return "In Progress"
    if row["finish_code"] == 0 and not row["progress"] == 1:
        return "Success"
    return "Failed"


def _waiting(row: dict) -> float:
    end = row["started_at"] or NOW
    return (end - row["created_at"]).total_seconds() / SECONDS_PER_DAY


def _processing(row: dict) -> float:
    end = row["completed_at"] or NOW
    return (end - row["started_at"]).total_seconds() / SECONDS_PER_DAY


def _baseline(moment: datetime) -> datetime:
    """DATEADD('day', DATEDIFF('day', moment, 2021-01-01), moment)."""
    shift = (BASELINE.date() - moment.date()).days
    return moment + timedelta(days=shift)


def _visible(rows: list[dict], days: int) -> list[dict]:
    """Filter: Days to Show, plus the author's Site 9 sheet filter."""
    cutoff = (NOW.date() - timedelta(days=days - 1))
    return [
        row
        for row in rows
        if row["created_at"].date() >= cutoff and row["site"] == "Site 9"
    ]


def check_oracle(rows: list[dict]) -> dict:
    # acceptance: extract-status-classification
    statuses = {"In Progress": 0, "Success": 0, "Failed": 0}
    for row in rows:
        statuses[_status(row)] += 1
    assert sum(statuses.values()) == len(rows), "Every task needs exactly one status"
    assert statuses["Success"] > 0 and statuses["Failed"] > 0
    # finish_code=2 (cancelled) must fall through to Failed, as the author's
    # ELSE branch does; that is what keeps the ELSE branch observable.
    cancelled = [r for r in rows if r["finish_code"] == 2]
    assert cancelled and all(_status(r) == "Failed" for r in cancelled)
    in_progress = [r for r in rows if _status(r) == "In Progress"]
    assert all(r["finish_code"] == 1 and r["progress"] != 100 for r in in_progress)

    # acceptance: waiting-and-processing-durations
    waits = [_waiting(row) for row in rows]
    runs = [_processing(row) for row in rows]
    assert max(waits) > WAIT_THRESHOLD, "No task waits longer than ten minutes"
    assert min(waits) < 0, "Queued tasks should not all start after they are created"
    assert all(0 <= value < 1 for value in runs), "Processing time must stay inside one day"
    # The Now parameter is only observable through unfinished tasks.
    unfinished = [r for r in rows if r["completed_at"] is None]
    assert unfinished, "No unfinished task exercises the Now parameter"
    for row in unfinished:
        expected = (NOW - row["started_at"]).total_seconds() / SECONDS_PER_DAY
        assert abs(_processing(row) - expected) < 1e-12

    # acceptance: baseline-same-day-normalisation
    for row in rows:
        assert _baseline(row["created_at"]).date() == BASELINE.date()
        assert _baseline(row["created_at"]).time() == row["created_at"].time()
        if row["started_at"] is not None:
            assert _baseline(row["started_at"]).date() == BASELINE.date()
            assert _baseline(row["started_at"]).time() == row["started_at"].time()

    # acceptance: over-wait-threshold-flag
    flagged = [row for row in rows if _waiting(row) > WAIT_THRESHOLD]
    assert flagged and len(flagged) < len(rows), "Threshold flag must split the data"

    # acceptance: days-to-show-filter
    windows = {}
    for days in (1, 5, 7, 10):
        selected = _visible(rows, days)
        assert selected, f"pDaysToShow={days} selects no tasks"
        assert all(row["site"] == "Site 9" for row in selected)
        windows[str(days)] = len(selected)
    assert windows["1"] < windows["5"] < windows["7"] <= windows["10"]
    default_window = _visible(rows, 5)
    assert default_window, "The default 5-day window is empty"

    return {
        "rows": len(rows),
        "sites": sorted({row["site"] for row in rows}),
        "statuses": statuses,
        "over_wait_threshold": len(flagged),
        "max_wait": max(waits),
        "max_processing": max(runs),
        "unfinished_tasks": len(unfinished),
        "window_rows": windows,
        "default_window_statuses": {
            name: sum(1 for row in default_window if _status(row) == name)
            for name in ("In Progress", "Success", "Failed")
        },
        "default_window_over_threshold": sum(
            1 for row in default_window if _waiting(row) > WAIT_THRESHOLD
        ),
    }


def check_workbook(root: etree._Element) -> None:
    # acceptance: locked-input-and-round-trip
    lock = json.loads((HERE / "inputs" / "source-lock.json").read_text(encoding="utf-8"))
    for item in lock["extracted_data"]:
        packaged = next(
            name for name in zipfile.ZipFile(OUTPUT).namelist()
            if Path(name).name == Path(item["file"]).name
        )
        import hashlib

        digest = hashlib.sha256(
            zipfile.ZipFile(OUTPUT).read(packaged)
        ).hexdigest()
        assert digest == item["sha256"], "Packaged extract differs from the locked input"
    editor = TWBEditor.open_existing(OUTPUT)
    sheets = set(editor.list_worksheets())
    assert {GANTT, KEY, "Data"} <= sheets, f"Missing sheets: {sorted(sheets)}"
    assert [item["name"] for item in editor.list_dashboards()] == [DASHBOARD]

    data_sources = [
        node
        for node in root.findall("datasources/datasource")
        if node.get("hasconnection") != "false"
    ]
    assert len(data_sources) == 1, "The replica must carry exactly one data source"
    datasource = data_sources[0]
    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in datasource.findall("column")
        if column.find("calculation") is not None
    }
    assert "DATEDIFF('second'" in formulas["Waiting Time"]
    assert "[Parameters].[Parameter 1]" in formulas["Waiting Time"]
    assert "ISNULL([started_at])" in formulas["Waiting Time"]
    assert "ISNULL([completed_at])" in formulas["Processing Time"]
    assert "DATEADD('day', DATEDIFF('day', [created_at], #2021-01-01#)" in formulas["Created At Baseline"]
    assert "DATEADD('day', DATEDIFF('day', [started_at], #2021-01-01#)" in formulas["Started At Baseline"]
    assert formulas["Over Wait Time Threshold"].endswith("> 0.007")
    assert "DATETRUNC('day', [created_at])" in formulas["Filter: Days to Show"]
    assert "[Parameters].[Parameter 2]" in formulas["Filter: Days to Show"]
    assert formulas["Extract Status"].count("ELSEIF") == 1
    assert "IF [Site] = 'Site 9' THEN 'Waiting'" in formulas["Key Label"]
    assert formulas["Key Order"] == "IF [Site] = 'Site 9' THEN 1 ELSE 0 END"
    assert "MIN(1)" in formulas["One"]
    # The readable captions are pass-through aliases, not new logic.
    for alias, physical in (
        ("Created At", "[created_at]"),
        ("Started At", "[started_at]"),
        ("Completed At", "[completed_at]"),
        ("Id", "[id]"),
        ("Title", "[title]"),
        ("Notes", "[notes]"),
        ("Finish Code", "[finish_code]"),
    ):
        assert formulas[alias] == physical, f"{alias} must be a pass-through alias"

    parameters = {
        column.get("caption"): column
        for column in root.findall("datasources/datasource[@name='Parameters']/column")
    }
    assert parameters["Now"].get("datatype") == "datetime"
    assert parameters["Now"].get("value") == "#2021-02-05 16:30:00#"
    days = parameters["pDaysToShow"]
    assert days.get("datatype") == "integer" and days.get("value") == "5"
    assert days.find("range").get("min") == "1" and days.find("range").get("max") == "10"
    assert "days" in days.get("default-format", "")

    # A calculated date referenced only by caption leaves unresolved
    # table-calculation metadata behind; this workbook must have none.
    assert not root.findall(".//table-calc"), "Unresolved table-calculation metadata"
    assert not root.findall(".//ordering-field"), "Unresolved ordering_field metadata"

    # acceptance: gantt-dual-axis-encoding
    gantt = root.find(f"worksheets/worksheet[@name='{GANTT}']")
    table = gantt.find("table")
    rows = table.findtext("rows") or ""
    columns = table.findtext("cols") or ""
    for required in ("Site", "none:Calculation_", "tdy:Calculation_"):
        assert required in rows, f"Gantt rows shelf is missing {required}"
    assert "Calculation_" in columns and columns.count("+") == 1, (
        "The two baselined datetime axes must share the folded columns shelf"
    )
    panes = table.findall("panes/pane")
    assert len(panes) == 2, "The Gantt needs exactly the waiting and processing panes"
    waiting_pane, processing_pane = panes
    waiting_encodings = {
        node.tag: node.get("column") for node in waiting_pane.find("encodings")
    }
    processing_encodings = {
        node.tag: node.get("column") for node in processing_pane.find("encodings")
    }
    assert "avg:" in waiting_encodings["size"] and "avg:" in processing_encodings["size"]
    assert waiting_encodings["size"] != processing_encodings["size"]
    assert "none:" in waiting_encodings["color"] and "none:" in processing_encodings["color"]
    assert waiting_encodings["color"] != processing_encodings["color"]
    # Both pane axes must be bound on the sheet, not only in <style>.
    assert waiting_pane.get("x-axis-name") and processing_pane.get("x-axis-name")
    assert waiting_pane.get("x-axis-name") != processing_pane.get("x-axis-name")
    assert waiting_pane.get("x-axis-name") in columns
    assert processing_pane.get("x-axis-name") in columns
    # The author's tooltips are reproduced on both panes.
    for pane in panes:
        tooltip = pane.find("customized-tooltip")
        assert tooltip is not None, "Each Gantt pane needs the author's tooltip"
        text = "".join(run.text or "" for run in tooltip.iter("run"))
        for phrase in ("Site:", "Object:", "Job ID:", "Created Time:", "Duration (hh:mm:ss):"):
            assert phrase in text, f"Tooltip is missing {phrase!r}"
    marks = {pane.find("mark").get("class") for pane in panes}
    assert marks == {"GanttBar"}, f"Expected GanttBar marks, got {marks}"
    axis_rule = table.find("style/style-rule[@element='axis']")
    folded = [
        encoding
        for encoding in axis_rule.findall("encoding")
        if encoding.get("fold") == "true"
    ]
    assert len(folded) == 1 and folded[0].get("synchronized") == "true"
    reference_lines = waiting_pane.findall("reference-line")
    assert float(processing_pane.find("style/style-rule/format[@attr='size']").get("value")) > 0.5
    assert len(reference_lines) == 2, "The 08:00-17:00 working-hours band needs two lines"
    # The band endpoints are the 08:00 and 17:00 instants of the normalised day,
    # declared as datetime fields so they stay exact on a datetime axis.
    by_formula = {line.get("formula"): line for line in reference_lines}
    assert set(by_formula) == {"min", "max"}
    endpoint_formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in datasource.findall("column")
        if column.get("caption") in {"Working Hours Start", "Working Hours End"}
    }
    assert endpoint_formulas == {
        "Working Hours Start": "#2021-01-01 08:00:00#",
        "Working Hours End": "#2021-01-01 17:00:00#",
    }
    for caption, formula in (
        ("Working Hours Start", "min"),
        ("Working Hours End", "max"),
    ):
        local = next(
            column.get("name")
            for column in datasource.findall("column")
            if column.get("caption") == caption
        )
        assert local.strip("[]") in by_formula[formula].get("value-column", "")
        assert any(local.strip("[]") in n.get("column", "") for n in waiting_pane.findall("encodings/lod")), "Reference band endpoint must be in query"
    assert {line.get("scope") for line in reference_lines} == {"per-pane"}
    assert {line.get("paired-id") for line in reference_lines} == {"refline0", "refline1"}
    band = table.find("style/style-rule[@element='refband']/format[@id='refline0']")
    assert band is not None and band.get("value") == "#f3faf9"
    filters = {
        node.get("column"): node
        for node in table.findall("view/filter")
    }
    assert len(filters) == 2, "Gantt needs the days-to-show filter and the Site filter"
    members = {
        node.get("member")
        for node in table.iter("groupfilter")
        if node.get("function") == "member"
    }
    assert members == {'"Site 9"', "true"}, f"Unexpected Gantt filter members: {members}"
    assert len(table.findall("view/slices/column")) == 2

    palettes = {
        encoding.get("field"): {
            mapping.find("bucket").text: mapping.get("to")
            for mapping in encoding.findall("map")
        }
        for encoding in datasource.findall("style/style-rule[@element='mark']/encoding")
    }
    assert palettes["[none:Calculation_" + next(
        column.get("name").strip("[]").removeprefix("Calculation_")
        for column in datasource.findall("column")
        if column.get("caption") == "Extract Status"
    ) + ":nk]"] == {"\"In Progress\"": "#4e79a7", "\"Success\"": "#bab0ac", "\"Failed\"": "#e15759"}

    # acceptance: key-legend-pairing
    key = root.find(f"worksheets/worksheet[@name='{KEY}']")
    assert key.find("table/panes/pane/mark").get("class") == "Bar"
    key_columns = key.findtext("table/cols") or ""
    assert "Calculation_" in key_columns and "*" in key_columns
    key_filter = key.find("table/view/filter")
    assert key_filter is not None
    members = {
        node.get("member")
        for node in key_filter.iter("groupfilter")
        if node.get("function") == "member"
    }
    assert members == {'"Site 7"', '"Site 9"'}
    sort = key.find("table/view/computed-sort")
    assert sort is not None, "Waiting must sort before Processing"
    assert sort.get("direction") == "DESC"
    key_labels = next(
        column.get("name")
        for column in datasource.findall("column")
        if column.get("caption") == "Key Label"
    )
    assert sort.get("column", "").endswith(key_labels.strip("[]") + ":nk]")
    order_field = next(
        column.get("name")
        for column in datasource.findall("column")
        if column.get("caption") == "Key Order"
    )
    assert order_field.strip("[]") in sort.get("using", "")
    key_encodings = {
        node.tag: node.get("column")
        for node in key.find("table/panes/pane/encodings")
    }
    assert key_encodings["color"] == key_encodings["size"], (
        "The key colours and sizes bars by Site"
    )

    # acceptance: dashboard-controls-and-legends
    dashboard = root.find(f"dashboards/dashboard[@name='{DASHBOARD}']")
    size = dashboard.find("size")
    assert (size.get("maxwidth"), size.get("maxheight")) == ("1000", "800")
    zones = dashboard.find("zones")
    worksheet_zones = [zone for zone in zones.iter("zone") if zone.get("name") == GANTT]
    assert any(zone.get("type-v2") in (None, "NONE") for zone in worksheet_zones)
    legends = [zone for zone in zones.iter("zone") if zone.get("type-v2") == "color"]
    assert {zone.get("pane-specification-id") for zone in legends} == {"1", "2"}
    controls = [zone for zone in zones.iter("zone") if zone.get("type-v2") == "filter"]
    assert len(controls) == 1 and controls[0].get("name") == GANTT
    assert controls[0].get("mode") == "checkdropdown"
    parameter_control = [
        zone for zone in zones.iter("zone") if zone.get("type-v2") == "paramctrl"
    ]
    assert len(parameter_control) == 1
    assert parameter_control[0].get("param") == "[Parameters].[Parameter 2]"
    assert parameter_control[0].get("mode") == "slider"
    assert parameter_control[0].get("custom-title") == "true"
    key_zone = [zone for zone in zones.iter("zone") if zone.get("name") == KEY]
    assert len(key_zone) == 1 and key_zone[0].get("show-title") == "false"
    text = " ".join(
        run.text or "" for run in dashboard.iter("run")
    )
    for phrase in (
        "WHEN DO EXTRACTS RUN DURING THE DAY?",
        "CHALLENGE BY : DONNA COLES",
        "#WOW2021  |  WEEK 36",
    ):
        assert phrase in text, f"Dashboard text is missing {phrase!r}"

    data_pane = root.find("worksheets/worksheet[@name='Data']/table/panes/pane")
    labels = data_pane.find("style/style-rule[@element='mark']/format[@attr='mark-labels-show']")
    assert labels is not None and labels.get("value") == "true", (
        "The Data crosstab shows its values"
    )

    data_window = root.find("windows/window[@name='Data']")
    assert data_window is not None and data_window.get("hidden") == "true", (
        "The supporting Data crosstab stays hidden, as the author shipped it"
    )


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")
    rows = _rows()
    summary = check_oracle(rows)
    root = _workbook()
    check_workbook(root)

    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "data-contract.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "rows={rows} sites={sites} statuses={statuses} over_wait={over_wait_threshold} "
        "windows={window_rows}".format(**summary)
    )


if __name__ == "__main__":
    verify()
    print("PASS")
