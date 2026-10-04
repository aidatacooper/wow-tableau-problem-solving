"""Independent raw-profit, date completion, subtotal and REST-data verification."""

import calendar
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def oracle():
    facts = next((HERE / "inputs").glob("*.hyper"))
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(facts)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Order Date","Profit" FROM "Extract"."Extract"'
        )
    daily = defaultdict(float)
    for day, profit in rows:
        daily[date.fromisoformat(str(day))] += profit or 0
    monthly = defaultdict(float)
    for day, profit in daily.items():
        monthly[(day.year, day.month)] += profit
    maxima = {
        year: max(value for (y, m), value in monthly.items() if y == year)
        for year in {d.year for d in daily}
    }
    expected = {}
    for (year, month), total in monthly.items():
        running = 0
        for n in range(1, calendar.monthrange(year, month)[1] + 1):
            day = date(year, month, n)
            profit = daily.get(day, 0)
            running += profit
            expected[day] = {
                "profit": profit,
                "actual": profit,
                "running": running,
                "negative": -profit,
                "monthly": total,
                "maximum": maxima[year],
                "colour": "Red" if profit < 0 else "Blue" if profit > 0 else "Grey",
            }
        assert abs(running - total) < 1e-7
    assert len(rows) == 9994
    return daily, monthly, maxima, expected


def number(value):
    value = value.replace("$", "").replace(",", "").strip()
    if value.lower() in {"", "null", "none"}:
        return None
    if value.startswith("("):
        value = "-" + value[1:-1]
    try:
        return float(value)
    except ValueError:
        return None


def metric(name):
    s = name.lower()
    if "max monthly" in s:
        return "maximum"
    if "profit for month" in s:
        return "monthly"
    if "running" in s and "actual" in s:
        return "year_running"
    if "running" in s or "cumulative" in s:
        return "running"
    if "negative profit" in s or "*-1" in s:
        return "negative"
    if "actual profit" in s:
        return "actual"
    if "profit" in s and "colour" not in s:
        return "profit"
    return None


def row_date(row):
    for key, value in row.items():
        if (
            "day of order date" in key.lower()
            or key.lower() in {"order date", "date", "report date"}
        ) and value:
            for fmt in [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%B %d %Y",
            ]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    pass
    month_value = next(
        (v for k, v in row.items() if "month of order date" in k.lower()), ""
    )
    month_names = {calendar.month_name[i].lower(): i for i in range(1, 13)}
    month = month_names.get(month_value.lower())
    if not month:
        match = re.search(r"\b(1[0-2]|[1-9])\b", month_value)
        if match:
            month = int(match.group())
    day = next((v for k, v in row.items() if "day of order date" in k.lower()), "")
    if month and day.isdigit():
        try:
            return date(2020, month, int(day))
        except ValueError:
            return None
    return None


