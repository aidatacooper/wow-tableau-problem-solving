"""Verify raw accounting data, October fiscal boundaries and all REST metrics."""

import csv
import json
import math
from collections import defaultdict
from datetime import date
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance: ww26-independent-data, ww26-artifact-contracts, ww26-cloud-states.


def oracle():
    file = next((HERE / "inputs").glob("*.hyper"))
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(file)) as c,
    ):
        rows = c.execute_list_query(
            'SELECT "Accounting Date","Account Number","Value" FROM "Extract"."Extract"'
        )
    assert len(rows) == 5582
    current = max(date(d.year, d.month, d.day) for d, _, _ in rows).replace(day=1)
    assert current == date(2020, 5, 1)
    fy_start = date(current.year if current.month >= 10 else current.year - 1, 10, 1)
    prev_end = date(current.year - 1, current.month, 1)
    prev_start = date(fy_start.year - 1, 10, 1)
    monthly = defaultdict(lambda: {"Sales": [], "OPP": []})
    current_facts = defaultdict(list)
    previous_facts = defaultdict(list)
    for raw, account, value in rows:
        d = date(raw.year, raw.month, 1)
        v = float(value)
        for metric, match in [
            ("Sales", account.startswith("5")),
            ("OPP", account.startswith(("5", "696"))),
        ]:
            if not match:
                continue
            monthly[d.isoformat()][metric].append(v)
            if fy_start <= d <= current:
                current_facts[metric].append(v)
            if prev_start <= d <= prev_end:
                previous_facts[metric].append(v)
    totals = {
        m: {
            "current": math.fsum(current_facts[m]),
            "previous": math.fsum(previous_facts[m]),
        }
        for m in ["Sales", "OPP"]
    }
    series = [
        {
            "month": d,
            "fiscal_year": int(d[:4]) + (int(d[5:7]) >= 10),
            **{m: math.fsum(vals[m]) for m in ["Sales", "OPP"]},
        }
        for d, vals in sorted(monthly.items())
    ]
    assert len(series) == 20 and sum(x["fiscal_year"] == 2020 for x in series) == 8
    states = {}
    for name, compare, budgets in [
        ("default", 0, {"Sales": 2300, "OPP": 3000}),
        ("prior-year", 1, {"Sales": 2300, "OPP": 3000}),
        ("low-budget", 0, {"Sales": 100, "OPP": 100}),
        ("high-budget", 0, {"Sales": 4000, "OPP": 4500}),
    ]:
        fields = {}
        for metric, values in totals.items():
            ref = budgets[metric] * 1e6 if compare == 0 else values["previous"]
            delta = values["current"] - ref
            ratio = delta / ref
            fields.update(
                {
                    f"Current FYTD {metric}": values["current"],
                    f"Prev FYTD {metric}": values["previous"],
                    f"{metric} Ref Line": ref,
                    f"{metric} Diff": delta,
                    f"{metric} Diff %": ratio,
                }
            )
        states[name] = {"metrics": fields, "budget_controls_visible": compare == 0}
    return {
        "raw_rows": len(rows),
        "current_month": current.isoformat(),
        "fy_start": fy_start.isoformat(),
        "previous_fy_start": prev_start.isoformat(),
        "totals": totals,
        "monthly": series,
        "states": states,
        "scope": "All 5,582 accounting facts, two complete 20-month series, October fiscal-year cutoffs, Sales prefix5 and OPP prefix5 or696, and all FYTD/reference/difference ratios.",
    }


def numeric(value, expected, sign_hint=None):
    import re

    text = value.strip().replace(",", "").replace("$", "").replace("%", "")
    if not text:
        assert expected is None
        return
    assert expected is not None
    factor = 0.01 if "%" in value else (1e6 if text.endswith("M") else 1)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    assert match, value
    clean = match.group()
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    actual = float(clean) * factor
    # Tableau REST replaces some custom triangle glyphs with U+FFFD. The
    # independently checked percentage in the same KPI CSV retains the sign.
    if "\u25bc" in text or (
        "\ufffd" in text and sign_hint is not None and sign_hint < 0
    ):
        actual = -abs(actual)
    tolerance = 0.501 * 10 ** (-decimals) * factor + 1e-9
    assert abs(actual - expected) <= tolerance, (value, actual, expected, tolerance)


