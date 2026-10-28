"""Raw-data oracle + emitted-formula evaluation; runtime/UI gates stay pending."""
from collections import defaultdict
import hashlib
import importlib.metadata
import json
import math
import subprocess
from pathlib import Path
from zipfile import ZipFile

import cwtwb
from cwtwb.validator import load_workbook_root, validate_against_schema
from tableauhyperapi import Connection, HyperProcess, Telemetry
from formula_oracle import WorkbookSQL

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/replicated-workbook.twbx"
RAW = HERE / "inputs/TEMP_0vk99460mvko1c1383vmf0pl4zzq.hyper"
INITIAL = {f"2020-{m:02d}-01" for m in (10, 11, 12)} | {f"2021-{m:02d}-01" for m in range(1, 7)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sdk_revision():
    """Read actual source provenance from a checkout or a pip VCS installation."""
    sdk_root = Path(cwtwb.__file__).resolve().parents[2]
    if (sdk_root / ".git").exists():
        return subprocess.check_output(["git", "-C", str(sdk_root), "rev-parse", "HEAD"], text=True).strip()
    try:
        direct_url = importlib.metadata.distribution("cwtwb").read_text("direct_url.json")
        return json.loads(direct_url or "{}").get("vcs_info", {}).get("commit_id")
    except (importlib.metadata.PackageNotFoundError, json.JSONDecodeError):
        return None


def close(actual, expected):
    if expected is None:
        assert actual is None, (actual, expected)
    elif isinstance(expected, (float, int)):
        assert actual is not None and math.isclose(float(actual), expected, rel_tol=1e-10, abs_tol=1e-6), (actual, expected)
    else:
        assert str(actual) == str(expected), (actual, expected)


def oracle(rows, selected):
    """Python fsum of raw rows, independent of workbook formulas."""
    monthly, states = defaultdict(list), defaultdict(list)
    for day, state, sales in rows:
        month = str(day)[:7] + "-01"
        monthly[month].append(sales)
        if month in selected:
            states[state].append(sales)
    monthly = {m: math.fsum(v) for m, v in monthly.items()}
    states = {s: math.fsum(v) for s, v in states.items()}
    present = sorted(set(monthly) & selected)
    total = math.fsum(monthly.values())
    selected_total = math.fsum(monthly[m] for m in present) if present else None
    state_rows = []
    for state in sorted(states, key=lambda s: (-states[s], s)):
        rank = 1 + sum(v > states[state] for v in states.values())
        state_rows.append(dict(state=state, sales=states[state], rank=rank, share=states[state] / selected_total,
                               color_group=str(rank if rank <= 3 else 10)))
    peak = max((monthly[m] for m in present), default=None)
    return dict(overall_total=total, overall_count=len(monthly), overall_average=total / len(monthly),
                selected_total=selected_total, selected_count=len(present),
                selected_average=selected_total / len(present) if present else None,
                first_month=present[0] if present else None, last_month=present[-1] if present else None,
                first_sales=monthly[present[0]] if present else None, last_sales=monthly[present[-1]] if present else None,
                endpoint_change=monthly[present[-1]] / monthly[present[0]] - 1 if present else None,
                peak_sales=peak, peak_months=[m for m in present if monthly[m] == peak],
                months=[dict(month=m, sales=monthly[m], selected_sales=monthly[m] if m in selected else None) for m in sorted(monthly)],
                states=state_rows, top_three=[s for s in state_rows if s["rank"] <= 3])


def contracts(root):
    # acceptance: native-set-action, default-state, reference-band, six-views
    ds = root.find("./datasources/datasource")
    names = {c.get("caption", c.get("name").strip("[]")): c.get("name").strip("[]") for c in ds.findall("column")}
    def contains(ref, name):
        return f":{names[name]}:" in (ref or "") or ref == "[" + names[name] + "]" or (ref or "").endswith(".[" + names[name] + "]")
    groups = ds.findall("group")
    assert len(groups) == 1 and groups[0].get("caption") == "Selected Months"
    members = groups[0].findall(".//groupfilter[@function='member']")
    assert len(members) == 9 and {m.get("member").strip("#")[:10] for m in members} == INITIAL
    assert all(m.get("member").startswith("#") and m.get("level") == "[" + names["Month"] + "]" for m in members)
    actions = root.findall("./actions/*")
    assert len(actions) == 1 and actions[0].tag == "edit-group-action", "No filter/parameter imitation"
    action = actions[0]
    assert action.find("activation").get("type") == "on-select"
    assert action.find("source").get("worksheet") == "Trend"
    assert action.find("source").get("dashboard") == "Reference Date Range"
    assert action.find("single-select").get("value") == "false"
    params = {p.get("name"): p.get("value") for p in action.findall("params/param")}
    assert params["selection-clear-set-option"] == "do-nothing"
    assert params["add-or-remove-marks"] == "assign"
    assert params["target-group"] == "[" + ds.get("name") + "]." + groups[0].get("name")
    assert root.find("./datasources/datasource[@name='Parameters']") is None
    sheets = {s.get("name"): s for s in root.findall("./worksheets/worksheet")}
    assert set(sheets) == {"Overall Summary", "Selected Summary", "Trend", "State Donut", "Top States", "State Map"}
    db = root.find("./dashboards/dashboard")
    assert db.find("size").get("maxwidth") == "1000" and db.find("size").get("maxheight") == "800"
    assert set(sheets) <= {z.get("name") for z in db.findall(".//zone")}
    for sheet in ("Overall Summary", "Selected Summary", "Trend"):
        assert not sheets[sheet].findall("table/view/filter")
    for sheet in ("State Donut", "Top States", "State Map"):
        chosen = [f for f in sheets[sheet].findall("table/view/filter") if contains(f.get("column"), "In Selection")]
        assert len(chosen) == 1 and chosen[0].find("groupfilter").get("member") == "true"
        assert chosen[0].get("context") is None
    for sheet, fields in [("Overall Summary", ["Overall Sales", "Overall Monthly Average"]),
                          ("Selected Summary", ["Selected Total", "Selected Monthly Average", "Selected Count", "Endpoint Change", "First Month", "Last Month"])]:
        encoded = [n.get("column") for n in sheets[sheet].findall(".//encodings/text")]
        assert all(any(contains(ref, name) for ref in encoded) for name in fields)
    trend = sheets["Trend"]
    assert contains(trend.findtext("table/cols"), "Month")
    assert all(contains(trend.findtext("table/rows"), n) for n in ("Sales", "Selected Sales"))
    assert len(trend.findall(".//pane/mark[@class='Line']")) == 2
    lines = trend.findall(".//reference-line")
    assert len(lines) == 2 and lines[0].get("paired-id") == lines[1].get("id") and lines[1].get("paired-id") == lines[0].get("id")
    for line, name, aggregation in zip(lines, ["First Month", "Last Month"], ["min", "max"]):
        assert contains(line.get("value-column"), name) and contains(line.get("axis-column"), "Month")
        assert line.get("formula") == aggregation and line.get("value") is None
        # Endpoints must be bound together on the pane carrying the band; an XML
        # reference alone rendered no band in actual VizQL.
        assert any(contains(n.get("column"), name) for n in line.getparent().findall("encodings/lod"))
    assert trend.find(".//style-rule[@element='refband']/format[@attr='fill-color']") is not None
    top = sheets["Top States"]
    rank_filter = next(f for f in top.findall("table/view/filter") if contains(f.get("column"), "State Rank"))
    assert rank_filter.findtext("min") == "1" and rank_filter.findtext("max") == "3"
    for field in ["State Rank", "State Share"]:
        instance = next(c for c in top.findall(".//column-instance") if contains(c.get("name"), field))
        calc = instance.find("table-calc")
        assert calc.get("ordering-type") == "Field"
        assert len(calc.findall("order")) == 1 and contains(calc.find("order").get("field"), "State")
    peak = next(c for c in trend.findall(".//column-instance") if contains(c.get("name"), "Selected Peak"))
    assert peak.find("table-calc").get("ordering-type") == "Field"
    assert contains(peak.find("table-calc/order").get("field"), "Month")
    assert contains(top.findtext("table/rows"), "State")
    donut = sheets["State Donut"]
    pie = next(p for p in donut.findall(".//pane") if p.find("mark").get("class") == "Pie")
    for tag, name in [("wedge-size", "Sales"), ("color", "Rank Color"), ("lod", "State")]:
        assert contains(pie.find("encodings/" + tag).get("column"), name)
    assert donut.find(".//mark[@class='Circle']") is not None
    assert sheets["State Map"].find(".//mark[@class='Multipolygon']") is not None
    assert contains(sheets["State Map"].find(".//encodings/color").get("column"), "Sales")
    return ["native-set-action", "default-state", "reference-band", "six-views"]


def numerical_checks(root, rows, connection, scenarios=None):
    # acceptance: raw-data-numerics, selection-state-numerics, state-ranking
    months = {str(day)[:7] + "-01" for day, _, _ in rows}
    if scenarios is None:
        scenarios = {"default": INITIAL, "alternate-q1-2019": {f"2019-{m:02d}-01" for m in (1, 2, 3)},
                     "single-june-2021": {"2021-06-01"}, "noncontiguous": {"2020-10-01", "2021-06-01"},
                     "all-months": months, "empty-set-robustness": set()}
    mapping = {"Overall Sales": "overall_total", "Overall Months": "overall_count", "Overall Monthly Average": "overall_average",
               "Selected Total": "selected_total", "Selected Count": "selected_count", "Selected Monthly Average": "selected_average",
               "First Month": "first_month", "Last Month": "last_month", "First Sales": "first_sales", "Last Sales": "last_sales", "Endpoint Change": "endpoint_change"}
    results = {}
    for scenario, selected in scenarios.items():
        expected, sql = oracle(rows, selected), WorkbookSQL(root, selected)
        actual = connection.execute_list_query('SELECT ' + ','.join(sql.field(n) for n in mapping) + ' FROM "Extract"."Extract" r LIMIT 1')[0]
        for name, value in zip(mapping, actual):
            close(value, expected[mapping[name]])
        query = 'SELECT ' + sql.field("Month") + ',SUM(r."Sales"),SUM(' + sql.field("Selected Sales") + '),' + sql.field("Selected Peak") + ' FROM "Extract"."Extract" r GROUP BY 1 ORDER BY 1'
        actual_months = connection.execute_list_query(query)
        assert len(actual_months) == len(expected["months"])
        for actual_row, expected_row in zip(actual_months, expected["months"]):
            for value, key in zip(actual_row[:3], ["month", "sales", "selected_sales"]):
                close(value, expected_row[key])
            close(actual_row[3], expected["peak_sales"] if expected_row["month"] in expected["peak_months"] else None)
        query = 'SELECT r."State",SUM(r."Sales"),' + ','.join(sql.field(n) for n in ["State Rank", "State Share", "Rank Color"]) + ' FROM "Extract"."Extract" r WHERE ' + sql.field("In Selection") + ' GROUP BY r."State" ORDER BY 2 DESC,1'
        actual_states = connection.execute_list_query(query)
        assert len(actual_states) == len(expected["states"])
        for actual_row, expected_row in zip(actual_states, expected["states"]):
            for value, key in zip(actual_row, ["state", "sales", "rank", "share", "color_group"]):
                close(value, expected_row[key])
        if actual_states:
            close(math.fsum(row[3] for row in actual_states), 1.0)
            close(math.fsum(row[1] for row in actual_states), expected["selected_total"])
        assert [row[0] for row in actual_states if 1 <= row[2] <= 3] == [row["state"] for row in expected["top_three"]]
        results[scenario] = {"selected_months": sorted(selected), "passed": True, **expected}
    return results


def verify():
    assert cwtwb.__version__ == "0.29.0a2", "Candidate SDK is required; a1 baseline remains archived"
    sdk_commit = sdk_revision()
    root = load_workbook_root(OUTPUT)
    schema = validate_against_schema(root)
    assert schema.schema_available and not schema.errors, schema.errors
    with ZipFile(OUTPUT) as archive:
        extracts = [n for n in archive.namelist() if n.endswith(".hyper")]
        assert len(extracts) == 1 and hashlib.sha256(archive.read(extracts[0])).hexdigest() == digest(RAW)
    checks = contracts(root)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={"log_config": ""}) as process:
        with Connection(process.endpoint, RAW) as connection:
            rows = connection.execute_list_query('SELECT "Order Date","State","Sales" FROM "Extract"."Extract"')
            assert len(rows) == 9994
            results = numerical_checks(root, rows, connection)
    checks += ["raw-data-numerics", "selection-state-numerics", "state-ranking"]
    evidence = {"status": "local-checks-pass-runtime-pending", "workbook_sha256": digest(OUTPUT), "input_sha256": digest(RAW),
                "sdk_version": cwtwb.__version__, "sdk_source": str(Path(cwtwb.__file__).parent.parent),
                "sdk_commit": sdk_commit, "raw_rows": len(rows),
                "xsd_strict_errors": [], "xsd_compatibility_warnings": schema.compatibility_warnings,
                "passed_acceptance": checks, "scenario_results": results,
                "limits": "Emitted-formula SQL evaluation is not Tableau VizQL. Desktop load, clicks, clearing, rendering, geocoding and corpus regression remain pending parent gates."}
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/local-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(checks)} local contracts; {len(results)} numerical states; {len(rows)} raw rows; Desktop/Cloud pending")


if __name__ == "__main__":
    verify()
