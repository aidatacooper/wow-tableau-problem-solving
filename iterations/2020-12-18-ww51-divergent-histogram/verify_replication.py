"""Independent locked raw-data oracle and actual Cloud/native contracts."""

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
YEARS = {"default": 2012, "year-2011": 2011, "year-2000": 2000, "year-2001": 2001}
ACCEPTANCE = [
    "distinct-country-bins",
    "dynamic-symmetric-domain",
    "native-histogram-layout",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    path = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, str(path)) as c:
            rows = c.execute_list_query(
                'SELECT "Country/Region","Year","Pivot Field Names","Pivot Field Values" FROM "Extract"."Extract"'
            )
    assert len(rows) == 5382
    bins = defaultdict(lambda: defaultdict(set))
    excluded = defaultdict(int)
    for country, year, sex, age in rows:
        assert year is not None and sex in {
            "Life Expectancy Female",
            "Life Expectancy Male",
        }
        if age is None:
            excluded[year.year] += 1
            continue
        assert isinstance(age, int)
        if country is not None:
            bins[year.year][(sex, age)].add(country)
    out = {}
    for year, groups in bins.items():
        marks = [
            {
                "sex": sex,
                "age": age,
                "count": len(countries),
                "signed_count": len(countries) if "Female" in sex else -len(countries),
            }
            for (sex, age), countries in sorted(groups.items())
        ]
        positive_max = max(r["signed_count"] for r in marks)
        peaks = {}
        for sex in ["Life Expectancy Female", "Life Expectancy Male"]:
            values = [r for r in marks if r["sex"] == sex]
            peak = max(r["count"] for r in values)
            peaks[sex] = {
                "count": peak,
                "ages": [r["age"] for r in values if r["count"] == peak],
            }
        out[str(year)] = {
            "marks": marks,
            "mark_count": len(marks),
            "excluded_null_age_rows": excluded[year],
            "reference_max": positive_max,
            "reference_min": -positive_max,
            "peaks": peaks,
        }
    assert set(out) == {str(y) for y in range(2000, 2013)}
    return {"raw_rows": len(rows), "years": out, "source_already_pivoted": True}


def number(text):
    return float(text.strip().replace(",", "").replace("\u2212", "-"))


def sexvalue(text):
    if "female" in text.lower():
        return "Life Expectancy Female"
    if "male" in text.lower():
        return "Life Expectancy Male"
    raise AssertionError(("Unknown sex", text))


def verify_cloud(data, artifact):
    manifest = HERE / "evidence/cloud-verification.json"
    if not manifest.exists():
        return []
    m = json.loads(manifest.read_text())
    proof = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert m["source_hashes"] == {"replica": artifact, "author": proof["export_sha256"]}
    assert m["browser_interaction_executed"] is False
    assert len(m["states"]) == len(YEARS) and {s["name"] for s in m["states"]} == set(
        YEARS
    )
    results = []
    for state in m["states"]:
        year = YEARS[state["name"]]
        filters = {} if state["name"] == "default" else {"year(Year)": str(year)}
        assert state["parameters"] == {} and state["filters"] == filters
        assert set(state["views"]) == {"author", "replica"}
        for image in state["views"].values():
            assert digest(HERE / image["path"]) == image["sha256"]
        assert len(state["data"]) == 2 and {x["role"] for x in state["data"]} == {
            "author",
            "replica",
        }
        expected = {(r["sex"], r["age"]): r for r in data["years"][str(year)]["marks"]}
        for item in state["data"]:
            assert (
                item["view"] == "Viz"
                and item["filters"] == filters
                and item["parameters"] == {}
            )
            path = HERE / item["path"]
            assert digest(path) == item["sha256"] and path.stat().st_size > 0
            rows = list(
                csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines())
            )
            assert rows, (path, "Empty active worksheet export")
            seen = set()
            for row in rows:
                agekey = next(
                    (
                        k
                        for k in row
                        if k in ["Life Expectancy Age", "Pivot Field Values"]
                    ),
                    None,
                )
                sexkey = next((k for k in row if "Pivot Field Names" in k), None)
                assert agekey and sexkey and row[agekey] and row[sexkey], (path, row)
                key = (sexvalue(row[sexkey]), int(number(row[agekey])))
                assert key in expected and key not in seen, (path, key)
                seen.add(key)
                # The native unsigned male number format does not expose mark-sign.
                # Raw oracle plus the exact conditional formula verify signed plotting.
                assert abs(number(row["Country Count"])) == expected[key]["count"], (
                    path,
                    key,
                    row,
                )
                for field, target in [
                    ("Max Count Ref Line", "reference_max"),
                    ("Max Count Ref Line (copy)", "reference_min"),
                ]:
                    assert row.get(field, "").strip(), (
                        path,
                        "Reference scope missing",
                        field,
                    )
                    assert number(row[field]) == data["years"][str(year)][target], (
                        path,
                        field,
                        row,
                    )
                if "Year" in row and row["Year"]:
                    assert re.search(r"\b" + str(year) + r"\b", row["Year"]), (
                        path,
                        "State did not select actualyear",
                        row,
                    )
            assert seen == set(expected), (
                path,
                "Whole age/sex coverage",
                len(seen),
                len(expected),
            )
            results.append(
                {
                    "state": state["name"],
                    "role": item["role"],
                    "year": year,
                    "rows": len(rows),
                    "complete_age_sex_marks": len(seen),
                    "all_reference_values_checked": True,
                    "passed": True,
                }
            )
    return results


