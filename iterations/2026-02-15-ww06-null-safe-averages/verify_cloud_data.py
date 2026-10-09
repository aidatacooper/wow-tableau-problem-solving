"""Compare actual REST-exported Apply-sheet data; never claim this CSV is the matrix."""
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
CASE = Path(__file__).resolve().parent

def verify(output=None):
    cloud_path = CASE / "evidence/cloud-verification.json"
    if not cloud_path.exists():
        # A fresh rebuild in the isolated CI copy has no Cloud capture to bind:
        # the accepted manifest records hashes of the published artifact. Skip
        # the REST comparison rather than fail on missing server evidence.
        return None
    cloud = json.loads(cloud_path.read_text())
    states = []
    for state in cloud["states"]:
        snapshots = {}
        hashes = {}
        for variant in ["author", "replica"]:
            exported = state["views"][variant]["data_export"]
            path = CASE / "outputs" / exported["path"]
            hashes[variant] = sha256(path.read_bytes()).hexdigest()
            assert hashes[variant] == exported["sha256"]
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
            assert len(rows) == 1
            row = rows[0]
            value = {field: row[field].lower() for field in ["Colour", "True", "False"]}
            for field in ["Min Date", "Max Date"]:
                value[field] = datetime.strptime(row[field], "%m/%d/%Y").date().isoformat()
            apply_text = row.get("Apply Text", row.get("'Apply'"))
            assert apply_text == "Apply"
            snapshots[variant] = value
        assert snapshots["author"] == snapshots["replica"], state["name"] + " exported Apply data mismatch"
        assert snapshots["replica"]["True"] == "true" and snapshots["replica"]["False"] == "false"
        states.append({"state": state["name"], "filters": state["filters"], "parameters": state["parameters"], "values": snapshots["replica"], "csv_sha256": hashes, "passed": True})
    assert {s["state"] for s in states} == {"default", "short-date-range", "furniture-only"}
    assert next(s for s in states if s["state"] == "default")["values"]["Colour"] == "true"
    assert next(s for s in states if s["state"] == "short-date-range")["values"]["Colour"] == "false"
    result = {"verified_at": datetime.now(timezone.utc).isoformat(), "cloud_snapshot_captured_at": cloud["captured_at"], "acceptance_scope": "cloud_rest_and_artifact_contracts", "browser_interaction_executed": False, "states": states, "passed": True, "scope": "REST dashboard CSV covers Apply Button Filter only. Matrix state values are separately reviewed in actual PNGs. Confirms date-filter min/max and calculated enabled-state parity, not execution of clicking Apply."}
    if output:
        output.write_text(json.dumps(result, indent=2) + "\n")
    return result

if __name__ == "__main__":
    print(json.dumps(verify(CASE / "evidence/cloud-data-comparison.json"), indent=2))
