# Acceptance: ww15-independent-data, ww15-artifact-contracts, ww15-cloud-states.
"""Independent daily-fact oracle, completed week grid and workbook contracts."""

import calendar
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
STATES = [
    ("default", "2019-10-24", 10),
    ("sunday", "2019-10-27", 4),
    ("monday", "2019-10-28", 1),
    ("current-only", "2019-10-24", 0),
]


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(
            h.endpoint, str(HERE / "inputs/Orders (Sample - Superstore).hyper")
        ) as c,
    ):
        table = next(
            t
            for s in c.catalog.get_schema_names()
            for t in c.catalog.get_table_names(s)
        )
        rows = c.execute_list_query('SELECT "Order Date","Sales" FROM ' + str(table))
    sums = defaultdict(list)
    for d, sales in rows:
        sums[date(d.year, d.month, d.day)].append(float(sales))
    daily = {d: math.fsum(v) for d, v in sums.items()}
    calendar_rows = list(
        csv.DictReader(
            (HERE / "inputs/daily-calendar.csv").open(encoding="utf-8", newline="")
        )
    )
    calendar_values = {
        date.fromisoformat(v["Order Date"]): float(v["Sales"]) for v in calendar_rows
    }
    begin = date(min(daily).year, 1, 1)
    end = date(max(daily).year, 12, 31)
    full_dates = {begin + timedelta(days=i) for i in range((end - begin).days + 1)}
    assert (
        len(calendar_rows) == len(calendar_values) == 1461
        and set(calendar_values) == full_dates
    )
    for d, actual in calendar_values.items():
        assert math.isclose(actual, daily.get(d, 0.0), abs_tol=1e-9), (
            d,
            actual,
            daily.get(d, 0.0),
        )
    assert math.isclose(
        math.fsum(calendar_values.values()),
        math.fsum(v for values in sums.values() for v in values),
        abs_tol=1e-8,
    )
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(
            hp.endpoint, str(HERE / "inputs/daily-calendar.hyper")
        ) as connection,
    ):
        typed = connection.execute_list_query(
            'SELECT "Order Date","Sales" FROM "Extract"."Extract"'
        )
    assert (
        len(typed) == len(calendar_values)
        and {date(d.year, d.month, d.day): float(v) for d, v in typed}
        == calendar_values
    )
    states = {}
    for name, ending, prior in STATES:
        end = date.fromisoformat(ending)
        start = end - timedelta(days=6)
        grid = []
        for back in range(prior, -1, -1):
            week = start - timedelta(weeks=back)
            for offset in range(7):
                d = week + timedelta(days=offset)
                grid.append(
                    {
                        "week": week.isoformat(),
                        "date": d.isoformat(),
                        "baseline": (start + timedelta(days=offset)).isoformat(),
                        "weekday": calendar.day_name[d.weekday()],
                        "sales": daily.get(d, 0.0),
                        "missing": d not in daily,
                        "latest": back == 0,
                    }
                )
        assert len(grid) == 7 * (prior + 1)
        states[name] = {
            "ending": ending,
            "prior": prior,
            "values": grid,
            "missing_count": sum(v["missing"] for v in grid),
        }
    assert len(rows) == 9994
    return {
        "row_count": len(rows),
        "states": states,
        "business_scope": "Complete seven-day grid for every selected current/prior week, including absent fact dates.",
    }


def parse_date(value):
    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y %I:%M:%S %p",
        "%a, %B %d, %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(value.strip(), fmt).date()  # noqa: DTZ007 - Tableau business date, not an instant.
        except ValueError:
            pass
    raise ValueError(value)


def number(raw):
    return float(raw.replace("$", "").replace(",", "").strip())


