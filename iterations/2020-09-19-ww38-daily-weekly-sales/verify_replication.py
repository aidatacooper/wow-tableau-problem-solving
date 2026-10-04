"""Independent raw-date scaffold, weekly sums and cumulative proportion oracle."""

import ast
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
EVENT = "Event Description (DimEvent)"


def day(value):
    return date.fromisoformat(str(value).split(" ")[0])


def oracle():
    data = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, data) as c:
            rows = c.execute_list_query(
                'SELECT "Actual Date","Day of Week","Day of Week Abbrev","Event Description (DimEvent)","Launch Date","Event Date (Dim Event)","Sold Amount" FROM "Extract"."Extract"'
            )
    daily, weekly, totals = {}, defaultdict(int), defaultdict(int)
    for actual, weekday, abbreviation, event, launch, event_date, sold in rows:
        actual, launch, event_date = day(actual), day(launch), day(event_date)
        assert weekday == (actual.isoweekday() % 7) + 1
        assert abbreviation.lower()[:3] == actual.strftime("%a").lower()
        monday = actual - timedelta(days=actual.weekday())
        launch_monday = launch - timedelta(days=launch.weekday())
        week = (monday - launch_monday).days // 7 + 1
        key = (event, actual)
        assert key not in daily
        daily[key] = {
            "sales": sold or 0,
            "week": week,
            "day": actual.isoweekday(),
            "type": "Launch Date"
            if actual == launch
            else "Event Date"
            if actual == event_date
            else "Regular",
            "group": 1 if event_date.month <= 6 else 2,
        }
        weekly[(event, week)] += sold or 0
        totals[event] += sold or 0
    cumulative, running = {}, defaultdict(int)
    for event, week in sorted(weekly):
        running[event] += weekly[(event, week)]
        cumulative[(event, week)] = {
            "sales": weekly[(event, week)],
            "cumulative": running[event],
            "total": totals[event],
            "percent": running[event] / totals[event],
        }
    assert len(rows) == len(daily) == 5040
    assert len(totals) == 12 and len(weekly) == 720
    for event, total in totals.items():
        assert running[event] == total
        dates = sorted(d for e, d in daily if e == event)
        assert (dates[-1] - dates[0]).days + 1 == len(dates)
        assert (
            sum(v["type"] == "Launch Date" for (e, _), v in daily.items() if e == event)
            == 1
        )
        assert (
            sum(v["type"] == "Event Date" for (e, _), v in daily.items() if e == event)
            == 1
        )
    return daily, cumulative, totals


