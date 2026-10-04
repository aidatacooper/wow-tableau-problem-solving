"""Independent all-record business oracle and native/Cloud workbook verification."""

import csv
import io
import json
import math
from collections import defaultdict, Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess, Telemetry, Connection

ACCEPTANCE_IDS = ["ww48-raw-oracle", "ww48-native-contracts", "ww48-cloud-data"]
HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def raw():
    file = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as p:
        with Connection(p.endpoint, str(file)) as c:
            return c.execute_list_query('SELECT * FROM "Extract"."Extract"')


def root():
    artifact = HERE / "outputs" / "replicated-workbook.twbx"
    with ZipFile(artifact) as z:
        twb = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
        for f in lock["extracted_data"]:
            original = HERE / f["file"]
            assert digest(original) == f["sha256"]
            member = next(n for n in z.namelist() if n.endswith(original.name))
            assert sha256(z.read(member)).hexdigest() == f["sha256"]
    return twb


def csvrows(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))


def number(value):
    return float(value.replace(",", "").replace("$", "").strip())


def verify():
    business = oracle()
    native(root())
    result = {
        "artifact_sha256": digest(HERE / "outputs/replicated-workbook.twbx"),
        "status": "passed",
        "raw_oracle": business,
        "native_contracts": "passed",
        "browser_interaction_executed": False,
    }
    manifest_path = HERE / "evidence/cloud-verification.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf8"))
        assert manifest["source_hashes"]["replica"] == result["artifact_sha256"]
        checks = []
        for state in manifest["states"]:
            for item in state["data"]:
                p = HERE / item["path"]
                assert digest(p) == item["sha256"]
                records = csvrows(p)
                assert records, f"Empty CSV {p.name}"
                check_cloud(
                    records, state["name"], item["view"], business, item["role"]
                )
                checks.append(
                    {
                        "state": state["name"],
                        "role": item["role"],
                        "view": item["view"],
                        "records": len(records),
                        "passed": True,
                    }
                )
        result["cloud_checks"] = checks
    else:
        result["cloud_checks"] = "not yet captured"
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "artifact_sha256": result["artifact_sha256"],
                "cloud_checks": result["cloud_checks"],
            },
            indent=2,
        )
    )


def oracle():
    facts = raw()
    assert len(facts) == 94333
    sessions = defaultdict(lambda: {"users": set(), "facts": 0, "descriptions": set()})
    for start, end, location, title, description, user in facts:
        key = f"{start.hour:02}:{start.minute:02}"
        group = sessions[key]
        group.update(
            {
                "start": str(start),
                "end": str(end),
                "location": location,
                "title": title,
                "minutes": (end.hour * 60 + end.minute)
                - (start.hour * 60 + start.minute),
            }
        )
        group["users"].add(user)
        group["descriptions"].add(description)
        group["facts"] += 1
    output = {}
    for key, group in sessions.items():
        assert len(group["descriptions"]) == 1
        output[key] = {
            k: v for k, v in group.items() if k not in {"users", "descriptions"}
        }
        output[key]["attendees"] = len(group["users"])
        output[key]["description"] = next(iter(group["descriptions"]))
        output[key]["day_proportion"] = group["minutes"] / 1440
    assert (
        len(output) == 17 and sum(x["location"] is None for x in output.values()) == 2
    )
    return {"facts": len(facts), "sessions": dict(sorted(output.items()))}


