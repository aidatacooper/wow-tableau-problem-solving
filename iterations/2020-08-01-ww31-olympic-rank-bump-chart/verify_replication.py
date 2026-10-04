"""Independent three-table Olympics oracle and nested ranking/VIT contracts."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


# Acceptance: ww31-three-table-oracle, ww31-native-rank-vit, ww31-cloud-rest.
def num(v):
    return float(v.replace(",", "").strip())


def verify():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        medals = c.execute_list_query(
            'SELECT "Country","Gold","Silver","Bronze","Year" FROM "Extract"."Extract (Extract.Extract)_72FC953A3CC8413E948D79B8CD93DB49"'
        )
        athletes = c.execute_list_query(
            'SELECT "Country","Medal","Athlete","Year" FROM "Extract"."Extract (Extract.Extract)_1E9BB58A261F452EBE047898ABB2452A"'
        )
        hosts = dict(
            c.execute_list_query(
                'SELECT "Year","Host Country" FROM "Extract"."Extract (Extract.Extract)_40C876C051114093BAFB7F02A036CAF2"'
            )
        )
    assert len(medals) == 1242 and len(athletes) == 33203 and len(hosts) == 28
    values = {}
    years = defaultdict(list)
    for country, g, s, b, year in medals:
        point = {
            "year": year,
            "country": country,
            "gold": g or 0,
            "silver": s or 0,
            "bronze": b or 0,
            "score": 3 * (g or 0) + 2 * (s or 0) + (b or 0),
            "medals": (g or 0) + (s or 0) + (b or 0),
            "host": hosts[year],
        }
        values[(year, country)] = point
        years[year].append(point)
    assert len(values) == 1242
    for year, points in years.items():
        for p in points:
            p["rank_min"] = 1 + sum(x["score"] > p["score"] for x in points)
            p["rank_max"] = sum(x["score"] >= p["score"] for x in points)
    athlete_counts = Counter(
        (year, country, athlete, medal) for country, medal, athlete, year in athletes
    )
    athlete_scores = defaultdict(int)
    for country, medal, athlete, year in athletes:
        athlete_scores[(year, country, athlete)] += {
            "Gold": 3,
            "Silver": 2,
            "Bronze": 1,
        }[medal]
    athlete_overall_scores = defaultdict(int)
    for (_year, _country, athlete), score in athlete_scores.items():
        athlete_overall_scores[athlete] += score
    top_athletes = set(
        sorted(athlete_overall_scores, key=lambda a: (-athlete_overall_scores[a], a))[
            :10
        ]
    )
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        r = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    assert len(r.findall("datasources/datasource/object-graph/objects/object")) == 3
    relationships = r.findall(
        "datasources/datasource/object-graph/relationships/relationship"
    )
    assert len(relationships) == 2
    assert len(r.findall("worksheets/worksheet")) == 5
    bump = r.find("worksheets/worksheet[@name='Bump']")
    assert [p.find("mark").get("class") for p in bump.findall("table/panes/pane")] == [
        "Line",
        "Shape",
    ]
    assert bump.find('table/style/style-rule/encoding[@reverse="true"]') is not None
    for name in ["Medals", "Top 10 Medalists"]:
        target = r.find("worksheets/worksheet[@name='" + name + "']")
        fs = [
            f
            for f in target.findall("table/view/filter")
            if "Tooltip" in f.get("column", "")
        ]
        assert len(fs) == 1
        g = fs[0].find("groupfilter")
        assert g.get("function") == "crossjoin" and len(g.findall("groupfilter")) == 2
        if name == "Top 10 Medalists":
            assert fs[0].get("context") == "true"
    for name in ["Top 10 Countries", "Top 10 Medalists", "Host in Top 10"]:
        assert (
            r.find("worksheets/worksheet[@name='" + name + "']/table/view/filter")
            is not None
        )
    host_size = r.find(
        "worksheets/worksheet[@name='Host in Top 10']/table/style/style-rule[@element='mark']/encoding[@attr='size']"
    )
    assert host_size is not None and host_size.get("reverse") == "true"
    assert (
        float(host_size.get("min-size")) == 0.2
        and float(host_size.get("max-size")) == 1
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"]:
        assert (
            hashlib.sha256((HERE / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    rank_column = r.find("datasources/datasource/column[@caption='Rank Score']").get(
        "name"
    )
    rank_tc = next(
        tc
        for tc in bump.findall(
            "table/view/datasource-dependencies/column-instance/table-calc"
        )
        if rank_column in tc.get("field", "")
    )
    assert len(rank_tc.findall("order")) == 3
    checks = []
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists():
        report = json.loads(manifest.read_text())
        expected_states = {
            "default": {},
            "year-2008": {"Year": "2008"},
            "year-2016": {"Year": "2016"},
        }
        expected_exports = {
            ("author", "Top 10 Medalists"),
            ("author", "Medals"),
            ("author", "Host in Top 10"),
            ("author", "Top 10 Countries"),
            ("author", "Bump"),
            ("replica", "Top 10 Countries"),
            ("replica", "Host in Top 10"),
            ("replica", "Medals"),
            ("replica", "Top 10 Medalists"),
            ("replica", "Bump"),
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
            selected_year = state.get("filters", {}).get("Year")
            for role in ["author", "replica"]:
                rows = list(
                    csv.DictReader(
                        (HERE / f"outputs/cloud-{role}-bump{suffix}.csv").open(
                            encoding="utf-8-sig"
                        )
                    )
                )
                visible = {}
                all_keys = set()
                for row in rows:
                    ck = next(
                        k
                        for k in row
                        if k
                        in ["Country (Extract2)", "Country Name", "Country (Medals)"]
                    )
                    key = (row["Year"], row[ck])
                    all_keys.add(key)
                    if key not in values:
                        # Tableau pads Country x Year domains for continuous bump paths.
                        # These rows have no original facts and must never get a top-10 rank.
                        assert all(
                            not v or num(v) == 0
                            for k, v in row.items()
                            if k in ["Gold", "Silver", "Bronze", "Score", "# Medals"]
                        )
                        assert all(
                            not v for k, v in row.items() if "Top 10 Rank Only" in k
                        ), (role, key, row)
                        continue
                    point = values[key]
                    for k, v in row.items():
                        if not v or v.lower() == "null":
                            continue
                        if k == "Score":
                            assert num(v) == point["score"], (key, v, point["score"])
                        if "Top 10 Rank Only" in k:
                            rank = int(num(v))
                            assert (
                                point["rank_min"] <= rank <= point["rank_max"]
                                and rank <= 10
                            ), (key, rank, point)
                            visible[key] = rank
                        if k in ["Gold", "Silver", "Bronze"]:
                            assert num(v) == point[k.lower()]
                expected_years = [selected_year] if selected_year else list(hosts)
                for year in expected_years:
                    assert {v for (y, c), v in visible.items() if y == year} == set(
                        range(1, 11)
                    ), (role, year)
                for name in ["host", "medals", "athletes", "top-countries"]:
                    export = list(
                        csv.DictReader(
                            (HERE / f"outputs/cloud-{role}-{name}{suffix}.csv").open(
                                encoding="utf-8-sig"
                            )
                        )
                    )
                    if name == "top-countries" and role == "author":
                        assert not export, (
                            "Original unused VIT target is empty outside its triggering tooltip."
                        )
                        continue
                    assert export, (name, role, state["name"])
                    exported_medals = set()
                    exported_athletes = set()
                    exported_hosts = set()
                    exported_top_countries = set()
                    for row in export:
                        if name in ["medals", "top-countries"]:
                            country_key = next(
                                k
                                for k in row
                                if k
                                in [
                                    "Country (Extract2)",
                                    "Country Name",
                                    "Country (Medals)",
                                ]
                            )
                            key = (row["Year"], row[country_key])
                            assert key in values, (name, role, key)
                            point = values[key]
                            if name == "medals":
                                measure = row["Measure Names"].lower()
                                assert measure in ["gold", "silver", "bronze"]
                                assert (
                                    num(row["Measure Values"] or "0") == point[measure]
                                ), (role, key, measure, row)
                                exported_medals.add((*key, measure))
                            else:
                                exported_top_countries.add(key)
                                assert num(row["Score"]) == point["score"]
                                assert (
                                    point["country"] == point["host"]
                                    or point["rank_min"] <= 10
                                ), (key, point)
                        if row.get("Year"):
                            assert row["Year"] in hosts
                        if name == "host":
                            year = row["Year"]
                            exported_hosts.add(year)
                            assert row["Host Country"] == hosts[year]
                            hp = values.get((year, hosts[year]))
                            assert hp is not None
                            for k, v in row.items():
                                if not v:
                                    continue
                                if "Score for Host" in k:
                                    assert num(v) == hp["score"]
                                if "Medals for Host" in k:
                                    assert num(v) == hp["medals"]
                                if (
                                    "Is Host in Top 10?" in k
                                    or "Host Indicator Size" in k
                                ):
                                    assert int(num(v)) == int(hp["rank_min"] <= 10)
                        if name == "athletes" and row.get("Athlete"):
                            ck = next(
                                k
                                for k in row
                                if k
                                in [
                                    "Country (Extract2)",
                                    "Country Name",
                                    "Country (Medals)",
                                ]
                            )
                            key = (row["Year"], row[ck], row["Athlete"])
                            assert (
                                key in athlete_scores and row["Athlete"] in top_athletes
                            ), key
                            if row.get("Medal"):
                                exported_athletes.add((*key, row["Medal"]))
                                for k, v in row.items():
                                    if v and (
                                        "COUNT(" in k
                                        or k.startswith(("Count of ", "CNT("))
                                        or k == "Medalists"
                                    ):
                                        assert (
                                            num(v)
                                            == athlete_counts[(*key, row["Medal"])]
                                        ), (key, k, v)
                    if name == "host":
                        assert exported_hosts == set(expected_years)
                        assert len(export) == len(expected_years)
                    if name == "top-countries":
                        # RANK_UNIQUE may choose different tied countries on separate
                        # sheets. Require every definite top-ten country and the host;
                        # the remaining boundary ties must still fill all ten slots.
                        for year in expected_years:
                            actual_countries = {
                                country
                                for y, country in exported_top_countries
                                if y == year
                            }
                            required = {
                                point["country"]
                                for point in years[year]
                                if point["rank_max"] <= 10
                            } | {hosts[year]}
                            assert required <= actual_countries, (
                                role,
                                state["name"],
                                year,
                                required - actual_countries,
                            )
                            hp = values[(year, hosts[year])]
                            assert len(actual_countries) == 10 + int(
                                hp["rank_min"] > 10
                            ), (role, state["name"], year, actual_countries)
                    if name == "medals":
                        expected_medals = {
                            (year, country, medal)
                            for year, country in values
                            if not selected_year or year == selected_year
                            for medal in ["gold", "silver", "bronze"]
                        }
                        assert exported_medals == expected_medals, (
                            role,
                            len(exported_medals),
                            len(expected_medals),
                        )
                    if name == "athletes":
                        expected_athletes = {
                            key
                            for key in athlete_counts
                            if key[2] in top_athletes
                            and (not selected_year or key[0] == selected_year)
                        }
                        assert exported_athletes == expected_athletes, (
                            role,
                            state["name"],
                            len(exported_athletes),
                            len(expected_athletes),
                        )
                checks.append(
                    {
                        "state": state["name"],
                        "role": role,
                        "visible_top10_marks": len(visible),
                        "exported_country_years_including_domain_padding": len(
                            all_keys
                        ),
                        "original_fact_country_years": sum(
                            1
                            for year, _country in values
                            if not selected_year or year == selected_year
                        ),
                        "five_sheet_exports": True,
                        "original_top_countries_scope": "Empty outside triggering VIT; not offered as data proof",
                        "passed": True,
                    }
                )
    data = {
        "country_years": list(values.values()),
        "athlete_medal_rows": len(athletes),
        "athlete_year_country_groups": len(athlete_scores),
        "hosts": hosts,
        "scope": "All1242 country/year medal totals, weighted scores/tie rank ranges, all33203 athlete medal rows and28 host years; native VIT field/context contracts.",
    }
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
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
        "PASS WW31 three-table oracle and native multi-field VIT; cloud="
        + ("passed" if checks else "pending")
    )


if __name__ == "__main__":
    verify()
