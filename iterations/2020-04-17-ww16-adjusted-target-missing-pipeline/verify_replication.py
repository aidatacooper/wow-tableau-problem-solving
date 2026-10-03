"""Independent pipeline facts and monthly-target oracle; full blend acceptance."""

import calendar
import csv
import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance: ww16-independent-data, ww16-artifact-contracts, ww16-cloud-states.


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


def oracle():
    rows = hyper_rows(
        "Pipeline (2020_04_15_WW16_Sales Pipeline).hyper",
        ["Closed Date", "Stage", "Sales"],
    )
    targets = hyper_rows(
        "Monthly Target (2020_04_15_WW16_Sales Pipeline).hyper", ["Date", "Target"]
    )
    target = {d.month: float(v) for d, v in targets}
    closed = defaultdict(list)
    pipeline = defaultdict(list)
    for d, stage, sales in rows:
        if d.year != 2020:
            continue
        if stage == "Closed Won":
            closed[d.month].append(float(sales))
        if stage in {"Negotiating", "Proposing"}:
            pipeline[d.month].append(float(sales))
    ytd_closed = math.fsum(v for m, values in closed.items() if m < 4 for v in values)
    ytd_target = math.fsum(v for m, v in target.items() if m < 4)
    missed = ytd_target - ytd_closed
    distributed = missed / 9
    values = []
    for m in range(1, 13):
        cw = math.fsum(closed[m])
        pl = math.fsum(pipeline[m]) if pipeline[m] else None
        adjusted = target[m] + distributed if m >= 4 else None
        missing = None
        if pl:
            if m == 4:
                missing = max(0.0, adjusted - cw - pl) if cw + pl < adjusted else None
            elif m > 4:
                missing = max(0.0, adjusted - pl)
            else:
                missing = 0.0
        values.append(
            {
                "month": m,
                "Closed Won": cw,
                "Pipeline": pl,
                "Target": target[m],
                "YTD Closed": ytd_closed,
                "YTD Target": ytd_target,
                "Missed Sales Value": missed,
                "Remaining Months": 9,
                "Distributed Missed Sales Value": distributed,
                "Adjusted Target": adjusted,
                "Missing Pipeline": missing,
            }
        )
    assert len(rows) == 9994 and len(targets) == 12
    return {
        "pipeline_row_count": len(rows),
        "target_row_count": len(targets),
        "as_of": "2020-04-15",
        "values": values,
        "business_scope": "2020 month aggregates; completed-month closed/target YTD shortfall distributed over nine current/future months. Native blending never multiplies monthly targets by opportunity count.",
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
    for capture in [*state["views"].values(), *state["data"]]:
        assert (
            sha256((HERE / capture["path"]).read_bytes()).hexdigest()
            == capture["sha256"]
        )
    lookup = {v["month"]: v for v in data["values"]}
    metrics = [
        "Closed Won",
        "Pipeline",
        "Target",
        "YTD Closed",
        "YTD Target",
        "Missed Sales Value",
        "Distributed Missed Sales Value",
        "Adjusted Target",
        "Missing Pipeline",
    ]
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
            raw = next(v for k, v in row.items() if "Closed Date" in k or k == "Month")
            names = {calendar.month_name[i]: i for i in range(1, 13)} | {
                calendar.month_abbr[i]: i for i in range(1, 13)
            }
            month = names.get(raw.strip())
            if month is None:
                month = int(raw.split("/")[0]) if "/" in raw else int(raw)
            seen.add(month)
            for metric in metrics:
                matches = [
                    v
                    for k, v in row.items()
                    if k == metric or k.endswith("(" + metric + ")")
                ]
                if not matches:
                    continue
                rawvalue = matches[0]
                value = lookup[month][metric]
                cells.add((month, metric))
                if value is None:
                    assert not rawvalue.strip(), (p, month, metric, rawvalue)
                else:
                    assert (
                        abs(float(rawvalue.replace("$", "").replace(",", "")) - value)
                        <= 0.51
                    ), (p, month, metric, rawvalue, value)
        assert seen == set(range(1, 13)), (p, seen)
        assert cells == {(m, k) for m in range(1, 13) for k in metrics}, (p, len(cells))
        checks.append(
            {
                "file": capture["path"],
                "months": 12,
                "metric_cells": len(cells),
                "scope": "Full month table, all nine pipeline/target/YTD/shortfall metrics; nullable values checked.",
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
    assert viz.find("join-lod-include-overrides/column") is not None
    assert viz.xpath('.//reference-line[@scope="per-cell"]')
    assert viz.xpath(
        'style/style-rule[@element="refline"]/format[@attr="line-pattern-only" and @value="dotted"]'
    )
    assert viz.xpath('panes/pane/mark[@class="GanttBar"]')
    assert len(r.xpath("worksheets/worksheet")) <= 3
    size = r.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "800" and size.get("maxheight") == "600"
    checks = verify_cloud(data)
    result = {
        "case": "ww16",
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
        "PASS: WW16 twelve monthly native blend aggregates and contracts; cloud="
        + result["cloud_status"]
    )
    return result


if __name__ == "__main__":
    verify()
