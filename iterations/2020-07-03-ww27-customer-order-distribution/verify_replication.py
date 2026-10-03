"""Independent customer-order buckets and every centered dot position."""

import ast
import csv
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def verify():
    # blank-sdk-build; locked-source-data; native-table-calculations;
    # complete-bucket-oracle; cloud-rest-comparison; cloud-visual-review
    source = (HERE / "build_replication.py").read_text(encoding="utf-8")
    assert 'TWBEditor("")' in source
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_")
        for n in ast.walk(ast.parse(source))
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    data = HERE / item["file"]
    assert sha256(data.read_bytes()).hexdigest() == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as package:
        root = etree.fromstring(
            package.read(next(n for n in package.namelist() if n.endswith(".twb")))
        )
        assert (
            sha256(
                package.read(
                    next(n for n in package.namelist() if n.endswith(".hyper"))
                )
            ).hexdigest()
            == item["sha256"]
        )
    assert root.xpath("//worksheet/@name") == ["Viz"]
    assert root.xpath('//dashboard/size[@maxwidth="900"][@maxheight="500"]')
    assert root.xpath('//worksheet//mark[@class="Circle"]')
    assert root.xpath(
        '//worksheet//mark-sizing[@mark-sizing-setting="marks-scaling-off"]'
    )
    columns = {
        n.get("caption"): n
        for n in root.xpath("/workbook/datasources/datasource/column[@caption]")
    }

    def formula(name):
        value = columns[name].find("calculation").get("formula")
        for caption, field in columns.items():
            value = value.replace(field.get("name"), "[" + caption + "]")
        return value.replace("[Parameters].", "")

    assert (
        columns["# Orders Per Customer"].find("calculation").get("formula")
        == "{FIXED [Segment],[Customer ID]: COUNTD([Order ID])}"
    )
    assert (
        formula("Marks to Plot")
        == "INT([# Customers per Order Count]/[pMarkIndicator])"
    )
    assert formula("Cols") == "[Index]%[Marks to Plot]"
    assert formula("# Customers per Order Count") == "WINDOW_SUM([# Customers])"
    calculations = root.xpath("//worksheet//column-instance/table-calc")
    assert calculations and all(
        n.get("ordering-type") == "Field"
        and "Customer ID" in n.get("ordering-field", "")
        for n in calculations
    )
    assert root.xpath('//worksheet//encodings/lod[contains(@column,"Customer ID")]')
    assert root.xpath(
        '//worksheet//style-rule[@element="axis"]/format[@attr="display"][@scope="cols"][@value="false"]'
    )
    assert root.xpath(
        '//worksheet//style-rule[@element="axis"]/format[@attr="title"][@scope="rows"][@value="Total Orders"]'
    )
    assert not root.xpath("//action")
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, data) as connection:
            rows = connection.execute_list_query(
                'SELECT "Segment","Customer ID","Order ID" FROM "Extract"."Extract"'
            )
    orders = defaultdict(set)
    for segment, customer, order in rows:
        orders[(segment, customer)].add(order)
    buckets = defaultdict(list)
    for (segment, customer), values in orders.items():
        buckets[(segment, len(values))].append(customer)
    expected = {}
    for parameter in [1, 5, 10]:
        expected[parameter] = {}
        for key, customers in buckets.items():
            count = len(customers) // parameter
            positions = [j - (count - 1) / 2 for j in range(count)]
            assert not positions or sum(positions) == 0
            expected[parameter][key] = {
                "customers": len(customers),
                "circles": count,
                "positions": positions,
            }
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "raw_rows": len(rows),
        "customers": len(orders),
        "buckets": {str(k): v for k, v in expected[5].items()},
        "cloud_scope": "Full customer-grain worksheet CSV, including all rendered overlapping customer marks; unique coordinates prove visible dot counts.",
    }
    manifest_path = HERE / "evidence/cloud-verification.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert manifest["source_hashes"]["replica"] == digest
        assert manifest["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert provenance["original_sha256"] == lock["locked_original_sha256"]
        assert {s["name"] for s in manifest["states"]} == {
            "default",
            "one-customer",
            "ten-customers",
        }
        checks = []
        for state in manifest["states"]:
            parameter = {"default": 5, "one-customer": 1, "ten-customers": 10}[
                state["name"]
            ]
            assert len(state["data"]) == 2
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
                assert exported, (path, "Empty export")
                seen = set()
                coords = defaultdict(set)
                for row in exported:
                    segment, customer = row["Segment"], row["Customer ID"]
                    count_key = next(k for k in row if "Orders Per Customer" in k)
                    order_count = int(float(row[count_key]))
                    assert order_count == len(orders[(segment, customer)])
                    key = (segment, order_count)
                    coordinate_key = next(k for k in row if "Cols Shifted" in k)
                    text = row[coordinate_key]
                    if not text or text.lower() in {"null", "none"}:
                        assert expected[parameter][key]["circles"] == 0
                        continue
                    position = float(text.replace(",", ""))
                    assert position in expected[parameter][key]["positions"], (
                        path,
                        key,
                        position,
                    )
                    coords[key].add(position)
                    seen.add((segment, customer))
                required = {
                    key
                    for key, value in orders.items()
                    if expected[parameter][(key[0], len(value))]["circles"] > 0
                }
                assert seen == required, (
                    path,
                    "Missing/extra customer marks",
                    len(seen),
                    len(required),
                )
                for key, bucket in expected[parameter].items():
                    assert coords[key] == set(bucket["positions"]), (
                        path,
                        key,
                        coords[key],
                        bucket,
                    )
                checks.append(
                    {"path": capture["path"], "rows": len(exported), "status": "pass"}
                )
        assert len(checks) == 6
        report["cloud_checks"] = checks
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        "PASS",
        len(rows),
        "raw rows;",
        len(orders),
        "customers;",
        len(buckets),
        "buckets; parameters 1/5/10",
    )


if __name__ == "__main__":
    verify()
