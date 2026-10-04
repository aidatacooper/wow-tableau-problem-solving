"""Verify complete NFL facts, drilldown groups, pagination and action contracts."""

import csv
import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import unquote
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "pPage No": 1,
    "pRows Per Page": 10,
    "pHeader MeasureNames ": "Measure1",
    "pHeader Position": "FB",
    "pLevel": 2,
    "pSelected Player ID": 10638,
}
MEASURES = {
    "Measure1": "Carries",
    "Measure2": "Yards",
    "Measure3": "Avg YPC",
    "Measure4": "TDs",
}


def oracle():
    p = next((HERE / "inputs").glob("*.hyper"))
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(p)) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "season","player_id","position","yards","touchdown" FROM "Extract"."Extract"'
        )
    assert len(rows) == 40736
    facts = defaultdict(list)
    seasons = defaultdict(list)
    for season, player, position, yards, td in rows:
        assert player is not None
        facts[int(player)].append((yards, td))
        seasons[(int(player), int(season))].append((yards, td))

    def stats(vals):
        total = sum(v[0] for v in vals if v[0] is not None)
        return {
            "Carries": len(vals),
            "Yards": total,
            "Avg YPC": total / len(vals),
            "TDs": sum(v[1] for v in vals if v[1] is not None),
        }

    assert len(facts) == 556
    return {
        "raw_rows": len(rows),
        "players": {str(p): stats(v) for p, v in facts.items()},
        "seasons": {f"{p}/{s}": stats(v) for (p, s), v in seasons.items()},
        "total_pages": 56,
        "scope": "Every40736 locked rushing play, all556 players and all player/season groups. Every REST page value checked directly against these full groups; CSV page coverage is bounded to requested states.",
    }


def number(text, expected):
    clean = text.replace(",", "").strip()
    assert clean and "#" not in clean
    actual = float(clean)
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    tol = 0.501 * 10 ** (-decimals) + 1e-9
    assert abs(actual - expected) <= tol, (text, actual, expected, tol)


def expected_page(data, params):
    values = {**DEFAULTS, **params}
    page = int(values["pPage No"])
    count = int(values["pRows Per Page"])
    chosen = MEASURES[values["pHeader MeasureNames "]]
    ascending = values["pHeader Position"] == "P"
    players = sorted(
        data["players"],
        key=lambda p: (
            data["players"][p][chosen] if ascending else -data["players"][p][chosen],
            int(p),
        ),
    )
    # Native Columns INDEX partitions the expanded arrow/DD-Level separately:
    # the selected player's season rows coexist with a full page of collapsed
    # players. Derive both partitions from raw facts, never from exported values.
    if int(values["pLevel"]) == 1:
        selected = str(values["pSelected Player ID"])
        collapsed = [player for player in players if player != selected]
        return collapsed[(page - 1) * count : page * count] + [selected], values
    return players[(page - 1) * count : page * count], values


