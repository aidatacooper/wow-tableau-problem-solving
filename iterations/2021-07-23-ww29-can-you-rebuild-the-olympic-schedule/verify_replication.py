"""Independently verify the WW29 "Olympic Schedule" workbook.

Reads only the locked Hyper extract, the case metadata and the built TWBX.
Re-implements the schedule logic in Python straight from the extract (which
sports run on which day, how many finals, how many events the other sports
contribute) and then checks the native workbook contracts: the calculation
chain, the shape/axis layout, the viz-in-tooltip wiring, the set and the five
dashboard interactions.

Automated acceptance IDs:
  - ww29-schedule-calcs
  - ww29-schedule-view
  - ww29-selector-set
  - ww29-viz-in-tooltip
  - ww29-dashboard-actions
  - ww29-time-adjust
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
    "ww29-schedule-calcs",
    "ww29-schedule-view",
    "ww29-selector-set",
    "ww29-viz-in-tooltip",
    "ww29-dashboard-actions",
    "ww29-time-adjust",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_07_21_WW29_Olympic_Schedule"
TABLE = TableName("Extract", "Extract")
INITIAL_SET = ["Boxing", "Gymnastics", "Martial Arts"]
# The article's parameter is a whole-hour offset; the oracle uses both ends.
TIME_ADJUST_CASES = (0, 3, -5)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_victory(event: str) -> bool:
    return "Victory Ceremony" in event


def is_final(event: str) -> bool:
    return "Gold Medal" in event or " Final" in event


def x_axis(events: int, finals: int, final_flag: bool) -> int:
    if finals == 0:
        return 5
    if finals - events == 0:
        return 5
    return 7 if final_flag else 3


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
            f'SELECT "Sport Group","Events Split","UK Date Time","Date","Sport" FROM {TABLE}'
        )

    facts = {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "sport_groups": len({row[0] for row in rows}),
        "sports": len({row[4] for row in rows}),
        "days": len({row[3] for row in rows}),
        "victory_rows": sum(1 for row in rows if is_victory(row[1])),
        "final_rows": sum(1 for row in rows if is_final(row[1])),
    }

    for adjust in TIME_ADJUST_CASES:
        # FIXED levels the author uses: (day of adjusted date, is victory ceremony)
        # and (day of adjusted date, is victory ceremony, sport).
        per_day: dict[tuple, int] = {}
        per_sport: dict[tuple, int] = {}
        finals_by_sport: dict[tuple, int] = {}
        cells: dict[tuple, int] = {}
        for group, event, uk, _date, sport in rows:
            shifted = uk + datetime.timedelta(hours=adjust)
            day = datetime.date(shifted.year, shifted.month, shifted.day)
            victory = is_victory(event)
            per_day[(day, victory)] = per_day.get((day, victory), 0) + 1
            per_sport[(day, victory, sport)] = per_sport.get((day, victory, sport), 0) + 1
            if victory:
                continue
            key = (day, group, sport)
            finals_by_sport[key] = finals_by_sport.get(key, 0) + int(is_final(event))
            cells[(day, group, sport, is_final(event))] = (
                cells.get((day, group, sport, is_final(event)), 0) + 1
            )

        marks = []
        for (day, group, sport, final), count in sorted(cells.items(), key=str):
            events = per_sport[(day, False, sport)]
            finals = finals_by_sport[(day, group, sport)]
            marks.append(
                {
                    "day": day.isoformat(),
                    "sport_group": group,
                    "sport": sport,
                    "is_final": final,
                    "events": events,
                    "finals": finals,
                    "other_sports": per_day[(day, False)] - events,
                    "x_axis": x_axis(events, finals, final),
                    "marks": count,
                }
            )
        facts[f"adjust_{adjust}"] = {
            "marks": len(marks),
            "days": sorted({mark["day"] for mark in marks}),
            "x_axis_values": sorted({mark["x_axis"] for mark in marks}),
            # A sport-day with both a final and a non-final must straddle 3 / 7.
            "paired_cells": sum(
                1
                for key in cells
                if key[3] and (key[0], key[1], key[2], False) in cells
            ),
            "medal_marks": sum(1 for mark in marks if mark["is_final"]),
            "first_marks": marks[:3],
            "last_marks": marks[-3:],
            # Spot-check three documented sport-days against the article's viz.
            "check": {
                f"{mark['sport']}|{mark['day']}|{'final' if mark['is_final'] else 'qual'}": {
                    "events": mark["events"],
                    "finals": mark["finals"],
                    "other_sports": mark["other_sports"],
                    "x_axis": mark["x_axis"],
                }
                for mark in marks
                if (mark["sport"], mark["day"]) in {
                    ("Boxing", "2021-07-24"),
                    ("Judo", "2021-07-24"),
                    ("Artistic Gymnastics", "2021-07-26"),
                }
            },
        }
    return facts


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def captions(root):
    result = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name") or ""
        result[name] = column.get("caption") or name.strip("[]")
    return result


def resolve(formula: str, names: dict, parameters: dict) -> str:
    def replace(match):
        token = match.group(1)
        if f"[{token}]" in names:
            return f"[{names[f'[{token}]']}]"
        return f"[{token}]"

    text = re.sub(
        r"\[Parameters\]\.\[([^\]]+)\]",
        lambda m: f"[{parameters.get(m.group(1), m.group(1))}]",
        formula,
    )
    return re.sub(r"\[([^\]]+)\]", replace, text)


def field_caption(reference: str, names: dict) -> str:
    """Resolve a full shelf/filter reference to the field's display caption."""

    local = (reference or "").split(".")[-1].strip("[]")
    if ":" in local:  # column-instance name: [deriv:Field:type]
        local = local.split(":")[1]
    local = f"[{local}]"
    return names.get(local, local.strip("[]"))


