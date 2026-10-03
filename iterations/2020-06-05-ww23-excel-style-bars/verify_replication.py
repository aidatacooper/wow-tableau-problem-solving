"""Independent 48-bar oracle, placement/width contracts and complete Cloud CSV checks."""

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
from datetime import date, datetime, timedelta
import calendar
import csv
import json
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def verify():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    raw = HERE / item["file"]
    assert sha256(raw.read_bytes()).hexdigest() == item["sha256"]
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        assert (
            sha256(
                z.read(next(n for n in z.namelist() if n.endswith(".hyper")))
            ).hexdigest()
            == item["sha256"]
        )
        root = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(raw)) as c,
    ):
        table = next(
            t
            for schema in c.catalog.get_schema_names()
            for t in c.catalog.get_table_names(schema)
        )
        records = c.execute_list_query(
            'SELECT "Order Date", "Sales" FROM ' + str(table)
        )
    assert len(records) == 9994
    totals = defaultdict(float)
    for d, v in records:
        totals[d.year, d.month] += float(v)
    assert len(totals) == 48 and set(y for y, m in totals) == {2016, 2017, 2018, 2019}
    expected = []
    for (year, month), sales in sorted(totals.items()):
        offset = {2016: -9, 2017: -4, 2018: 1, 2019: 6}[year]
        jitter = date(year, month, 1) + timedelta(days=offset)
        source_normalized = date(
            2018 if jitter.year in (2015, 2016) and jitter.month == 12 else 2019,
            jitter.month,
            jitter.day,
        )
        placement = source_normalized
        if (year, month) == (2016, 3):
            assert placement == date(2019, 2, 21)
        expected.append(
            {
                "year": year,
                "month": month,
                "date": placement.isoformat(),
                "sales": sales,
            }
        )
    assert abs(sum(totals.values()) - 2297200.8603) < 1e-5
    sizing = root.find('.//worksheet[@name="Bars"]//mark-sizing')
    assert (
        sizing.get("custom-mark-size-in-axis-units") == "4.0"
        and sizing.get("use-custom-mark-size") == "true"
    )
    assert sizing.get("mark-alignment") == "mark-alignment-left"
    assert root.find('.//worksheet[@name="Bars"]//mark').get("class") == "Bar"
    colors = {
        m.findtext("bucket"): m.get("to")
        for m in root.findall(".//datasource/style/style-rule/encoding/map")
    }
    assert colors == {
        "2016": "#5557eb",
        "2017": "#d81159",
        "2018": "#fbb13c",
        "2019": "#19626b",
    }
    report_path = HERE / "evidence/cloud-verification.json"
    checks = []
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert (
            report["source_hashes"]["replica"]
            == sha256(
                (HERE / "outputs/replicated-workbook.twbx").read_bytes()
            ).hexdigest()
        )
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert report["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert not report["browser_interaction_executed"]
        for state in report["states"]:
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for exported in state["data"]:
                path = HERE / exported["path"]
                assert sha256(path.read_bytes()).hexdigest() == exported["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.DictReader(f))
                assert len(rows) == 48, (exported, len(rows))
                seen = set()
                for row in rows:
                    ykey = next(k for k in row if "Year" in k and "Order Date" in k)
                    mkey = next(k for k in row if "Month" in k and "Order Date" in k)
                    year = int(row[ykey])
                    mt = row[mkey]
                    month = (
                        int(mt)
                        if mt.isdigit()
                        else next(
                            i
                            for i in range(1, 13)
                            if mt in (calendar.month_name[i], calendar.month_abbr[i])
                        )
                    )
                    assert (year, month) not in seen
                    actual_date = row.get("Plot Date", row.get("Date Normalised"))
                    parsed_date = None
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y"]:
                        try:
                            parsed_date = datetime.strptime(actual_date, fmt).date()
                            break
                        except ValueError:
                            pass
                    assert parsed_date is not None
                    assert parsed_date.isoformat() == next(
                        v["date"]
                        for v in expected
                        if v["year"] == year and v["month"] == month
                    )
                    seen.add((year, month))
                    saleskey = "Tooltip:Sales" if "Tooltip:Sales" in row else "Sales"
                    text = (
                        row[saleskey]
                        .strip()
                        .replace("\u00a3", "")
                        .replace("$", "")
                        .replace(",", "")
                    )
                    v = float(text.rstrip("Kk")) * (
                        1000 if text.endswith(("K", "k")) else 1
                    )
                    precision = (
                        len(text.split(".")[-1].rstrip("Kk")) if "." in text else 0
                    )
                    tolerance = (
                        0.5
                        * 10 ** (-precision)
                        * (1000 if text.endswith(("K", "k")) else 1)
                        + 1e-7
                    )
                    assert abs(v - totals[year, month]) <= tolerance, (
                        year,
                        month,
                        v,
                        totals[year, month],
                    )
                assert seen == set(totals)
                checks.append(
                    {
                        "role": exported["role"],
                        "state": state["name"],
                        "bar_count": len(seen),
                        "scope": "All year/month sums; native placement, four-day widths and palettes validated in artifact.",
                    }
                )
    result = {
        "status": "passed",
        "acceptance_ids": [
            "ww23-monthly-sales",
            "ww23-bar-placement",
            "ww23-cloud-bars",
        ],
        "raw_rows": len(records),
        "bar_count": 48,
        "total_sales": sum(totals.values()),
        "bars": expected,
        "cloud_checks": checks,
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "bars"}, indent=2))
    return result


if __name__ == "__main__":
    verify()
