"""Independent state/city totals and native set-action contracts."""

import csv
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


# Acceptance: ww30-data-oracle, ww30-native-drill-down, ww30-cloud-rest.
def number(value):
    return float(value.replace(",", "").replace("$", "").strip())


def verify():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        facts = c.execute_list_query(
            'SELECT "State","City","Sales","Profit" FROM "Extract"."Extract"'
        )
    states = {}
    cities = {}
    for state, city, sales, profit in facts:
        for target, key in [(states, state), (cities, state + "|" + city)]:
            pair = target.setdefault(key, [0.0, 0.0])
            pair[0] += sales
            pair[1] += profit
    assert len(facts) == 8399 and len(states) == 48
    data = {
        "fact_rows": len(facts),
        "states": states,
        "cities": cities,
        "scope": "All state totals and every state/city pair independently aggregated from locked raw Hyper.",
    }
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"]:
        assert (
            hashlib.sha256((HERE / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        r = etree.fromstring(
            z.read(next(x for x in z.namelist() if x.endswith(".twb")))
        )
    assert len(r.findall("worksheets/worksheet")) == 1
    assert (
        r.find(
            "datasources/datasource/group[@caption='Selected State']/groupfilter"
        ).get("function")
        == "empty-level"
    )
    a = r.find("actions/edit-group-action[@caption='Drill Down']")
    assert a is not None
    assert a.find("activation").get("type") == "on-select" and (
        a.find("add-or-remove-marks") is None
        or a.find("add-or-remove-marks").get("value") == "assign"
    )
    assert (
        a.find("params/param[@name='selection-clear-set-option']").get("value")
        == "exclude-all"
    )
    assert (
        r.find("datasources/datasource/column[@caption='Profit to Plot']/calculation")
        .get("formula")
        .startswith("IF ATTR([Selected State])")
    )
    sheet = r.find("worksheets/worksheet[@name='Scatter']")
    fs = sheet.findall("table/view/filter")
    assert len(fs) == 1 and fs[0].find("groupfilter").get("member") == "true"
    axis = sheet.find("table/style/style-rule[@element='axis']")
    assert {f.get("value") for f in axis.findall("format[@attr='title']")} >= {
        "Sales",
        "Profit",
    }
    manifest = HERE / "evidence/cloud-verification.json"
    checks = []
    if manifest.exists():
        report = json.loads(manifest.read_text())
        expected_states = {
            "default": {},
            "california": {"State": "California"},
            "texas": {"State": "Texas"},
        }
        expected_exports = {("author", "Scatter"), ("replica", "Scatter")}
        records = report["states"]
        assert len(records) == len(expected_states)
        assert {record["name"] for record in records} == set(expected_states)
        provenance = json.loads((HERE / "evidence/export-provenance.json").read_text())
        assert provenance["original_sha256"] == lock["source_workbook"]["sha256"]
        assert report["source_hashes"]["author"] == provenance["export_sha256"]
        for record in records:
            assert record["filters"] == expected_states[record["name"]]
            assert record["parameters"] == {}
            assert set(record["views"]) == {"author", "replica"}
            assert len(record["data"]) == len(expected_exports)
            assert {
                (entry["role"], entry["view"]) for entry in record["data"]
            } == expected_exports
            assert len({entry["path"] for entry in record["data"]}) == len(
                expected_exports
            )
        assert report.get("browser_interaction_executed") is False
        for state_record in report["states"]:
            entries = list(state_record["views"].values()) + state_record["data"]
            for entry in entries:
                file = HERE / entry["path"]
                assert (
                    file.is_file()
                    and hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"]
                ), entry["path"]

        assert report["source_hashes"]["replica"] == digest
        for state in report["states"]:
            suffix = "" if state["name"] == "default" else "-" + state["name"]
            expected = (
                states
                if state["name"] == "default"
                else {state["filters"]["State"]: states[state["filters"]["State"]]}
            )
            for role in ["author", "replica"]:
                rows = list(
                    csv.DictReader(
                        (HERE / f"outputs/cloud-{role}-scatter{suffix}.csv").open(
                            encoding="utf-8-sig"
                        )
                    )
                )
                actual = {
                    row["Display Value"]: [
                        number(row[next(k for k in row if "Sales to Plot" in k)]),
                        number(row[next(k for k in row if "Profit to Plot" in k)]),
                    ]
                    for row in rows
                }
                assert set(actual) == set(expected), (
                    state["name"],
                    role,
                    actual.keys(),
                )
                for key, pair in actual.items():
                    for x, y in zip(pair, expected[key]):
                        assert math.isclose(x, y, abs_tol=0.51), (key, x, y)
                checks.append(
                    {
                        "state": state["name"],
                        "role": role,
                        "rows": len(rows),
                        "passed": True,
                    }
                )
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    result = {
        "passed": True,
        "artifact_sha256": digest,
        "independent_data_rows": len(facts),
        "cloud_status": "passed" if checks else "pending",
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        "PASS WW30 raw state/city oracle and native drill-down; cloud="
        + result["cloud_status"]
    )


if __name__ == "__main__":
    verify()
