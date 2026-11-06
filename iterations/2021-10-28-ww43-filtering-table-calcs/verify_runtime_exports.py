"""Check saved REST exports against the raw-row oracle; no live actions inferred."""
import csv
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from verify_replication import raw_rows, oracle, SENTINEL

HERE = Path(__file__).resolve().parent
FROZEN = "83893921f3dbaa372e88baa3a82f3027e352f1828ddbab242d63efa10fedc379"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    return Decimal(value.replace("$", "").replace(",", "").strip())


def month(value):
    return datetime.strptime(value, "%m/%d/%Y").date().isoformat()


def verify():
    assert digest(HERE / "outputs/replicated-workbook.twbx") == FROZEN
    captures = json.loads((HERE / "evidence/cloud-verification.json").read_text(encoding="utf8"))
    exports = json.loads((HERE / "evidence/cloud-csv.json").read_text(encoding="utf8"))
    for manifest in (captures, exports):
        assert manifest["source_hashes"]["replica"] == FROZEN
    assert captures["browser_interaction_executed"] is False
    for state in captures["states"]:
        for record in state["views"].values():
            assert digest(HERE / record["path"]) == record["sha256"]
    for record in exports["records"]:
        assert digest(HERE / record["path"]) == record["sha256"]

    rows = raw_rows()
    full_months = sorted({row[0].isoformat() for row in rows})
    results = []
    for state, expected_count in (("default", 48), ("june-2018", 1), ("copiers-full", 32), ("machines-full", 39)):
        records = {(r["role"], r["view"]): r for r in exports["records"] if r["state"] == state}
        trend_record = records[("replica", "Trend")]
        categories = [trend_record["filters"]["Sub-Category"]] if trend_record["filters"] else None
        start = end = date(2018, 6, 1) if state == "june-2018" else SENTINEL
        expected, expected_bars, lo, hi = oracle(rows, start, end, categories)
        expected = {m: (sales, rolling) for m, sales, rolling in expected}
        observed = {}
        for row in read_rows(HERE / trend_record["path"]):
            key = month(row["Order Date Month"])
            values = number(row["Sales"]), number(row["Rolling Average"])
            assert key not in observed or observed[key] == values, (state, key, "inconsistent duplicate pane rows")
            observed[key] = values
        assert set(observed) == set(expected) and len(observed) == expected_count
        raw_error = max(abs(observed[m][i] - expected[m][i]) for m in observed for i in (0, 1))
        assert raw_error <= Decimal("0.00501"), (state, raw_error)
        author = {}
        for row in read_rows(HERE / records[("author", "Data")]["path"]):
            key = month(row["Order Date Month"])
            if lo.isoformat() <= key <= hi.isoformat():
                metric = "sales" if row["Measure Names"] == "Sales" else "rolling"
                value = number(row["Measure Values"])
                assert (key, metric) not in author or author[key, metric] == value
                author[key, metric] = value
        assert set(m for m, _ in author) == set(observed)
        author_error = max(abs(author[m, metric] - expected[m][i]) for m in observed for i, metric in enumerate(("sales", "rolling")))
        assert author_error <= Decimal("0.00051"), (state, author_error)

        # Direct REST category filtering applies to Bars too, unlike the desired
        # native action (Bars -> Trend only). Check the actual exported scope.
        if categories:
            expected_bars = [r for r in expected_bars if r[0] in categories]
        expected_bars = {c: (sales, avg) for c, sales, avg in expected_bars}
        observed_bars = {}
        for row in read_rows(HERE / records[("replica", "Bars")]["path"]):
            key = row["Sub-Category"]
            values = number(row["Sales"]), number(row["Avg Monthly Sales"])
            assert key not in observed_bars or observed_bars[key] == values
            observed_bars[key] = values
        assert set(observed_bars) == set(expected_bars)
        bar_error = max(abs(observed_bars[c][i] - expected_bars[c][i]) for c in observed_bars for i in (0, 1))
        assert bar_error <= Decimal("0.00501"), (state, bar_error)
        results.append({
            "state": state, "status": "pass", "observed_months": len(observed),
            "missing_from_full_calendar": [m for m in full_months if m not in observed],
            "bar_categories": len(observed_bars), "raw_trend_max_error": str(raw_error),
            "author_data_max_error": str(author_error), "bar_max_error": str(bar_error),
            "first_three_observed": [{"month": m, "sales": str(observed[m][0]), "rolling": str(observed[m][1])} for m in sorted(observed)[:3]],
            "actual_scope": "REST category filter also applies to Bars" if categories else "REST parameter injection" if state == "june-2018" else "initial view"
        })
    report = {
        "artifact_sha256": FROZEN, "status": "pass-with-scoped-runtime-coverage",
        "sources": ["evidence/cloud-verification.json", "evidence/cloud-csv.json", "inputs/WOW2021_Superstore_Orders.csv"],
        "scenario_results": results, "browser_interaction_executed": False,
        "limits": [
            "Author comparison uses its development Data sheet, not Chart.",
            "Observed exported monthly marks agree for Copiers and Machines; this is not exhaustive dashboard densification testing.",
            "REST filters affect Bars directly and do not test native action isolation.",
            "Drag, min/max selection aggregation, clear, repeated zoom, multi-select and reset remain unverified."
        ]
    }
    (HERE / "evidence/cloud-data-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": report["status"], "states": [{"name": r["state"], "months": r["observed_months"], "bar_categories": r["bar_categories"]} for r in results]}, indent=2))


if __name__ == "__main__":
    verify()
