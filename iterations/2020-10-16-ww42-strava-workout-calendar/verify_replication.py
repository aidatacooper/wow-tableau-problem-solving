"""Independent raw activity oracle, zero-day completeness and native blends."""

import calendar
import csv
import json
import math
import re
from collections import defaultdict
from datetime import date
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import unquote

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = ["daily-zero-calendar", "monthly-weekly-totals", "three-year-bans"]


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(
            h.endpoint, str(HERE / "inputs/TEMP_1bdxkpy13x6eq915qhj8e16rn32h.hyper")
        ) as c:
            days = c.execute_list_query('SELECT "Date" FROM "Extract"."Extract"')
        with Connection(
            h.endpoint, str(HERE / "inputs/TEMP_04r3f5b0jg8h101drwlwq0pqgfqk.hyper")
        ) as c:
            facts = c.execute_list_query(
                'SELECT "Activity ID","DateTime","Miles","Seconds" FROM "Extract"."Extract"'
            )
    assert len(days) == 2922
    result = {}
    for year in [2020, 2019, 2018]:
        scaffold = [
            date(r[0].year, r[0].month, r[0].day) for r in days if r[0].year == year
        ]
        assert len(scaffold) == (366 if calendar.isleap(year) else 365) and len(
            set(scaffold)
        ) == len(scaffold)
        daily = defaultdict(list)
        for fact in facts:
            d = fact[1]
            if d.year == year:
                daily[date(d.year, d.month, d.day)].append(fact)
        values = {
            d.isoformat(): math.fsum(f[3] for f in daily[d]) / 3600 for d in scaffold
        }
        months = defaultdict(list)
        weeks = defaultdict(list)
        for d in scaffold:
            months[d.month].append(values[d.isoformat()])
            week = ((d - date(year, 1, 1)).days + date(year, 1, 1).weekday()) // 7 + 1
            weeks[week].append(values[d.isoformat()])
        yearfacts = [f for f in facts if f[1].year == year]
        result[str(year)] = {
            "days": values,
            "zero_days": sum(v == 0 for v in values.values()),
            "months": {str(m): math.fsum(v) for m, v in months.items()},
            "weeks": {str(w): math.fsum(v) for w, v in weeks.items()},
            "bans": {
                "Hours": math.fsum(f[3] for f in yearfacts) / 3600,
                "Miles": math.fsum(f[2] for f in yearfacts),
                "# Actvities": len([f for f in yearfacts if f[0] is not None]),
            },
        }
    return {
        "calendar_rows": len(days),
        "activity_rows": len(facts),
        "years": result,
        "week_start": "monday",
        "scope": "All locked raw activities, independent per-day aggregation against every calendar scaffold day, all month/week totals and complete year BANs.",
    }


def numeric(text, target, tolerance=0.050001):
    cleaned = text.strip().replace(",", "")
    assert cleaned and "#" not in cleaned
    assert math.isclose(float(cleaned), target, rel_tol=0, abs_tol=tolerance), (
        text,
        target,
    )


def parsedate(text, year):
    match = re.search(r"(20\d\d)-(\d{1,2})-(\d{1,2})", text)
    if match:
        return date(*map(int, match.groups()))
    match = re.search(r"^(\d{1,2})/(\d{1,2})/(20\d\d)", text)
    if match:
        m, d, y = map(int, match.groups())
        return date(y, m, d)
    for m in range(1, 13):
        match = re.search(
            r"\b(?:"
            + calendar.month_name[m]
            + "|"
            + calendar.month_abbr[m]
            + r")\s+(\d{1,2})(?:,)?\s+(20\d\d)",
            text,
            re.IGNORECASE,
        )
        if match:
            return date(int(match.group(2)), m, int(match.group(1)))
        reverse = re.search(
            r"\b(\d{1,2})\s+(?:"
            + calendar.month_name[m]
            + "|"
            + calendar.month_abbr[m]
            + r")\s+(20\d\d)",
            text,
            re.IGNORECASE,
        )
        if reverse:
            return date(int(reverse.group(2)), m, int(reverse.group(1)))
    raise AssertionError(("Unknown CSV date", text, year))