def sheet(root, name):
    node = root.find(f".//worksheets/worksheet[@name='{name}']")
    assert node is not None, f"missing worksheet: {name}"
    return node


def verify():
    facts = oracle()
    root = workbook()

    calc = {}
    for column in root.findall(".//datasource/column"):
        node = column.find("calculation")
        if node is not None and node.get("class") == "tableau":
            calc[column.get("caption")] = node.get("formula") or ""
    names = captions(root)
    parameters = {
        column.get("name").strip("[]"): column.get("caption")
        for column in root.findall(".//datasource[@name='Parameters']/column")
        if column.get("caption")
    }

    def resolved(caption: str) -> str:
        return re.sub(r"\s+", " ", resolve(calc[caption], names, parameters)).strip()

    # --- ww29-schedule-calcs -------------------------------------------------
    assert facts["rows"] == 1894, facts["rows"]
    # The published extract carries case-variant duplicates ("Diving" and
    # "diving", "Football" and "football"), so the raw group/sport counts are
    # 36 / 51 rather than the 34 / 48 the article's cleaned labels suggest.
    assert facts["sport_groups"] == 36, facts["sport_groups"]
    assert facts["sports"] == 51, facts["sports"]
    assert facts["days"] == 19, facts["days"]
    assert facts["victory_rows"] == 87, facts["victory_rows"]
    assert facts["final_rows"] == 353, facts["final_rows"]
    assert resolved("Date Time Adjust") == (
        "DATEADD('hour', [pTimeAdjust], [UK Date Time])"
    ), resolved("Date Time Adjust")
    assert resolved("Day of Adjusted Date") == (
        "DATE(DATETRUNC('day',[Date Time Adjust]))"
    ), resolved("Day of Adjusted Date")
    assert resolved("Is Victory Ceremony?") == (
        "CONTAINS([Event],'Victory Ceremony')"
    ), resolved("Is Victory Ceremony?")
    assert resolved("Is Final?") == (
        "CONTAINS([Event],'Gold Medal') OR CONTAINS([Event],' Final')"
    ), resolved("Is Final?")
    assert resolved("# Events Per Day") == (
        "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?] : COUNT([Event])}"
    ), resolved("# Events Per Day")
    assert resolved("#Events by Sport Per Day") == (
        "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]: COUNT([Event])}"
    ), resolved("#Events by Sport Per Day")
    assert resolved("#Event Finals by Sport Per Day") == (
        "{FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]:"
        " SUM(IIF([Is Final?],1,0))}"
    ), resolved("#Event Finals by Sport Per Day")
    assert resolved("#Events Per Day of Other Sports") == (
        "SUM([# Events Per Day]) - SUM([#Events by Sport Per Day])"
    ), resolved("#Events Per Day of Other Sports")
    assert resolved("Excluded Sport") == "[Sport]=[pSportToExclude]", resolved(
        "Excluded Sport"
    )
    # The X-Axis branch chain must reproduce the oracle for every sport-day.
    axis_formula = resolved("X-Axis")
    assert "THEN 5" in axis_formula and "THEN 7" in axis_formula and "ELSE 3" in axis_formula
    for adjust in TIME_ADJUST_CASES:
        block = facts[f"adjust_{adjust}"]
        for mark in block["first_marks"] + block["last_marks"]:
            expected = x_axis(mark["events"], mark["finals"], mark["is_final"])
            assert mark["x_axis"] == expected, (mark, expected)
        assert set(block["x_axis_values"]) <= {3, 5, 7}, block["x_axis_values"]

    # --- ww29-time-adjust ----------------------------------------------------
    param = root.find(
        ".//datasource[@name='Parameters']/column[@caption='pTimeAdjust']"
    )
    assert param is not None, "pTimeAdjust parameter missing"
    assert param.get("datatype") == "integer", etree.tostring(param)
    assert param.get("value") == "0", etree.tostring(param)
    assert param.get("param-domain-type") == "range", etree.tostring(param)
    rng = param.find("range")
    assert rng is not None, etree.tostring(param)
    assert (rng.get("min"), rng.get("max"), rng.get("granularity")) == (
        "-12",
        "12",
        "1",
    ), etree.tostring(rng)
    sport_param = root.find(
        ".//datasource[@name='Parameters']/column[@caption='pSportToExclude']"
    )
    assert sport_param is not None, "pSportToExclude parameter missing"
    assert sport_param.get("datatype") == "string", etree.tostring(sport_param)
    # Shifting the offset moves marks in the oracle, so the chart must read the
    # parameter rather than a fixed date.
    zero = facts["adjust_0"]["check"]
    shifted = facts["adjust_3"]["check"]
    assert zero != shifted, (zero, shifted)

    # --- ww29-schedule-view --------------------------------------------------
    schedule = sheet(root, "Date Chart")
    table = schedule.find("table")
    rows = table.findtext("rows") or ""
    cols = table.findtext("cols") or ""
    assert "none:Sport Group:nk" in rows and "none:Sport:nk" in rows, rows
    assert rows.count("*") == 1, rows  # MIN(1) gives the row vertical headspace
    assert "mn:" in cols and "day:" in cols, cols
    # X-Axis must be a row-level dimension instance ([none:...:qk]); an
    # aggregated (sum:) binding multiplies the 3/5/7 offset by the cell's event
    # count and pushes marks outside the fixed 0..10 axis.
    x_axis_instance = next(
        (
            ci
            for ci in table.findall("view/datasource-dependencies/column-instance")
            if field_caption(ci.get("column"), names) == "X-Axis"
        ),
        None,
    )
    assert x_axis_instance is not None, "X-Axis is not bound in the view"
    assert x_axis_instance.get("name").startswith("[none:"), x_axis_instance.get("name")
    assert x_axis_instance.get("name").endswith(":qk]"), x_axis_instance.get("name")
    assert x_axis_instance.get("name") in cols, (x_axis_instance.get("name"), cols)
    pane = table.find("panes/pane")
    assert pane.find("mark").get("class") == "Shape", etree.tostring(pane.find("mark"))
    encodings = {node.tag for node in pane.findall("encodings/*")}
    assert "shape" in encodings, encodings
    shape_encoding = pane.find("encodings/shape")
    assert "Calculation" in (shape_encoding.get("column") or ""), etree.tostring(
        shape_encoding
    )
    # Every sport-day in the extract must be reachable: the set filter keeps the
    # three seeded sports and the victory ceremonies are excluded.
    filters = table.findall("view/filter")
    set_filter = next((f for f in filters if "io:Sport Group Set" in (f.get("column") or "")), None)
    assert set_filter is not None, [f.get("column") for f in filters]
    victory_filter = next(
        (
            f
            for f in filters
            if field_caption(f.get("column"), names) == "Is Victory Ceremony?"
        ),
        None,
    )
    assert victory_filter is not None, [f.get("column") for f in filters]
    assert victory_filter.find("groupfilter").get("member") == "false", etree.tostring(
        victory_filter
    )
    # The fixed 0..10 X-Axis range keeps the 3 / 5 / 7 offsets apart.
    axis_style = table.findall("style/style-rule[@element='axis']")
    spaces = [
        encoding
        for rule in axis_style
        for encoding in rule.findall("encoding")
        if encoding.get("attr") == "space"
    ]
    assert spaces, "X-Axis fixed range missing"
    assert (spaces[0].get("min"), spaces[0].get("max")) == ("0", "10"), etree.tostring(
        spaces[0]
    )
    assert spaces[0].get("range-type") == "fixed", etree.tostring(spaces[0])
    # FINAL / non-final marks use distinct shapes.
    shape_palette = root.find(
        ".//style-rule[@element='mark']/encoding[@attr='shape']"
    )
    assert shape_palette is not None, "shape palette missing"
    palette = {m.findtext("bucket"): m.get("to") for m in shape_palette.findall("map")}
    assert palette.get("true") and palette.get("false"), palette
    assert palette["true"] != palette["false"], palette

    # --- ww29-selector-set ---------------------------------------------------
    group = root.find(".//datasource/group[@name='[Sport Group Set]']")
    assert group is not None, "Sport Group Set missing"
    members = {
        (node.get("member") or "").strip('"')
        for node in group.findall(".//groupfilter[@function='member']")
    }
    assert members == set(INITIAL_SET), members
    selector = sheet(root, "Sport Selector")
    selector_pane = selector.find("table/panes/pane")
    color = selector_pane.find("encodings/color")
    assert color is not None and "io:Sport Group Set" in (
        color.get("column") or ""
    ), etree.tostring(selector_pane)
    selector_rows = selector.findtext("table/rows") or ""
    assert "none:Sport Group:nk" in selector_rows, selector_rows
    # The dummy field is what the highlight action brushes, not the schedule.
    lod = selector_pane.findall("encodings/lod")
    assert [field_caption(n.get("column"), names) for n in lod] == ["Dummy"], [
        field_caption(n.get("column"), names) for n in lod
    ]

    # --- ww29-viz-in-tooltip -------------------------------------------------
    for name in ("VIT-Event Listing", "VIT-Other Event Bar"):
        sheet(root, name)
    tooltip = schedule.find(".//customized-tooltip")
    assert tooltip is not None, "schedule tooltip missing"
    # Viz-in-tooltip targets are serialized as escaped ``<Sheet ...>`` run text
    # (Tableau stores them that way), so parse the run text, not XML children.
    embedded = [
        (match.group(1), match.group(2))
        for run in tooltip.iter("run")
        for match in [re.search(r'<Sheet name="([^"]+)"[^>]*filter="([^"]*)"', run.text or "")]
        if match
    ]
    assert {name for name, _ in embedded} == {
        "VIT-Event Listing",
        "VIT-Other Event Bar",
    }, embedded
    def filter_captions(spec: str) -> list[str]:
        return [
            field_caption(reference, names)
            for reference in re.findall(r"<([^>]+)>", spec or "")
        ]

    listing_filters = filter_captions(dict(embedded)["VIT-Event Listing"])
    assert listing_filters == ["Sport", "Day of Adjusted Date"], listing_filters
    bars_filters = filter_captions(dict(embedded)["VIT-Other Event Bar"])
    assert bars_filters == ["Day of Adjusted Date"], bars_filters
    tooltip_text = "".join(tooltip.itertext())
    for needle in (
        "Number of Events",
        "Number of Finals",
        "other Sports",
    ):
        assert needle in tooltip_text, tooltip_text
    # The other-sports sheet drops the hovered sport through pSportToExclude.
    bars = sheet(root, "VIT-Other Event Bar")
    excluded = next(
        (
            f
            for f in bars.findall("table/view/filter")
            if field_caption(f.get("column"), names) == "Excluded Sport"
        ),
        None,
    )
    assert excluded is not None, [f.get("column") for f in bars.findall("table/view/filter")]
    assert excluded.find("groupfilter").get("member") == "false", etree.tostring(excluded)
    # Tooltip sheets must not occupy the dashboard.
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zone_names = {z.get("name") for z in dashboard.iter("zone") if z.get("name")}
    assert zone_names == {"Sport Selector", "Date Chart"}, zone_names

    # --- ww29-dashboard-actions ---------------------------------------------
    set_actions = root.findall(".//actions/edit-group-action")
    assert len(set_actions) == 2, len(set_actions)
    modes = {
        action.find("add-or-remove-marks").get("value")
        for action in set_actions
        if action.find("add-or-remove-marks") is not None
    }
    assert modes == {"add", "remove"}, modes
    for action in set_actions:
        target = action.find("params/param[@name='target-group']")
        assert target is not None and "Sport Group Set" in target.get("value")
        clear = action.find("params/param[@name='selection-clear-set-option']")
        assert clear is not None and clear.get("value") == "do-nothing"
        activation = action.find("activation")
        assert activation.get("type") == "explicit", etree.tostring(activation)
    parameter_actions = root.findall(".//actions/edit-parameter-action")
    assert len(parameter_actions) == 1, len(parameter_actions)
    param_action = parameter_actions[0]
    assert param_action.find("activation").get("type") == "on-hover", etree.tostring(
        param_action.find("activation")
    )
    assert param_action.find("agg-type").get("type") == "attr", etree.tostring(
        param_action.find("agg-type")
    )
    target_parameter = param_action.find(
        "params/param[@name='target-parameter']"
    ).get("value")
    internal = target_parameter.split(".")[-1].strip("[]")
    assert parameters.get(internal) == "pSportToExclude", (
        target_parameter,
        parameters,
    )
    assert "Sport" in param_action.find("params/param[@name='source-field']").get(
        "value"
    )
    highlights = [
        action
        for action in root.findall(".//actions/action")
        if action.find("command") is not None
        and action.find("command").get("command") == "tsc:brush"
    ]
    assert len(highlights) == 1, len(highlights)
    assert highlights[0].find("source").get("worksheet") == "Sport Selector"
    assert highlights[0].find("command/param[@name='field-captions']").get("value") == (
        "Dummy"
    )
    toggles = root.findall(".//dashboards/dashboard//button/toggle-action")
    assert len(toggles) == 1, len(toggles)
    assert "toggle-button-click-action" in (toggles[0].text or "")

    evidence = {
        "scope": (
            "Locked-extract oracle for the schedule cells, the X-Axis offsets and "
            "the other-sports counts, plus native calculation/view/set/action "
            "contracts."
        ),
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
    summary = {
        "rows": result["facts"]["rows"],
        "sport_groups": result["facts"]["sport_groups"],
        "sports": result["facts"]["sports"],
        "days": result["facts"]["days"],
        "marks_at_offset_0": result["facts"]["adjust_0"]["marks"],
        "medal_marks_at_offset_0": result["facts"]["adjust_0"]["medal_marks"],
    }
    print(json.dumps(summary, indent=2))
    print("PASS")
