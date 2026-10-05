"""Independently verify raw 2012 population and native geographic layer contracts."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "all-country-2012-map",
    "selected-country-donut",
    "select-and-clear-parameter",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"]
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Country/Region","Region","Year","Population Total","Population Urban" FROM "Extract"."Extract"'
        )
    assert len(rows) == 2691
    assert all(country and region and year for country, region, year, _, _ in rows)
    assert (
        max(Counter((country, year.year) for country, _, year, _, _ in rows).values())
        == 1
    )
    years = Counter(year.year for _, _, year, _, _ in rows)
    assert years == Counter({year: 207 for year in range(2000, 2013)})
    cells = []
    for country, region, year, total, urban in rows:
        if year.year != 2012:
            continue
        assert total is not None and total > 0 and (urban is None or 0 <= urban <= 1)
        cells.append(
            {
                "country": country,
                "region": region,
                "year": 2012,
                "population_total": total,
                "urban": urban,
                "nonurban": None if urban is None else 1 - urban,
            }
        )
    cells.sort(key=lambda cell: cell["country"])
    assert (
        len(cells) == 207
        and sum(cell["population_total"] for cell in cells) == 7014951860
    )
    assert {cell["country"] for cell in cells if cell["urban"] is None} == {
        "Kosovo",
        "St. Martin (French part)",
    }
    return {
        "input_sha256": item["sha256"],
        "raw_rows": len(rows),
        "country_year_unique": True,
        "year_counts": dict(sorted(years.items())),
        "2012_country_count": len(cells),
        "null_urban_country_count": 2,
        "2012_population_total": sum(cell["population_total"] for cell in cells),
        "region_counts": dict(Counter(cell["region"] for cell in cells)),
        "cells": cells,
    }


def native(root):
    assert len(root.findall("worksheets/worksheet")) == 1
    worksheet = root.find('worksheets/worksheet[@name="Map"]')
    assert worksheet is not None
    assert "Latitude (generated)" in worksheet.findtext("table/rows")
    assert "Longitude (generated)" in worksheet.findtext("table/cols")
    dashboard = root.find("dashboards/dashboard")
    size = dashboard.find("size")
    assert size.get("maxwidth") == "1000" and size.get("maxheight") == "800"
    assert set(dashboard.xpath(".//zone[@name]/@name")) == {"Map"}
    parameter = root.find(
        'datasources/datasource[@name="Parameters"]/column[@caption="pSelectedCountry"]'
    )
    assert parameter.get("datatype") == "string" and parameter.get("value") in {
        '""',
        "''",
    }
    ds = next(
        ds
        for ds in root.findall("datasources/datasource")
        if ds.get("name") != "Parameters"
    )
    fields = {
        c.get("caption", c.get("name").strip("[]")): c for c in ds.findall("column")
    }
    param_reference = "[Parameters]." + parameter.get("name")
    formulas = {
        "All Countries": f"IF {param_reference}='' THEN [Country/Region] END",
        "Selected Country": f"IF {param_reference}=[Country/Region] THEN [Country/Region] END",
        "Population Non-Urban": "1-[Population Urban]",
    }
    for caption, expected in formulas.items():
        formula = fields[caption].find("calculation").get("formula")
        assert "".join(formula.split()) == "".join(expected.split()), (caption, formula)
    for caption in ["All Countries", "Selected Country"]:
        assert fields[caption].get("semantic-role") in {
            "[Country].[Name]",
            "[Country].[ISO3166_2]",
        }
    filters = worksheet.findall("table/view/filter")
    year_filters = [f for f in filters if "yr:Year:ok" in f.get("column", "")]
    assert len(year_filters) == 1 and year_filters[0].xpath(".//@member") == ["2012"]
    measure_filter = [f for f in filters if "Measure Names" in f.get("column", "")]
    assert len(measure_filter) == 1
    members = measure_filter[0].xpath(".//@member")
    assert len(members) == 2
    assert any("sum:Population Urban:qk" in member for member in members)
    assert any(
        "sum:" + fields["Population Non-Urban"].get("name").strip("[]") + ":qk"
        in member
        for member in members
    )
    panes = worksheet.find("table/panes")
    assert panes.get("customization-axis") == "layer"
    layers = [
        pane for pane in panes.findall("pane") if pane.find("encodings/lod") is not None
    ]
    assert len(layers) == 4
    assert [pane.find("mark").get("class") for pane in layers] in [
        ["Multipolygon", "Multipolygon", "Pie", "Circle"],
        ["Multipolygon", "Multipolygon", "Pie", "Automatic"],
    ]
    for index, pane in enumerate(layers):
        token = (
            fields["All Countries" if index == 0 else "Selected Country"]
            .get("name")
            .strip("[]")
        )
        assert any(
            token in node.get("column", "") for node in pane.findall("encodings/lod")
        )
        if index in {0, 1, 3}:
            assert "Region" in pane.find("encodings/color").get("column")
    assert "Measure Names" in layers[2].find("encodings/color").get("column")
    assert "Multiple Values" in layers[2].find("encodings/wedge-size").get("column")
    assert "Population Urban" in layers[3].find("encodings/text").get("column")
    assert "urban dwellers" in "".join(layers[3].find("customized-label").itertext())
    action = root.find("actions/edit-parameter-action")
    assert action.find("activation").get("type") == "on-select"
    assert action.find("source").get("worksheet") == "Map"
    assert action.find("source").get("dashboard") == dashboard.get("name")
    assert action.find("agg-type").get("type") == "attr"
    assert action.find("clear-option").get("type") == "assign-fixed-value"
    assert action.find("clear-option").get("value") == "s:LROOT:"
    params = {p.get("name"): p.get("value") for p in action.findall("params/param")}
    assert fields["All Countries"].get("name").strip("[]") in params["source-field"]
    assert params["target-parameter"] == param_reference
    return {
        "worksheet_count": 1,
        "native_layers": 4,
        "select_event": "on-select",
        "clear_behavior": "assign empty string",
        "browser_interaction_executed": False,
    }


def matches_display(value, exact, kind):
    if not value:
        return exact is None
    number = float(value.replace(",", "").rstrip("M%"))
    expected = exact / 1000000 if kind == "population" else exact * 100
    return abs(number - expected) <= 0.50000001


def cloud(data, artifact):
    manifest_path = HERE / "evidence/cloud-verification.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text())
    export = json.loads((HERE / "evidence/author-export-contract.json").read_text())
    assert manifest["source_hashes"] == {
        "author": export["prepared_sha256"],
        "replica": artifact,
    }
    assert manifest["browser_interaction_executed"] is False
    states = {state["name"]: state for state in manifest["states"]}
    assert set(states) == {"default", "china", "russia", "reset"}
    cells = data["cells"]
    by_country = {cell["country"]: cell for cell in cells}
    checked = []
    for name, selected in [
        ("default", ""),
        ("china", "China"),
        ("russia", "Russia"),
        ("reset", ""),
    ]:
        state = states[name]
        assert state["parameters"] == (
            {} if name == "default" else {"pSelectedCountry": selected}
        )
        assert state["filters"] == {} and set(state["views"]) == {"author", "replica"}
        assert len(state["data"]) == 2
        assert {item["role"] for item in state["data"]} == {"author", "replica"}
        for item in list(state["views"].values()) + state["data"]:
            assert digest(HERE / item["path"]) == item["sha256"]
        for item in state["data"]:
            assert (
                item["view"] == "Map"
                and item["parameters"] == state["parameters"]
                and item["filters"] == {}
            )
            path = HERE / item["path"]
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            assert len(rows) == (24 if selected else 221)
            assert rows and {
                "All Countries",
                "Selected Country",
                "Region",
                "Measure Names",
                "Measure Values",
                "Population Total",
                "Population Urban",
            } <= set(rows[0])
            all_keys, selected_keys, wedges = set(), set(), set()
            country_rows = Counter()
            null_regions = Counter()
            null_wedges = Counter()
            numeric_rows = 0
            for row in rows:
                country = row["All Countries"] or row["Selected Country"]
                measure = row["Measure Names"]
                assert measure in {
                    "",
                    "No Measure Value",
                    "Population Urban",
                    "Population Non-Urban",
                }
                if country:
                    assert country in by_country and not (
                        row["All Countries"] and row["Selected Country"]
                    )
                    cell = by_country[country]
                    country_rows[country] += 1
                    if row["All Countries"]:
                        assert not selected
                        all_keys.add(country)
                    else:
                        assert country == selected
                        selected_keys.add(country)
                    assert row["Country/Region"] == country
                    assert not row["Region"] or row["Region"] == cell["region"]
                    assert matches_display(
                        row["Population Total"], cell["population_total"], "population"
                    )
                    if item["role"] == "replica" or row["Selected Country"]:
                        assert matches_display(
                            row["Population Urban"], cell["urban"], "urban"
                        )
                    elif row["Population Urban"]:
                        assert cell["urban"] is not None and matches_display(
                            row["Population Urban"], cell["urban"], "urban"
                        )
                    if measure in {"Population Urban", "Population Non-Urban"}:
                        field = "urban" if measure == "Population Urban" else "nonurban"
                        assert abs(float(row["Measure Values"]) - cell[field]) < 1e-8
                        wedges.add(measure)
                else:
                    assert row["Country/Region"] == "*"
                    region = row["Region"]
                    if measure in {"Population Urban", "Population Non-Urban"}:
                        null_wedges[measure] += 1
                    else:
                        null_regions[region] += 1
                    candidates = []
                    if measure in {"Population Urban", "Population Non-Urban"}:
                        candidates.append(
                            [cell for cell in cells if cell["country"] != selected]
                        )
                    else:
                        candidates.append(
                            [cell for cell in cells if cell["region"] == region]
                        )
                        if selected:
                            candidates.append(
                                [
                                    cell
                                    for cell in cells
                                    if cell["region"] == region
                                    and cell["country"] != selected
                                ]
                            )
                    matched = False
                    for group in candidates:
                        if not group:
                            continue
                        total = sum(cell["population_total"] for cell in group)
                        urban = sum(
                            cell["urban"] for cell in group if cell["urban"] is not None
                        )
                        if not matches_display(
                            row["Population Total"], total, "population"
                        ):
                            continue
                        if row["Population Urban"] and not matches_display(
                            row["Population Urban"], urban, "urban"
                        ):
                            continue
                        if measure in {"Population Urban", "Population Non-Urban"}:
                            field = (
                                "urban" if measure == "Population Urban" else "nonurban"
                            )
                            expected = sum(
                                cell[field] for cell in group if cell[field] is not None
                            )
                            if abs(float(row["Measure Values"]) - expected) >= 1e-8:
                                continue
                        else:
                            assert not row["Measure Values"]
                        matched = True
                        break
                    assert matched, (path, "Unreconciled NULL geography aggregate", row)
                numeric_rows += 1
            assert all_keys == (set(by_country) if not selected else set())
            assert selected_keys == ({selected} if selected else set())
            assert wedges == (
                {"Population Urban", "Population Non-Urban"} if selected else set()
            )
            assert country_rows == (
                {selected: 4}
                if selected
                else Counter({country: 1 for country in by_country})
            )
            assert null_regions == Counter(
                {region: 3 if selected else 2 for region in data["region_counts"]}
            )
            assert null_wedges == Counter(
                {"Population Urban": 1, "Population Non-Urban": 1}
            )
            checked.append(
                {
                    "state": name,
                    "role": item["role"],
                    "file": item["path"],
                    "sha256": item["sha256"],
                    "csv_rows": len(rows),
                    "independently_reconciled_rows": numeric_rows,
                    "all_country_keys": len(all_keys),
                    "selected_country_keys": sorted(selected_keys),
                    "selected_wedges": sorted(wedges),
                    "scope": "Complete worksheet conditional geographic keys; every numeric row reconciled including NULL-geography aggregates. Population totals checked at integer-million CSV precision and urban tooltips at integer-percent precision; pie shares checked at exported numerical precision.",
                }
            )
    return checked


def verify():
    path = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(path) as archive:
        root = etree.fromstring(
            archive.read(
                next(name for name in archive.namelist() if name.endswith(".twb"))
            )
        )
    data = oracle()
    contract = native(root)
    proof_path = HERE / "evidence/build-provenance.json"
    if proof_path.exists() and (HERE / "evidence/cloud-verification.json").exists():
        proof = json.loads(proof_path.read_text())
        assert proof["artifact_sha256"] == digest(path)
        assert (
            proof["builder_sha256"]
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
    checks = cloud(data, digest(path))
    result = {
        "status": "pass",
        "artifact_sha256": digest(path),
        "acceptance_ids": ACCEPTANCE,
        "oracle": data,
        "native_contract": contract,
        "cloud_checks": checks,
        "browser_interaction_executed": False,
    }
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS WW09 raw/native; Cloud=" + ("passed" if checks else "pending"))
    return digest(path)


if __name__ == "__main__":
    verify()