def cloud(data, digest):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf-8"))
    proof = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    assert (
        report["source_hashes"]["replica"] == digest
        and report["source_hashes"]["author"] == proof["export_sha256"]
    )
    assert proof["original_sha256"] == lock["source_workbook"]["sha256"]
    assert report["browser_interaction_executed"] is False
    states = {
        "default": {},
        "year-2019": {"year(BLEND: Date)": "2019"},
        "year-2018": {"year(BLEND: Date)": "2018"},
    }
    assert len(report["states"]) == 3 and {s["name"] for s in report["states"]} == set(
        states
    )
    exports = {
        (role, sheet)
        for role in ["author", "replica"]
        for sheet in ["Calendar", "Weekly Profile", "BANs"]
    }
    checks = []
    for state in report["states"]:
        assert state["parameters"] == {} and state["filters"] == states[state["name"]]
        year = int(state["filters"].get("year(BLEND: Date)", "2020"))
        targets = data["years"][str(year)]
        assert set(state["views"]) == {"author", "replica"}
        assert (
            len(state["data"]) == 6
            and {(x["role"], x["view"]) for x in state["data"]} == exports
        )
        for item in state["views"].values():
            assert (
                sha256((HERE / item["path"]).read_bytes()).hexdigest() == item["sha256"]
            )
        for item in state["data"]:
            p = HERE / item["path"]
            assert sha256(p.read_bytes()).hexdigest() == item["sha256"]
            assert item["parameters"] == {} and item["filters"] == states[state["name"]]
            rows = [
                {k.strip(): v for k, v in row.items()}
                for row in csv.DictReader(
                    p.read_text(encoding="utf-8-sig").splitlines()
                )
            ]
            assert rows, (p, "Empty business CSV cannot prove correctness")
            if item["view"] == "Calendar":
                seen = set()
                summaries = set()
                daily_multiplicity = defaultdict(int)
                for row in rows:
                    if row.get("Date", "").strip() and row.get("Hours", "").strip():
                        d = parsedate(row["Date"], year)
                        key = d.isoformat()
                        assert key in targets["days"], (p, key)
                        daily_multiplicity[key] += 1
                        assert daily_multiplicity[key] == 1, (
                            p,
                            key,
                            "Duplicate populated daily value",
                        )
                        seen.add(key)
                        numeric(row["Hours"], targets["days"][key])
                    if row.get("Hours in Month", "").strip():
                        monthname = row.get("Month Name Abbrev", "").strip()
                        assert monthname in [
                            calendar.month_abbr[m].upper() for m in range(1, 13)
                        ], (p, row)
                        month = next(
                            m
                            for m in range(1, 13)
                            if calendar.month_abbr[m].upper() == monthname
                        )
                        numeric(
                            row["Hours in Month"],
                            targets["months"][str(month)],
                            0.50001,
                        )
                        summaries.add(month)
                assert seen == set(targets["days"]), (
                    p,
                    "Daily coverage",
                    len(seen),
                    len(targets["days"]),
                )
                assert set(daily_multiplicity.values()) == {1}
                assert summaries == set(range(1, 13)), (
                    p,
                    "Monthly coverage",
                    summaries,
                )
            elif item["view"] == "Weekly Profile":
                seen = set()
                for row in rows:
                    wkfield = next(k for k in row if "Week" in k)
                    week = int(re.search(r"\d+", row[wkfield]).group())
                    assert str(week) in targets["weeks"] and week not in seen
                    seen.add(week)
                    numeric(row["Hours"], targets["weeks"][str(week)])
                assert seen == {int(w) for w in targets["weeks"]}
            else:
                assert len(rows) == 3, (p, "Expected three native BAN axis rows")
                coverage = set()
                for row in rows:
                    for metric, value in targets["bans"].items():
                        if row.get(metric, "").strip():
                            numeric(
                                row[metric],
                                value,
                                1e-7 if metric == "# Actvities" else 0.500001,
                            )
                            coverage.add(metric)
                assert coverage == set(targets["bans"])
            checks.append(
                {
                    "state": state["name"],
                    "role": item["role"],
                    "view": item["view"],
                    "rows": len(rows),
                    "passed": True,
                }
            )
    return checks