def cloud(data, digest):
    p = HERE / "evidence/cloud-verification.json"
    if not p.exists():
        return []
    report = json.loads(p.read_text(encoding="utf8"))
    assert report["source_hashes"]["replica"] == digest
    proof = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf8")
    )
    assert report["source_hashes"]["author"] == proof["export_sha256"]
    checks = []
    for state in report["states"]:
        expected, params = expected_page(data, state.get("parameters", {}))
        for image in state["views"].values():
            assert (
                sha256((HERE / image["path"]).read_bytes()).hexdigest()
                == image["sha256"]
            )
        for item in state["data"]:
            p = HERE / item["path"]
            assert sha256(p.read_bytes()).hexdigest() == item["sha256"]
            rows = [
                {k.strip(): v for k, v in r.items()}
                for r in csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines())
            ]
            assert rows, (p, "Empty CSV")
            if item["view"] == "Table":
                seen = set()
                groups = set()
                for row in rows:
                    player = (
                        row.get(
                            "Player Id",
                            row.get("Display Player ID", row.get("player_id", "")),
                        )
                        .replace(",", "")
                        .strip()
                    )
                    assert player in data["players"], (p, row)
                    season = row.get("Season to Display", "").strip()
                    key = f"{player}/{season}" if season else player
                    metric = data["seasons"][key] if season else data["players"][player]
                    if "Measure Names" in row:
                        label = row["Measure Names"].strip()
                        name = "Yards" if label in {"yards", "Yards"} else label
                        assert name in metric
                        number(row["Measure Values"], metric[name])
                        seen.add((player, season, name))
                    else:
                        for name in ["Carries", "Yards", "Avg YPC", "TDs"]:
                            field = next(
                                (k for k in row if k.lower() == name.lower()), None
                            )
                            assert field is not None, (p, row, name)
                            number(row[field], metric[name])
                            seen.add((player, season, name))
                    if season:
                        assert int(params["pLevel"]) == 1 and player == str(
                            params["pSelected Player ID"]
                        )
                    groups.add((player, season))
                assert all(
                    sum(1 for p, s, m in seen if (p, s) == group) == 4
                    for group in groups
                )
                actual_players = {p for p, s in groups}
                assert actual_players == set(expected), (
                    p,
                    actual_players,
                    set(expected),
                )
                expected_groups = {(player, "") for player in expected}
                if int(params["pLevel"]) == 1:
                    selected = str(params["pSelected Player ID"])
                    expected_groups.remove((selected, ""))
                    expected_groups.update(
                        (selected, key.split("/")[1])
                        for key in data["seasons"]
                        if key.startswith(selected + "/")
                    )
                assert groups == expected_groups, (p, groups, expected_groups)
                checks.append(
                    {
                        "state": state["name"],
                        "role": item["role"],
                        "view": "Table",
                        "groups": len(groups),
                        "metric_values": len(seen),
                        "scope": "All four metrics for every player/season group on the requested page; ties independently checked against the full roster.",
                    }
                )
            else:
                if item["view"] == "Header":
                    header_marks = set()
                    for row in rows:
                        measure = row.get("Measure Names", "")
                        if not measure:
                            active = [
                                f"Measure{i}"
                                for i in range(1, 5)
                                if row.get(f"Measure{i}", "").strip()
                            ]
                            assert len(active) == 1, (p, row)
                            measure = active[0]
                        position = row.get("position", row.get("Position"))
                        assert position in {"FB", "H", "P"}
                        index = int(measure[-1])
                        number(
                            row.get("Min. First Page No", row.get("First Page No", "")),
                            1,
                        )
                        selected = (
                            measure == params["pHeader MeasureNames "]
                            and position == params["pHeader Position"]
                        )
                        assert (
                            row[f"Measure{index} | tf"].lower() == str(selected).lower()
                        )
                        if item["role"] == "replica":
                            label = row[f"Header Label{index}"]
                            expected_label = (
                                MEASURES[measure]
                                if position == "H"
                                else ("\u25bc" if position == "FB" else "\u25b2")
                            )
                            assert label == expected_label, (p, label, expected_label)
                        elif position != "H":
                            assert row["Tooltip - Sort"] == (
                                "Sort Descending"
                                if position == "FB"
                                else "Sort Ascending"
                            )
                        header_marks.add((measure, position))
                    assert header_marks == {
                        (m, pos) for m in MEASURES for pos in {"FB", "H", "P"}
                    }
                else:
                    page = int(params["pPage No"])
                    field = {
                        "Curr Page": "Current Page No",
                        "Prev Page": "Page No Minus 1",
                        "Next Page": "Page No Plus 1",
                    }[item["view"]]
                    target = (
                        page
                        if item["view"] == "Curr Page"
                        else (
                            max(1, page - 1)
                            if item["view"] == "Prev Page"
                            else min(data["total_pages"], page + 1)
                        )
                    )
                    for row in rows:
                        number(row.get("Min. " + field, row.get(field, "")), target)
                        if item["view"] == "Curr Page":
                            number(
                                row.get("Min. Total Pages", row.get("Total Pages", "")),
                                data["total_pages"],
                            )
                        elif item["role"] == "replica":
                            glyph = (
                                "Previous Page Glyph"
                                if item["view"] == "Prev Page"
                                else "Next Page Glyph"
                            )
                            assert row[glyph] == (
                                "\u25c0" if item["view"] == "Prev Page" else "\u25b6"
                            )
                checks.append(
                    {
                        "state": state["name"],
                        "role": item["role"],
                        "view": item["view"],
                        "rows": len(rows),
                        "scope": "Complete four-measure/three-direction header domain and binding, reset-to-1 source, page/total/clamped navigation targets and replica glyphs independently verified.",
                    }
                )
    return checks


