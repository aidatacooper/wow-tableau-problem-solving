"""Independent calendar domains and fact metrics, with native mobile contracts."""

import json
import math
import csv
from collections import defaultdict
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import unquote

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
STATES = {
    "default": ("2019-06-01", "2019-06-06", "2019-06-18"),
    "july": ("2019-07-01", "2019-07-01", "2019-07-07"),
    "leap-february": ("2016-02-01", "2016-02-10", "2016-02-29"),
    "december": ("2018-12-01", "2018-12-18", "2018-12-31"),
}


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c:
            tables = c.catalog.get_table_names("Extract")
            orders = next(t for t in tables if "Orders_" in str(t))
            dates = next(t for t in tables if "Dates Table" in str(t))
            facts = c.execute_list_query(
                f'SELECT "Order Date", "Sales", "Profit", "Quantity" FROM {orders}'
            )
            calendar = {
                date(d.year, d.month, d.day)
                for (d,) in c.execute_list_query(f'SELECT "Date" FROM {dates}')
            }
    assert len(facts) == 9994 and len(calendar) == 1461
    grouped = defaultdict(list)
    for d, sales, profit, quantity in facts:
        grouped[date(d.year, d.month, d.day)].append((sales, profit, quantity))
    result = {}
    for name, (month, start, end) in STATES.items():
        m, lo, hi = map(date.fromisoformat, (month, start, end))
        cells = [d for d in sorted(calendar) if (d.year, d.month) == (m.year, m.month)]
        daily = []
        for d in sorted(grouped):
            if lo <= d <= hi:
                rows = grouped[d]
                daily.append(
                    {
                        "date": d.isoformat(),
                        "Sales": math.fsum(r[0] for r in rows),
                        "Profit": math.fsum(r[1] for r in rows),
                        "Quantity": sum(r[2] for r in rows),
                    }
                )
        result[name] = {
            "month": month,
            "start": start,
            "end": end,
            "calendar": [
                {
                    "date": d.isoformat(),
                    "weekday": d.strftime("%a"),
                    "color": "Hot Pink"
                    if d in (lo, hi)
                    else "Pink"
                    if lo < d < hi
                    else "White",
                }
                for d in cells
            ],
            "daily": daily,
            "totals": {
                metric: math.fsum(r[metric] for r in daily)
                for metric in ("Sales", "Profit", "Quantity")
            },
            "year_picker": [2016, 2017, 2018, 2019],
            "month_picker": list(range(1, 13)),
        }
    return {"facts": len(facts), "distinct_dates": len(calendar), "states": result}


def parsed_date(text):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise AssertionError(("Expected complete date including year", text))


