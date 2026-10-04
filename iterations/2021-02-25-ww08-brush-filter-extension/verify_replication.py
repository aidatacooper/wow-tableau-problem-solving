"""Independently count raw monthly sightings and audit real extension contracts."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "monthly-borough-counts",
    "endpoint-change-colors",
    "real-brush-extension-contract",
]
BOROUGHS = ["BROOKLYN", "MANHATTAN", "BRONX", "QUEENS", "STATEN ISLAND"]
URL = "https://extensions.tableauusercontent.com/sandbox/brush-filter/index.html"
SETTINGS = {
    "chartBackgroundColor": "#ffffff",
    "chartColor": "#0093a7",
    "sheetIdSetting": "0",
    "vizBackgroundColor": "#ffffff",
    "xAxisSetting": "MONTH(Created Date)",
    "yAxisSetting": "AGG(# of Sightings)",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text())
    path = HERE / lock["extracted_data"][0]["file"]
    assert digest(path) == lock["extracted_data"][0]["sha256"]
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as conn,
    ):
        rows = conn.execute_list_query(
            'SELECT "Created Date","Borough" FROM "Extract"."Extract"'
        )
    assert len(rows) == 158923 and all(d is not None for d, b in rows), (
        "COUNT(date) equals row count only when every date is non-null"
    )
    counts = Counter()
    dates = defaultdict(list)
    excluded = Counter()
    for day, borough in rows:
        month = date(day.year, day.month, 1)
        if not date(2010, 1, 1) <= month <= date(2021, 2, 1):
            excluded[str(borough)] += 1
            continue
        counts[borough, month.isoformat()] += 1
        dates[borough, month.isoformat()].append(day)
    cells = []
    endpoint = {}
    for borough in BOROUGHS + ["Unspecified"]:
        months = sorted(m for b, m in counts if b == borough)
        first, last = months[0], months[-1]
        start, end = counts[borough, first], counts[borough, last]
        change = (
            "INCREASE" if end > start else "DECREASE" if end < start else "NO CHANGE"
        )
        endpoint[borough] = {
            "first_month": first,
            "last_month": last,
            "start_count": start,
            "end_count": end,
            "change": change,
        }
        cells.extend(
            {
                "borough": borough,
                "month": month,
                "sightings": counts[borough, month],
                "change": change,
            }
            for month in months
        )
    return {
        "raw_rows": len(rows),
        "null_dates": 0,
        "visible_cells": sum(c["borough"] in BOROUGHS for c in cells),
        "visible_sightings": sum(
            c["sightings"] for c in cells if c["borough"] in BOROUGHS
        ),
        "outside_date_range_rows": dict(excluded),
        "default_excluded_unspecified_rows": sum(
            c["sightings"] for c in cells if c["borough"] == "Unspecified"
        ),
        "endpoints": endpoint,
        "cells": cells,
    }


def month(value):
    for pattern in ["%B %Y", "%b %y", "%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"]:
        try:
            d = datetime.strptime(value, pattern)  # noqa: DTZ007 -- source value is a calendar month without a time zone
            return date(d.year, d.month, 1).isoformat()
        except ValueError:
            pass
    raise AssertionError(("Unknown Cloud month encoding", value))


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
    assert (
        manifest["browser_interaction_executed"] is False
        and len(manifest["states"]) == 2
    )
    for state in manifest["states"]:
        assert state["parameters"] == {} and state["filters"] == (
            {} if state["name"] == "default" else {"Borough": "BROOKLYN"}
        )
        assert len(state["data"]) == 2 and set(state["views"]) == {"author", "replica"}
        for item in list(state["views"].values()) + state["data"]:
            assert digest(HERE / item["path"]) == item["sha256"]


def cloud(data):
    if not (HERE / "evidence/cloud-verification.json").exists():
        return []
    checked = []
    for suffix, boroughs in [
        ("", BOROUGHS),
        ("-exclude-brooklyn", BOROUGHS[1:] + ["Unspecified"]),
    ]:
        expected = {
            (cell["borough"], cell["month"]): cell
            for cell in data["cells"]
            if cell["borough"] in boroughs
        }
        for role in ["author", "replica"]:
            path = HERE / f"outputs/cloud-{role}-borough{suffix}.csv"
            if not path.exists():
                return []
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == len(expected), (path, len(rows), len(expected))
            seen = set()
            for row in rows:
                date_key = next(k for k in row if "Created Date" in k)
                key = (row["Borough"], month(row[date_key]))
                assert key not in seen and key in expected
                seen.add(key)
                assert (
                    int(row["# of Sightings"].replace(",", ""))
                    == expected[key]["sightings"]
                )
                assert row["Change"] == expected[key]["change"]
                assert month(row["Start Month"]) == "2010-01-01"
                assert month(row["End Month"]) == (
                    "2021-02-01" if not suffix else "2020-09-01"
                )
                if role == "replica":
                    end = data["endpoints"][key[0]]
                    assert (
                        int(row["Start Count"].replace(",", "")) == end["start_count"]
                    )
                    assert int(row["End Count"].replace(",", "")) == end["end_count"]
            assert seen == set(expected)
            checked.append(
                {
                    "state": suffix.lstrip("-") or "default",
                    "role": role,
                    "csv_cells": len(rows),
                    "raw_monthly_counts_and_change": "pass",
                    "file": str(path.relative_to(HERE)),
                    "sha256": digest(path),
                }
            )
    return checked


def verify():
    path = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(path) as z:
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    manifest = root.find(
        "referenced-extensions/referenced-extension/manifest/dashboard-extension"
    )
    assert (
        manifest.get("id") == "com.starschema.extension.brushfilter.sandboxed"
        and manifest.get("extension-version") == "0.1.0"
    )
    assert (
        manifest.findtext("source-location/url") == URL
        and manifest.findtext("min-api-version") == "1.1"
    )
    assert manifest.find("context-menu/configure-context-menu-item") is not None
    reference = root.find(
        "referenced-extensions/referenced-extension/referenced-views/referenced-view"
    )
    assert (
        reference.get("instances") == "1"
        and reference.get("viewId") == "2021_02_24_WW08_Brush_Filter_Extension"
    )
    dashboard = root.find("dashboards/dashboard")
    zones = dashboard.xpath('zones/zone[@type-v2="dashboard-object"]')
    assert len(zones) == 1
    zone = zones[0]
    addon = zone.find("add-in")
    assert addon.get("extension-url") == URL and addon.get("add-in-id") == manifest.get(
        "id"
    )
    assert {
        s.get("key"): s.get("value") for s in addon.findall("instance-settings/setting")
    } == SETTINGS
    assert addon.find("type-settings/dashboard") is not None
    sheets = set(dashboard.xpath(".//zone[@name]/@name"))
    assert sheets == {"by Borough"}, (
        "Extension sheetId 0 must bind the only dashboard worksheet"
    )
    size = dashboard.find("size")
    assert size.get("maxwidth") == "1366" and size.get("maxheight") == "768"
    worksheet = root.find('worksheets/worksheet[@name="by Borough"]')
    assert worksheet.find("table/panes/pane/mark").get("class") == "Line"
    assert "tmn:Created Date:qk" in worksheet.findtext("table/cols")
    ds = next(
        d
        for d in root.findall("datasources/datasource")
        if d.get("name") != "Parameters"
    )
    fields = {c.get("caption"): c for c in ds.findall("column")}
    assert (
        fields["# of Sightings"].find("calculation").get("formula")
        == "COUNT([Created Date])"
    )
    deps = worksheet.find("table/view/datasource-dependencies")
    change = deps.xpath(
        "column-instance[@column=$name]", name=fields["Change"].get("name")
    )
    assert len(change) == 1 and len(change[0].findall("table-calc")) == 3
    for tc in change[0].findall("table-calc")[1:]:
        assert tc.get("ordering-type") == "Field" and "tmn:Created Date:qk" in tc.find(
            "order"
        ).get("field")
    colors = ds.xpath('style/style-rule[@element="mark"]/encoding/map')
    assert {m.findtext("bucket").strip('"'): m.get("to") for m in colors} == {
        "DECREASE": "#31a1b3",
        "INCREASE": "#f28e2b",
        "NO CHANGE": "#b4b7b7",
    }
    data = oracle()
    proof_path = HERE / "evidence/build-provenance.json"
    if proof_path.exists() and (HERE / "evidence/cloud-verification.json").exists():
        proof = json.loads(proof_path.read_text())
        assert (
            proof["artifact_sha256"] == digest(path)
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
    verify_manifest(digest(path))
    checks = cloud(data)
    (HERE / "outputs/data-oracle.json").write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "artifact_sha256": digest(path),
                "acceptance_ids": ACCEPTANCE,
                "oracle": data,
                "cloud_checks": checks,
                "extension_contract": "Real identity, HTTPS sandbox endpoint, settings, bound sheet 0 and configuration menu verified",
                "browser_interaction_executed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS WW08 raw/native extension; Cloud=" + ("passed" if checks else "pending")
    )
    return digest(path)


if __name__ == "__main__":
    verify()
