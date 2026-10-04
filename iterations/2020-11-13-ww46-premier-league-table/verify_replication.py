"""Full team-match oracle, independently recovered opponents and native blend/TC contracts."""

import csv
import json
from datetime import datetime
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
FACTS = "TEMP_1f3qskj0te9n9v1f3avp71ojhhal.hyper"
HOME = "TEMP_0jwezo318cddv716gtx140t8vf36.hyper"
AWAY = "TEMP_1utfxg4148kl101dumirh0r0cn6d.hyper"
STATES = {
    "default": None,
    "arsenal": "Arsenal",
    "liverpool": "Liverpool",
    "chelsea": "Chelsea",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:

        def read(file):
            with Connection(
                process.endpoint, str(HERE / "inputs" / file)
            ) as connection:
                return connection.execute_list_query(
                    'SELECT * FROM "Extract"."Extract"'
                )

        facts, home, away = read(FACTS), read(HOME), read(AWAY)
    assert len(facts) == 156 and len(home) == len(away) == 78 and home == away
    fixtures = {}
    for d, home_team, away_team, outcome in home:
        day = f"{d.year:04}-{d.month:02}-{d.day:02}"
        assert (day, home_team) not in fixtures and (day, away_team) not in fixtures
        fixtures[day, home_team] = {
            "opposition": away_team,
            "venue": "Home Team",
            "ftr": outcome,
        }
        fixtures[day, away_team] = {
            "opposition": home_team,
            "venue": "Away Team",
            "ftr": outcome,
        }
    teams, outcomes = defaultdict(list), defaultdict(list)
    for d, home_goals, away_goals, ftr, venue, team in facts:
        day = f"{d.year:04}-{d.month:02}-{d.day:02}"
        match = fixtures[day, team]
        assert match["venue"] == venue and match["ftr"] == ftr
        win = venue == "Home Team" and ftr == "H" or venue == "Away Team" and ftr == "A"
        result = "W" if win else "T" if ftr == "D" else "L"
        points = 3 if result == "W" else 1 if result == "T" else 0
        goals, against = (
            (home_goals, away_goals)
            if venue == "Home Team"
            else (away_goals, home_goals)
        )
        row = {
            "date": day,
            "team": team,
            "opposition": match["opposition"],
            "venue": venue,
            "result": result,
            "points": points,
            "goals": goals,
            "against": against,
        }
        teams[team].append(row)
        outcomes[day, frozenset((team, match["opposition"]))].append(row)
    assert len(outcomes) == 78 and all(len(r) == 2 for r in outcomes.values())
    for rows in outcomes.values():
        a, b = rows
        assert a["goals"] == b["against"] and a["against"] == b["goals"]
        assert (a["result"], b["result"]) in {("W", "L"), ("L", "W"), ("T", "T")}
    summary = {}
    for team, rows in teams.items():
        rows.sort(key=lambda r: r["date"])
        count = Counter(r["result"] for r in rows)
        for index, row in enumerate(rows, 1):
            row["index"] = index
            row["size"] = len(rows)
            row["index_to_plot"] = index - (len(rows) - 5)
        summary[team] = {
            "Matches Played": len(rows),
            "Wins": count["W"],
            "Ties": count["T"],
            "Losses": count["L"],
            "Total Points": sum(r["points"] for r in rows),
            "Points by result": {
                result: sum(r["points"] for r in rows if r["result"] == result)
                for result in ("W", "T", "L")
            },
            "matches": rows,
            "last5": rows[-5:],
        }
        assert len(rows) in (7, 8) and len(summary[team]["last5"]) == 5
        assert [r["index_to_plot"] for r in summary[team]["last5"]] == [1, 2, 3, 4, 5]
    assert (
        len(summary) == 20 and sum(s["Matches Played"] for s in summary.values()) == 156
    )
    ranked = sorted(summary, key=lambda team: (-summary[team]["Total Points"], team))
    return {
        "facts": len(facts),
        "fixtures": 78,
        "teams": summary,
        "ranked": ranked,
        "last5_marks": 100,
        "scope": "Every 156 pivoted fact and 78 unique original fixture; all team metrics, results, chronological indexes, blended opponents and score orientations independently recomputed.",
    }


def native(root):
    sources = [
        d
        for d in root.findall("datasources/datasource")
        if d.get("name") != "Parameters"
    ]
    assert len(sources) == 3
    primary = sources[0]
    captions = {
        c.get("caption", c.get("name", "").strip("[]")): c
        for c in primary.findall("column")
    }
    for caption, required in [
        ("Matches Played", "COUNT([Date])"),
        ("Wins", "'W'"),
        ("Ties", "'T'"),
        ("Losses", "'L'"),
    ]:
        formula = captions[caption].find("calculation").get("formula")
        assert "FIXED" in formula and required in formula
    assert "INDEX()" in captions["Index"].find("calculation").get("formula")
    assert "SIZE()" in captions["Size"].find("calculation").get("formula")
    for caption in ("Home Opposition", "Away Opposition"):
        column = captions[caption]
        assert column.get("datatype") == "string" and column.get("type") == "nominal"
        assert column.find("calculation").get("formula").startswith("ATTR([federated.")
    chart = root.find("worksheets/worksheet[@name='Chart']")
    table = root.find("worksheets/worksheet[@name='Table']")
    bar = root.find("worksheets/worksheet[@name='Bar']")
    assert chart.find("table/panes/pane/mark").get("class") == "Circle"
    assert chart.find("table/panes/pane").get("x-axis-name") is not None
    assert chart.find("table/panes/pane/encodings/color") is not None
    chart_style = chart.find("table/panes/pane/style")
    for element, attributes in {
        "cell": {"text-align": "center", "vertical-align": "center"},
        "datalabel": {"color-mode": "match", "font-size": "8", "font-weight": "bold"},
    }.items():
        actual = {
            n.get("attr"): n.get("value")
            for n in chart_style.findall(f"style-rule[@element='{element}']/format")
        }
        assert attributes.items() <= actual.items(), (element, actual)
    date_detail = chart.find("table/panes/pane/encodings/lod").get("column")
    assert date_detail.endswith(".[none:Date:qk]"), (
        "Match detail must retain exact dates, not default Month grain"
    )
    assert (
        chart.find("table/panes/pane/mark-sizing").get("mark-sizing-setting")
        == "marks-scaling-off"
    )
    assert len(chart.findall("table/view/datasources/datasource")) == 3
    assert len(chart.findall("table/view/datasource-dependencies")) == 3
    primary_dependencies = next(
        d
        for d in chart.findall("table/view/datasource-dependencies")
        if d.get("datasource") == primary.get("name")
    )
    physical = {
        c.get("name")
        for c in primary_dependencies.findall("column")
        if c.find("calculation") is None
    }
    assert physical == {
        "[Date]",
        "[FTHG]",
        "[FTAG]",
        "[FTR]",
        "[Pivot Field Names]",
        "[Pivot Field Values]",
    }, physical
    assert len(chart.findall("table/view/filter")) == 1
    links = chart.findall(
        "table/view/datasource-dependencies/column-instance[@derivation='Attribute']"
    )
    assert len(links) >= 2
    local = captions["Last 5 matches only"].get("name")
    filter_column = chart.find("table/view/filter").get("column")
    ci = next(
        c
        for c in chart.findall("table/view/datasource-dependencies/column-instance")
        if c.get("column") == local and filter_column.endswith("." + c.get("name"))
    )
    assert ci.findall("table-calc")
    for caption in ("Index", "Size"):
        calc_id = captions[caption].get("name")
        addressed = chart.xpath(
            "table/view/datasource-dependencies/column-instance/table-calc[@ordering-type='Field']"
        )
        assert any(n.get("field", "").endswith("." + calc_id) for n in addressed)
    for worksheet in (bar, chart):
        sort = worksheet.find("table/view/computed-sort")
        assert sort is not None and sort.get("direction") == "DESC"
    assert {p.find("mark").get("class") for p in bar.findall("table/panes/pane")} == {
        "Bar",
        "GanttBar",
    }
    bar_panes = bar.findall("table/panes/pane")
    assert all(p.get("x-axis-name") for p in bar_panes)
    assert bar_panes[0].get("x-axis-name") != bar_panes[1].get("x-axis-name")
    assert bar_panes[0].find("encodings/color") is not None
    assert bar_panes[1].find("encodings/text") is not None
    assert (
        bar_panes[1]
        .find("style/style-rule[@element='mark']/format[@attr='mark-color']")
        .get("value")
        == "#00000000"
    )
    assert (
        bar.find("table/style/style-rule[@element='axis']/encoding[@attr='space']")
        is not None
    )
    assert (
        table.find("table/panes/pane/encodings/text")
        .get("column")
        .endswith(".[Multiple Values]")
    )
    assert len(table.findall("table/view/filter/groupfilter/groupfilter")) == 4
    assert not root.findall("actions/action"), "Source has no dashboard actions."
    dashboard = root.find("dashboards/dashboard")
    assert (
        dashboard.find("size").get("maxwidth") == "800"
        and dashboard.find("size").get("maxheight") == "735"
    )
    for sheet, x, y, w, h in [
        ("Table", 8, 40, 403, 622),
        ("Bar", 411, 95, 185, 567),
        ("Chart", 596, 95, 196, 567),
    ]:
        zone = next(
            z for z in dashboard.findall("zones//zone") if z.get("name") == sheet
        )
        expected = (
            round(x * 125),
            round(y * 100000 / 735),
            round(w * 125),
            round(h * 100000 / 735),
        )
        assert tuple(int(zone.get(k)) for k in ("x", "y", "w", "h")) == expected
    return ["ww46-native-contracts"]


def cloud(data, workbook_hash):
    # ww46-cloud-states: strict measure/date/header coverage adapted after first native export.
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return {"status": "pending"}
    report = json.loads(path.read_text(encoding="utf-8"))
    provenance = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
    )
    assert report["source_hashes"] == {
        "author": provenance["export_sha256"],
        "replica": workbook_hash,
    }
    checked = []
    assert {s["name"] for s in report["states"]} == set(STATES)
    for state in report["states"]:
        assert state["name"] in STATES
        for item in state["views"].values():
            assert digest(HERE / item["path"]) == item["sha256"]
        for item in state["data"]:
            file = HERE / item["path"]
            assert digest(file) == item["sha256"]
            rows = list(
                csv.DictReader(file.read_text(encoding="utf-8-sig").splitlines())
            )
            assert rows, (file, "Empty main worksheet")
            selected = STATES[state["name"]]
            teams = {selected} if selected else set(data["teams"])
            assert {r["Team"] for r in rows} == teams, (file, "Incomplete teams")
            if item["view"] == "Table":
                actual = {
                    (r["Team"], r["Measure Names"]): float(r["Measure Values"])
                    for r in rows
                }
                expected = {
                    (team, metric): data["teams"][team][metric]
                    for team in teams
                    for metric in ("Matches Played", "Wins", "Ties", "Losses")
                }
                assert len(actual) == len(rows) and actual == expected, (
                    file,
                    actual,
                    expected,
                )
            elif item["view"] == "Bar":
                actual = {}
                for row in rows:
                    team, result = row["Team"], row["Win-Loss-Draw"]
                    key = (team, result)
                    assert key not in actual
                    target = data["teams"][team]
                    points = (
                        target["Points by result"][result]
                        if result
                        else target["Total Points"]
                    )
                    assert float(row["Points"]) == points, (file, row, points)
                    if not result:
                        assert float(row["Total Points"]) == target["Total Points"]
                    actual[key] = points
                expected = {
                    (team, result)
                    for team in teams
                    for result in {r["result"] for r in data["teams"][team]["matches"]}
                    | {""}
                }
                assert set(actual) == expected, (file, "Incomplete result segments")
            elif item["view"] == "Chart":
                expected = {
                    (team, row["date"]): row
                    for team in teams
                    for row in data["teams"][team]["last5"]
                }
                actual = set()
                for row in rows:
                    day = datetime.strptime(row["Date"], "%m/%d/%Y").date().isoformat()
                    key = row["Team"], day
                    assert key not in actual and key in expected, (file, key)
                    target = expected[key]
                    assert (
                        row["Win-Loss-Draw"]
                        == row["Colour WLD Circle"]
                        == target["result"]
                    )
                    assert row["Opposition"] == target["opposition"], (
                        file,
                        row,
                        target,
                    )
                    for column, metric in (
                        ("Index To Plot", "index_to_plot"),
                        ("Points", "points"),
                        ("Team Score", "goals"),
                        ("Opposition Score", "against"),
                    ):
                        assert float(row[column]) == target[metric], (
                            file,
                            column,
                            row,
                            target,
                        )
                    actual.add(key)
                assert actual == set(expected), (
                    file,
                    "Missing chronological last-five matches",
                )
            else:
                raise AssertionError((file, item["view"]))
            checked.append(
                {
                    "file": item["path"],
                    "rows": len(rows),
                    "scope": "Full expected team membership and all four standings metrics, all present stacked result segments and totals, or complete last-five dates/indexes/results/opponents/scores",
                }
            )
    assert len(checked) == 24
    return {
        "status": "passed",
        "checks": checked,
        "browser_interaction_executed": False,
    }


def verify():
    workbook = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    with ZipFile(workbook) as archive:
        root = etree.fromstring(
            archive.read(next(n for n in archive.namelist() if n.endswith(".twb")))
        )
        for record in lock["extracted_data"]:
            assert digest(HERE / record["file"]) == record["sha256"]
            member = next(
                n
                for n in archive.namelist()
                if Path(n).name == Path(record["file"]).name
            )
            assert sha256(archive.read(member)).hexdigest() == record["sha256"]
    data = oracle()
    native_checks = native(root)
    workbook_hash = digest(workbook)
    result = {
        "workbook_sha256": workbook_hash,
        "acceptance_checks": ["ww46-raw-data", *native_checks],
        "oracle": data,
        "cloud": cloud(data, workbook_hash),
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        "PASS WW46 156 team matches / 78 fixtures / 20 standings / 100 last5 with opponents and score orientation; Cloud=",
        result["cloud"]["status"],
    )


if __name__ == "__main__":
    verify()