def csv_check(path, role, view, state, expected, daily, monthly):
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    assert rows, (path, "Empty export is not data proof")
    scope_month = {"june": 6, "november": 11}.get(state)
    observed = defaultdict(set)
    subtotal = defaultdict(set)
    comparisons = 0
    minimum = min(d for d in daily if d.year == 2020)
    maximum = max(d for d in daily if d.year == 2020)
    completed = {
        d
        for d in expected
        if minimum <= d <= maximum and (scope_month is None or d.month == scope_month)
    }
    year_running = {}
    run = 0
    for d in sorted(completed):
        run += expected[d]["profit"]
        year_running[d] = run
    required_months = {d.month for d in completed}
    for row in rows:
        d = row_date(row)
        measure = row.get("Measure Names")
        values = (
            [(metric(measure), row.get("Measure Values", ""))]
            if measure
            else [(metric(k), v) for k, v in row.items() if metric(k)]
        )
        month_name = next(
            (v for k, v in row.items() if "month of order date" in k.lower()), ""
        )
        m = next(
            (
                i
                for i in range(1, 13)
                if month_name.lower() == calendar.month_name[i].lower()
            ),
            None,
        )
        if m is not None:
            quarter = row.get("Quarter of Order Date")
            if quarter:
                assert quarter == f"Q{(m - 1) // 3 + 1}", (path, m, quarter)
            position = row.get("Cols")
            if position:
                assert int(position) == (m - 1) % 3 + 1, (path, m, position)
        is_total = any(
            v == "All"
            for k, v in row.items()
            if "day of order date" in k.lower() or k.lower() == "report date"
        )
        if not d:
            assert is_total and m is not None, (
                path,
                "Unrecognized date/subtotal row",
                row,
            )
            assert m in required_months, (path, "Wrong subtotal month", m)
            base = monthly[(2020, m)]
            targets = {
                "profit": base,
                "actual": base,
                "running": base,
                "negative": -base,
                "monthly": base,
                "maximum": max(v for (y, _), v in monthly.items() if y == 2020),
                "year_running": sum(
                    monthly[(2020, n)] for n in required_months if n <= m
                ),
            }
        else:
            assert d in completed, (path, d, "Wrong REST year/month/date grain")
            targets = {**expected[d], "year_running": year_running[d]}
        for name, value in values:
            actual = number(value)
            if name is None:
                continue
            if actual is None:
                assert (
                    d is not None
                    and d not in daily
                    and name not in {"actual", "year_running"}
                ), (path, d, name, "Unexpected null")
                continue
            target = targets[name]
            precision = (
                0.51
                if "." not in value
                else 0.5 * 10 ** (-len(value.rsplit(".", 1)[1])) + 1e-7
            )
            assert abs(actual - target) <= precision, (
                path,
                d or m,
                name,
                actual,
                target,
                precision,
            )
            (subtotal if is_total else observed)[name].add(m if is_total else d)
            comparisons += 1
        colour = row.get("Colour")
        if colour:
            assert colour == (
                "Blue"
                if targets["actual"] > 0
                else "Red"
                if targets["actual"] < 0
                else "Grey"
            ), (path, d, colour)
    fact_days = {d for d in daily if d in completed}
    assert observed["actual"] == completed, (
        path,
        "Missing completed dates",
        len(observed["actual"]),
        len(completed),
    )
    assert fact_days <= observed["running"], (path, "Running endpoint coverage missing")
    assert (
        subtotal["actual"] == required_months and subtotal["running"] == required_months
    ), (path, "Month subtotal coverage missing")
    if view == "Data":
        assert fact_days <= observed["profit"]
        assert observed["year_running"] == completed, (
            path,
            "Year-running diagnostic coverage missing",
        )
        assert subtotal["year_running"] == required_months
    assert comparisons > 0
    return {
        "role": role,
        "view": view,
        "state": state,
        "csv_rows": len(rows),
        "compared_values": comparisons,
        "calendar_days": len(completed),
        "fact_days": len(fact_days),
        "daily_keys": {k: len(v) for k, v in observed.items()},
        "subtotal_months": {k: sorted(v) for k, v in subtotal.items()},
    }