def cloud(data, digest):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf8"))
    assert report["source_hashes"]["replica"] == digest
    provenance = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf8")
    )
    assert report["source_hashes"]["author"] == provenance["export_sha256"]
    checks = []
    for state in report["states"]:
        expected = data["states"][state["name"]]
        month = date.fromisoformat(expected["month"])
        for item in state["views"].values():
            assert (
                sha256((HERE / item["path"]).read_bytes()).hexdigest() == item["sha256"]
            )
        for item in state["data"]:
            file = HERE / item["path"]
            assert sha256(file.read_bytes()).hexdigest() == item["sha256"]
            rows = list(
                csv.DictReader(file.read_text(encoding="utf-8-sig").splitlines())
            )
            assert rows, (file, "Empty worksheet export")
            view = item["view"]
            if view == "Calendar":
                actual = {
                    r["Date Control"]: (r["COLOUR : Date"], r["Day of Week Abbrev"])
                    for r in rows
                }
                target = {
                    r["date"]: (r["color"], r["weekday"]) for r in expected["calendar"]
                }
                assert actual == target
            elif view == "BAN":
                values = {
                    r["Measure Names"]: float(
                        r["Measure Values"].replace(",", "").replace("$", "")
                    )
                    for r in rows
                }
                assert set(values) == set(expected["totals"])
                assert all(
                    abs(values[k] - v) < 1e-6 for k, v in expected["totals"].items()
                ), (file, values, expected["totals"])
            elif view == "Line ":
                target = {r["date"]: r for r in expected["daily"]}
                seen = set()
                for row in rows:
                    day = parsed_date(row["Date"]).isoformat()
                    if day not in target:
                        assert all(
                            not row[m] or float(row[m].replace(",", "")) == 0
                            for m in ("Sales", "Profit", "Quantity")
                        )
                        continue
                    seen.add(day)
                    for metric in ("Sales", "Profit", "Quantity"):
                        assert "$" not in row[metric], (
                            file,
                            "Daily fact precision must remain complete",
                        )
                        assert (
                            abs(
                                float(row[metric].replace(",", ""))
                                - target[day][metric]
                            )
                            < 1e-6
                        )
                assert seen == set(target)
            elif view == "Year":
                assert {int(r["Year of Date"]) for r in rows} == {
                    2016,
                    2017,
                    2018,
                    2019,
                }
                assert all(
                    (r["COLOUR:Selected Year"].lower() == "true")
                    == (int(r["Year of Date"]) == month.year)
                    for r in rows
                )
            elif view == "Month":
                names = {
                    name: i
                    for i, name in enumerate(
                        (
                            "January",
                            "February",
                            "March",
                            "April",
                            "May",
                            "June",
                            "July",
                            "August",
                            "September",
                            "October",
                            "November",
                            "December",
                        ),
                        1,
                    )
                }
                seen = set()
                for row in rows:
                    number = names[row["Month of Date"].split()[0]]
                    seen.add(number)
                    assert int(row["Month Row"]) == (number - 1) // 4 + 1
                    assert int(row["Month Col"]) == (number - 1) % 4 + 1
                    assert (row["COLOUR:Selected Month"].lower() == "true") == (
                        number == month.month
                    )
                assert seen == set(range(1, 13))
            elif view == "Month Name":
                assert (
                    len(rows) == 1
                    and parsed_date(next(iter(rows[0].values()))) == month
                )
            elif view == "Selected Period":
                assert len(rows) == 1
                for label, target in (
                    ("Date Selection Start", expected["start"]),
                    ("Date Selection End", expected["end"]),
                ):
                    field = next(k for k in rows[0] if label in k)
                    assert parsed_date(rows[0][field]).isoformat() == target
            elif view in {"Next Month Control", "Prev Month Control"}:
                assert len(rows) == 1
                ordinal = (
                    month.year * 12
                    + month.month
                    - 1
                    + (1 if view.startswith("Next") else -1)
                )
                ordinal = min(max(ordinal, 2016 * 12), 2019 * 12 + 11)
                expected_date = date(ordinal // 12, ordinal % 12 + 1, 1)
                date_label = "Next Month" if view.startswith("Next") else "Prev Month"
                date_field = next(k for k in rows[0] if date_label in k)
                assert parsed_date(rows[0][date_field]) == expected_date
            else:
                raise AssertionError(("Unvalidated worksheet", view))
            checks.append(
                {
                    "state": state["name"],
                    "role": item["role"],
                    "view": view,
                    "rows": len(rows),
                }
            )
    assert len(checks) == 72
    return checks


def verify():
    data = oracle()
    workbook = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(workbook.read_bytes()).hexdigest()
    with ZipFile(workbook) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
        for item in lock["extracted_data"]:
            path = HERE / item["file"]
            assert sha256(path.read_bytes()).hexdigest() == item["sha256"]
            assert (
                sha256(
                    z.read(next(n for n in z.namelist() if n.endswith(path.name)))
                ).hexdigest()
                == item["sha256"]
            )
    for item in lock.get("derived_data", []):
        path = HERE / item["file"]
        assert sha256(path.read_bytes()).hexdigest() == item["sha256"]
    assert root.xpath(
        "//worksheet[@name='Calendar']//style-rule[@element='axis']/encoding[@range-type='fixed' and @min='0' and @max='1']"
    )
    assert root.xpath(
        "//worksheet[@name='Calendar']//style-rule[@element='mark']/format[@attr='mark-labels-cull' and @value='false']"
    )
    assert (
        len(
            root.xpath(
                "//worksheet[contains(@name,'Month Control')]//mark[@class='Text']"
            )
        )
        == 2
    )
    dashboard = root.find("dashboards/dashboard")
    phone = dashboard.xpath("devicelayouts/devicelayout[@name='Phone']")
    assert len(phone) == 1
    assert etree.tostring(dashboard.find("zones")) == etree.tostring(
        phone[0].find("zones")
    )
    assert dashboard.xpath("zones//zone[@type='dashboard-object']")
    assert dashboard.xpath(
        "zones//zone[@name='Year' and @hidden-by-user='true'] | zones//zone[@hidden-by-user='true']"
    )
    assert root.xpath("//worksheet[@name='Calendar']//pane[@x-axis-name]")
    assert not root.xpath(
        "//worksheet[@name='Line ']//format[@attr='display' and @scope='rows' and @value='false']"
    )
    assert (
        len(
            root.xpath(
                "//worksheet[@name='Line ']//format[@attr='title' and @scope='rows' and @value='']"
            )
        )
        == 3
    )
    actions = root.xpath("/workbook/actions/edit-parameter-action")
    assert len(actions) == 5
    assert len({a.get("name") for a in root.xpath("/workbook/actions/*[@name]")}) == 8
    assert all(a.find("activation").get("type") == "on-select" for a in actions)
    assert all(
        "[min:" in a.xpath("params/param[@name='source-field']/@value")[0]
        for a in actions
        if a.get("caption") != "Set dates"
    )
    columns = {
        c.get("caption"): c
        for c in root.xpath("/workbook/datasources/datasource/column")
    }
    parameter_columns = {
        c.get("name"): c.get("caption")
        for c in root.xpath(
            "/workbook/datasources/datasource[@name='Parameters']/column"
        )
    }
    expected_actions = {
        "Set dates": ("Calendar", "Date Control", "pSelectedDates"),
        "Next month": ("Next Month Control", "Next Month", "pMonthSelected"),
        "Previous month": ("Prev Month Control", "Prev Month", "pMonthSelected"),
        "Select year": ("Year", "Month Date", "pMonthSelected"),
        "Select month": ("Month", "Month Date", "pMonthSelected"),
    }
    assert {a.get("caption") for a in actions} == set(expected_actions)
    for action in actions:
        sheet, field, parameter = expected_actions[action.get("caption")]
        assert action.find("source").get("worksheet") == sheet
        source_ref = action.xpath("params/param[@name='source-field']/@value")[0]
        instance_name = source_ref.split(".")[-1]
        instance = root.xpath(
            "//worksheet[@name=$sheet]//column-instance[@name=$name]",
            sheet=sheet,
            name=instance_name,
        )
        assert len(instance) == 1
        declared = root.xpath(
            "//worksheet[@name=$sheet]//datasource-dependencies/column[@name=$name]",
            sheet=sheet,
            name=instance[0].get("column"),
        )
        assert len(declared) == 1 and declared[0].get("caption") == field
        target = action.xpath("params/param[@name='target-parameter']/@value")[0]
        assert parameter_columns[target.split(".")[-1]] == parameter
        assert action.find("agg-type").get("type") == "attr"
        assert not action.xpath("params/param[@name='clear-value']")
    deselection_actions = root.xpath("/workbook/actions/action")
    assert len(deselection_actions) == 3
    for action in deselection_actions:
        sheet = action.find("source").get("worksheet")
        assert sheet in {"Calendar", "Year", "Month"}
        assert action.xpath("command/param[@name='target']/@value") == [sheet]
        assert action.find("activation").get("auto-clear") == "true"
        expression = unquote(action.find("link").get("expression"))
        assert columns["True"].get("name") in expression
        assert columns["False"].get("name") in expression
    for caption, glyph in [
        ("Navigation Direction", "\u276f"),
        ("Previous Direction", "\u276e"),
    ]:
        assert columns[caption].find("calculation").get("formula") == f"'{glyph}'"
    for caption in ["COLOUR : Date", "Dates to Show", "COLOUR:Selected Month"]:
        formula = columns[caption].find("calculation").get("formula")
        assert "[Date Selection Start]" not in formula and "[Month Date]" not in formula
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "acceptance_ids": [
            "ww39-calendar-fact-oracle",
            "ww39-date-range-parameter-actions",
            "ww39-phone-picker-contract",
            "ww39-cloud-states",
        ],
        "oracle": data,
        "cloud_checks": cloud(data, digest),
        "browser_interaction_executed": False,
        "phone_browser_render_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf8"
    )
    print(
        "PASS WW39 9994 facts /1461 unique calendar dates /four raw parameter states/native Phone clone; Cloud "
        + ("passed" if report["cloud_checks"] else "pending")
    )


if __name__ == "__main__":
    verify()
