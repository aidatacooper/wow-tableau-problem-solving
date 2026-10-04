"""Independent complete state-day moving averages and native cartogram contracts."""

import csv
import datetime
import hashlib
import json
import math
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


# Acceptance: ww32-full-state-day-oracle, ww32-native-cartogram, ww32-cloud-rest.
def number(text):
    return float(text.replace(",", "").replace("$", "").strip())


def verify():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        count = c.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"')
        facts = c.execute_list_query(
            """SELECT "PROVINCE_STATE_NAME",CAST("REPORT_DATE" AS DATE),SUM("PEOPLE_POSITIVE_NEW_CASES_COUNT") FROM "Extract"."Extract" WHERE "REPORT_DATE">=TIMESTAMP '2020-03-01 00:00:00' AND "REPORT_DATE"<=TIMESTAMP '2020-07-31 00:00:00' GROUP BY 1,2 ORDER BY 1,2"""
        )
    assert count == 529950
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        r = etree.fromstring(
            z.read(next(x for x in z.namelist() if x.endswith(".twb")))
        )
    row_formula = r.find(
        "datasources/datasource/column[@caption='Rows']/calculation"
    ).get("formula")
    col_formula = r.find(
        "datasources/datasource/column[@caption='Columns']/calculation"
    ).get("formula")
    positions = {
        state: [
            int(row),
            int(dict(re.findall("WHEN '([^']+)' THEN ([0-9]+)", col_formula))[state]),
        ]
        for state, row in re.findall("WHEN '([^']+)' THEN ([0-9]+)", row_formula)
    }
    assert (
        len(positions) == 51
        and positions["Alaska"] == [1, 1]
        and positions["Florida"] == [8, 10]
    )
    expected_positions = json.loads(
        (HERE / "inputs/cartogram-positions.json").read_text()
    )
    assert positions == expected_positions
    grouped = {}
    for state, date, total in facts:
        if state in positions:
            grouped.setdefault(state, []).append([str(date), int(total)])
    assert len(grouped) == 51
    data = []
    for state, rows in grouped.items():
        averages = [
            sum(x[1] for x in rows[max(0, i - 6) : i + 1])
            / len(rows[max(0, i - 6) : i + 1])
            for i in range(len(rows))
        ]
        maximum = max(averages)
        for (date, total), avg in zip(rows, averages):
            data.append(
                {
                    "state": state,
                    "date": date,
                    "new_cases": total,
                    "moving_average": avg if rows.index([date, total]) >= 6 else None,
                    "normalised": avg / maximum
                    if rows.index([date, total]) >= 6
                    else None,
                    "row": positions[state][0],
                    "column": positions[state][1],
                }
            )
    assert len(r.findall("worksheets/worksheet")) == 1
    assert [
        x.find("mark").get("class")
        for x in r.findall("worksheets/worksheet/table/panes/pane")
    ] == ["Text", "Area"]
    assert (
        r.find(
            "datasources/datasource/column[@caption='7 day moving Avg']/calculation"
        ).get("formula")
        == "WINDOW_AVG(SUM([PEOPLE_POSITIVE_NEW_CASES_COUNT]),-6,0)"
    )
    assert (
        r.find("datasources/datasource/column[@caption='Normalised Value']/calculation")
        .get("formula")
        .count("/")
        == 1
    )
    filters = r.find("worksheets/worksheet[@name='Map']").findall("table/view/filter")
    assert len(filters) == 2 and any(
        f.find("groupfilter") is not None
        and f.find("groupfilter").get("member") == "true"
        for f in filters
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"] + lock.get("derived_data", []):
        assert (
            hashlib.sha256((HERE / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    state_maximum = {
        state: max(
            x["moving_average"]
            for x in data
            if x["state"] == state and x["moving_average"] is not None
        )
        for state in positions
    }
    checks = []
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        report = json.loads(manifest.read_text())
        expected_states = {
            "default": {},
            "california": {"PROVINCE_STATE_NAME": "California"},
            "texas": {"PROVINCE_STATE_NAME": "Texas"},
        }
        expected_exports = {("author", "Data"), ("replica", "Map")}
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
        assert report["source_hashes"]["replica"] == digest
        assert report.get("browser_interaction_executed") is False
        for state_record in report["states"]:
            for entry in list(state_record["views"].values()) + state_record["data"]:
                assert (
                    hashlib.sha256((HERE / entry["path"]).read_bytes()).hexdigest()
                    == entry["sha256"]
                )
        for state in report["states"]:
            for export in state["data"]:
                if export["role"] == "author":
                    assert export["view"] == "Data" and export["filters"] == {}
                else:
                    assert (
                        export["view"] == "Map"
                        and export["filters"] == state["filters"]
                    )
            suffix = "" if state["name"] == "default" else "-" + state["name"]
            for role in ["author", "replica"]:
                expected = {
                    (x["state"], x["date"]): x
                    for x in data
                    if role == "author"
                    or state["name"] == "default"
                    or x["state"] == state["filters"]["PROVINCE_STATE_NAME"]
                }
                file = HERE / f"outputs/cloud-{role}-map{suffix}.csv"
                assert file.stat().st_size > 0, "Empty worksheet CSV is not proof."
                rows = list(csv.DictReader(file.open(encoding="utf-8-sig")))
                pivot = {}
                ignored = 0
                for row in rows:
                    state_name = row.get(
                        "Province State Name", row.get("PROVINCE_STATE_NAME")
                    )
                    if state_name not in positions:
                        ignored += 1
                        continue
                    text = row["Report Date"]
                    date = None
                    for fmt in ["%m/%d/%Y", "%B, %d", "%b %d, %Y", "%Y-%m-%d"]:
                        try:
                            parsed = datetime.datetime.strptime(text, fmt).replace(
                                tzinfo=datetime.timezone.utc
                            )
                            date = (
                                parsed.replace(year=2020).date().isoformat()
                                if fmt == "%B, %d"
                                else parsed.date().isoformat()
                            )
                            break
                        except ValueError:
                            pass
                    assert date is not None, text
                    key = (state_name, date)
                    assert key in expected, key
                    e = expected[key]
                    values = pivot.setdefault(key, {})
                    for keycol, axis in [("Rows", "row"), ("Columns", "column")]:
                        assert int(number(row[keycol])) == e[axis]
                    if role == "author":
                        values[row["Measure Names"]] = row["Measure Values"]
                    else:
                        for k, v in row.items():
                            if k in [
                                "7 day moving Avg",
                                "Normalised Value",
                                "Min. Plot State",
                                "PEOPLE_POSITIVE_NEW_CASES_COUNT",
                            ]:
                                if k in values:
                                    assert values[k] == v, (key, k, values[k], v)
                                values[k] = v
                assert set(pivot) == set(expected), (
                    role,
                    state["name"],
                    len(pivot),
                    len(expected),
                )
                for key, values in pivot.items():
                    e = expected[key]
                    raw = values[
                        "People Positive New Cases Count"
                        if role == "author"
                        else "PEOPLE_POSITIVE_NEW_CASES_COUNT"
                    ]
                    assert number(raw) == e["new_cases"], (key, raw, e["new_cases"])
                    avg = values["7 day moving Avg"]
                    norm = values[
                        "Normalised Value along Report Date"
                        if role == "author"
                        else "Normalised Value"
                    ]
                    if e["moving_average"] is None:
                        assert avg == "" and norm == "", (key, avg, norm)
                    else:
                        assert math.isclose(
                            number(avg), e["moving_average"], abs_tol=0.51
                        ), (key, avg, e["moving_average"])
                        assert math.isclose(
                            number(norm), e["normalised"], abs_tol=1e-8
                        ), (key, norm, e["normalised"])
                    if role == "author":
                        maximum = state_maximum[key[0]]
                        assert math.isclose(
                            number(values["Max Avg Per State along Report Date"]),
                            maximum,
                            abs_tol=0.51,
                        )
                    label = values["Min. Plot State"]
                    assert (label != "") == (key[1] == "2020-05-16"), (key, label)
                    if label:
                        assert number(label) == 1.75
                checks.append(
                    {
                        "role": role,
                        "state": state["name"],
                        "export_rows": len(rows),
                        "complete_mapped_state_days": len(pivot),
                        "export_scope": "Unfiltered original Data: all 51 mapped states/DC"
                        if role == "author"
                        else "Map filtered by requested REST state",
                        "source_data_state_filter_applied": False
                        if role == "author"
                        else None,
                        "unmapped_rows_outside_cartogram_scope": ignored,
                        "passed": True,
                    }
                )
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(
            {
                "fact_rows": count,
                "positions": positions,
                "state_days": data,
                "scope": "All 51 US state/DC daily totals, trailing seven-row means, per-state maximum normalisation and cartogram positions.",
            },
            indent=2,
        )
        + "\n"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "passed": True,
                "artifact_sha256": digest,
                "independent_state_days": len(data),
                "cloud_status": "passed" if checks else "pending",
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS WW32 complete state/day oracle; cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    verify()
