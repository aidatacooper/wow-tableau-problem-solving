"""Independently check slicer logic, complete fact totals and REST business CSVs."""

# Acceptance: raw-fact-oracle, native-artifact-contracts
import csv
import itertools
import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
SHEETS = ["Region", "Category", "Segment", "Ship Mode"]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def oracle():
    fields = [
        "Order ID",
        "Ship Mode",
        "Segment",
        "State",
        "Region",
        "Category",
        "Sub-Category",
        "Sales",
        "Quantity",
    ]
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        records = c.execute_list_query(
            "SELECT "
            + ",".join('"' + s + '"' for s in fields)
            + ' FROM "Extract"."Extract"'
        )
    assert len(records) == 9994
    rows = [dict(zip(fields, r)) for r in records]
    result = {}
    for sheet in SHEETS:
        groups = defaultdict(list)
        for row in rows:
            groups[row[sheet]].append(row)
        result[sheet] = {
            key: {
                "Sales": math.fsum(r["Sales"] for r in values),
                "Quantity": sum(r["Quantity"] for r in values),
                "Orders": len({r["Order ID"] for r in values}),
            }
            for key, values in groups.items()
        }
    assert [len(result[s]) for s in SHEETS] == [4, 3, 3, 4]
    # Independent truth tables: inactive slicers do not contribute to OR, and
    # native all-domain defaults include every fact at every parameter field.
    truth = []
    for active in itertools.product((False, True), repeat=3):
        for members in itertools.product((False, True), repeat=3):
            membership = [members[i] if active[i] else True for i in range(3)]
            conjunction = all(membership)
            disjunction = (
                any(membership[i] for i in range(3) if active[i])
                if any(active)
                else True
            )
            truth.append(
                {
                    "active": active,
                    "membership": membership,
                    "AND": conjunction,
                    "OR": disjunction,
                }
            )
    subsets = []
    for logic in ("AND", "OR"):
        chosen = [
            r
            for r in rows
            if (all if logic == "AND" else any)(
                [
                    r["Region"] == "West",
                    r["Category"] == "Furniture",
                    r["Segment"] == "Consumer",
                ]
            )
        ]
        subsets.append(
            {
                "logic": logic,
                "facts": len(chosen),
                "Sales": math.fsum(r["Sales"] for r in chosen),
                "Quantity": sum(r["Quantity"] for r in chosen),
                "Orders": len({r["Order ID"] for r in chosen}),
            }
        )
    assert subsets[0]["facts"] < subsets[1]["facts"]
    return {
        "facts": len(records),
        "complete_sheet_totals": result,
        "logic_truth_table": truth,
        "independent_subset_oracles": subsets,
        "subset_scope": "Raw independent oracle plus native formula contract only; no Cloud set-membership event executed.",
    }


def native(root):
    sheets = root.findall("worksheets/worksheet")
    assert {s.get("name") for s in sheets} == set(SHEETS)
    params = root.findall("datasources/datasource[@name='Parameters']/column")
    assert len(params) == 5
    groups = root.findall("datasources/datasource/group")
    assert len(groups) == 3
    for group in groups:
        gf = group.find("groupfilter")
        assert gf.get("function") == "level-members"
        assert (
            gf.get("{http://www.tableausoftware.com/xml/user}ui-enumeration") == "all"
        )
        assert gf.get("level")
    cols = {
        c.get("caption", c.get("name", "").strip("[]")): c
        for c in root.findall("datasources/datasource/column")
    }
    formula = cols["In Combined Set"].find("calculation").get("formula")
    assert "AND" in formula and "OR" in formula and formula.count("ELSEIF") == 5
    assert (
        cols["Order Count"].find("calculation").get("formula") == "COUNTD([Order ID])"
    )
    for s in sheets:
        assert s.find("table/panes/pane/mark").get("class") == "Bar"
        assert " * " in s.findtext("table/cols")
        assert s.find("table/panes/pane/encodings/color") is not None
        assert s.find("table/panes/pane/customized-label") is not None
        assert s.find("table/view/filter") is None
    controls = root.findall(
        "dashboards/dashboard/zones//zone[@type-v2='setMembership']"
    )
    assert len(controls) == 3
    assert all(
        c.get("mode") == "checkdropdown" and c.get("show-apply") == "true"
        for c in controls
    )
    for sheet in sheets:
        assert len(sheet.findall("table/panes/pane/encodings/text")) == 2
        assert sheet.findtext(
            "layout-options/title/formatted-text/run"
        ) == "By " + sheet.get("name")
    size = root.find("dashboards/dashboard/size")
    assert (size.get("maxwidth"), size.get("maxheight")) == ("1190", "900")
    return {
        "passed": True,
        "dynamic_all_domain_sets": 3,
        "set_controls": 3,
        "parameters": 5,
        "business_sheets": 4,
        "browser_events_executed": False,
    }