def verify():
    # blank-sdk-build; locked-inputs; native-weekly-table-calculations;
    # complete-daily-weekly-oracle; cloud-rest-comparison; cloud-visual-review
    source = (HERE / "build_replication.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    assert 'TWBEditor("")' in source
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_") for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.ImportFrom) and (n.module or "").startswith("cwtwb.")
        for n in ast.walk(tree)
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    for item in lock["extracted_data"]:
        assert sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        assert (
            sha256(
                z.read(next(n for n in z.namelist() if n.endswith(".hyper")))
            ).hexdigest()
            == lock["extracted_data"][0]["sha256"]
        )
    assert root.xpath("//worksheet/@name") == [
        "Viz",
        "CHK:Daily Data",
        "CHK:Weekly Data",
    ]
    assert root.xpath('//dashboard/size[@maxwidth="1600"][@maxheight="900"]')
    assert len(root.xpath('//worksheet[@name="Viz"]//mark[@class="GanttBar"]')) == 2
    assert (
        len(
            root.xpath(
                '//worksheet[@name="Viz"]//mark-sizing[@mark-sizing-setting="marks-scaling-off"]'
            )
        )
        == 2
    )
    assert not root.xpath("//action")
    columns = {
        n.get("caption"): n
        for n in root.xpath("/workbook/datasources/datasource/column[@caption]")
    }

    def formula(name):
        result = columns[name].find("calculation").get("formula")
        for caption, column in columns.items():
            result = result.replace(column.get("name"), "[" + caption + "]")
        return result.replace("[Parameters].", "")

    assert (
        formula("% Total Sales")
        == "RUNNING_SUM(SUM([Ticket Sales]))/[Total Sales Per Event]"
    )
    assert formula("Total Sales Per Event") == "TOTAL(SUM([Sold Amount]))"
    assert (
        formula("Day Position") == "IF [Day of Week]=1 THEN 7 ELSE [Day of Week]-1 END"
    )
    week_name = columns["Week No From Launch"].get("name")[1:-1]
    calculations = root.xpath("//worksheet//column-instance/table-calc")
    assert calculations and all(
        n.get("ordering-type") == "Field" and week_name in n.get("ordering-field", "")
        for n in calculations
    )
    assert root.xpath(
        '//worksheet[@name="Viz"]//style-rule[@element="axis"]/encoding[@min="0"][@max="1"]'
    )
    assert len(root.xpath('//dashboard/zones//zone[@type-v2="paramctrl"]')) == 2
    daily, weekly, totals = oracle()
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "raw_rows": len(daily),
        "events": len(totals),
        "weekly_marks": len(weekly),
        "event_totals": totals,
        "scope": "Full 5040 raw daily records; every 720 event/week aggregate, zero scaffold, cumulative sum and denominator independently recomputed. Cloud comparison pending until captured.",
        "browser_interaction_executed": False,
    }
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        cloud = json.loads(manifest.read_text(encoding="utf-8"))
        assert cloud["source_hashes"]["replica"] == digest
        proof = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert cloud["source_hashes"]["author"] == proof["comparison_sha256"]
        assert proof["original_sha256"] == lock["source_workbook"]["sha256"]
        assert cloud["browser_interaction_executed"] is False
        assert {s["name"] for s in cloud["states"]} == {
            "default",
            "yoy",
            "spring",
            "fall-yoy",
        }
        checks = []
        for state in cloud["states"]:
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for capture in state["data"]:
                path = HERE / capture["path"]
                assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as f:
                    exported = list(csv.DictReader(f))
                assert exported, path
                view = capture["view"]
                author = path.name.startswith("cloud-author")
                group = (
                    1
                    if state["name"] == "spring"
                    else 2
                    if state["name"] == "fall-yoy"
                    else 0
                )
                selected = {
                    key: value
                    for key, value in daily.items()
                    if not group or value["group"] == group
                }
                observed_daily, observed_weekly = {}, {}

                def numeric(value):
                    if not value.strip():
                        return None
                    return float(
                        value.replace("$", "").replace(",", "").replace("%", "")
                    ) / (100 if "%" in value else 1)

                def parse_date(value):
                    if "/" in value:
                        month, dd, year = map(int, value.split("/"))
                        return date(year, month, dd)
                    return date.fromisoformat(value[:10])

                if view == "CHK:Daily Data":
                    expected = {
                        key: value
                        for key, value in daily.items()
                        if key[0] in {"2019 EVENT #1", "2020 EVENT #1", "2020 EVENT #6"}
                    }
                    for row in exported:
                        key = (row[EVENT], parse_date(row["Actual Date"]))
                        assert key not in observed_daily and key in expected, (
                            path,
                            key,
                        )
                        value = row.get("Ticket Sales", row.get("Measure Values", ""))
                        assert numeric(value) == expected[key]["sales"], (
                            path,
                            key,
                            value,
                            expected[key],
                        )
                        observed_daily[key] = row
                    assert set(observed_daily) == set(expected), (
                        path,
                        "Daily diagnostic coverage",
                    )
                elif view == "CHK:Weekly Data":
                    expected = {
                        key: value
                        for key, value in weekly.items()
                        if key[0] == "2020 EVENT #6"
                    }
                    metrics = {
                        "Ticket Sales": "sales",
                        "Running Sum of Ticket Sales": "cumulative",
                        "Cumulative Sales": "cumulative",
                        "Total Sales Per Event": "total",
                        "% Total Sales": "percent",
                    }
                    for row in exported:
                        key = (row[EVENT], int(row["Week No From Launch"]))
                        metric = metrics[row["Measure Names"].split(" along ")[0]]
                        assert (
                            key in expected
                            and metric not in observed_weekly.setdefault(key, {})
                        ), (path, key, metric)
                        actual = numeric(row["Measure Values"])
                        target = expected[key][metric]
                        assert actual is not None and abs(actual - target) <= (
                            1e-9 if metric == "percent" else 0
                        ), (path, key, metric, actual, target)
                        observed_weekly[key][metric] = actual
                    assert set(observed_weekly) == set(expected) and all(
                        len(v) == 4 for v in observed_weekly.values()
                    ), (path, "Weekly diagnostic coverage")
                elif view == "Viz":
                    selected_events = {event for event, _ in selected}
                    max_week = max(value["week"] for value in selected.values())
                    expected_weeks = {
                        (event, week)
                        for event in selected_events
                        for week in range(1, max_week + 1)
                    }
                    comparison = "yoy" in state["name"]
                    for row in exported:
                        event = row[EVENT]
                        week = int(row["Week No From Launch"])
                        assert row["Display"] == (
                            event[-2:] if comparison else event[:4]
                        ), (path, row)
                        if row["Actual Date"]:
                            key = (event, parse_date(row["Actual Date"]))
                            assert key in selected and key not in observed_daily, (
                                path,
                                key,
                            )
                            target = selected[key]
                            pos = row["Day No of Week" if author else "Day Position"]
                            assert (
                                int(pos) == target["day"]
                                and row["Type of Day"] == target["type"]
                                and week == target["week"]
                            ), (path, key, row, target)
                            assert numeric(row["Ticket Sales"]) == target["sales"], (
                                path,
                                key,
                                row,
                                target,
                            )
                            observed_daily[key] = row
                        else:
                            key = (event, week)
                            assert (
                                key in expected_weeks and key not in observed_weekly
                            ), (path, key)
                            previous = weekly.get(key)
                            if previous is None:
                                last = max(w for e, w in weekly if e == event)
                                target = {**weekly[(event, last)], "sales": None}
                            else:
                                target = previous
                            running_key = (
                                "Running Sum of Ticket Sales"
                                if author
                                else "Cumulative Sales"
                            )
                            assert numeric(row[running_key]) == target["cumulative"], (
                                path,
                                key,
                                "cumulative",
                                row,
                                target,
                            )
                            percent = numeric(row["% Total Sales"])
                            assert (
                                percent is not None
                                and abs(percent - target["percent"]) <= 0.000501
                            ), (path, key, "percent", percent, target["percent"])
                            assert numeric(row["Ticket Sales"]) == target["sales"], (
                                path,
                                key,
                                "weekly sales",
                                row,
                                target,
                            )
                            if not author and previous is not None:
                                assert (
                                    numeric(row["Total Sales Per Event"])
                                    == target["total"]
                                ), (path, key, "denominator")
                            observed_weekly[key] = row
                    assert set(observed_daily) == set(selected), (
                        path,
                        "Main daily coverage",
                        len(observed_daily),
                        len(selected),
                    )
                    assert set(observed_weekly) == expected_weeks, (
                        path,
                        "Main weekly coverage",
                        len(observed_weekly),
                        len(expected_weeks),
                    )
                else:
                    raise AssertionError((path, "Unknown export grain", view))
                checks.append(
                    {
                        "path": capture["path"],
                        "rows": len(exported),
                        "daily_marks": len(observed_daily),
                        "weekly_marks": len(observed_weekly),
                        "status": "pass",
                    }
                )
        assert len(checks) == 24
        report["cloud_checks"] = checks
        report["status"] = "pass"
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    assert report["status"] == "pass", "Cloud numeric parsing/review remains required"
    print("PASS", len(daily), "daily rows;", len(weekly), "event/week marks")


if __name__ == "__main__":
    verify()
