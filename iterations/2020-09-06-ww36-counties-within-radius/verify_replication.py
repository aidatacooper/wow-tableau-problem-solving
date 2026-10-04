"""Locked county census, independent percentiles and great-circle radius scenarios."""

import ast, csv, json, math
from collections import Counter
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent


def raw():
    data = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, data) as c:
            rows = c.execute_list_query(
                'SELECT "County, State","State","County","Cumulative Case Count","Date","latitude","longitude","num_staffed_beds","num_icu_beds","num_ventilators_est" FROM "Extract"."Extract"'
            )
    return {
        r[0]: {
            "state": r[1],
            "county": r[2],
            "cases": r[3],
            "date": str(r[4]),
            "lat": r[5],
            "lon": r[6],
            "beds": r[7],
            "icu": r[8],
            "vents": r[9],
        }
        for r in rows
    }


def percentile(rows):
    counts = Counter(r["beds"] for r in rows.values() if r["beds"] is not None)
    ranks, seen = {}, 0
    for value, count in sorted(counts.items()):
        ranks[value] = (
            (seen + count - 1) / (sum(counts.values()) - 1)
            if sum(counts.values()) > 1
            else 0
        )
        seen += count
    return {
        key: None if r["beds"] is None else ranks[r["beds"]] for key, r in rows.items()
    }


def miles(a, b):
    p, q = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p - q
    dl = math.radians(a["lon"] - b["lon"])
    return (
        3958.7613
        * 2
        * math.asin(
            min(
                1,
                math.sqrt(
                    math.sin(dp / 2) ** 2
                    + math.cos(p) * math.cos(q) * math.sin(dl / 2) ** 2
                ),
            )
        )
    )


