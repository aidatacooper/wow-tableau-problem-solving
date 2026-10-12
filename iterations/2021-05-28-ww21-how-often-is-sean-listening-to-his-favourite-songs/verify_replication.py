"""Independently verify the WW21 favourite-songs scatter + timeline workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the per-song days/plays scatter aggregates from the raw rows and
checks the native workbook contracts that carry the solution chain.

Automated acceptance IDs:
  - ww21-scatter-aggregates
  - ww21-selected-song-set
  - ww21-plot-switch
  - ww21-timeline
  - ww21-plays-filter
  - ww21-interactions
"""

import datetime
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww21-scatter-aggregates",
    "ww21-selected-song-set",
    "ww21-plot-switch",
    "ww21-timeline",
    "ww21-plays-filter",
    "ww21-interactions",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_05_26_WW21_Favourite_Songs"
TABLE = TableName("Extract", "Extract")
DATE_FORMATS = ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M:%S %p")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_date(value: str) -> datetime.date:
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unexpected timestamp: {value!r}")


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
            f'SELECT "SongID","TimeStamp_UTC" FROM {TABLE}'
        )
    assert len(rows) == 62907, "row count changed"
    per_song = {}
    for song_id, timestamp in rows:
        per_song.setdefault(song_id, []).append(parse_date(timestamp))
    filtered = {
        song_id: days for song_id, days in per_song.items() if 50 <= len(days) <= 100
    }
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "songs": len(per_song),
        "filtered_songs": len(filtered),
        "filtered_days_range": [
            min((max(days) - min(days)).days for days in filtered.values()),
            max((max(days) - min(days)).days for days in filtered.values()),
        ],
        "filtered_plays_range": [
            min(len(days) for days in filtered.values()),
            max(len(days) for days in filtered.values()),
        ],
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root):
    """Map display captions to formulas, resolving internal field references."""
    raw = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is not None:
            raw[column.get("name")] = (column.get("caption"), calc.get("formula") or "")
    names = {name.strip("[]"): name for name in raw}

    def resolve(formula: str) -> str:
        def replace(match):
            token = match.group(1)
            if token.startswith("Calculation_") and token in names:
                caption = raw[names[token]][0]
                return f"[{caption}]"
            return match.group(0)

        import re

        return re.sub(r"\[([^\]]+)\]", replace, formula)

    return {caption: resolve(formula) for caption, formula in raw.values()}


def captions(root):
    """Map every datasource column name to its display caption."""
    result = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name") or ""
        result[name] = column.get("caption") or name.strip("[]")
    return result


def labelled(reference: str, names: dict) -> str:
    """Return the display caption for a fully-qualified internal reference.

    References look like ``[federated.xxx].[usr:Calculation_ABC:qk]``; the
    token of interest is the bracketed internal column name with its
    derivation prefix and type suffix stripped.
    """
    if not reference:
        return ""
    import re

    parts = re.findall(r"\[([^\]]+)\]", reference)
    for token in reversed(parts):
        if token.startswith("federated."):
            continue
        match = re.match(r"^(?:usr|sum|avg|attr|none|io|mn|yr|dy|cnt|cum):(.*?):(?:qk|nk|ok)$", token)
        if match:
            return names.get(f"[{match.group(1)}]", match.group(1))
        return names.get(f"[{token}]", token)
    return ""