def number(text):
    return float(text.strip().replace("$", "").replace(",", ""))


def cloud_checks(raw):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return {"passed": False, "status": "pending_cloud_capture"}
    capture = json.loads(manifest.read_text(encoding="utf-8"))
    assert capture["source_hashes"]["replica"] == digest(
        HERE / "outputs/replicated-workbook.twbx"
    )
    assert {s["name"] for s in capture["states"]} == {
        "default",
        "orders-and",
        "quantity-or",
        "region-category-or",
    }
    summaries = []
    for state in capture["states"]:
        assert {(r["role"], r["view"]) for r in state["data"]} == {
            (role, view)
            for role in ("author", "replica")
            for view in ["Region", "Category", "Segment", "Ship Mode"]
        }

        metric = state.get("parameters", {}).get("Selected Measure", "Sales")
        for record in state["data"]:
            sheet = record["view"]
            expected = raw["complete_sheet_totals"][sheet]
            path = HERE / record["path"]
            assert digest(path) == record["sha256"]
            rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
            assert rows, path.name
            seen = set()
            checks = 0
            for row in rows:
                key = row[sheet]
                assert key in expected
                seen.add(key)
                candidates = [
                    value
                    for header, value in row.items()
                    if "Measure to Display" in header
                    and "Prefix" not in header
                    and value
                ]
                assert candidates, (path.name, row)
                for value in candidates:
                    assert abs(number(value) - expected[key][metric]) <= (
                        0.51 if metric == "Sales" else 0.001
                    ), (path.name, key, metric, value, expected[key][metric])
                    checks += 1
                if "In Combined Set" in row:
                    assert row["In Combined Set"].lower() == "true", (path.name, row)
                prefixes = [
                    value
                    for header, value in row.items()
                    if "Measure to Display Prefix" in header
                ]
                assert prefixes, (path.name, "missing native prefix binding")
                assert all(
                    value == ("$" if metric == "Sales" else "") for value in prefixes
                ), (path.name, prefixes, metric)
                for header, value in row.items():
                    if "Selected | Omitted" in header:
                        assert value == "selected", (path.name, value)
            assert seen == set(expected)
            summaries.append(
                {
                    "state": state["name"],
                    "role": record["role"],
                    "sheet": sheet,
                    "metric": metric,
                    "rows": len(rows),
                    "groups": len(seen),
                    "metric_checks": checks,
                }
            )
        for record in state["views"].values():
            assert digest(HERE / record["path"]) == record["sha256"]
    assert len(capture["states"]) == 4 and len(summaries) == 32
    return {
        "passed": True,
        "status": "verified",
        "exports": summaries,
        "scope": "All four full business worksheets; parameter-state changes plus stored all-domain sets. Subset membership truth tables are independent raw oracles, not browser or REST set execution.",
    }


def verify():
    raw = oracle()
    workbook = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(workbook) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    report = {
        "artifact_sha256": digest(workbook),
        "raw_oracle": raw,
        "native_contracts": native(root),
        "cloud": cloud_checks(raw),
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("Raw/native PASS; Cloud", report["cloud"]["status"])
    return report


if __name__ == "__main__":
    verify()