def cloud(data):
    import calendar

    file = HERE / "evidence/cloud-verification.json"
    if not file.exists():
        return []
    report = json.loads(file.read_text())
    assert (
        report["source_hashes"]["replica"]
        == sha256((HERE / "outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    )
    provenance = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert report["source_hashes"]["author"] == provenance["export_sha256"]
    assert not report["browser_interaction_executed"]
    assert [s["name"] for s in report["states"]] == list(data["states"])
    monthly = {
        (calendar.month_name[int(row["month"][5:7])], row["fiscal_year"]): row
        for row in data["monthly"]
    }
    checks = []
    for state in report["states"]:
        expected = data["states"][state["name"]]["metrics"]
        budgets = {"Sales": 2300, "OPP": 3000}
        if state["name"] == "low-budget":
            budgets = {"Sales": 100, "OPP": 100}
        if state["name"] == "high-budget":
            budgets = {"Sales": 4000, "OPP": 4500}
        source_metrics = {}
        for metric in ("Sales", "OPP"):
            current = data["totals"][metric]["current"]
            previous = data["totals"][metric]["previous"]
            budget = budgets[metric] * 1e6
            source_metrics.update(
                {
                    f"Current FYTD {metric}": current,
                    f"Prev FYTD {metric}": previous,
                    f"Curr v Prev {metric} Diff": current - previous,
                    f"Curr v Prev {metric} Diff %": (current - previous) / previous,
                    f"Min. Budget {metric} Ref Line": budget,
                    f"Curr v Budget {metric} Diff": current - budget,
                    f"Curr v Budget {metric} Diff %": (current - budget) / budget,
                    f"{metric} Ref Line": expected[f"{metric} Ref Line"],
                }
            )
        for image in state["views"].values():
            assert (
                sha256((HERE / image["path"]).read_bytes()).hexdigest()
                == image["sha256"]
            )
        for capture in state["data"]:
            path = HERE / capture["path"]
            assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
            rows = list(
                csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines())
            )
            rows = [{k.strip(): v for k, v in row.items()} for row in rows]
            assert rows, (path, "Empty CSV is not evidence")
            seen = set()
            numeric_count = 0
            view = capture["view"]
            if view == "Data":
                metrics = source_metrics if capture["role"] == "author" else expected
                for row in rows:
                    name = row["Measure Names"].strip()
                    assert name in metrics, (capture, row)
                    numeric(row["Measure Values"], metrics[name])
                    seen.add(name)
                    numeric_count += 1
                assert seen == set(metrics), (path, seen, set(metrics))
                scope = "All16 original prior/budget/current/reference diagnostic metrics or all10 replica selected-comparison metrics, at actual CSV decimal precision."
            elif view.endswith("Trend"):
                metric = view.split()[0]
                for row in rows:
                    year_text = row.get(
                        "Year of Accounting Date", row.get("Fiscal Year", "")
                    ).strip()
                    month = row["Month of Accounting Date"].strip()
                    value = row.get(metric, "").strip()
                    latest = row.get(f"Current Month {metric}", "").strip()
                    if year_text and value:
                        year = int(year_text.removeprefix("FY "))
                        key = (month, year)
                        assert key in monthly, (path, row)
                        numeric(value, monthly[key][metric])
                        numeric_count += 1
                        seen.add(key)
                    elif value:
                        raise AssertionError(
                            ("Undeclared year for numeric trend mark", path, row)
                        )
                    if latest:
                        assert month == "May"
                        numeric(latest, monthly[("May", 2020)][metric])
                        numeric_count += 1
                    elif year_text == "FY 2020" and month == "May":
                        # The Circle pane may export its latest marker separately.
                        assert any(
                            r.get(f"Current Month {metric}", "").strip() for r in rows
                        )
                assert seen == set(monthly), (path, set(monthly) - seen)
                scope = "Every20 nonnull month/year aggregate (12prior,8current), latest May2020 marker, null domain-completion marks explicitly excluded."
            elif view.endswith("Bar") or view.endswith("KPI"):
                metric = view.split()[0]
                for row in rows:
                    ratio_text = row.get(f"{metric} Diff %", "")
                    sign_hint = (
                        float(ratio_text.replace("%", "")) if ratio_text else None
                    )
                    for name in (
                        f"Current FYTD {metric}",
                        f"{metric} Ref Line",
                        f"{metric} Diff",
                        f"{metric} Diff %",
                    ):
                        if name in row:
                            numeric(row[name], expected[name], sign_hint=sign_hint)
                            numeric_count += 1
                            seen.add(name)
                    color = row.get(f"COLOUR:{metric} Diff")
                    if color is not None:
                        ratio = expected[f"{metric} Diff %"]
                        assert color == (
                            "Difference < -5%"
                            if ratio < -0.05
                            else "Difference > 5%"
                            if ratio > 0.05
                            else "-5% <= Difference <= 5%"
                        )
                required = (
                    {f"Current FYTD {metric}", f"{metric} Ref Line"}
                    if view.endswith("Bar")
                    else {f"{metric} Diff", f"{metric} Diff %"}
                )
                assert required <= seen, (path, seen)
                scope = "Complete displayed FYTD/reference bar or signed difference/ratio KPI; triangle-corrupted source CSV uses its independently checked percentage sign."
            elif view == "Year Legend":
                labels = {
                    row.get("Year of Accounting Date", row.get("Fiscal Year", ""))
                    for row in rows
                }
                assert labels == {"FY 2019", "FY 2020"}
                scope = "Both fiscal-year legend members."
            elif view == "Diff Legend":
                labels = {
                    row.get("Account Number", row.get("Legend Label", ""))
                    for row in rows
                }
                assert labels == {
                    "Difference > 5%",
                    "Difference < -5%",
                    "-5% <= Difference <= 5%",
                }
                scope = "All three inclusive/strict difference legend members."
            else:
                raise AssertionError(("Unhandled worksheet", view))
            checks.append(
                {
                    "file": capture["path"],
                    "role": capture["role"],
                    "state": state["name"],
                    "rows": len(rows),
                    "numeric_cells_checked": numeric_count,
                    "scope": scope,
                }
            )
    assert len(checks) == 72
    (HERE / "evidence/cloud-data-comparison.json").write_text(
        json.dumps({"status": "pass", "checks": checks}, indent=2) + "\n"
    )
    return checks


def verify():
    data = oracle()
    output = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    with ZipFile(output) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for item in lock["extracted_data"]:
            assert (
                sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
            )
            assert (
                sha256(
                    z.read(
                        next(
                            n
                            for n in z.namelist()
                            if Path(n).name == Path(item["file"]).name
                        )
                    )
                ).hexdigest()
                == item["sha256"]
            )
    assert len(root.findall("worksheets/worksheet")) == 10
    dates = root.xpath('//column[@name="[Accounting Date]"]')
    assert dates and all(c.get("fiscal-year-start") == "10" for c in dates)
    for metric in ["Sales", "OPP"]:
        trend = root.find(f'worksheets/worksheet[@name="{metric} Trend"]')
        assert trend.xpath('.//pane/mark[@class="Line"]') and trend.xpath(
            './/pane/mark[@class="Circle"]'
        )
        assert trend.xpath('.//encoding[@fold="true" and @synchronized="true"]')
        assert root.xpath(f'worksheets/worksheet[@name="{metric} Bar"]//reference-line')
        month = trend.find(
            "table/view/datasource-dependencies/column-instance[@column='[Accounting Date]'][@derivation='Month']"
        )
        assert month is not None and month.get("type") == "ordinal"
        assert trend.xpath(
            "table/style/style-rule[@element='label']/format[@attr='text-format'][@value='iLLL']"
        )
        assert trend.xpath(
            "table/style/style-rule[@element='label']/format[@attr='text-orientation'][@value='-90']"
        )
        assert (
            len(
                trend.xpath(
                    "table/style/style-rule[@element='axis']/format[@attr='display'][@value='false'][@scope='rows']"
                )
            )
            >= 2
        )
        reference = trend.find(".//reference-line")
        assert reference.get("scope") == "per-table" and reference.get("label") == "Avg"
        assert trend.xpath(
            "table/style/style-rule[@element='refline']/format[@attr='line-pattern-only'][@value='dotted']"
        )
        bar = root.find(f'worksheets/worksheet[@name="{metric} Bar"]')
        assert bar.find("table/panes/pane/encodings/color") is not None
        assert bar.xpath(
            ".//style-rule[@element='mark']/format[@attr='size'][@value='0.74662983417510986']"
        )
        kpi = root.find(f'worksheets/worksheet[@name="{metric} KPI"]')
        assert not kpi.findall("table/panes/pane/encodings/color")
        assert kpi.xpath(
            "table/style/style-rule[@element='table-div']/format[@attr='stroke-color'][@value='#000000']"
        )
    assert root.xpath("//dashboard-zone-visibility-node")
    parameter = root.xpath(
        'datasources/datasource[@name="Parameters"]/column[@caption="Compare Filter"]'
    )[0]
    assert {m.get("value") for m in parameter.findall("members/member")} == {"0", "1"}
    assert parameter.get("alias") == "FYTD vs Budget FYTD"
    for name in ("Year Legend", "Diff Legend"):
        sheet = root.find(f'worksheets/worksheet[@name="{name}"]')
        assert sheet.xpath(
            "table/style/style-rule[@element='label']/format[@attr='display'][@value='false']"
        )
    dashboard = root.find("dashboards/dashboard")
    assert all(
        zone.get("show-title") == "false"
        for zone in dashboard.findall("zones//zone[@name]")
    )
    outlines = dashboard.xpath(
        "zones//zone/zone-style[format[@attr='border-style'][@value='solid'] and format[@attr='border-color'][@value='#898989']]"
    )
    assert len(outlines) == 2
    size = root.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "800" and size.get("maxheight") == "500"
    for metric in ("Sales", "OPP"):
        column = root.xpath(
            "//datasources/datasource/column[@caption=$caption]",
            caption=f"{metric} Diff",
        )[0]
        assert column.get("default-format") == '*\u25b2"$"#,##0,,M;\u25bc"$"#,##0,,M'
    checks = cloud(data)
    result = {
        "case": "ww26",
        "status": "pass",
        "artifact_sha256": sha256(output.read_bytes()).hexdigest(),
        "oracle": data,
        "cloud_status": "passed" if checks else "pending",
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        "PASS WW26 complete fiscal accounting oracle/native controls; cloud="
        + result["cloud_status"]
    )
    return result


if __name__ == "__main__":
    verify()
