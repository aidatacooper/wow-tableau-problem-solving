"""Verify raw measures and complete native predictive-model outputs."""

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = ["three-measure-model", "five-future-years", "measure-selector-action"]
STATES = {
    "": "Total Enrollment",
    "-black-students": "% Black Students",
    "-non-black-students": "% Non-Black Students",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    data = HERE / lock["extracted_data"][0]["file"]
    assert digest(data) == lock["extracted_data"][0]["sha256"]
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(data)) as conn,
    ):
        rows = conn.execute_list_query(
            'SELECT "Year 1","Total enrollment 2 All students","Total enrollment 2 Black students" FROM "Extract"."Extract" ORDER BY "Year 1"'
        )
    assert len(rows) == 26 and [r[0] for r in rows] == list(range(1993, 2019))
    values = {
        year: {
            "Total Enrollment": total,
            "% Black Students": black / total,
            "% Non-Black Students": 1 - black / total,
        }
        for year, total, black in rows
    }
    return {
        "training_rows": 26,
        "training_years": list(values),
        "prediction_years": list(range(1993, 2024)),
        "values": values,
        "model_validation_scope": "Raw actual measures and residual/title arithmetic independently recomputed. Tableau GP outputs compared with source for every date/metric; no independent GP parameter fitting claimed.",
    }


def number(value):
    return None if not value.strip() else float(value.replace(",", "").replace("%", ""))


def close(actual, expected, tolerance=0.051):
    assert actual is not None and math.isclose(
        actual, expected, rel_tol=1e-7, abs_tol=tolerance
    ), (actual, expected)


def verify_manifest(artifact):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return
    manifest = json.loads(path.read_text())
    export = json.loads((HERE / "evidence/author-export-contract.json").read_text())
    assert manifest["source_hashes"] == {
        "author": export["export_sha256"],
        "replica": artifact,
    }
    assert manifest["browser_interaction_executed"] is False
    assert len(manifest["states"]) == 3
    expected = {
        "default": {},
        "black-students": {"pSelect_Measure": "% Black Students"},
        "non-black-students": {"pSelect_Measure": "% Non-Black Students"},
    }
    for state in manifest["states"]:
        assert state["parameters"] == expected[state["name"]] and state["filters"] == {}
        assert len(state["data"]) == 2 and set(state["views"]) == {"author", "replica"}
        for item in list(state["views"].values()) + state["data"]:
            assert digest(HERE / item["path"]) == item["sha256"]


def cloud(data):
    if not (HERE / "evidence/cloud-verification.json").exists():
        return []
    results = []
    for suffix, measure in STATES.items():
        files = [
            HERE / f"outputs/cloud-{role}-chart{suffix}.csv"
            for role in ("author", "replica")
        ]
        if not all(p.exists() for p in files):
            return []
        mappings = []
        for path in files:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            assert len(rows) == 62, (
                path,
                len(rows),
                "Full prediction chart must include five future years",
            )
            year_col = next(
                k
                for k in rows[0]
                if "Year" in k
                and k not in ("Title Latest Year", "Title Future Year")
                and not k.startswith("ATTR")
            )
            parsed = {int(number(row[year_col])): row for row in rows}
            assert Counter(int(number(row[year_col])) for row in rows) == Counter(
                {year: 2 for year in range(1993, 2024)}
            )
            assert len({tuple(row.items()) for row in rows}) == 31
            mappings.append(parsed)
        author, replica = mappings
        for year in range(1993, 2024):
            source = author[year]
            current = replica[year]
            close(
                number(current["Predicted Value"]),
                number(source["Predicted Value"]),
                max(1e-8, abs(number(source["Predicted Value"])) * 1e-7),
            )
            scale = 0.001 if measure == "Total Enrollment" else 100
            close(
                number(current["Tooltip - Predicted Value"]),
                number(current["Predicted Value"]) * scale,
            )
            if year <= 2018:
                actual = data["values"][year][measure] * scale
                for row in [source, current]:
                    close(number(row["Tooltip - Actual Value"]), actual)
                    close(
                        number(row["Tooltip - Residual"]),
                        actual - number(row["Predicted Value"]) * scale,
                    )
            else:
                assert all(
                    number(row["Actual Value"]) is None
                    and number(row["Tooltip - Actual Value"]) is None
                    for row in [source, current]
                )
            for key in ["Latest Year +5 - Predicted", "Latest Year - Actual"]:
                close(number(current[key]), number(source[key]))
            assert current["Increase | Decrease"] == source["Increase | Decrease"]
            expected_suffix = (
                ("K" if measure == "Total Enrollment" else "%") if year <= 2018 else ""
            )
            assert (
                current["Tooltip - Value Suffix"]
                == source["Tooltip - Value Suffix"]
                == expected_suffix
            )
        results.append(
            {
                "state": suffix.lstrip("-") or "default",
                "measure": measure,
                "years_each_role": 31,
                "independent_training_actuals": 26,
                "future_prediction_pairs": 5,
                "source_prediction_pairs": 31,
                "files": [
                    {"file": str(p.relative_to(HERE)), "sha256": digest(p)}
                    for p in files
                ],
            }
        )
    return results


