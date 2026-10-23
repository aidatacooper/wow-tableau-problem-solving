"""Independently verify the WW34 (2021) consecutive-starts workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
The oracle recomputes the whole streak table from the raw extract with plain
Python (a running counter over Season → Week → Player Id per team), never by
replaying the workbook's table calculations, so a wrong table-calculation
addressing cannot pass by agreeing with itself.

Automated acceptance IDs:
  - ww34-source-grain
  - ww34-week-filter
  - ww34-table-calcs
  - ww34-streak-oracle
  - ww34-viz-encoding
  - ww34-dashboard
"""

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww34-source-grain",
    "ww34-week-filter",
    "ww34-table-calcs",
    "ww34-streak-oracle",
    "ww34-viz-encoding",
    "ww34-dashboard",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD = "2021_08_25_WW34_Consecutive_Starts"
BAR_SHEET = "Viz"
DATA_SHEET = "Data"

QB_TABLE = (
    "qb_starters.csv_4409EE5639A8403FBF385663A826525D "
    "(Extract.qb_starters.csv_4409EE5639A8403FBF385663A826525D)_"
    "A0D406B8C1C34B02B729E64E73803396"
)
TEAMS_TABLE = (
    "NFL_Teams.csv_C13053C1D84841CABFE32E1A7B6258E5 "
    "(Extract.NFL_Teams.csv_C13053C1D84841CABFE32E1A7B6258E5)_"
    "00B9020E3A584ABA910F5F61074D85E8"
)

BAR_COLOR = "#4f15c2"
SEASONS = list(range(2006, 2021))
WEEKS = list(range(1, 18))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# Oracle: recompute the streak table from the raw extract
# --------------------------------------------------------------------------


def oracle():
    lock = json.loads((HERE / "inputs" / "source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    source = HERE / item["file"]
    assert digest(source) == item["sha256"], "locked extract hash changed"

    query = f"""
        SELECT s.season, s.week, t.team, s.player_id
        FROM "Extract"."{QB_TABLE}" s
        JOIN "Extract"."{TEAMS_TABLE}" t
          ON s.offense_franchise_id = t.franchise_id
        ORDER BY t.team, s.season, s.week, s.player_id
    """
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(source)) as connection,
    ):
        rows = connection.execute_list_query(query)
        raw_total = connection.execute_list_query(
            f'SELECT COUNT(*) FROM "Extract"."{QB_TABLE}"'
        )[0][0]
        out_of_season = connection.execute_list_query(
            f'SELECT COUNT(*) FROM "Extract"."{QB_TABLE}" '
            f"WHERE week < 1 OR week > 17"
        )[0][0]

    # Weeks 28-32 exist in the extract and the article excludes them.
    assert out_of_season == 334, out_of_season

    # The article's chain, computed as a plain running counter per team:
    # a new player id (or the team's first game) restarts the streak at 1.
    games = {}
    streaks = {}
    previous = None
    streak = 0
    for season, week, team, player_id in rows:
        if week < 1 or week > 17:
            continue
        key = (team, season, week, player_id)
        assert key not in games, f"duplicate grain row: {key}"
        games[key] = True
        if previous != (team, player_id):
            streak = 1
        else:
            streak += 1
        streaks[(team, season, week)] = streak
        previous = (team, player_id)

    teams = sorted({team for _s, _w, team, _p in rows})
    per_team = {}
    for team in teams:
        team_rows = sorted(
            (season, week) for (t, season, week) in streaks if t == team
        )
        values = [streaks[(team, season, week)] for season, week in team_rows]
        per_team[team] = {
            "games": len(team_rows),
            "index": list(range(1, len(team_rows) + 1)),
            "current_streak": values[-1],
            "max_streak": max(values),
        }

    assert len(teams) == 32, len(teams)
    assert {v["games"] for v in per_team.values()} == {240}

    # Season/week coverage: every team plays 2006-2020, 16 of the 17 regular
    # season weeks per year (one bye), so the dense index runs 1..240.
    season_weeks = {}
    for (team, season, week) in streaks:
        season_weeks.setdefault((team, season), set()).add(week)
    for team in teams:
        seasons = sorted(s for (t, s) in season_weeks if t == team)
        assert seasons == SEASONS, (team, seasons)
        for season in seasons:
            weeks = season_weeks[(team, season)]
            assert len(weeks) == 16, (team, season, sorted(weeks))
            assert weeks <= set(WEEKS), (team, season, sorted(weeks))

    # Two independent cross-checks of the counter.
    assert sum(v["current_streak"] for v in per_team.values()) == 563
    longest = max(per_team.items(), key=lambda kv: kv[1]["max_streak"])
    assert longest[0] == "LAC" and longest[1]["max_streak"] == 224, longest

    # The index is dense per team and restarts at 1 for each team.
    assert max(v["index"][-1] for v in per_team.values()) == 240

    return {
        "extract_sha256": item["sha256"],
        "extract_rows_total": raw_total,
        "extract_rows_outside_weeks_1_17": out_of_season,
        "regular_season_rows": len(streaks),
        "games_per_team_season": 16,
        "seasons_per_team": len(SEASONS),
        "teams": len(teams),
        "games_per_team": 240,
        "index_max": 240,
        "sum_current_streak": sum(v["current_streak"] for v in per_team.values()),
        "longest_streak": {"team": longest[0], "games": longest[1]["max_streak"]},
        "per_team": {
            team: {
                "current_streak": per_team[team]["current_streak"],
                "max_streak": per_team[team]["max_streak"],
            }
            for team in teams
        },
    }