def verify():
    data = oracle()
    p = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(p.read_bytes()).hexdigest()
    with ZipFile(p) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
        for f in lock["extracted_data"]:
            path = HERE / f["file"]
            assert sha256(path.read_bytes()).hexdigest() == f["sha256"]
            assert (
                sha256(
                    z.read(next(n for n in z.namelist() if n.endswith(path.name)))
                ).hexdigest()
                == f["sha256"]
            )
    captions = {
        c.get("caption"): c
        for c in root.xpath("/workbook/datasources/datasource/column")
    }
    for caption in ["DD Level", "Season to Display", "Page No Plus 1"]:
        formula = captions[caption].find("calculation").get("formula")
        assert "[Max Level]" not in formula and "[Total Pages]" not in formula
    arrow = captions["Player ID Arrow"].find("calculation").get("formula")
    assert "\u25bc" in arrow and "\u25b6" in arrow
    assert root.xpath("//worksheet[@name='Header']//pane[@x-axis-name]")
    assert not root.xpath("//worksheet[@name='Header']//pane[@y-axis-name]")
    actions = root.xpath("/workbook/actions/edit-parameter-action")
    assert (
        len(actions) == 7
        and len({a.get("name") for a in root.xpath("/workbook/actions/*[@name]")}) == 10
    )
    names = {a.get("caption") for a in actions}
    assert names == {
        "Selected Player",
        "Set Level",
        "Set Sort Direction",
        "Set Sort Measure",
        "Reset Page",
        "Page -",
        "Page +",
    }
    sort_action = next(a for a in actions if a.get("caption") == "Set Sort Measure")
    assert sort_action.xpath(
        "params/param[@name='source-field' and contains(@value,':Measure Names')]"
    )
    for action in actions:
        assert action.find("activation").get("type") == "on-select"
        if action.get("caption") in {"Reset Page", "Page -", "Page +"}:
            assert (
                "[min:" in action.xpath("params/param[@name='source-field']/@value")[0]
            )
    expected_actions = {
        "Selected Player": ("Table", "Display Player ID", "pSelected Player ID"),
        "Set Level": ("Table", "DD Level", "pLevel"),
        "Set Sort Direction": ("Header", "position", "pHeader Position"),
        "Set Sort Measure": ("Header", "Measure Names", "pHeader MeasureNames "),
        "Reset Page": ("Header", "First Page No", "pPage No"),
        "Page -": ("Prev Page", "Page No Minus 1", "pPage No"),
        "Page +": ("Next Page", "Page No Plus 1", "pPage No"),
    }
    parameters = {
        c.get("name"): c.get("caption")
        for c in root.xpath(
            "/workbook/datasources/datasource[@name='Parameters']/column"
        )
    }
    for action in actions:
        sheet, field, parameter = expected_actions[action.get("caption")]
        assert action.find("source").get("worksheet") == sheet
        assert action.find("agg-type").get("type") == "attr"
        target = action.xpath("params/param[@name='target-parameter']/@value")[0]
        assert parameters[target.split(".")[-1]] == parameter
        source_ref = action.xpath("params/param[@name='source-field']/@value")[0]
        if field != "Measure Names":
            instance = source_ref.split(".")[-1]
            ci = root.xpath(
                "//worksheet[@name=$sheet]//column-instance[@name=$name]",
                sheet=sheet,
                name=instance,
            )
            assert len(ci) == 1
            column = ci[0].get("column")
            definitions = root.xpath(
                "//worksheet[@name=$sheet]//datasource-dependencies/column[@name=$name]",
                sheet=sheet,
                name=column,
            )
            assert len(definitions) == 1
            assert definitions[0].get("caption", column.strip("[]")) == field
        assert not action.xpath("params/param[@name='clear-value']"), (
            "Native parameter actions preserve current values on clear"
        )
    deselect = root.xpath("/workbook/actions/action")
    assert len(deselect) == 3
    for action in deselect:
        sheet = action.find("source").get("worksheet")
        assert sheet in {"Header", "Prev Page", "Next Page"}
        assert action.find("activation").get("auto-clear") == "true"
        assert action.xpath("command/param[@name='target']/@value") == [sheet]
        expression = unquote(action.find("link").get("expression"))
        assert captions["true"].get("name") in expression
        assert captions["false"].get("name") in expression

    assert root.xpath("//worksheet[@name='Table']//computed-sort[@direction='DESC']")
    assert not root.xpath("//worksheet[@name='Table']//shelf-sort-v2")
    assert root.xpath("//worksheet[@name='Table']//mark[@class='Automatic']")
    assert not root.xpath(
        "//worksheet[@name='Table']//pane/style/style-rule[@element='cell']/format[@attr='text-align' and @value='right']"
    )
    assert root.xpath(
        "//worksheet[@name='Table']//format[@attr='band-level' and @scope='rows' and @value='3']"
    )
    assert len(root.xpath("//worksheet[@name='Header']//panes/pane")) == 4
    assert root.xpath("//worksheet[@name='Table']//column-instance/table-calc[@field]")
    assert root.xpath("//worksheet[@name='Table']//filter/groupfilter[@member='true']")
    checks = cloud(data, digest)
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "acceptance_ids": [
            "ww40-full-play-oracle",
            "ww40-drilldown-pagination",
            "ww40-custom-header-actions",
            "ww40-cloud-pages",
        ],
        "oracle": data,
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf8"
    )
    print(
        "PASS WW40 full40736 plays /556 players/native action contracts; Cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    verify()
