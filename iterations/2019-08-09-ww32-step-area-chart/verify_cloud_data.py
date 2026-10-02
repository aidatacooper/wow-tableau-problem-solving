"""Compare Cloud CSV snapshots without treating data equality as visual acceptance."""
import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

FIELDS = ["Colour:Diff", "LABEL: Max Diff + Shift", "LABEL: Min Diff + Shift", "LABEL:First Last if not max or min", "LABEL:Sales in Month Max", "LABEL:Sales in Month Min", "Sales Next Value", "Size - Dual Axis", "Measure Values", "Sales In Month"]

def compare(author_path, replica_path):
    def read(path):
        with path.open(encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))
    author, replica = read(author_path), read(replica_path)
    def key(row):
        return (row["Category"].lower(), row["Day of Month Position To Plot"], row["Measure Names"].split(" along ")[0])
    a = {key(row): row for row in author}
    b = {key(row): row for row in replica}
    assert len(a) == len(author) and len(b) == len(replica), "duplicate normalized row keys"
    assert a.keys() == b.keys(), "different dimension/measure keys"
    differences = [{"key": k, "field": field, "author": a[k][field], "replica": b[k][field]} for k in sorted(a) for field in FIELDS if a[k][field] != b[k][field]]
    result = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "author_csv_sha256": sha256(author_path.read_bytes()).hexdigest(),
        "replica_csv_sha256": sha256(replica_path.read_bytes()).hexdigest(),
        "author_rows": len(author), "replica_rows": len(replica),
        "key_fields": ["Category", "Day of Month Position To Plot", "Measure Names"],
        "normalization": {"Category": "lowercase caption only", "Measure Names": "strip author addressing annotation after literal ' along '"},
        "keys_equal": True, "compared_fields": FIELDS,
        "cell_differences": len(differences), "differences": differences,
        "scope": "Default Cloud view data only; not visual acceptance or interactive behavior",
    }
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("author_csv", type=Path)
    parser.add_argument("replica_csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.author_csv, args.replica_csv)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    raise SystemExit(0 if result["cell_differences"] == 0 else 1)