def verify():
    facts = oracle()
    root = workbook()
    calc = formulas(root)
    names = captions(root)

    # --- ww21-scatter-aggregates -------------------------------------------
    assert "DATEPARSE" in calc["Date Played"] and "TimeStamp_UTC" in calc["Date Played"]
    assert calc["Min Date per Song"] == "{FIXED [SongID]:MIN([Date Played])}"
    assert calc["Max Date per Song"] == "{FIXED [SongID] : MAX([Date Played])}"
    assert calc["Days since first listen"] == (
        "DATEDIFF('day', [Min Date per Song], [Max Date per Song])"
    )
    assert calc["Total Plays per Song"] == "{FIXED [SongID]: [Total Plays]}"
    assert "COUNT(" in calc["Total Plays"]
    # The oracle's filtered range must be inside 50..100 and non-empty.
    low, high = facts["filtered_plays_range"]
    assert low == 50 and high <= 100, facts
    assert facts["filtered_songs"] == 89, facts

    # --- ww21-selected-song-set --------------------------------------------
    group = root.find(".//datasource/group[@caption='Selected Song']")
    assert group is not None, "Selected Song set missing"
    assert group.get("name") == "[Selected Song]"
    assert group.find("groupfilter").get("function") == "empty-level"
    set_instance = root.find(".//datasource/column-instance[@name='[io:Selected Song:nk]']")
    assert set_instance is not None, "set In/Out instance missing"

    # --- ww21-plot-switch ---------------------------------------------------
    assert calc["Days to Plot"] == (
        "IF ATTR([Selected Song]) THEN AVG([Days To Date]) "
        "ELSE SUM([Days since first listen]) END"
    )
    assert calc["Plays to Plot"] == (
        "IF ATTR([Selected Song]) THEN RUNNING_SUM([Total Plays]) "
        "ELSE SUM([Total Plays per Song]) END"
    )
    assert calc["Days To Date"] == "DATEDIFF('day',[Min Date per Song],[Date Played])"

    # --- ww21-timeline ------------------------------------------------------
    assert calc["Is Last?"] == "LAST()=0"
    assert calc["Last Plays to Plot"] == "IF [Is Last?] THEN Sum([Total Plays per Song]) END"
    chart = root.find(".//worksheets/worksheet[@name='Chart']")
    assert chart is not None, "missing Chart worksheet"
    panes = chart.findall("table/panes/pane")
    assert len(panes) == 2, f"expected the dual-axis chart, got {len(panes)}"
    marks = [pane.find("mark").get("class") for pane in panes]
    assert marks == ["Circle", "Line"], marks
    line = panes[1]
    path = line.find("encodings/path")
    assert path is not None and labelled(path.get("column"), names) == "Date Played"
    interpolation = line.find(
        "style/style-rule[@element='mark']/format[@attr='line-interpolation']"
    )
    assert interpolation is not None and interpolation.get("value") == "step"
    color = line.find("encodings/color")
    assert color is not None and labelled(color.get("column"), names) == "Selected Song"
    rows = chart.findtext("table/rows") or ""
    assert "Last Plays to Plot" in rows or any(
        labelled(ref, names) == "Last Plays to Plot" for ref in __import__("re").findall(r"\[[^\]]+\]", rows)
    ), rows
    cols = chart.findtext("table/cols") or ""
    assert "Days to Plot" in cols or any(
        labelled(ref, names) == "Days to Plot" for ref in __import__("re").findall(r"\[[^\]]+\]", cols)
    ), cols
    # The running total must be addressed by the exact date. Find the
    # column-instance carrying a <table-calc><order> and check its caption.
    order_fields = [
        node.get("field")
        for node in chart.findall(
            "table/view/datasource-dependencies/column-instance/table-calc/order"
        )
    ]
    assert order_fields, "no table-calculation ordering field"
    assert all(labelled(ref, names) == "Date Played" for ref in order_fields), order_fields

    # --- ww21-plays-filter --------------------------------------------------
    filters = chart.findall(".//view/filter")
    assert any(
        f.get("class") == "quantitative"
        and f.find("min").text == "50"
        and f.find("max").text == "100"
        for f in filters
    ), "Total Plays per Song range filter missing"

    # --- ww21-interactions --------------------------------------------------
    set_actions = root.findall(".//actions/edit-group-action")
    assert len(set_actions) == 1, set_actions
    action = set_actions[0]
    assert action.get("caption") == "Set1"
    assert action.find("activation").get("type") == "on-select"
    assert action.find("single-select").get("value") == "true"
    assert action.find("params/param[@name='add-or-remove-marks']").get("value") == "assign"
    target = action.find("params/param[@name='target-group']").get("value")
    assert "Selected Song" in target, target
    highlights = [
        a
        for a in root.findall(".//actions/action")
        if a.find("command") is not None
        and a.find("command").get("command") == "tsc:brush"
    ]
    assert highlights, "highlight action missing"
    assert highlights[0].find("command/param[@name='field-captions']").get("value") == "True"
    assert "True" in calc
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    evidence = {
        "scope": "Locked-extract oracle plus native scatter/timeline workbook contracts.",
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