def verify():
    artifact = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(artifact) as archive:
        root = etree.fromstring(
            archive.read(next(n for n in archive.namelist() if n.endswith(".twb")))
        )
    sheet = root.find('worksheets/worksheet[@name="Chart"]')
    extend = sheet.find("table/extend-time-series/extended-column")
    assert (
        extend is not None
        and extend.get("num-periods") == "5"
        and extend.get("period-type") == "year"
    )
    assert sheet.find("table/view/calcs-on-densified-marks").get("value") == "true"
    ds = next(
        d
        for d in root.findall("datasources/datasource")
        if d.get("name") != "Parameters"
    )
    fields = {c.get("caption", c.get("name")): c for c in ds.findall("column")}
    assert "MODEL_QUANTILE('model=gp',0.5," in fields["Predicted Value"].find(
        "calculation"
    ).get("formula")
    assert extend.get("column").endswith("." + fields["Year"].get("name"))
    assert [p.find("mark").get("class") for p in sheet.findall("table/panes/pane")] == [
        "Area",
        "Line",
    ]
    assert len(root.findall("worksheets/worksheet")) == 2
    selector = root.find('worksheets/worksheet[@name="Measure Select"]')
    assert selector.find("table/panes/pane/mark").get("class") == "Bar"
    assert selector.findtext("table/rows").endswith(".[:Measure Names]")
    assert len(selector.xpath("table/view/manual-sort/dictionary/bucket")) == 3
    assert (
        len(
            selector.xpath(
                'table/view/filter/groupfilter/groupfilter[@function="member"]'
            )
        )
        == 3
    )
    assert (
        selector.find("table/panes/pane/encodings/lod")
        .get("column")
        .endswith(".[Multiple Values]")
    )
    action = root.find("actions/edit-parameter-action")
    assert action is not None
    native = etree.tostring(action, encoding="unicode")
    assert (
        "Measure Select" in native
        and "on-select" in native
        and "do-nothing" in native
        and "Measure Names" in native
    )
    assert (
        action.find("clear-option").get("type") == "do-nothing"
        and action.find("agg-type").get("type") == "attr"
    )
    size = root.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "1200" and size.get("maxheight") == "600"
    for worksheet in root.findall("worksheets/worksheet"):
        filters = worksheet.findall("table/view/filter")
        assert not any(
            "mn:Year 1" in f.get("column", "") or "tdy:Year 1" in f.get("column", "")
            for f in filters
        )
    data = oracle()
    proof_path = HERE / "evidence/build-provenance.json"
    if proof_path.exists() and (HERE / "evidence/cloud-verification.json").exists():
        proof = json.loads(proof_path.read_text())
        assert (
            proof["artifact_sha256"] == digest(artifact)
            and proof["builder_sha256"]
            == hashlib.sha256(
                (HERE / "build_replication.py")
                .read_text(encoding="utf-8")
                .encode("utf-8")
            ).hexdigest()
        )
        assert (
            proof["source_workbook_used_by_builder"] is False
            and proof["public_sdk_only"] is True
        )
    verify_manifest(digest(artifact))
    checks = cloud(data)
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    evidence = {
        "status": "pass",
        "artifact_sha256": digest(artifact),
        "acceptance_ids": ACCEPTANCE,
        "oracle": data,
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print("PASS WW05 native GP/selector; Cloud=" + ("passed" if checks else "pending"))
    return digest(artifact)


if __name__ == "__main__":
    verify()