def verify():
    output = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(output.read_bytes()).hexdigest()
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    assert not lock["source_workbook_used_by_builder"]
    with ZipFile(output) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for entry in lock["extracted_data"]:
            p = HERE / entry["file"]
            assert (
                p.stat().st_size == entry["bytes"]
                and sha256(p.read_bytes()).hexdigest() == entry["sha256"]
            )
            packed = next(n for n in z.namelist() if n.endswith(p.name))
            assert sha256(z.read(packed)).hexdigest() == entry["sha256"]
    ds = root.findall("datasources/datasource")
    assert len(ds) == 2
    assert all(d.find("date-options").get("start-of-week") == "monday" for d in ds)
    assert not root.xpath('//relation[@type="join"]')
    names = {"Calendar", "Weekly Profile", "BANs"}
    assert {s.get("name") for s in root.findall("worksheets/worksheet")} == names
    for sheet in root.findall("worksheets/worksheet"):
        assert len(sheet.findall("table/view/datasources/datasource")) == 2
        assert sheet.find("table/join-lod-include-overrides/column") is not None
        assert any(
            "yr:" in f.get("column", "") for f in sheet.findall("table/view/filter")
        )
    dashboard = root.find("dashboards/dashboard")
    assert (
        dashboard.find("size").get("maxwidth") == "1680"
        and dashboard.find("size").get("maxheight") == "1020"
    )
    zone = dashboard.xpath('zones//zone[@type-v2="filter"]')[0]
    assert (
        zone.get("mode") == "slider"
        and zone.get("show-slider") == "false"
        and zone.get("show-all") == "false"
    )
    assert dashboard.xpath(
        'datasource-dependencies/column-instance[@derivation="Year"]'
    )
    assert not dashboard.xpath('zones//zone[@type-v2="layout-basic"]')
    cal = root.find('worksheets/worksheet[@name="Calendar"]')
    assert [p.find("mark").get("class") for p in cal.findall("table/panes/pane")] == [
        "Automatic",
        "Text",
        "Bar",
    ]
    assert cal.xpath('.//column-instance/table-calc[@ordering-type="Field"]')
    assert cal.xpath(
        './/column-instance[@column="[Date]" and @derivation="None" and @type="quantitative"]'
    )
    assert cal.xpath('.//format[@attr="background-color" and @value="#f5f5fa"]')
    # The two measures occupy separate halves of each monthly cell.
    space = cal.xpath('table/style/style-rule[@element="axis"]/encoding[@attr="space"]')
    assert len(space) == 2 and all(x.get("fold") == "false" for x in space)
    textpane = cal.find('table/panes/pane[@id="1"]')
    barpane = cal.find('table/panes/pane[@id="2"]')
    rich_runs = textpane.findall("customized-label/formatted-text/run")
    assert [x.get("fontsize") for x in rich_runs if x.get("fontsize")] == [
        "16",
        "16",
        "9",
    ]
    assert all(
        x.get("fontname") == "Times New Roman" for x in rich_runs if x.get("fontsize")
    )
    assert len(textpane.findall("encodings/text")) == 3
    assert (
        len(textpane.findall("encodings/lod"))
        == len(barpane.findall("encodings/lod"))
        == 1
    )
    assert textpane.find("encodings/lod").get("column") == barpane.find(
        "encodings/lod"
    ).get("column")
    assert barpane.xpath(
        'style/style-rule[@element="mark"]/format[@attr="mark-labels-show" and @value="false"]'
    )
    month_field = root.xpath(
        '/workbook/datasources/datasource/column[@caption="Hours in Month"]'
    )[0]
    hours_field = root.xpath(
        '/workbook/datasources/datasource/column[@caption="Hours"]'
    )[0]
    raw_dates = [
        field
        for datasource in ds
        for field in datasource.findall("column")
        if field.get("datatype") == "date" and field.find("calculation") is None
    ]
    assert len(raw_dates) == 1
    raw_date_name = raw_dates[0].get("name")
    assert (
        month_field.find("calculation").get("formula")
        == "IF MIN(DAY("
        + raw_date_name
        + "))=28 THEN WINDOW_SUM("
        + hours_field.get("name")
        + ") END"
    )

    monthly_instance = cal.xpath(
        ".//column-instance[@column=$column]", column=month_field.get("name")
    )[0]
    monthly_orders = monthly_instance.findall("table-calc/order")
    assert (
        len(monthly_orders) == 4
        and "day:Date:ok" in monthly_orders[0].get("field")
        and "none:Date:qk" in monthly_orders[1].get("field")
    )
    for index, caption in [(2, "Month Name Abbrev"), (3, "LABEL:Hours")]:
        field = root.xpath(
            "/workbook/datasources/datasource/column[@caption=$caption]",
            caption=caption,
        )[0]
        assert monthly_orders[index].get("field").endswith(field.get("name"))
    actions = root.findall("actions/action")
    assert (
        len(actions) == 3
        and {a.find("source").get("worksheet") for a in actions} == names
    )
    for a in actions:
        assert (
            a.find("activation").get("type") == "on-select"
            and a.find("activation").get("auto-clear") == "true"
        )
        assert a.find('command/param[@name="target"]').get("value") == a.find(
            "source"
        ).get("worksheet")
        sheet = root.find(
            "worksheets/worksheet[@name='" + a.find("source").get("worksheet") + "']"
        )
        true_field = root.xpath(
            '/workbook/datasources/datasource/column[@caption="True"]'
        )[0]
        false_field = root.xpath(
            '/workbook/datasources/datasource/column[@caption="False"]'
        )[0]
        expression = unquote(a.find("link").get("expression"))
        assert false_field.get("name") + "~s0=<" in expression
        assert true_field.get("name") + "~na>" in expression
        assert (
            a.find("link").get("include-null")
            == a.find("link").get("multi-select")
            == "true"
        )

        for caption in ["True", "False"]:
            field = root.xpath(
                "/workbook/datasources/datasource/column[@caption=$caption]",
                caption=caption,
            )[0]
            assert field.find("calculation").get("formula") == caption.upper()
            for pane in sheet.findall("table/panes/pane"):
                lod_bound = any(
                    field.get("name")[1:-1] in e.get("column", "")
                    for e in pane.findall("encodings/lod")
                )
                tooltip_bound = any(
                    field.get("name")[1:-1] in (run.text or "")
                    for run in pane.findall("customized-tooltip/formatted-text/run")
                )
                assert lod_bound or (
                    sheet.get("name") == "Calendar" and tooltip_bound
                ), (
                    sheet.get("name"),
                    pane.get("id"),
                    caption,
                    "Action field must be bound on every actual pane",
                )
    data = oracle()
    checks = cloud(data, digest)
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "artifact_sha256": digest,
                "acceptance_ids": ACCEPTANCE,
                "oracle": data,
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "PASS WW42 raw activity/calendar and native blend contracts; Cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    try:
        verify()
    except (AssertionError, KeyError, StopIteration, ValueError) as exc:
        artifact = HERE / "outputs/replicated-workbook.twbx"
        (HERE / "evidence/functional-verification.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                    "reason": str(exc),
                    "browser_interaction_executed": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise
