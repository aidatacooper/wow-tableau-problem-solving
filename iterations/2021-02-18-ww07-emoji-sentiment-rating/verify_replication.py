"""Independent emoji relational oracle, native extension contract and REST checks."""

from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict
import base64, csv, hashlib, json, math
from lxml import etree as E
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "complete-emoji-relational-oracle",
    "native-extension-filter-top20",
    "cloud-sentiment-layout-data",
]
CATEGORIES = [
    "Smileys & People",
    "Animals & Nature",
    "Food & Drink",
    "Activities",
    "Travel & Places",
    "Objects",
    "Symbols",
    "Flags",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        tabs = c.catalog.get_table_names("Extract")
        s = next(t for t in tabs if "Sentiment" in str(t))
        d = next(t for t in tabs if "emoji_df" in str(t))
        facts = c.execute_list_query(f"SELECT * FROM {s}")
        dictionary = c.execute_list_query(f"SELECT * FROM {d}")
    mapping = dict(dictionary)
    assert len(facts) == 969 and len(dictionary) == len(mapping) == 4159
    rows = []
    for emoji, count, position, negative, neutral, positive, name in facts:
        group = mapping.get(emoji)
        if group in ("People & Body", "Smileys & Emotion"):
            group = "Smileys & People"
        assert count == negative + neutral + positive
        rows.append(
            {
                "emoji": emoji,
                "occurrences": count,
                "position": position,
                "negative": negative,
                "neutral": neutral,
                "positive": positive,
                "name": name,
                "category": group,
                "% Positive": positive / count,
                "% Neutral": neutral / count,
                "% Negative": negative / count,
            }
        )
    groups = {
        group: sum(x["occurrences"] for x in rows if x["category"] == group)
        for group in CATEGORIES
    }
    states = {}
    for group in [None, *CATEGORIES]:
        scope = rows if group is None else [x for x in rows if x["category"] == group]
        states["default" if group is None else group] = sorted(
            scope, key=lambda x: (-x["occurrences"], x["emoji"])
        )[:20]
    matched = [x for x in rows if x["category"] is not None]
    assert len(matched) == 736 and len(rows) - len(matched) == 233
    total = sum(x["occurrences"] for x in matched)
    average = {
        "position": sum(x["position"] for x in matched) / len(matched),
        "occurrences": total / len(matched),
        "% Positive": sum(x["positive"] for x in matched) / total,
        "% Neutral": sum(x["neutral"] for x in matched) / total,
        "% Negative": sum(x["negative"] for x in matched) / total,
    }
    assert len(states["Flags"]) == 3
    return {
        "sentiment_rows": 969,
        "dictionary_unique_emoji": 4159,
        "matched_rows": 736,
        "null_category_rows": 233,
        "occurrences_all": sum(x["occurrences"] for x in rows),
        "occurrences_matched": total,
        "groups": groups,
        "top20_by_category": states,
        "average_matched": average,
        "facts": rows,
    }


def native():
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        r = E.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))
    ds = r.find("./datasources/datasource")
    assert ds.find(".//relationship") is not None
    g = ds.find('./column[@name="[Group (group)]"]/calculation')
    assert g.get("class") == "categorical-bin"
    assert set(x.text.strip('"') for x in g.findall("bin/value")) == {
        "People & Body",
        "Smileys & Emotion",
    }
    top = r.find('./worksheets/worksheet[@name="Top 20"]')
    assert top.find('table/view/filter[@context="true"]') is not None
    gf = top.find('table/view/filter/groupfilter[@count="20"]')
    assert gf is not None and gf.get("end") == "top"
    assert len(top.findall("table/panes/pane")) == 3
    one = next(
        c.get("name").strip("[]")
        for c in ds.findall("column")
        if c.get("caption") == "One"
    )
    for name, aggregate in (("Top 20", "sum"), ("Avg", "avg")):
        shelf = r.findtext(f'./worksheets/worksheet[@name="{name}"]/table/cols')
        assert "[Multiple Values]" in shelf and f"[{aggregate}:Position:qk]" in shelf
        assert f"[usr:{one}:qk]" in shelf, (name, shelf)
    assert "[Multiple Values]" in r.findtext(
        './worksheets/worksheet[@name="by Group"]/table/cols'
    )
    for name in ("Avg", "by Group"):
        w = r.find(f'./worksheets/worksheet[@name="{name}"]')
        filters = w.findall("table/view/filter")
        group_filter = next(
            f.find("groupfilter")
            for f in filters
            if "Group (group)" in f.get("column", "")
        )
        assert group_filter.get("function") == "except"
        assert (
            group_filter.get("{http://www.tableausoftware.com/xml/user}ui-enumeration")
            == "exclusive"
        )
        assert (
            group_filter.find('groupfilter[@function="member"]').get("member")
            == "%null%"
        )
    mn_colors = ds.findall(
        './style/style-rule/encoding[@attr="color"][@field="[:Measure Names]"]/map'
    )
    assert {x.get("to") for x in mn_colors} == {"#a9d2d8", "#f9d3a0", "#cc99af"}
    actual = {
        s.get("key"): s.get("value")
        for s in r.findall("./dashboards/dashboard//add-in/instance-settings/setting")
    }
    settings = json.loads((HERE / "inputs/extension-settings.json").read_text())
    for key, value in settings.items():
        assert json.loads(actual[key]) == value, (key, value, actual[key])
    shapes = json.loads(actual["shapes"])
    assert len(shapes) == 8
    assert [x["values"][0]["value"] for x in shapes] == CATEGORIES and all(
        x["active"] is False and x["type"] == "rectangle" for x in shapes
    )
    assert json.loads(actual["worksheets"]) == ["Top 20"] and json.loads(
        actual["dimensions"]
    ) == ["Group (group)"]
    image = json.loads(actual["image"])
    assert (
        base64.b64decode(image["data"])
        == (HERE / "inputs/extension-category-image.png").read_bytes()
    )
    m = r.find("./referenced-extensions/referenced-extension/manifest")
    d = m.find("dashboard-extension")
    assert (
        d.get("id") == "com.tableau.extensions.junglebook.sandboxed"
        and d.get("extension-version") == "1.0.0"
    )
    assert (
        d.findtext("source-location/url")
        == "https://extensions.tableauusercontent.com/sandbox/jungle-book/index.html"
    )
    assert (
        base64.b64decode(d.findtext("icon"))
        == (HERE / "inputs/extension-icon.png").read_bytes()
    )
    zone = r.find('./dashboards/dashboard//zone[@type-v2="dashboard-object"]')
    assert zone.find("add-in").get("extension-url") == d.findtext("source-location/url")
    assert not r.findall("./actions/action")
    return {
        "logical_relationship_preserved": True,
        "context_before_top20": True,
        "real_sandbox_extension": True,
        "eight_original_rectangle_groups": True,
        "target_only_top20": True,
        "image_icon_exact": True,
        "browser_extension_execution": False,
    }


def numeric(raw):
    return float(raw.replace(",", "").replace("%", "")) / (100 if "%" in raw else 1)


def value(raw, expected, label, tolerance=None):
    assert raw != "", (label, "missing numeric value")
    actual = numeric(raw)
    if tolerance is None:
        digits = len(raw.split(".")[1].replace("%", "")) if "." in raw else 0
        tolerance = 0.5 * 10 ** (-digits) / (100 if "%" in raw else 1) + 1e-8
    assert abs(actual - expected) <= tolerance, (label, raw, expected, tolerance)


def cloud(data):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return {"status": "pending"}
    proof = json.loads(path.read_text())
    assert proof["source_hashes"]["replica"] == sha(
        HERE / "outputs/replicated-workbook.twbx"
    )
    assert proof["browser_interaction_executed"] is False
    export = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert proof["source_hashes"]["author"] == export["export_sha256"]
    checks = []
    assert len(proof["states"]) == 3
    for state in proof["states"]:
        group = state["filters"].get("Group (group)")
        selected = data["top20_by_category"][group or "default"]
        expected_top = {x["emoji"]: x for x in selected}
        expected_groups = {
            k: v for k, v in data["groups"].items() if group is None or k != group
        }
        if group is not None:
            expected_groups[""] = sum(
                x["occurrences"] for x in data["facts"] if x["category"] is None
            )
        facts = [
            x
            for x in data["facts"]
            if (x["category"] is not None if group is None else x["category"] != group)
        ]
        occurrence = sum(x["occurrences"] for x in facts)
        average = {
            "Avg. Position": sum(x["position"] for x in facts) / len(facts),
            "Avg. Occurrences": occurrence / len(facts),
            **{
                name: sum(x[key] for x in facts) / occurrence
                for name, key in (
                    ("% Positive", "positive"),
                    ("% Neutral", "neutral"),
                    ("% Negative", "negative"),
                )
            },
        }
        for image in state["views"].values():
            assert sha(HERE / image["path"]) == image["sha256"]
        for record in state["data"]:
            csv_path = HERE / record["path"]
            assert sha(csv_path) == record["sha256"]
            with csv_path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            role = record["role"]
            view = record["view"]
            if view == "Top 20":
                required = {
                    "Emoji",
                    "Unicode name",
                    "#",
                    "Position",
                    "% Positive",
                    "% Neutral",
                    "% Negative",
                    "Measure Names",
                    "Measure Values",
                }
                assert required <= set(reader.fieldnames), (
                    role,
                    state["name"],
                    "missing Top20 axes/measures",
                    reader.fieldnames,
                )
                keys = set()
                positions = set()
                for row in rows:
                    key = (row["Emoji"], row["Measure Names"])
                    assert key not in keys
                    keys.add(key)
                    expected = expected_top[row["Emoji"]]
                    assert row["Unicode name"] == expected["name"]
                    value(row["#"], expected["occurrences"], key, 1e-8)
                    if row["Position"]:
                        value(row["Position"], expected["position"], key)
                        positions.add(row["Emoji"])
                    for field in ("% Positive", "% Neutral", "% Negative"):
                        value(row[field], expected[field], (key, field))
                    if row["Measure Names"]:
                        value(
                            row["Measure Values"],
                            expected[row["Measure Names"]],
                            (key, "measure value"),
                        )
                assert positions == set(expected_top), (
                    "Position coverage must contain every selected emoji"
                )
                assert keys == {
                    (emoji, name)
                    for emoji in expected_top
                    for name in ("", "% Positive", "% Neutral", "% Negative")
                }
            elif view == "by Group":
                keys = set()
                for row in rows:
                    category = row["Group (group)"]
                    measure = (
                        "Occurrences"
                        if "Occurrence" in row["Measure Names"]
                        else "Zero"
                    )
                    key = (category, measure)
                    assert key not in keys
                    keys.add(key)
                    value(row["Occurrences"], expected_groups[category], key, 1e-8)
                    if category == "" and measure == "Zero":
                        assert row["Measure Values"] == "", (
                            "Unmatched logical-category MIN(0) is NULL in both source and replica"
                        )
                    else:
                        value(
                            row["Measure Values"],
                            expected_groups[category]
                            if measure == "Occurrences"
                            else 0,
                            key,
                            1e-8,
                        )
                assert keys == {
                    (category, name)
                    for category in expected_groups
                    for name in ("Zero", "Occurrences")
                }
            elif view == "Avg":
                keys = set()
                position_seen = False
                for row in rows:
                    measure = row["Measure Names"]
                    assert measure not in keys
                    keys.add(measure)
                    for field, expected in average.items():
                        if field == "Avg. Position" and not row[field]:
                            continue
                        value(row[field], expected, (role, state["name"], field))
                        if field == "Avg. Position":
                            position_seen = True
                    if measure:
                        value(
                            row["Measure Values"],
                            average[measure],
                            (role, state["name"], measure),
                        )
                assert position_seen
                assert keys == (
                    {"% Positive", "% Neutral", "% Negative"}
                    | ({""} if role == "replica" else set())
                )
            else:
                raise AssertionError(view)
            checks.append(
                {
                    "file": record["path"],
                    "state": state["name"],
                    "role": role,
                    "view": view,
                    "rows": len(rows),
                    "complete_keys": len(keys),
                    "status": "pass",
                }
            )
    return {
        "status": "passed",
        "checks": checks,
        "category_state_scope": "REST category overrides select that category in the inclusive Top20 context filter, but replace the default null exclusion with category exclusion in byGroup/Avg, bringing null-category facts into those CSV scopes, faithfully matching source. Dashboard renders remain default under these REST overrides. Image clicks target only Top20 by native extension contract; no clicks were executed.",
        "precision_scope": "Integer occurrence values exact; percentages/positions checked against raw oracle at exported display precision.",
    }


def verify():
    data = oracle()
    contract = native()
    rest = cloud(data)
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True), encoding="utf8"
    )
    result = {
        "status": "pass",
        "acceptance_ids": ACCEPTANCE,
        "artifact_sha256": sha(HERE / "outputs/replicated-workbook.twbx"),
        "raw_oracle": {
            k: v for k, v in data.items() if k not in ("facts", "top20_by_category")
        },
        "native": contract,
        "cloud": rest,
    }
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf8"
    )
    print("PASS WW07 raw/native; Cloud=" + rest["status"])


if __name__ == "__main__":
    verify()
