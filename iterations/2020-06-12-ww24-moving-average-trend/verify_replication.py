"""Recompute complete county history before latest-date filtering; verify paired REST data."""

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
from datetime import date, datetime
import csv, json, math
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def parse_date(text):
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise AssertionError(("Unrecognized date", text))


def numeric(text, expected):
    if not text.strip():
        assert expected is None
        return
    assert expected is not None
    clean = text.strip().replace(",", "")
    places = len(clean.split(".")[1]) if "." in clean else 0
    assert abs(float(clean) - expected) <= 0.5 * 10 ** (-places) + 1e-7, (
        text,
        expected,
    )


def calculate_history(history):
    history.sort()
    previous = None
    days = None
    for i, (d, v) in enumerate(history):
        moving = []
        for width in (3, 14):
            vals = [
                h[1]["New Cases"]
                for h in history[max(0, i - width + 1) : i + 1]
                if h[1]["New Cases"] is not None
            ]
            moving.append(sum(vals) / len(vals) if vals else None)
        short, long = moving
        inc = int(short is not None and long is not None and short > long)
        decrease = short is not None and long is not None and short <= long
        days = (
            1
            if i == 0 or inc != previous
            else days + 1
            if days is not None and (inc or decrease)
            else None
        )
        v.update(
            {
                "3 Day Moving Avg": short,
                "14 Day Moving Avg": long,
                "Increase | Decrease": "INCREASE" if inc else "DECREASE",
                "Days in Trend": days,
            }
        )
        previous = inc


def oracle():
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
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(raw)) as c,
    ):
        table = next(
            t
            for schema in c.catalog.get_schema_names()
            for t in c.catalog.get_table_names(schema)
        )
        rows = c.execute_list_query(
            'SELECT "PROVINCE_STATE_NAME","COUNTY_NAME","REPORT_DATE","PEOPLE_POSITIVE_NEW_CASES_COUNT","PEOPLE_POSITIVE_CASES_COUNT" FROM '
            + str(table)
        )
    assert len(rows) == 422143
    daily = {}
    excluded = 0
    for state, county, d, new, total in rows:
        if county is None:
            excluded += 1
            continue
        key = (state, county, date(d.year, d.month, d.day).isoformat())
        assert key not in daily, ("Duplicate rawcounty/day", key)
        daily[key] = {"New Cases": new, "Reported Cases": total}
    maxdate = max(k[2] for k in daily)
    assert maxdate == "2020-06-07"
    histories = defaultdict(list)
    for (state, county, d), v in daily.items():
        histories[state, county].append((d, v))
    bar_daily = {}
    for (state, county), history in histories.items():
        calculate_history(history)
        bar_history = [
            (d, {"New Cases": v["New Cases"], "Reported Cases": v["Reported Cases"]})
            for d, v in history
            if d >= "2020-03-08"
        ]
        calculate_history(bar_history)
        for d, v in bar_history:
            bar_daily[state, county, d] = v
    assert bar_daily["Tennessee", "Davidson", "2020-03-08"]["14 Day Moving Avg"] == 1
    davidson = daily["Tennessee", "Davidson", maxdate]
    assert (
        davidson["New Cases"] == 124
        and davidson["Reported Cases"] == 6156
        and davidson["Days in Trend"] == 1
    )
    assert math.isclose(
        davidson["3 Day Moving Avg"], 108.33333333333333
    ) and math.isclose(davidson["14 Day Moving Avg"], 101.78571428571429)
    return (
        daily,
        bar_daily,
        {
            "raw_rows": len(rows),
            "excluded_null_county_rows": excluded,
            "county_count": len(histories),
            "max_date": maxdate,
            "default_latest": davidson,
        },
    )