def verify_cloud(data):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return []
    report = json.loads(manifest.read_text(encoding="utf-8"))
    assert (
        report["source_hashes"]["replica"]
        == sha256((HERE / "outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    )
    assert {s["name"] for s in report["states"]} == set(data["states"])
    checks = []
    for state in report["states"]:
        expected = data["states"][state["name"]]["values"]
        lookup = {(v["week"], v["weekday"]): v for v in expected}
        for capture in [*state["views"].values(), *state["data"]]:
            p = HERE / capture["path"]
            assert sha256(p.read_bytes()).hexdigest() == capture["sha256"]
        for capture in state["data"]:
            p = HERE / capture["path"]
            rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
            seen = set()
            for row in rows:
                week = next(v for k, v in row.items() if "Order Date Week" in k)
                week = parse_date(week).isoformat()
                baseline = next(v for k, v in row.items() if "Order Date Baseline" in k)
                weekday = (
                    baseline.strip()
                    if baseline.strip() in calendar.day_name
                    else calendar.day_name[parse_date(baseline).weekday()]
                )
                key = week, weekday
                value = lookup[key]
                seen.add(key)
                sales = next(v for k, v in row.items() if "Inc Null Sales" in k)
                assert abs(number(sales) - value["sales"]) <= 0.51, (
                    p,
                    key,
                    sales,
                    value,
                )
                rawdate = next(
                    (
                        v
                        for k, v in row.items()
                        if ("Tooltip Order Date" in k or "TOOLTIP:Order Date" in k)
                        and v
                    ),
                    None,
                )
                if rawdate:
                    assert parse_date(rawdate).isoformat() == value["date"], (
                        p,
                        key,
                        rawdate,
                    )
                missingtext = next((v for k, v in row.items() if "No Sales" in k), None)
                if missingtext is not None:
                    assert missingtext.strip() == (
                        "no sales" if value["sales"] == 0 else ""
                    ), (p, key, missingtext)
            expected_keys = set(lookup)
            source_limitation = []
            if "cloud-author-" in p.name and state["name"] == "current-only":
                missing_leading = expected[0]
                assert missing_leading["missing"] and missing_leading["sales"] == 0
                absent = (missing_leading["week"], missing_leading["weekday"])
                expected_keys.remove(absent)
                source_limitation = [missing_leading["date"]]
            assert seen == expected_keys, (p, len(seen), len(expected_keys))
            checks.append(
                {
                    "state": state["name"],
                    "file": capture["path"],
                    "week_day_cells": len(seen),
                    "zero_fact_dates": sum(v["missing"] for v in expected),
                    "author_missing_leading_zero_dates": source_limitation,
                }
            )
    assert len(checks) == 8
    (HERE / "evidence/cloud-data-comparison.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "checks": checks,
                "scope": "Every current/prior-week weekday cell, zero sales and available tooltip dates; no button CSV proof.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return checks


def verify():
    data = oracle()
    output = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    with ZipFile(output) as z:
        r = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for item in lock["extracted_data"]:
            assert (
                sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
            )
        for derivative in lock["derived_data"]:
            assert (
                sha256((HERE / derivative["file"]).read_bytes()).hexdigest()
                == derivative["sha256"]
            )
        derivative = next(
            v
            for v in lock["derived_data"]
            if v["file"] == "inputs/daily-calendar.hyper"
        )
        embedded = next(
            n for n in z.namelist() if Path(n).name == "daily-calendar.hyper"
        )
        assert sha256(z.read(embedded)).hexdigest() == derivative["sha256"]
    assert r.xpath("worksheets/worksheet/@name") == ["Viz"]
    assert r.xpath("worksheets/worksheet//mark/@class") == ["Line"]
    assert ":ok]" in r.find("worksheets/worksheet/table/cols").text
    assert "[mn:" not in r.find("worksheets/worksheet/table/cols").text
    assert r.xpath(
        "worksheets/worksheet/table/panes/pane/encodings/lod[contains(@column, ':ok]')]"
    )
    range_fields = r.xpath("worksheets/worksheet/table/show-full-range/column/text()")
    assert len(range_fields) == 1 and "none:" not in range_fields[0]
    assert len(r.xpath('//datasource[@name="Parameters"]/column')) == 2
    assert r.xpath(
        '//pane/style/style-rule/format[@attr="mark-markers-mode" and @value="all"]'
    )
    assert r.xpath('//column/calculation[contains(@formula,"LOOKUP(SUM([Sales]),0)")]')
    assert r.xpath(
        '//customized-tooltip/formatted-text/run[contains(text(),"Weeks are trended")]'
    )
    title_tokens = r.xpath(
        "worksheets/worksheet/layout-options/title/formatted-text/run/text()"
    )
    assert sum("<[Parameters]." in t for t in title_tokens) == 2
    assert sum("<[federated." in t for t in title_tokens) == 2
    # Every dynamic weekday title token must resolve to an actual detail field.
    # Tooltip-only dependencies rendered the title as "None to None" in Cloud.
    details = set(
        r.xpath("worksheets/worksheet/table/panes/pane/encodings/lod/@column")
    )
    assert all(t[1:-1] in details for t in title_tokens if "<[federated." in t)
    size = r.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "1300" and size.get("maxheight") == "700"
    checks = verify_cloud(data)
    result = {
        "case": "ww15",
        "status": "pass",
        "artifact_sha256": sha256(output.read_bytes()).hexdigest(),
        "oracle": data,
        "cloud_status": "passed" if checks else "pending",
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PASS: WW15 complete dynamic seven-day grids and public workbook contracts; cloud="
        + result["cloud_status"]
    )
    return result


if __name__ == "__main__":
    verify()
