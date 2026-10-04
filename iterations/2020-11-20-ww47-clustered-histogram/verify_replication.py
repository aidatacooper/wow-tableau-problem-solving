"""Independent all-record business oracle and native/Cloud workbook verification."""

import csv
import io
import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess, Telemetry, Connection

ACCEPTANCE_IDS = ["ww47-raw-oracle", "ww47-native-contracts", "ww47-cloud-data"]
HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def raw():
    file = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as p:
        with Connection(p.endpoint, str(file)) as c:
            return c.execute_list_query('SELECT * FROM "Extract"."Extract"')


def root():
    artifact = HERE / "outputs" / "replicated-workbook.twbx"
    with ZipFile(artifact) as z:
        twb = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
        lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf8"))
        for f in lock["extracted_data"]:
            original = HERE / f["file"]
            assert digest(original) == f["sha256"]
            member = next(n for n in z.namelist() if n.endswith(original.name))
            assert sha256(z.read(member)).hexdigest() == f["sha256"]
    return twb


def csvrows(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))


def number(value):
    return float(value.replace(",", "").replace("$", "").strip())


def verify():
    business = oracle()
    native(root())
    result = {
        "artifact_sha256": digest(HERE / "outputs/replicated-workbook.twbx"),
        "status": "passed",
        "raw_oracle": business,
        "native_contracts": "passed",
        "browser_interaction_executed": False,
    }
    manifest_path = HERE / "evidence/cloud-verification.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf8"))
        assert manifest["source_hashes"]["replica"] == result["artifact_sha256"]
        checks = []
        for state in manifest["states"]:
            for item in state["data"]:
                p = HERE / item["path"]
                assert digest(p) == item["sha256"]
                records = csvrows(p)
                assert records, f"Empty CSV {p.name}"
                check_cloud(
                    records, state["name"], item["view"], business, item["role"]
                )
                checks.append(
                    {
                        "state": state["name"],
                        "role": item["role"],
                        "view": item["view"],
                        "records": len(records),
                        "passed": True,
                    }
                )
        result["cloud_checks"] = checks
    else:
        result["cloud_checks"] = "not yet captured"
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "artifact_sha256": result["artifact_sha256"],
                "cloud_checks": result["cloud_checks"],
            },
            indent=2,
        )
    )


def oracle():
    facts = raw()
    assert len(facts) == 3312
    orders = defaultdict(lambda: {"sales": 0.0, "segments": set()})
    for oid, day, segment, sales in facts:
        assert day.year == 2020
        orders[oid]["sales"] += sales
        orders[oid]["segments"].add(segment)
    bins = defaultdict(set)
    details = {}
    for oid, row in orders.items():
        assert len(row["segments"]) == 1
        segment = next(iter(row["segments"]))
        upper = math.ceil(row["sales"] / 100) * 100
        capped = min(2100, upper)
        amount = capped - {"Consumer": 75, "Corporate": 50, "Home Office": 25}[segment]
        bins[segment.upper(), amount].add(oid)
        details[oid] = {
            "value": row["sales"],
            "upper": upper,
            "segment": segment,
            "x": amount,
        }
    assert len(orders) == 1687
    return {
        "facts": len(facts),
        "distinct_orders": len(orders),
        "orders": details,
        "groups": [
            {"segment": segment, "x": x, "count": len(ids)}
            for (segment, x), ids in sorted(bins.items())
        ],
    }


def native(r):
    chart = r.find("worksheets/worksheet[@name='Chart']")
    assert chart is not None
    assert chart.find("table/panes/pane/mark").get("class") == "Bar"
    assert ":none:" not in chart.findtext("table/cols")
    assert ".[none:" in chart.findtext("table/cols")
    assert ".[usr:" in chart.findtext("table/rows")
    columns = {
        c.get("caption", c.get("name", "").strip("[]")): c
        for c in r.findall("datasources/datasource/column")
    }
    assert "COUNTD([Order ID])" in columns["# ORDERS"].find("calculation").get(
        "formula"
    )
    assert "FIXED [Order ID]" in columns["Order Value"].find("calculation").get(
        "formula"
    )
    assert "CEILING" in columns["Round Up to 100"].find("calculation").get("formula")
    assert chart.find("table/panes/pane/customized-tooltip/formatted-text") is not None
    band = chart.findall("table/panes/pane/reference-line")
    assert len(band) == 2
    assert {float(x.get("value")) for x in band} == {2000, 2100}
    ids = {x.get("id") for x in band}
    assert all(
        x.get("paired-id") in ids and x.get("paired-id") != x.get("id") for x in band
    )
    assert next(x for x in band if x.get("value") == "2100").get("label") == "$2000+"
    assert (
        chart.find(
            "table/style/style-rule[@element='refband']/format[@attr='fill-color']"
        ).get("value")
        == "#f5f5f5"
    )
    label_style = chart.find("table/style/style-rule[@element='refline']")
    assert label_style.find("format[@attr='vertical-align']").get("value") == "top"
    assert label_style.find("format[@attr='color']").get("value") == "#000000"
    assert label_style.find("format[@attr='font-weight']").get("value") == "bold"
    axis = chart.find("table/style/style-rule[@element='axis']/encoding")
    assert (
        axis.get("min") == "12"
        and axis.get("max") == "2099"
        and axis.get("range-type") == "fixed"
    )
    legend = r.find("dashboards/dashboard/zones//zone[@type-v2='color']")
    assert (
        legend is not None
        and legend.get("name") == "Chart"
        and legend.get("leg-item-layout") == "horz"
    )
    size = r.find("dashboards/dashboard/size")
    assert size.get("maxwidth") == "1400" and size.get("maxheight") == "800"


def check_cloud(records, state, view, business, role):
    expected = {
        (g["segment"], g["x"]): g["count"]
        for g in business["groups"]
        if state == "default" or g["segment"] == state.upper()
    }
    actual = {}
    for row in records:
        sk = next(k for k in row if "segment" in k.lower() and "upper" in k.lower())
        xk = next(k for k in row if k.upper() == "SALE AMOUNT")
        ck = next(k for k in row if "ORDERS" in k.upper())
        key = row[sk].upper(), int(number(row[xk]))
        assert key not in actual
        actual[key] = int(number(row[ck]))
        if role == "author":
            segment, x = key
            assert row["Segment"].upper() == segment
            high = x >= 2000
            upper = x + {"CONSUMER": 75, "CORPORATE": 50, "HOME OFFICE": 25}[segment]
            assert row["TOOLTIP : between"] == ("" if high else " between")
            assert row["TOOLTIP : symbol"] == ("$2000+" if high else " - ")
            assert row["TOOLTIP : Lower"] == ("" if high else f"${upper - 100:,}")
            assert row["TOOLTIP : Upper"] == ("" if high else f"${upper:,}")

    assert actual == expected, (
        role,
        state,
        len(actual),
        len(expected),
        actual,
        expected,
    )


if __name__ == "__main__":
    verify()