def verify():
    output = HERE / "outputs/replicated-workbook.twbx"
    artifact = digest(output)
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    assert lock["source_workbook_used_by_builder"] is False
    proof_path = HERE / "evidence/export-provenance.json"
    if proof_path.exists():
        proof = json.loads(proof_path.read_text())
        assert (
            proof["original_sha256"] == lock["source_workbook"]["sha256"]
            and proof["business_xml_unchanged"] is True
        )
    # Source export provenance belongs to comparison evidence, not the inputs
    # required to rebuild and independently validate a generated workbook.
    # verify_cloud still requires that proof whenever a Cloud manifest exists.
    with ZipFile(output) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        for item in lock["extracted_data"]:
            path = HERE / item["file"]
            assert (
                digest(path) == item["sha256"] and path.stat().st_size == item["bytes"]
            )
            packed = next(n for n in z.namelist() if n.endswith(path.name))
            assert hashlib.sha256(z.read(packed)).hexdigest() == item["sha256"]
    ds = root.find("datasources/datasource")
    count = ds.xpath('column[@caption="Country Count"]')[0]
    assert count.get("default-format") == "n#,##0;#,##0"
    assert (
        count.find("calculation").get("formula")
        == "IF CONTAINS(ATTR([Pivot Field Names]),'Female') THEN COUNTD([Country/Region]) ELSE -COUNTD([Country/Region]) END"
    )
    refs = {
        label: ds.xpath("column[@caption=$caption]", caption=label)[0]
        for label in ["Max Count Ref Line", "Max Count Ref Line (copy)"]
    }
    assert (
        refs["Max Count Ref Line"].find("calculation").get("formula")
        == "WINDOW_MAX(" + count.get("name") + ")"
    )
    assert (
        refs["Max Count Ref Line (copy)"].find("calculation").get("formula")
        == "-WINDOW_MAX(" + count.get("name") + ")"
    )
    viz = root.xpath('//worksheet[@name="Viz"]')[0]
    panes = viz.findall("table/panes/pane")
    assert len(panes) == 1 and panes[0].find("mark").get("class") == "Bar"
    assert panes[0].find("view/breakdown").get("value") == "off"
    assert len(panes[0].findall("reference-line")) == 3
    assert {x.get("formula") for x in panes[0].findall("reference-line")} == {
        "min",
        "max",
    }
    zero = ds.xpath('column[@caption="Zero Axis Line"]')[0]
    assert zero.find("calculation").get("formula") == "0"
    zero_ref = panes[0].xpath('reference-line[@id="refline2"]')[0]
    assert zero.get("name")[1:-1] in zero_ref.get("value-column")
    assert zero_ref.get("label-type") == "none"
    assert viz.xpath(
        'table/style/style-rule[@element="refline"]/format[@id="refline2" and @attr="stroke-color" and @value="#c0c0c0"]'
    )
    assert panes[0].xpath(
        'style/style-rule[@element="datalabel"]/format[@attr="color-mode" and @value="match"]'
    )
    assert panes[0].xpath(
        'style/style-rule[@element="datalabel"]/format[@attr="font-weight" and @value="bold"]'
    )
    axis_formats = viz.xpath('table/style/style-rule[@element="axis"]/format')
    age_field = ds.xpath('column[@caption="Life Expectancy Age"]')[0]
    assert any(
        x.get("attr") == "display"
        and x.get("value") == "false"
        and x.get("scope") == "rows"
        and count.get("name")[1:-1] in x.get("field", "")
        for x in axis_formats
    )
    assert any(
        x.get("attr") == "title"
        and x.get("value") == "AVG. LIFE EXPECTANCY"
        and x.get("scope") == "cols"
        and age_field.get("name")[1:-1] in x.get("field", "")
        for x in axis_formats
    )
    assert viz.xpath(
        'table/style/style-rule[@element="table-div"]/format[@scope="rows" and @attr="stroke-color" and @value="#c0c0c0"]'
    )
    for label, field in refs.items():
        ci = viz.xpath(".//column-instance[@column=$column]", column=field.get("name"))
        assert len(ci) == 1 and ci[0].find("table-calc").get("ordering-type") == "Field"
        orders = ci[0].findall("table-calc/order")
        assert len(orders) == 2
        assert orders[1].get("field").endswith("[Pivot Field Names]")
        assert any(
            field.get("name")[1:-1] in e.get("column")
            for e in panes[0].findall("encodings/lod")
        )
    assert panes[0].xpath(
        'style/style-rule[@element="mark"]/format[@attr="mark-labels-mode" and @value="range"]'
    )
    assert panes[0].find("mark-sizing").get("mark-alignment") == "mark-alignment-left"
    tooltip = "".join(panes[0].xpath("customized-tooltip/formatted-text/run/text()"))
    assert (
        "[attr:Year:ok]" in tooltip
        and "[none:Pivot Field Names:nk]" in tooltip
        and "# Countries:" in tooltip
    )
    assert count.get("name")[1:-1] in tooltip
    assert viz.xpath(
        'table/style/style-rule[@element="axis"]/encoding[@min="30" and @max="95"]'
    )
    assert all(
        color in etree.tostring(root, encoding="unicode")
        for color in ["#a39fc9", "#31a1b3"]
    )
    dash = root.find("dashboards/dashboard")
    assert (
        dash.find("size").get("maxwidth") == "1300"
        and dash.find("size").get("maxheight") == "800"
    )
    filters = dash.xpath('zones//zone[@type-v2="filter"]')
    assert (
        len(filters) == 1
        and filters[0].get("mode") == "dropdown"
        and filters[0].get("show-all") == "false"
    )
    assert not root.findall("actions/action")
    data = oracle()
    checks = verify_cloud(data, artifact)
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "artifact_sha256": artifact,
                "acceptance_ids": ACCEPTANCE,
                "oracle": data,
                "cloud_checks": checks,
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS WW51 raw distinct-country bins/native source reference formulas; Cloud="
        + ("passed" if checks else "pending")
    )
    return artifact


if __name__ == "__main__":
    verify()