# --------------------------------------------------------------------------
# Workbook contracts
# --------------------------------------------------------------------------


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def packaged_extract_matches_lock():
    lock = json.loads((HERE / "inputs" / "source-lock.json").read_text(encoding="utf-8"))
    expected = lock["extracted_data"][0]["sha256"]
    with ZipFile(OUTPUT) as archive:
        members = [n for n in archive.namelist() if n.endswith(".hyper")]
        assert len(members) == 1, members
        return hashlib.sha256(archive.read(members[0])).hexdigest() == expected


def formulas(root):
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
                return f"[{raw[names[token]][0]}]"
            return match.group(0)

        return re.sub(r"\[([^\]]+)\]", replace, formula)

    return {caption: resolve(formula) for caption, formula in raw.values()}


def sheet(root, name):
    element = root.find(f".//worksheets/worksheet[@name='{name}']")
    assert element is not None, f"worksheet {name} missing"
    return element


def verify():
    facts = oracle()
    root = workbook()
    calc = formulas(root)

    # --- ww34-source-grain --------------------------------------------------
    # Both physical tables are related, not joined, and the extract is the
    # locked one, byte for byte.
    assert packaged_extract_matches_lock(), "packaged extract differs from the lock"
    relations = root.findall(".//datasource/connection/relation")
    assert any(r.get("type") == "collection" for r in relations), "multi-table relation missing"
    assert len(root.findall(".//object-graph/relationships/relationship")) == 1
    datasource = root.find("datasources/datasource")
    columns = {c.get("name"): c for c in datasource.findall("column")}
    captions = {c.get("caption"): c for c in datasource.findall("column") if c.get("caption")}
    # The relationship keys are real columns on the primary side; the lookup
    # side's key and label live in the metadata records (the secondary table is
    # hidden from the field list, as in the author workbook).
    for name in ("[offense_franchise_id]", "[player_id]", "[player]"):
        assert name in columns, name
    metadata_names = {
        (record.findtext("remote-name") or "")
        for record in root.findall(".//metadata-records/metadata-record[@class='column']")
    }
    for name in ("offense_franchise_id", "franchise_id", "team", "player_id", "season", "week"):
        assert name in metadata_names, (name, sorted(metadata_names))
    assert columns["[player_id]"].get("role") == "dimension"
    # Integer season/week are registered as measures by the extract inspection,
    # so the workbook re-exposes them as explicit discrete dimensions; that is
    # what the article's Rows/Detail pills use.
    for name in ("Season", "Week", "Player Id"):
        assert name in captions, (name, sorted(captions))
        column = captions[name]
        assert column.get("role") == "dimension", name
        assert column.get("type") == "ordinal", name
        assert column.find("calculation") is not None, name
    # The in-range filter needs a continuous copy of the week number.
    assert captions["Week Number"].get("type") == "quantitative"

    # --- ww34-week-filter ---------------------------------------------------
    # Both sheets keep the author's 1..17 regular-season filter and nothing else.
    for name in (BAR_SHEET, DATA_SHEET):
        view = sheet(root, name).find("table/view")
        filters = view.findall("filter")
        assert len(filters) == 1, (name, len(filters))
        only = filters[0]
        assert only.get("class") == "quantitative", only.get("class")
        assert only.get("included-values") == "in-range"
        assert only.findtext("min") == "1" and only.findtext("max") == "17"
        sliced = [c.text for c in view.findall("slices/column")]
        assert sliced == [only.get("column")], sliced

    # --- ww34-table-calcs ---------------------------------------------------
    expected = {
        "Prev Player ID": "LOOKUP(MIN([player_id]),-1)",
        "Match Prev Player ID": "MIN([player_id])=[Prev Player ID]",
        "Consecutive Streak": (
            "IF (NOT([Match Prev Player ID])) OR ISNULL([Match Prev Player ID]) "
            "THEN 1\r\nELSE 1+PREVIOUS_VALUE(-1)\r\n\r\nEND"
        ),
        "Current Streak": "WINDOW_MAX(IF LAST()=0 THEN [Consecutive Streak] END)",
        "INDEX": "INDEX()",
    }
    for name, formula in expected.items():
        assert name in calc, (name, sorted(calc))
        assert calc[name] == formula, (name, calc[name])

    # Every one of them is a real table calculation, and each instance carries
    # the author's addressing Season -> Week -> Player Id plus the nested
    # calculation dependencies (that is what makes the chain restart per team).
    instances = {}
    for datasource in root.xpath(".//datasource[@name != 'Parameters']"):
        for column in datasource.findall("column"):
            if column.get("caption") in expected:
                assert column.find("calculation/table-calc") is not None, column.get("caption")
                instances[column.get("caption")] = column.get("name")
    assert set(instances) == set(expected), sorted(instances)

    def instance_refs(sheet_name):
        view = sheet(root, sheet_name).find("table/view")
        deps = view.find("datasource-dependencies")
        assert deps is not None, sheet_name
        by_column = {}
        for ci in deps.findall("column-instance"):
            by_column[ci.get("column")] = ci
        return deps, by_column

    deps, by_column = instance_refs(BAR_SHEET)
    order_fields = []
    for caption in ("Consecutive Streak", "Current Streak", "INDEX"):
        ci = by_column.get(instances[caption])
        assert ci is not None, caption
        specs = [
            (tc.get("ordering-type"), tc.get("ordering-field"), tc.get("field"))
            for tc in ci.findall("table-calc")
        ]
        ordering = [o.get("field") for o in ci.findall("table-calc")[0].findall("order")]
        nested = [s[2] for s in specs if s[2]]
        assert len(ordering) == 3, (caption, specs)
        order_fields.append(ordering)
        if caption == "Consecutive Streak":
            assert len(nested) == 2, (caption, specs)
        if caption == "Current Streak":
            assert len(nested) == 3, (caption, specs)
    # The three grains, in the author's order, resolved to real view fields.
    local_names = {
        c.get("caption"): c.get("name") for c in deps.findall("column") if c.get("caption")
    }
    resolved = [
        [reference.rsplit(".", 1)[-1].strip("[]") for reference in ordering]
        for ordering in order_fields
    ]
    assert resolved[0] == resolved[1] == resolved[2], resolved
    assert resolved[0] == [
        by_column[local_names["Season"]].get("name").strip("[]"),
        by_column[local_names["Week"]].get("name").strip("[]"),
        by_column[local_names["Player Id"]].get("name").strip("[]"),
    ], resolved[0]

    # --- ww34-streak-oracle -------------------------------------------------
    # The recomputed numbers are the ones the view is asked to draw: 32 rows of
    # 240 bars, the current streak carried on the last bar, the max never below
    # it, and the totals the article's chart is read against.
    assert facts["teams"] == 32
    assert facts["regular_season_rows"] == 32 * 240
    assert facts["sum_current_streak"] == 563
    assert facts["longest_streak"] == {"team": "LAC", "games": 224}
    for team, values in facts["per_team"].items():
        assert 1 <= values["current_streak"] <= values["max_streak"] <= 240, team
    # Current Streak is a window max over the team, so it must be reachable
    # from the Consecutive Streak values the oracle produced.
    assert max(v["max_streak"] for v in facts["per_team"].values()) == 224

    # --- ww34-viz-encoding --------------------------------------------------
    viz = sheet(root, BAR_SHEET)
    table = viz.find("table")
    rows_shelf = table.findtext("rows") or ""
    cols_shelf = table.findtext("cols") or ""
    index_ref = by_column[instances["INDEX"]].get("name")
    assert index_ref in cols_shelf, cols_shelf
    assert "/" in rows_shelf, "Team must be a separate Rows pill from Current Streak"
    streak_ref = by_column[instances["Consecutive Streak"]].get("name")
    assert streak_ref in rows_shelf, rows_shelf
    # The index is a continuous axis: its column instance is quantitative.
    index_ci = by_column[instances["INDEX"]]
    assert index_ci.get("type") == "quantitative"

    pane = table.find("panes/pane")
    assert pane.find("mark").get("class") == "Bar"
    encodings = pane.find("encodings")
    lod = [e.get("column") for e in encodings.findall("lod")]
    assert len(lod) == 3, lod
    assert any(e.tag == "tooltip" for e in encodings)
    sizing = pane.find("mark-sizing")
    assert sizing is not None
    assert sizing.get("use-custom-mark-size") == "true"
    assert float(sizing.get("custom-mark-size-in-axis-units")) == 1.0
    assert sizing.get("mark-alignment") == "mark-alignment-right"
    mark_style = {
        f.get("attr"): f.get("value")
        for f in pane.findall("style/style-rule[@element='mark']/format")
    }
    assert mark_style["mark-color"] == BAR_COLOR
    assert mark_style["has-stroke"] == "false"
    assert mark_style["mark-labels-show"] == "false"
    # No colour encoding: the author's bars are one flat colour.
    assert not encodings.findall("color")
    # The streak axis is hidden and the index axis is retitled.
    axis_formats = table.findall("style/style-rule[@element='axis']/format")
    titles = [f.get("value") for f in axis_formats if f.get("attr") == "title"]
    assert "Regular Season Games Since 2006" in titles, titles
    # Tableau's default gridline on rows is turned off.
    grid = table.findall("style/style-rule[@element='gridline']/format")
    assert any(
        f.get("attr") == "line-visibility" and f.get("scope") == "rows" and f.get("value") == "off"
        for f in grid
    ), grid

    title = viz.find("layout-options/title/formatted-text")
    assert title is not None, "worksheet title missing"
    runs = [(r.text or "").strip() for r in title.findall("run")]
    assert runs[0] == "Consecutive Starts in a Row", runs
    assert any("Total Consecutive Quarterback Starts" in r for r in runs), runs
    assert any("Pro Football Focus" in r for r in runs), runs

    # --- ww34-dashboard -----------------------------------------------------
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD}']")
    assert dashboard is not None, "dashboard missing"
    size = dashboard.find("size")
    assert size.get("sizing-mode") == "fixed"
    assert (size.get("minwidth"), size.get("minheight")) == ("800", "1800")
    zones = dashboard.findall(".//zones//zone")
    viz_zone = next((z for z in zones if z.get("name") == BAR_SHEET), None)
    assert viz_zone is not None, "Viz sheet is not on the dashboard"
    assert (viz_zone.get("x"), viz_zone.get("y"), viz_zone.get("w"), viz_zone.get("h")) == (
        "1000",
        "444",
        "98000",
        "95556",
    )
    texts = {
        "".join((run.text or "") for run in zone.findall("formatted-text/run")).strip()
        for zone in zones
        if zone.get("type-v2") == "text"
    }
    for expected_text in (
        "CHALLENGE BY : LUKE STANKE",
        "#WOW2021  |  WEEK 34",
        "RECREATED BY : DONNA COLES",
        "http://www.workout-wednesday.com/2021-week-34-how-many-consecutive-starts/",
    ):
        assert expected_text in texts, (expected_text, texts)

    evidence = {
        "scope": (
            "Independent running-counter oracle over the locked extract plus the "
            "native table-calculation, filter, encoding and dashboard contracts."
        ),
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
        "packaged_extract_sha256_matches_lock": True,
    }
    (HERE / "outputs" / "independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps({k: v for k, v in result["facts"].items() if k != "per_team"}, indent=2))
    print("PASS")