def native(r):
    viz = r.find("worksheets/worksheet[@name='Viz']")
    panes = viz.findall("table/panes/pane")
    assert len(panes) == 2 and all(p.find("mark").get("class") == "Bar" for p in panes)
    assert ".[none:Start time:qk]" in viz.findtext("table/cols")
    sizing = panes[1].find("mark-sizing")
    assert sizing.get("mark-sizing-setting") == "marks-scaling-on"
    assert sizing.get("mark-alignment") == "mark-alignment-left"
    assert panes[1].find("encodings/size") is not None
    assert all(p.find("customized-tooltip/formatted-text") is not None for p in panes)
    axes = viz.find("table/style/style-rule[@element='axis']")
    time_axis = next(x for x in axes.findall("encoding") if x.get("scope") == "cols")
    assert (
        time_axis.get("major-spacing") == "15.0"
        and time_axis.get("major-units") == "minutes"
    )
    assert time_axis.get("range-type") != "fixed"
    assert axes.find("format[@attr='render-fold-reversed']").get("value") == "true"
    hidden_y = [
        x
        for x in axes.findall("format")
        if x.get("scope") == "rows" and x.get("attr") == "display"
    ]
    assert len(hidden_y) == 2 and all(x.get("value") == "false" for x in hidden_y)
    assert axes.find("format[@attr='title']").get("value") == ""
    columns = {
        c.get("caption", c.get("name", "").strip("[]")): c
        for c in r.findall("datasources/datasource/column")
    }
    assert "COUNTD([User Name (Original Name)])" in columns["# of Turkeys"].find(
        "calculation"
    ).get("formula")
    assert "DATEDIFF('minute'" in columns["Duration (mins)"].find("calculation").get(
        "formula"
    )
    assert "24*60" in columns["Duration Proportion of Day"].find("calculation").get(
        "formula"
    )
    assert r.find("worksheets/worksheet[@name='Data']") is not None
    size = r.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "1000" and size.get("maxheight") == "600"


def clock(value):
    value = value.strip()
    if " | " in value:
        value = value.split(" | ")[0]
    for fmt in ["%I:%M %p", "%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            pass
    raise AssertionError(f"Unsupported exported time {value}")


def check_cloud(records, state, view, business, role):
    expected = {
        k: v
        for k, v in business["sessions"].items()
        if state == "default" or str(v["location"]).lower() == state
    }
    assert expected
    if view == "Data":
        actual = {}
        for row in records:
            key = clock(row["Session Key"] if role == "replica" else row["Start time"])
            metric = row["Measure Names"]
            assert (key, metric) not in actual
            actual[key, metric] = number(row["Measure Values"])
            if role == "author":
                e = expected[key]
                assert (
                    row["Session Title"] == e["title"]
                    and row["Session Description"] == e["description"]
                )
                assert clock(row["End time"]) == clock(e["end"])
                assert row["Location"] == (e["location"] or "Break")
        wanted = {
            (key, metric): value
            for key, e in expected.items()
            for metric, value in [
                ("# of Turkeys", e["attendees"]),
                ("Avg. Duration (mins)", e["minutes"]),
                ("Avg. Duration Proportion of Day", e["day_proportion"]),
            ]
        }
        assert actual.keys() == wanted.keys(), (
            role,
            state,
            actual.keys(),
            wanted.keys(),
        )
        for key, value in wanted.items():
            assert abs(actual[key] - value) <= 6e-10, (
                role,
                state,
                key,
                actual[key],
                value,
            )
    elif view == "Viz":
        counts = Counter()
        duration_counts = Counter()
        for row in records:
            key = clock(row["Start time"])
            assert key in expected
            e = expected[key]
            assert number(row["# of Turkeys"]) == e["attendees"]
            counts[key] += 1
            if role == "author":
                assert (
                    row["Session Title"] == e["title"]
                    and row["Session Description"] == e["description"]
                )
                assert clock(row["End time"]) == clock(e["end"])
                assert number(row["Avg. Duration (mins)"]) == e["minutes"]
                assert row["Location"] == (e["location"] or "Break")
            proportion = row.get("Avg. Duration Proportion of Day", "")
            if proportion:
                assert abs(number(proportion) - e["day_proportion"]) <= 6e-10
                duration_counts[key] += 1
            elif role == "replica":
                assert row["Location"] == (e["location"] or "")
        assert counts == Counter({key: 2 for key in expected}), (role, state, counts)
        assert duration_counts == Counter({key: 1 for key in expected}), (
            role,
            state,
            duration_counts,
        )
    else:
        raise AssertionError(f"Unexpected view {view}")


if __name__ == "__main__":
    verify()
