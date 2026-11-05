"""Validate PAT REST evidence against the frozen WW41 artifact contract.

This deliberately validates captured files and XML contracts only. It never
claims that a REST parameter request or static action is a browser event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ARTIFACT_SHA = "7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb"
EXPECTED_STATES = {"default", "top-one", "top-sixteen", "top-all"}
EXPECTED_VIEWS = {
    "Contribution Pie",
    "Highlight Table",
    "Contribution Summary",
    "Top Sub-Category Contribution",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", nargs="?", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    case = args.case_dir.resolve()
    verification = json.loads((case / "evidence/cloud-verification.json").read_text(encoding="utf-8"))
    csv_manifest = json.loads((case / "evidence/cloud-csv.json").read_text(encoding="utf-8"))
    assert verification["source_hashes"]["replica"] == ARTIFACT_SHA
    assert verification["browser_interaction_executed"] is False
    assert verification["acceptance_scope"] == "cloud_rest_and_artifact_contracts"
    records = verification["states"]
    assert {item["name"] for item in records} == EXPECTED_STATES
    assert {item["views"]["replica"]["name"] for item in records} == {"Top Sub-Category Contribution"}
    csv_records = csv_manifest["records"]
    assert {item["state"] for item in csv_records} == EXPECTED_STATES
    assert {item["view"] for item in csv_records if item["role"] == "replica"} == EXPECTED_VIEWS
    for item in csv_records:
        path = case / item["path"]
        assert path.is_file(), path
        assert sha256(path) == item["sha256"], path
        assert path.stat().st_size == item["bytes"], path
    print(json.dumps({"status": "rest-contract-pass", "states": sorted(EXPECTED_STATES), "csv_records": len(csv_records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
