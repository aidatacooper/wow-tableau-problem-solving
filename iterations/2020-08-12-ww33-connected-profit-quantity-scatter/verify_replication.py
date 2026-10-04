"""Independent 72 category-month points and all insight extrema."""

import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


# Acceptance: ww33-monthly-oracle, ww33-native-set-insights, ww33-cloud-rest.
def number(v):
    return float(v.replace(",", "").replace("%", "").strip()) / (100 if "%" in v else 1)


def date(text):
    for fmt in ["%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y"]:
        try:
            return (
                datetime.datetime.strptime(text, fmt)
                .replace(tzinfo=datetime.timezone.utc)
                .strftime("%Y-%m-01")
            )
        except ValueError:
            pass
    raise ValueError(text)


def verify():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        count = c.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"')
        rows = c.execute_list_query(
            """SELECT "Category",CAST(DATE_TRUNC('month',"Order Date") AS DATE),SUM("Sales"),SUM("Profit"),SUM("Quantity") FROM "Extract"."Extract" WHERE "Order Date">=DATE '2018-01-01' AND "Order Date"<DATE '2020-01-01' GROUP BY 1,2 ORDER BY 1,2"""
        )
    assert count == 9994 and len(rows) == 72
    points = [
        {
            "category": cat,
            "month": str(month),
            "sales": sales,
            "profit": profit,
            "quantity": quantity,
            "profit_ratio": profit / sales,
        }
        for cat, month, sales, profit, quantity in rows
    ]
    extrema = {}
    for cat in sorted({p["category"] for p in points}):
        values = [p for p in points if p["category"] == cat]
        extrema[cat] = {
            name: max(values, key=lambda p: (sign * p[field], p["month"]))
            for name, field, sign in [
                ("max_pr", "profit_ratio", 1),
                ("min_pr", "profit_ratio", -1),
                ("max_quantity", "quantity", 1),
                ("min_quantity", "quantity", -1),
            ]
        }
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        r = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    assert len(r.findall("worksheets/worksheet")) == 2
    assert (
        r.find(
            "datasources/datasource/group[@caption='Selected Category']/groupfilter"
        ).get("function")
        == "empty-level"
    )
    a = r.find("actions/edit-group-action[@caption='Select Category']")
    assert a.find("single-select").get("value") == "true"
    assert a.find("activation").get("type") == "on-select"
    assert (
        a.find("params/param[@name='selection-clear-set-option']").get("value")
        == "exclude-all"
    )
    scatter = r.find("worksheets/worksheet[@name='Scatter']")
    assert [
        p.find("mark").get("class") for p in scatter.findall("table/panes/pane")
    ] == ["Circle", "Line"]
    assert (
        scatter.find("table/panes/pane/encodings/lod") is not None
        and scatter.find("table/panes/pane/encodings/path") is not None
    )
    scatter_filters = scatter.findall("table/view/filter")
    insight_filters = r.find("worksheets/worksheet[@name='Insights']").findall(
        "table/view/filter"
    )
    assert len(scatter_filters) == 1 and len(insight_filters) == 3
    for filters in [scatter_filters, insight_filters]:
        year_filter = next(
            f for f in filters if "[yr:Order Date:ok]" in f.get("column", "")
        )
        assert {
            m.get("member") for m in year_filter.findall("groupfilter/groupfilter")
        } == {"2018", "2019"}
    selected_filter = next(
        f for f in insight_filters if "[io:Selected Category:nk]" in f.get("column", "")
    )
    assert selected_filter.find("groupfilter").get("member") == "true"
    index_name = r.find("datasources/datasource/column[@caption='Index=Size']").get(
        "name"
    )
    index_filter = next(
        f for f in insight_filters if index_name[1:-1] in f.get("column", "")
    )
    assert index_filter.find("groupfilter").get("member") == "true"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"]:
        assert (
            hashlib.sha256((HERE / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    checks = []
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        report = json.loads(manifest.read_text())
        expected_states = {
            "default": {},
            "technology": {"Category": "Technology"},
            "furniture": {"Category": "Furniture"},
        }
        expected_exports = {
            ("author", "Scatter"),
            ("author", "Insights"),
            ("replica", "Scatter"),
            ("replica", "Insights"),
        }
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
            expected = {
                (p["category"], p["month"]): p
                for p in points
                if state["name"] == "default"
                or p["category"] == state["filters"]["Category"]
            }
            for role in ["author", "replica"]:
                actual = list(
                    csv.DictReader(
                        (HERE / f"outputs/cloud-{role}-scatter{suffix}.csv").open(
                            encoding="utf-8-sig"
                        )
                    )
                )
                seen = set()
                for row in actual:
                    mk = next(k for k in row if "Month Year" in k)
                    key = (row["Category"], date(row[mk]))
                    assert key in expected
                    seen.add(key)
                    p = expected[key]
                    qk = next(k for k in row if "Quantity" in k)
                    pk = next(k for k in row if "Profit Ratio" in k)
                    assert number(row[qk]) == p["quantity"]
                    assert math.isclose(
                        number(row[pk]), p["profit_ratio"], abs_tol=0.0051
                    ), (key, row[pk], p["profit_ratio"])
                assert seen == set(expected), (
                    role,
                    state["name"],
                    len(seen),
                    len(expected),
                )
                insights = list(
                    csv.DictReader(
                        (HERE / f"outputs/cloud-{role}-insights{suffix}.csv").open(
                            encoding="utf-8-sig"
                        )
                    )
                )
                assert not insights, (
                    "Initial set remains empty; no Insight marks expected from ordinary Category REST filters."
                )
                checks.append(
                    {
                        "state": state["name"],
                        "role": role,
                        "complete_category_months": len(seen),
                        "initial_insights_empty": True,
                        "passed": True,
                    }
                )
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(
            {
                "fact_rows": count,
                "points": points,
                "extrema": extrema,
                "scope": "Every 2018/19 category-month quantity and profit ratio; complete four extrema plus tie-last-month date for each category.",
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
                "cloud_status": "passed" if checks else "pending",
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS WW33 monthly scatter and insight oracle; cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    verify()
