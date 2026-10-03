"""Independent weekday calendar, MTD facts and monthly-plan verification."""

import calendar
import csv
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance: ww17-independent-data, ww17-artifact-contracts, ww17-cloud-states.


def hyper_rows(filename, columns):
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(HERE / "inputs" / filename)) as conn,
    ):
        table = next(
            t
            for s in conn.catalog.get_schema_names()
            for t in conn.catalog.get_table_names(s)
        )
        return conn.execute_list_query(
            "SELECT " + ",".join('"' + c + '"' for c in columns) + " FROM " + str(table)
        )


def weekdays(first, last):
    return sum(
        (first + timedelta(days=n)).weekday() < 5
        for n in range((last - first).days + 1)
    )


def oracle():
    rows = hyper_rows(
        "TEMP_0w4rjxf1y3op0w154ltbd1f67pji.hyper", ["Region", "Date", "Sales"]
    )
    plans = hyper_rows(
        "TEMP_0jid4k908s0rnf1fdypy20ecq2fb.hyper", ["Region", "Date", "Plan"]
    )
    today = max(date(d.year, d.month, d.day) for _, d, _ in rows)
    start = today.replace(day=1)
    end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elapsed = weekdays(start, today)
    total = weekdays(start, end)
    facts = defaultdict(list)
    plan = {}
    for region, d, value in plans:
        if (d.year, d.month) == (today.year, today.month):
            assert region not in plan
            plan[region] = float(value)
    for region, d, sales in rows:
        if start <= date(d.year, d.month, d.day) <= today:
            facts[region].append(float(sales))
    values = []
    for region in sorted(plan):
        mtd = math.fsum(facts[region])
        run = mtd / elapsed * total
        values.append(
            {
                "Region": region,
                "MTD": mtd,
                "Run Rate": run,
                "Plan": plan[region],
                "below_plan": run < plan[region],
            }
        )
    assert (
        len(rows) == 92
        and len(plans) == 4
        and today.isoformat() == "2020-04-23"
        and elapsed == 17
        and total == 22
    )
    # Weekend and month-boundary cases independently exercise the business calendar.
    assert weekdays(date(2020, 2, 1), date(2020, 2, 29)) == 20
    assert weekdays(date(2020, 3, 1), date(2020, 3, 31)) == 22
    assert weekdays(date(2020, 4, 1), date(2020, 4, 25)) == 18
    return {
        "actual_row_count": len(rows),
        "plan_row_count": len(plans),
        "as_of": today.isoformat(),
        "elapsed_weekdays": elapsed,
        "month_weekdays": total,
        "values": values,
        "business_scope": "All four region MTD sums; weekday-only elapsed/full-month denominator; one monthly Plan per region, never repeated by daily actual count.",
    }


def verify_cloud(data):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return []
    report = json.loads(manifest.read_text(encoding="utf-8"))
    assert (
        report["source_hashes"]["replica"]
        == sha256((HERE / "outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    )
    assert [s["name"] for s in report["states"]] == ["default"]
    state = report["states"][0]
    checks = []
    lookup = {v["Region"]: v for v in data["values"]}
    for capture in [*state["views"].values(), *state["data"]]:
        assert (
            sha256((HERE / capture["path"]).read_bytes()).hexdigest()
            == capture["sha256"]
        )
    for capture in state["data"]:
        p = HERE / capture["path"]
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if rows and "Measure Names" in rows[0]:
            pivot = {}
            for row in rows:
                dimensions = {
                    k: v
                    for k, v in row.items()
                    if k not in {"Measure Names", "Measure Values"}
                }
                key = tuple(dimensions.items())
                name = row["Measure Names"].split(" along ")[0]
                target = pivot.setdefault(key, dimensions)
                assert name not in target, (p, name, dimensions)
                target[name] = row["Measure Values"]
            rows = list(pivot.values())
        seen = set()
        cells = set()
        for row in rows:
            region = row["Region"]
            assert region in lookup
            seen.add(region)
            for metric in ("MTD", "Run Rate", "Plan"):
                raw = next(
                    (
                        v
                        for k, v in row.items()
                        if k == metric
                        or k == ("MTD Sales" if metric == "MTD" else metric)
                        or k.endswith("(" + metric + ")")
                    ),
                    None,
                )
                assert raw is not None, (p, metric, row)
                actual = float(raw.replace("$", "").replace(",", ""))
                assert abs(actual - lookup[region][metric]) <= 0.51, (
                    p,
                    region,
                    metric,
                    actual,
                    lookup[region][metric],
                )
                cells.add((region, metric))
        assert seen == set(lookup) and len(cells) == 12, (p, seen, cells)
        checks.append(
            {
                "file": capture["path"],
                "regions": 4,
                "metric_cells": 12,
                "scope": "Every region monthly MTD, run rate and plan; independent17/22-weekday calendar.",
            }
        )
    assert len(checks) == 2
    (HERE / "evidence/cloud-data-comparison.json").write_text(
        json.dumps({"status": "pass", "checks": checks}, indent=2) + "\n",
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
    assert len(r.xpath('datasources/datasource[@name!="Parameters"]')) == 2
    viz = r.xpath('worksheets/worksheet[@name="Viz"]/table')[0]
    assert len(viz.xpath("view/datasources/datasource")) == 2
    assert len(viz.findall("join-lod-include-overrides/column")) == 2
    assert viz.xpath('panes/pane/mark[@class="Bar"]') and viz.xpath(
        'panes/pane/mark[@class="GanttBar"]'
    )
    assert viz.xpath(
        'style/style-rule[@element="axis"]/encoding[@fold="true" and @synchronized="true"]'
    )
    assert len(r.xpath("worksheets/worksheet")) == 3
    size = r.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "375" and size.get("maxheight") == "667"
    assert r.xpath('//customized-label//run[@fontcolor="#e03426"]')
    checks = verify_cloud(data)
    result = {
        "case": "ww17",
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
        "PASS: WW17 complete region weekday run rates and native blend/phone-size contracts; cloud="
        + result["cloud_status"]
    )
    return result


if __name__ == "__main__":
    verify()