def verify():
    # daily-waterfall; native-completion; cloud-matrix
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    assert lock["source_workbook_used_by_builder"] is False
    for item in lock["extracted_data"]:
        assert digest(HERE / item["file"]) == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    identity = digest(artifact)
    with ZipFile(artifact) as archive:
        root = etree.fromstring(
            archive.read(next(n for n in archive.namelist() if n.endswith(".twb")))
        )
    assert not root.findall("actions/action")
    assert not root.xpath('/workbook/datasources/datasource[@name="Parameters"]')
    chart = root.xpath('//worksheet[@name="Chart"]')[0]
    assert chart.xpath('table/panes/pane/mark[@class="GanttBar"]')
    assert chart.xpath('table/panes/pane/mark[@class="Line"]')
    assert "day:Order Date:ok" in chart.findtext("table/cols")
    assert "qr:Order Date:ok" in chart.findtext("table/rows")
    assert chart.xpath("table/show-full-range/column") and chart.xpath(
        "table/subtotals/column"
    )
    assert chart.xpath(
        'table/panes/pane/style/style-rule/format[@attr="mark-transparency" and @value="0"]'
    )
    names = []
    for sheet in ["Chart", "Data"]:
        ws = root.xpath("//worksheet[@name=$sheet]", sheet=sheet)[0]
        dep = next(
            d
            for d in ws.findall("table/view/datasource-dependencies")
            if d.get("datasource") != "Parameters"
        )
        definitions = {
            c.get("caption", c.get("name")): c for c in dep.findall("column")
        }
        if sheet == "Chart":
            negative = definitions["Negative Profit"]
            assert (
                negative.find("calculation").get("formula").replace(" ", "")
                == "SUM([Profit])*-1"
            )
            sizes = ws.xpath(
                "table/panes/pane[mark/@class='GanttBar']/encodings/size/@column"
            )
            negative_ci = dep.xpath(
                "column-instance[@column=$field]", field=negative.get("name")
            )[0]
            assert sizes == [f"[{dep.get('datasource')}].{negative_ci.get('name')}"]
        name = definitions["Running Profit"].get("name")
        ci = dep.xpath("column-instance[@column=$field]", field=name)[0]
        assert ci.get("derivation") == "User"
        assert ci.find("table-calc").get("ordering-type") == "Field"
        assert (
            "day:Order Date:ok" if sheet == "Chart" else "tdy:Order Date:ok"
        ) in ci.find("table-calc").get("ordering-field")
        assert re.search(r":\d+\]$", ci.get("name"))
        names.append(ci.get("name"))
        assert ws.xpath("table/show-full-range/column") and ws.xpath(
            "table/subtotals/column"
        )
        assert not ws.xpath(
            "table/view/datasource-dependencies/column-instance[@visual-totals]"
        )
        assert "2020" in "".join(ws.xpath("table/view/filter/groupfilter/@member"))
        if sheet == "Data":
            date_ci = dep.xpath("column-instance[@derivation='Day-Trunc']")
            assert len(date_ci) == 1 and date_ci[0].get("type") == "ordinal"
            assert date_ci[0].get("name") == "[tdy:Order Date:ok]"
            assert "tdy:Order Date:ok" in ws.findtext("table/rows")
            yearly = definitions["Running Actual Profit"]
            assert (
                yearly.find("calculation/table-calc").get("ordering-type") == "Columns"
            )
            yearly_ci = dep.xpath(
                "column-instance[@column=$field]", field=yearly.get("name")
            )[0]
            assert yearly_ci.find("table-calc").get("ordering-type") == "Columns"
    assert len(set(names)) == 2
    daily, monthly, maxima, expected = oracle()
    output = {
        "status": "pass",
        "artifact_sha256": identity,
        "scope": "Locked raw oracle and native artifact contracts; Cloud checks only if complete matching manifest exists.",
        "raw_facts": 9994,
        "year2020_fact_days": sum(d.year == 2020 for d in daily),
        "year2020_calendar_days": sum(d.year == 2020 for d in expected),
        "year2020_profit": sum(v for d, v in daily.items() if d.year == 2020),
        "months": {str(m): v for (y, m), v in monthly.items() if y == 2020},
        "cloud": None,
    }
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        capture = json.loads(manifest.read_text())
        assert capture["source_hashes"]["replica"] == identity
        provenance = json.loads((HERE / "evidence/export-provenance.json").read_text())
        assert provenance["source_sha256"] == lock["source_workbook"]["sha256"]
        assert capture["source_hashes"]["author"] == provenance["export_sha256"]
        assert capture["browser_interaction_executed"] is False
        assert {s["name"] for s in capture["states"]} == {"default", "june", "november"}
        results = []
        for state in capture["states"]:
            assert len(state["data"]) == 4
            for image in state["views"].values():
                assert digest(HERE / image["path"]) == image["sha256"]
            for record in state["data"]:
                path = HERE / record["path"]
                assert digest(path) == record["sha256"]
                results.append(
                    csv_check(
                        path,
                        record["role"],
                        record["view"],
                        state["name"],
                        expected,
                        daily,
                        monthly,
                    )
                )
        output["cloud"] = results
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps(
                {"status": "pass", "artifact_sha256": identity, "checks": results},
                indent=2,
            )
            + "\n"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    return output


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
