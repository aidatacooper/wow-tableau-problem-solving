"""Fail-closed checks for the WW44 PAT REST capture contract.

The verifier consumes manifests produced by the Cloud REST capture job.  It
does not authenticate, publish, or claim browser actions.  A future capture
can be checked by passing its manifest paths explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT_SHA = "07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd"
EXPECTED_STATES = {"default", "quarter", "year"}
EXPECTED_PARAMS = {
    "default": {},
    "quarter": {"pDatePart": "Quarter", "Period": "Quarter"},
    "year": {"pDatePart": "Year", "Period": "Year"},
}
EXPECTED_VIEWS = {"Period KPIs", "Profit Performers", "WW44 Profit Performers"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_cloud_manifest(path: Path, case_dir: Path) -> int:
    manifest = load(path)
    assert manifest.get("acceptance_scope") == "cloud_rest_and_artifact_contracts"
    assert manifest.get("browser_interaction_executed") is False
    assert manifest["source_hashes"]["replica"] == ARTIFACT_SHA
    assert set(item["name"] for item in manifest["states"]) == EXPECTED_STATES
    workbooks = manifest["workbooks"]
    assert workbooks["author"]["views"][0]["id"] == "d46c7d95-6b21-4a1e-a99a-a7b7ce77bc8d"
    assert workbooks["replica"]["views"][2]["id"] == "a0c499a4-319e-42de-a465-d73ab27f41be"
    for state in manifest["states"]:
        assert state["parameters"] == EXPECTED_PARAMS[state["name"]]
        for role in ("author", "replica"):
            view = state["views"][role]
            image = case_dir / view["path"]
            assert image.is_file(), image
            assert sha(image) == view["sha256"], image
            assert png_size(image) == tuple(view["size"]), image
    return len(manifest["states"])


def check_csv_manifest(path: Path, case_dir: Path) -> int:
    manifest = load(path)
    assert manifest["source_hashes"]["replica"] == ARTIFACT_SHA
    assert manifest["scope"] == "REST worksheet data, no browser events"
    records = manifest["records"]
    assert len(records) == 9
    seen = set()
    for record in records:
        assert record["role"] == "replica"
        assert record["view"] in EXPECTED_VIEWS
        assert record["state"] in EXPECTED_STATES
        assert record["parameters"] == EXPECTED_PARAMS[record["state"]]
        key = (record["view"], record["state"])
        assert key not in seen, key
        seen.add(key)
        csv_path = case_dir / record["path"]
        assert csv_path.is_file(), csv_path
        assert sha(csv_path) == record["sha256"], csv_path
        assert csv_path.stat().st_size == record["bytes"], csv_path
    assert {state for _, state in seen} == EXPECTED_STATES
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud", type=Path, default=HERE / "evidence/cloud-verification.json")
    parser.add_argument("--csv", type=Path, default=HERE / "evidence/cloud-csv.json")
    args = parser.parse_args()
    artifact = HERE / "outputs/replicated-workbook.twbx"
    assert sha(artifact) == ARTIFACT_SHA, artifact
    states = check_cloud_manifest(args.cloud, HERE)
    records = check_csv_manifest(args.csv, HERE)
    print(f"PASS: artifact SHA256 {ARTIFACT_SHA}; {states} REST image states; {records} REST CSV records; browser events unclaimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