def verify():
    # blank-sdk-build; locked-inputs; native-calculations; complete-data-oracle;
    # cloud-rest-comparison; cloud-visual-review
    text = (HERE / "build_replication.py").read_text(encoding="utf-8-sig")
    assert 'TWBEditor("")' in text
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_")
        for n in ast.walk(ast.parse(text))
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    for item in lock["extracted_data"]:
        assert sha256((HERE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        assert (
            sha256(
                z.read(next(n for n in z.namelist() if n.endswith(".hyper")))
            ).hexdigest()
            == lock["extracted_data"][0]["sha256"]
        )
    assert root.xpath("//worksheet/@name") == [
        "Cases Bar",
        "Data",
        "Map - Main",
        "Map - AL",
        "Map - HI",
        "Utilisation Bar",
    ]
    assert root.xpath('//dashboard/size[@maxwidth="1366"][@maxheight="968"]')
    assert root.xpath(
        '//zone[@type-v2="setMembership"][@name="Map - Main"][@mode="dropdown"]'
    )
    assert root.xpath(
        '//windows/window[@name="Map - Main"]//card[@type="setMembership"][@mode="dropdown"]'
    )
    assert len(root.xpath('//worksheet//mark[@class="Multipolygon"]')) == 6
    assert not root.xpath("//action")
    assert not root.xpath('//calculation[contains(@formula,"TODAY(")]')
    columns = {
        n.get("caption"): n
        for n in root.xpath("/workbook/datasources/datasource/column[@caption]")
    }

    def formula(name):
        value = columns[name].find("calculation").get("formula")
        for caption, column in columns.items():
            value = value.replace(column.get("name"), "[" + caption + "]")
        return value.replace("[Parameters].", "")

    assert (
        formula("Within n miles")
        == "([Count Selected States]=1 AND [Distance]<=[n miles]) OR [Count Selected States]>1"
    )
    assert (
        formula("Distance")
        == "DISTANCE([Selected County Start Point],[End Point],'miles')"
    )
    assert (
        formula("Percentile Beds") == "RANK_PERCENTILE(SUM([num_staffed_beds]),'asc')"
    )
    native_contexts = {}
    percentile_name = columns["Percentile Beds"].get("name")
    assert columns["Percentile Beds"].xpath(
        "calculation/table-calc/@ordering-type"
    ) == ["Columns"]
    for sheet in ["Map - Main", "Map - AL", "Map - HI"]:
        worksheet = root.xpath('//worksheet[@name="' + sheet + '"]')[0]
        binding = worksheet.xpath(".//pane/encodings/color/@column")
        assert len(binding) == 1
        instance_name = binding[0].split("].[", 1)[1]
        instance_name = "[" + instance_name
        instance = worksheet.xpath('.//column-instance[@name="' + instance_name + '"]')[
            0
        ]
        assert instance.get("column") == percentile_name
        assert instance_name.rsplit(":", 1)[-1].rstrip("]").isdigit(), instance_name
        style_binding = worksheet.xpath(
            './/style/style-rule[@element="mark"]/encoding[@attr="color"]/@field'
        )
        assert binding[0] in style_binding, (sheet, binding[0], style_binding)
        assert instance.xpath("table-calc/@ordering-type") == ["Field"]
        assert [
            f.rsplit("].[", 1)[1].rstrip("]")
            for f in instance.xpath("table-calc/order/@field")
        ] == ["County", "County, State", "State"]
        assert worksheet.xpath(
            './/column[@name="'
            + percentile_name
            + '"]/calculation/table-calc/@ordering-type'
        ) == ["Columns"]
        native_contexts[sheet] = {
            "base_ordering": "Columns",
            "instance_ordering": "Field",
            "addressing": ["County", "County, State", "State"],
            "binding": binding[0],
        }
    all_rank_instances = root.xpath(
        '//worksheet//column-instance[@column="' + percentile_name + '"]'
    )
    assert len(all_rank_instances) == 5
    assert len({node.get("name") for node in all_rank_instances}) == 5, (
        "Workbook-wide rank contexts must be distinct across worksheets"
    )
    main_color = root.xpath('//worksheet[@name="Map - Main"]//encodings/color/@column')[
        0
    ]
    assert root.xpath('//zone[@type-v2="color"][@name="Map - Main"]/@param') == [
        main_color
    ]
    for sheet in ["Cases Bar", "Data"]:
        worksheet = root.xpath('//worksheet[@name="' + sheet + '"]')[0]
        instance = worksheet.xpath(
            './/column-instance[@column="' + percentile_name + '"]'
        )[0]
        assert instance.get("name").rsplit(":", 1)[-1].rstrip("]").isdigit()
        assert instance.xpath("table-calc/@ordering-type") == ["Field"]
        actual_fields = [
            field.rsplit("].[", 1)[1].rstrip("]")
            for field in instance.xpath("table-calc/order/@field")
        ]
        assert actual_fields == (
            ["io:Selected County:nk", "County, State"]
            if sheet == "Cases Bar"
            else ["County, State", "State"]
        )
        bindings = worksheet.xpath(
            ".//encodings/*/@column | .//measure-values/*/@name | .//measure-values/*/@column | .//groupfilter/@member"
        )
        assert any(instance.get("name") in field for field in bindings), (
            sheet,
            instance.get("name"),
            bindings,
        )
    setname = root.xpath('//group[@caption="Selected County"]/@name')[0]
    members = root.xpath(
        '//group[@caption="Selected County"]//groupfilter[@function="member"]/@member'
    )
    rows = raw()
    assert len(rows) == len(members) == 3142
    with (HERE / "inputs/county-members.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        index = list(csv.DictReader(stream))
    assert {r["County, State"] for r in index} == set(rows)
    assert len({r["date"] for r in rows.values()}) == 1 and {
        r["date"] for r in rows.values()
    } == {"2020-08-26"}
    maps = {
        name: {
            k: r
            for k, r in rows.items()
            if (
                r["state"] not in ["Alaska", "Hawaii"]
                if name == "Map - Main"
                else r["state"] == ("Alaska" if name == "Map - AL" else "Hawaii")
            )
        }
        for name in ["Map - Main", "Map - AL", "Map - HI"]
    }
    independent = []
    anchor = "Autauga County, Alabama"
    assert anchor in rows
    for radius in [0, 50, 100, 250, 500]:
        selected = {k: r for k, r in rows.items() if miles(rows[anchor], r) <= radius}
        assert anchor in selected
        independent.append(
            {
                "anchor": anchor,
                "radius_miles": radius,
                "county_count": len(selected),
                "cases": sum(r["cases"] or 0 for r in selected.values()),
                "hospital_beds": sum(r["beds"] or 0 for r in selected.values()),
                "method": "Independent spherical great-circle computation; not a REST-executed set selection. Source native DISTANCE contract separately checked.",
            }
        )
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "counties": len(rows),
        "raw_totals": {
            metric: sum(r[metric] or 0 for r in rows.values())
            for metric in ["cases", "beds", "icu", "vents"]
        },
        "map_counts": {n: len(v) for n, v in maps.items()},
        "native_percentile_contexts": native_contexts,
        "radius_scenarios": independent,
        "browser_interaction_executed": False,
        "scope": "Default All set and mile parameter REST states. Single-county membership is an artifact/formula and independent-distance scope; no REST set-member manipulation has been validated.",
    }
    cloudpath = HERE / "evidence/cloud-verification.json"
    if cloudpath.exists():
        cloud = json.loads(cloudpath.read_text(encoding="utf-8"))
        assert cloud["source_hashes"]["replica"] == digest
        proof = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert cloud["source_hashes"]["author"] == proof["comparison_sha256"]
        assert proof["original_sha256"] == lock["source_workbook"]["sha256"]
        assert cloud["browser_interaction_executed"] is False
        assert {s["name"] for s in cloud["states"]} == {
            "default",
            "miles-50",
            "miles-250",
        }
        checks = []
        for state in cloud["states"]:
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for capture in state["data"]:
                path = HERE / capture["path"]
                assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    exported = list(csv.DictReader(stream))
                assert exported, path
                author = path.name.startswith("cloud-author")
                view = capture["view"]

                def number(value):
                    if not value.strip():
                        return None
                    return float(value.replace(",", "").replace("%", "")) / (
                        100 if "%" in value else 1
                    )

                def check(value, target, tolerance=0):
                    actual = number(value)
                    assert (
                        actual is None
                        if target is None
                        else actual is not None and abs(actual - target) <= tolerance
                    ), (path, value, target)

                if view in ["Cases Bar", "Data"]:
                    wanted = rows
                    pct = percentile(wanted)
                    seen = {}
                    for row in exported:
                        key = row["County, State"]
                        assert key in wanted, (path, key)
                        if view == "Cases Bar":
                            assert (
                                key not in seen
                                and row["In / Out of Selected County"] == "In"
                            ), (path, key)
                            check(row["Cumulative Case Count"], wanted[key]["cases"])
                            check(row["Percentile Beds"], pct[key], 0.000051)
                            seen[key] = True
                        else:
                            metric = row["Measure Names"].split(" along ")[0]
                            assert metric not in seen.setdefault(key, {}), (
                                path,
                                key,
                                metric,
                            )
                            if metric.startswith("Percentile"):
                                check(row["Measure Values"], pct[key], 1e-9)
                            else:
                                assert not author and metric in {
                                    "num_staffed_beds",
                                    "Hospital Beds",
                                }, (
                                    path,
                                    metric,
                                )
                                check(row["Measure Values"], wanted[key]["beds"])
                            seen[key][metric] = True
                    assert set(seen) == set(wanted), (
                        path,
                        "Full county coverage",
                        len(seen),
                        len(wanted),
                    )
                    if view == "Data":
                        assert all(len(v) == 2 for v in seen.values())
                elif view in maps:
                    wanted = maps[view]
                    pct = percentile(wanted)
                    seen = set()
                    outlines = set()
                    aliases = {
                        "beds": "Hospital Beds" if author else "num_staffed_beds",
                        "icu": "ICU Beds" if author else "num_icu_beds",
                        "vents": "Ventilators (est)"
                        if author
                        else "num_ventilators_est",
                    }
                    for row in exported:
                        key = row["County, State"]
                        if not key:
                            state_name = row["States with n miles"]
                            assert (
                                state_name in {r["state"] for r in wanted.values()}
                                and state_name not in outlines
                            ), (path, row)
                            outlines.add(state_name)
                            continue
                        assert key in wanted and key not in seen, (path, key)
                        target = wanted[key]
                        assert (
                            row["State"] == target["state"]
                            and row["County"] == target["county"]
                        ), (path, key, row)
                        check(row["Cumulative Case Count"], target["cases"])
                        check(row["Percentile Beds"], pct[key], 0.000051)
                        for metric, column in aliases.items():
                            check(row[column], target[metric])
                        seen.add(key)
                    assert seen == set(wanted), (
                        path,
                        "Full map county coverage",
                        len(seen),
                        len(wanted),
                    )
                    assert outlines == {r["state"] for r in wanted.values()}, (
                        path,
                        "Native state overlay coverage",
                        outlines,
                    )
                elif view == "Utilisation Bar":
                    names = {
                        "Hospital Beds": "beds",
                        "ICU Beds": "icu",
                        "Ventilators (est)": "vents",
                        "Ventilators": "vents",
                    }
                    seen = set()
                    for row in exported:
                        metric = names[row["Measure Names"]]
                        assert metric not in seen
                        check(
                            row["Measure Values"],
                            sum(r[metric] or 0 for r in rows.values()),
                        )
                        seen.add(metric)
                    assert seen == {"beds", "icu", "vents"}
                else:
                    raise AssertionError((path, "Unknown grain", view))
                checks.append(
                    {
                        "path": capture["path"],
                        "rows": len(exported),
                        "view": view,
                        "status": "pass",
                    }
                )
        assert len(checks) == 36
        report["cloud_checks"] = checks
        report["status"] = "pass"
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    assert report["status"] == "pass", (
        "Cloud CSV full-grain comparisons remain required"
    )
    print(
        "PASS",
        len(rows),
        "locked counties; native set control; independent radius scenarios",
    )


if __name__ == "__main__":
    verify()