def contracts():
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        r = etree.fromstring(
            z.read(next(n for n in z.namelist() if n.endswith(".twb")))
        )
    columns = r.findall("datasources/datasource/column")
    names = {
        c.get("name"): c.get("caption") or c.get("name").strip("[]") for c in columns
    }
    formulas = {
        c.get("caption"): c.find("calculation").get("formula")
        for c in columns
        if c.find("calculation") is not None and c.get("caption")
    }
    for k in formulas:
        for internal, caption in names.items():
            formulas[k] = formulas[k].replace(internal, "[" + caption + "]")
    assert (
        formulas["3 Day Moving Avg"] == "WINDOW_AVG(SUM([New Cases]),-2,0)"
        and formulas["14 Day Moving Avg"] == "WINDOW_AVG(SUM([New Cases]),-13,0)"
    )
    assert (
        "PREVIOUS_VALUE" in formulas["Days in Trend"]
        and "LOOKUP(MIN([Report Date]),0)" in formulas["Show Data for Latest Date"]
    )
    assert "NOT ISNULL([COUNTY_NAME])" in formulas["Max Date"]
    assert formulas["County Sort"] == "-{FIXED [State],[County]:SUM([Reported Cases])}"
    assert formulas["Line Direction"] == "[Increase | Decrease]"
    moving_parameter = r.find(
        'datasources/datasource[@name="Parameters"]/column[@caption="Moving Avg Selector"]'
    )
    assert moving_parameter.get("alias") == "14 Day Moving Avg"
    direction_column = next(
        c.get("name").strip("[]")
        for c in columns
        if c.get("caption") == "Line Direction"
    )
    line = r.find('.//worksheet[@name="Bar&Line"]')
    assert any(
        direction_column in e.get("column", "")
        for e in line.findall(".//encodings/color")
    )
    palette = next(
        e
        for e in r.findall("datasources/datasource/style/style-rule/encoding")
        if direction_column in e.get("field", "")
    )
    assert {m.findtext("bucket"): m.get("to") for m in palette.findall("map")} == {
        '"DECREASE"': "#76b7b2",
        '"INCREASE"': "#e15759",
    }
    table = r.find('.//worksheet[@name="Table"]')
    assert (
        table.find(
            'table/style/style-rule[@element="header"]/format[@attr="height"]'
        ).get("value")
        == "56"
    )

    latest_internal = next(
        c.get("name").strip("[]")
        for c in columns
        if c.get("caption") == "Show Data for Latest Date"
    )
    for name in ["BAN", "Map", "Table"]:
        w = r.find('.//worksheet[@name="' + name + '"]')
        f = next(
            f
            for f in w.findall("table/view/filter")
            if latest_internal in f.get("column", "")
        )
        assert (
            "[usr:" in f.get("column") and f.find("groupfilter").get("member") == "true"
        )
        contexts = w.findall('.//table-calc[@ordering-type="Field"]')
        assert contexts
        assert all(
            "[none:" in c.get("ordering-field", "")
            and c.get("ordering-field", "").endswith(":ok]")
            for c in contexts
        )

    w = r.find('.//worksheet[@name="Bar&Line"]')
    contexts = w.findall('.//table-calc[@ordering-type="Field"]')
    assert contexts and all(
        "[none:" in c.get("ordering-field", "")
        and c.get("ordering-field", "").endswith(":qk]")
        for c in contexts
    )
    q = w.find('table/view/filter[@class="quantitative"]')
    assert q.findtext("min") == "#2020-03-08#"
    assert not any(
        latest_internal in f.get("column", "") for f in w.findall("table/view/filter")
    )
    assert r.find('.//worksheet[@name="Map"]//geometry') is not None
    county = next(c for c in columns if c.get("caption") == "County")
    state = next(c for c in columns if c.get("caption") == "State")
    assert "County" in county.get("semantic-role", "") and "State" in state.get(
        "semantic-role", ""
    )
    assert (
        r.find('.//window[@class="dashboard"]//viewpoint[@name="Table"]/zoom').get(
            "type"
        )
        == "fit-width"
    )
    assert (
        r.find(
            './/worksheet[@name="Table"]/table/style/style-rule[@element="cell"]/format[@attr="text-format"][@value="n#,##0;-#,##0"][@field]'
        )
        is None
    )
    assert (
        r.find(
            './/worksheet[@name="Table"]/table/style/style-rule[@element="cell"]/format[@attr="text-format"][@value="n#,##0;-#,##0"]'
        ).get("field")
        is None
    )
    assert len(r.findall('.//dashboard/zones//zone[@type-v2="paramctrl"]')) == 2
    return r


