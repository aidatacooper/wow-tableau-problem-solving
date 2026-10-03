"""Independent Hyper date oracle and artifact action/visibility contracts.

Acceptance: ww04-date-oracle, ww04-selector-action, ww04-context-controls,
ww04-cloud-states. ww04-visual uses separately reviewed Cloud images.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import unquote
import csv
import json
import math
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
STATES = [("default", "Last 14 Days", 14), ("last30", "Last 30 Days", 30),
          ("last-n", "Last N Days", 60), ("custom", "Custom Dates", None)]


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c:
        table = next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        records = c.execute_list_query('SELECT "Order Date", "Sales", "Profit" FROM ' + str(table))
    rows = [(date(d.year, d.month, d.day), float(s), float(p)) for d, s, p in records]
    latest = max(d for d, _, _ in rows)
    states = {}
    for state, selector, days in STATES:
        selected = [(d, s, p) for d, s, p in rows if (d > latest - timedelta(days=days) if days else date(2019, 1, 1) <= d <= date(2019, 12, 31))]
        daily = defaultdict(list)
        for d, sales, profit in selected:
            daily[d.isoformat()].append(sales)
        sales, profit = math.fsum(r[1] for r in selected), math.fsum(r[2] for r in selected)
        states[state] = {"selector": selector, "row_count": len(selected), "sales": sales, "profit": profit,
                         "profit_ratio": profit / sales, "daily_sales": {d: math.fsum(v) for d, v in sorted(daily.items())},
                         "first_date": min(d for d, _, _ in selected).isoformat(), "last_date": max(d for d, _, _ in selected).isoformat()}
    assert len(rows) == 9994 and latest == date(2019, 12, 30)
    assert states["default"]["first_date"] > (latest - timedelta(days=14)).isoformat()
    assert states["custom"]["last_date"] == latest.isoformat()
    return {"source_rows": len(rows), "latest_date": latest.isoformat(), "states": states}


def verify_cloud(data):
    """Check all KPI and daily-sales CSV rows, with Cloud display rounding."""
    checks = []
    for state, _, _ in STATES:
        suffix = "" if state == "default" else "-" + state
        expected = data["states"][state]
        for role in ["author", "replica"]:
            kpi = HERE / f"outputs/cloud-{role}-kpis{suffix}.csv"
            trend = HERE / f"outputs/cloud-{role}-trend{suffix}.csv"
            if not kpi.exists() or not trend.exists():
                continue
            with kpi.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            assert len(rows) == 3
            for row in rows:
                name = row["Measure Names"]
                key = {"Sales": "sales", "Profit": "profit", "Profit Ratio": "profit_ratio"}[name]
                raw = row["Measure Values"].replace(",", "").replace("$", "")
                actual = float(raw.rstrip("%")) / (100 if raw.endswith("%") else 1)
                places = len(raw.rstrip("%").split(".")[1]) if "." in raw else 0
                tolerance = (0.5 * 10 ** -places) / (100 if raw.endswith("%") else 1) + 1e-8
                assert abs(actual - expected[key]) <= tolerance, (kpi, key, actual, expected[key])
            with trend.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            actual_dates = set()
            date_counts = Counter()
            for row in rows:
                date_column = next(k for k in row if "Order Date" in k)
                text = row[date_column]
                parsed = None
                for pattern in ["%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        parsed = datetime.strptime(text, pattern).date().isoformat()
                        break
                    except ValueError:
                        continue
                assert parsed is not None, (trend, text)
                actual_dates.add(parsed)
                date_counts[parsed] += 1
                amount = float(row["Sales"].replace(",", "").replace("$", ""))
                assert abs(amount - expected["daily_sales"][parsed]) <= 0.500001, (trend, parsed, amount)
            assert actual_dates == set(expected["daily_sales"]), (trend, actual_dates)
            assert set(date_counts.values()) <= {1, 2} and len(set(date_counts.values())) == 1
            checks.append({"role": role, "state": state, "daily_marks": len(actual_dates), "kpi_rows": 3,
                           "csv_rows": len(rows), "axis_copies_per_date": next(iter(date_counts.values())),
                           "files": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in [kpi, trend]}})
    report = {"status": "pass", "scope": "All three KPI values and complete daily-sales series for each exported state; no selector-button CSV used as data proof.", "checks": checks}
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/cloud-data-checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def verify():
    artifact = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(artifact) as z:
        root = etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))
        packaged_hypers = [sha256(z.read(n)).hexdigest() for n in z.namelist() if n.endswith(".hyper")]
    dashboard = root.find("dashboards/dashboard")
    assert dashboard.get("name") == "2020_01_22_WW04_Relative_and_Custom_Dates"
    assert {w.get("name") for w in root.findall("worksheets/worksheet")} == {"BANs", "Selector", "Sales trend"}
    columns = {c.get("caption", c.get("name").strip("[]")): c for c in root.findall("datasources/datasource/column")}
    assert columns["Date Selector"].get("value") == '"Last 14 Days"'
    assert "DATEADD('day',-14" in columns["In Timeframe"].find("calculation").get("formula")
    for sheet in ["BANs", "Sales trend"]:
        ws = root.find(f"worksheets/worksheet[@name='{sheet}']")
        assert any(n.get("member") == "true" for n in ws.findall("table/view/filter/groupfilter"))
    action = root.find("actions/edit-parameter-action")
    assert action.find("source").get("worksheet") == "Selector"
    assert action.find("activation").get("type") == "on-select"
    assert action.find("params/param[@name='source-field']").get("value").endswith(".[:Measure Names]")
    assert action.find("params/param[@name='target-parameter']").get("value") == "[Parameters]." + columns["Date Selector"].get("name")
    assert action.find("clear-option") is None
    reset = root.find("actions/action")
    assert reset.find("command/param[@name='target']").get("value") == "Selector"
    assert reset.find("source").get("worksheet") == "Selector"
    assert reset.find("activation").get("type") == "on-select"
    assert reset.find("activation").get("auto-clear") == "true"
    link = unquote(reset.find("link").get("expression"))
    assert columns["True"].get("name") in link and columns["False"].get("name") in link
    assert len(root.findall("datagraph/graph/nodes/dashboard-zone-visibility-node")) == 2
    fields = [n.get("fieldname") for n in root.findall("datagraph/graph/nodes/single-value-field-node")]
    assert any(columns["Show N Days"].get("name") in f for f in fields)
    assert any(columns["Show Custom Dates"].get("name") in f for f in fields)
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    assert lock["source_workbook_used_by_builder"] is False
    for item in lock["extracted_data"]:
        assert sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
        assert item["sha256"] in packaged_hypers
    provenance_file = HERE / "evidence/export-provenance.json"
    if provenance_file.exists():
        provenance = json.loads(provenance_file.read_text(encoding="utf-8"))
        assert provenance["original_sha256"] == lock["locked_original_sha256"]
        assert provenance["comparison_used_by_replica_builder"] is False
    cloud_file = HERE / "evidence/cloud-verification.json"
    if cloud_file.exists():
        cloud_capture = json.loads(cloud_file.read_text(encoding="utf-8"))
        assert cloud_capture["source_hashes"]["replica"] == sha256(artifact.read_bytes()).hexdigest()
        assert cloud_capture["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert cloud_capture["browser_interaction_executed"] is False
        assert {state["name"] for state in cloud_capture["states"]} == {state for state, _, _ in STATES}
        for state in cloud_capture["states"]:
            for export in list(state["views"].values()) + state["data"]:
                assert sha256((HERE / export["path"]).read_bytes()).hexdigest() == export["sha256"]
    result = oracle()
    if (HERE / "outputs/cloud-replica-kpis-custom.csv").exists():
        cloud = verify_cloud(result)
        assert len(cloud["checks"]) == 8
        result["cloud_csv_status"] = cloud["status"]
    result.update({"status": "pass", "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                   "interaction_scope": "Serialized selector parameter/filter actions and zone visibility; no browser event execution claimed."})
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
