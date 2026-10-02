"""Compare real Cloud CSV snapshots; report coverage and numerical precision."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

CASE = Path(__file__).resolve().parent.name

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))

def day(value):
    for pattern in ("%m/%d/%Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Unsupported date: " + value)

def number(value):
    return Decimal(value.replace(",", "").replace("%", "").replace("$", "").strip())

def compare(directory, suffix):
    ap = directory / ("cloud-author" + suffix + ".csv")
    bp = directory / ("cloud-replica" + suffix + ".csv")
    ar, br = rows(ap), rows(bp)
    if "ww04" in CASE:
        def canonical(row):
            return (day(row.get("Display Date", row.get("Day of Display Date"))),), {"Moving Average": row["Moving Average"], "Sales": row["Sales"]}
        numeric = {"Moving Average": Decimal("0.000000001"), "Sales": Decimal("0.000000001")}
        scope = "Daily date keys for chosen aggregation; Sales and Moving Average. Duplicate Measure Names marks are merged only when both numerical values agree."
    elif "ww05" in CASE:
        def canonical(row):
            return ("KPI",), {"PR - Today": row.get("PR - Today", row.get("Avg. PR - Today")), "PR Difference": row.get("PR Difference", row.get("Avg. PR Difference")), "PR Direction Up": row["PR Direction Up"], "PR Direction Down": row["PR Direction Down"]}
        numeric = {"PR - Today": Decimal("0"), "PR Difference": Decimal("0")}
        scope = "Dashboard CSV is KPI sheet only, not trend lines. Percentages compared at displayed 0.1 percentage-point precision; no claim of equality of unrounded source ratios. Author pToday field is absent in replica CSV and not compared."
    else:
        def canonical(row):
            return (row["Month of Order Date"], row["Segment"]), {"% Difference": row["% Difference"], "Avg Orders Per Day Per Segment Per Month": row["Avg Orders Per Day Per Segment Per Month"], "COLOUR:Difference": row["COLOUR:Difference"], "Gantt Size": row.get("Gantt Size", row.get("[Difference]*-1")), "Overall Avg Orders Per Day Per Segment": row["Overall Avg Orders Per Day Per Segment"]}
        numeric = {"% Difference": Decimal("0"), "Avg Orders Per Day Per Segment Per Month": Decimal("0"), "Gantt Size": Decimal("0.000000001"), "Overall Avg Orders Per Day Per Segment": Decimal("0")}
        scope = "36 month/segment marks. Averages compared as exported two-decimal values, percent as exported whole percentage points; Gantt Size compared at CSV precision. Author duplicate tooltip average and replica extra rounded Difference are excluded from field-set equality."
    def keyed(source):
        result = {}
        duplicates = 0
        for row in source:
            key, values = canonical(row)
            if key in result:
                assert result[key] == values, "Conflicting duplicate measure marks: " + str(key)
                duplicates += 1
            result[key] = values
        return result, duplicates
    a, ad = keyed(ar)
    b, bd = keyed(br)
    common = a.keys() & b.keys()
    missing, extra = sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())
    differences = []
    maxima = {f: Decimal("0") for f in numeric}
    for key in sorted(common):
        for field in a[key]:
            if field in numeric:
                delta = abs(number(a[key][field]) - number(b[key][field]))
                maxima[field] = max(maxima[field], delta)
                different = delta > numeric[field]
            else:
                different = a[key][field] != b[key][field]
                delta = None
            if different:
                differences.append({"key": key, "field": field, "author": a[key][field], "replica": b[key][field], "absolute_difference": str(delta) if delta is not None else None})
    return {
        "state": suffix.lstrip("-") or "default",
        "author_csv_sha256": sha256(ap.read_bytes()).hexdigest(),
        "replica_csv_sha256": sha256(bp.read_bytes()).hexdigest(),
        "author_rows": len(ar), "replica_rows": len(br),
        "author_unique_keys": len(a), "replica_unique_keys": len(b),
        "author_duplicate_marks_merged": ad, "replica_duplicate_marks_merged": bd,
        "compared_fields": list(next(iter(a.values()))), "common_keys": len(common),
        "missing_replica_keys": missing, "extra_replica_keys": extra,
        "maximum_absolute_difference_on_common_keys": {f: str(value) for f, value in maxima.items()},
        "numeric_tolerances": {f: str(value) for f, value in numeric.items()},
        "cell_differences": len(differences), "differences": differences,
        "passed": not (missing or extra or differences), "scope": scope,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-dir", type=Path, default=Path(__file__).resolve().parent / "outputs")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    states = ["", "-quarter-six-periods", "-week-six-periods"] if "ww04" in CASE else ["", "-different-today"] if "ww05" in CASE else [""]
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "case": CASE, "normalization": "Parse both date formats to ISO date; remove comma separators and percent/currency symbols for Decimal arithmetic; map explicit semantic column aliases; merge identical measure marks only.", "states": [compare(args.csv_dir, state) for state in states]}
    cloud_metadata = Path(__file__).resolve().parent / "evidence/cloud-verification.json"
    if cloud_metadata.exists():
        snapshot = json.loads(cloud_metadata.read_text())
        report["cloud_snapshot_metadata_at_verification"] = {"captured_at": snapshot.get("captured_at"), "source_hashes": snapshot.get("source_hashes")}
    report["passed"] = all(state["passed"] for state in report["states"])
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    raise SystemExit(0 if report["passed"] else 1)