def verify_cloud(daily, bar_daily, summary):
    path = HERE / "evidence/cloud-verification.json"
    checks = []
    if not path.exists():
        return checks
    report = json.loads(path.read_text(encoding="utf-8"))
    assert (
        report["source_hashes"]["replica"]
        == sha256((HERE / "outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    )
    provenance = json.loads(
        (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
    )
    assert report["source_hashes"]["author"] == provenance["comparison_sha256"]
    assert not report["browser_interaction_executed"]
    for state in report["states"]:
        parameter = state.get("parameters", {}).get(
            "State - County Parameter", "Tennessee - Davidson"
        )
        region, selected = parameter.split(" - ", 1)
        width = int(state.get("parameters", {}).get("Moving Avg Selector", 14))
        for image in state["views"].values():
            assert (
                sha256((HERE / image["path"]).read_bytes()).hexdigest()
                == image["sha256"]
            )
        for export in state["data"]:
            path = HERE / export["path"]
            assert sha256(path.read_bytes()).hexdigest() == export["sha256"]
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            view = export["view"]
            seen = set()
            checked = 0
            for row in rows:
                county = row.get("County", row.get("COUNTY_NAME", selected))
                region_row = row.get(
                    "State",
                    row.get(
                        "Province State Name", row.get("PROVINCE_STATE_NAME", region)
                    ),
                )
                datekey = next(
                    (k for k in row if k in ["Report Date", "REPORT_DATE"]), None
                )
                day = parse_date(row[datekey]) if datekey else summary["max_date"]
                expected = (bar_daily if view == "Bar&Line" else daily)[
                    region_row, county, day
                ]
                if view == "BAN":
                    assert county == selected and day == summary["max_date"]
                if "Measure Names" in row:
                    metric = " ".join(row["Measure Names"].split(" along ")[0].split())
                    metric = (
                        metric.replace("Sum of ", "").replace("SUM(", "").rstrip(")")
                    )
                    assert metric in [
                        "Reported Cases",
                        "New Cases",
                        "3 Day Moving Avg",
                        "14 Day Moving Avg",
                        "Moving Avg To Display",
                    ], metric
                    numeric(
                        row["Measure Values"],
                        expected[f"{width} Day Moving Avg"]
                        if metric == "Moving Avg To Display"
                        else expected[metric],
                    )
                    seen.add((county, day, metric))
                    checked += 1
                for metric in [
                    "Reported Cases",
                    "New Cases",
                    "3 Day Moving Avg",
                    "14 Day Moving Avg",
                    "Days in Trend",
                    "Increase | Decrease",
                    "Moving Avg To Display",
                ]:
                    col = next(
                        (
                            k
                            for k in row
                            if k == metric or k.startswith(metric + " along ")
                        ),
                        None,
                    )
                    if col:
                        value = (
                            expected[f"{width} Day Moving Avg"]
                            if metric == "Moving Avg To Display"
                            else expected[metric]
                        )
                        if metric == "Increase | Decrease":
                            assert row[col] == value
                        else:
                            numeric(row[col], value)
                        seen.add((county, day, metric))
                        checked += 1
            if view == "Table":
                counties = {
                    c for s, c, d in daily if s == region and d == summary["max_date"]
                }
                assert {
                    (c, summary["max_date"], m)
                    for c in counties
                    for m in [
                        "Reported Cases",
                        "New Cases",
                        "3 Day Moving Avg",
                        "14 Day Moving Avg",
                    ]
                } <= seen, (export, seen)
            elif view == "Bar&Line":
                days = {
                    d
                    for s, c, d in daily
                    if s == region and c == selected and d >= "2020-03-08"
                }
                assert {(selected, d, "New Cases") for d in days} <= seen
                assert {(selected, d, "Moving Avg To Display") for d in days} <= seen
            elif view == "BAN":
                assert (selected, summary["max_date"], "Days in Trend") in seen and (
                    selected,
                    summary["max_date"],
                    "Increase | Decrease",
                ) in seen
            assert checked > 0
            checks.append(
                {
                    "role": export["role"],
                    "state": state["name"],
                    "view": view,
                    "rows": len(rows),
                    "checked_values": checked,
                    "scope": "Latest table/BAN recomputed from complete raw county histories. Bar/line independently recomputed after its physical March 8 date filter, including complete selected-county daily values.",
                }
            )
    return checks


def verify():
    daily, bar_daily, summary = oracle()
    contracts()
    checks = verify_cloud(daily, bar_daily, summary)
    result = {
        "status": "passed",
        "acceptance_ids": [
            "ww24-history-oracle",
            "ww24-latest-trend",
            "ww24-geographic-contract",
            "ww24-cloud-states",
        ],
        **summary,
        "cloud_checks": checks,
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    verify()
