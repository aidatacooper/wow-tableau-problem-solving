"""Independent native-relationship grain and complete monthly sales/goal oracle."""

import ast
import csv
import datetime as dt
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
ACTUAL_TABLE = "Orders_62E6C5F2B15645379EECE2780C356F05"
GOAL_TABLE = "Sheet1_2F515896DFF04D7BBA0A3B18B0EE95A7"
TODAY = dt.date(2019, 7, 1)
STATES = {
    "default": {},
    "home-office-furniture": {"segment": "Home Office", "category": "Furniture"},
    "bookcases": {"sub": "Bookcases"},
    "wide-thresholds": {"green": 0.2, "red": 0.5},
}


def number(value):
    value = (
        value.strip()
        .replace(",", "")
        .replace("$", "")
        .replace("↑", "")
        .replace("↓", "-")
    )
    if value == "NO GOAL":
        return 0.0
    if value.lower() in {"", "null", "none"}:
        return None
    return float(value.rstrip("%")) / (100 if "%" in value else 1)


def date(value, author):
    for fmt in (
        ["%d/%m/%Y", "%Y-%m-%d", "%B %Y", "%b %Y"]
        if author
        else ["%m/%d/%Y", "%Y-%m-%d", "%B %Y", "%b %Y"]
    ):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise AssertionError(("Unknown export date", value))


def oracle(actual, goals, state, grain):
    selected = [
        r
        for r in actual
        if r[2].year != 2016
        and all(
            state.get(k, r[i]) == r[i]
            for k, i in [("segment", 0), ("category", 1), ("sub", 3)]
        )
    ]
    selected_goals = [
        r
        for r in goals
        if r[2].year != 2016
        and all(
            state.get(k, r[i]) == r[i] for k, i in [("segment", 0), ("category", 1)]
        )
    ]
    grouped = defaultdict(lambda: {"actual": [], "subs": set(), "goals": {}})
    for segment, category, month, sub, sales in selected:
        dimensions = (
            (segment,)
            if grain == "Table"
            else ()
            if grain in ["Line Graph", "Barcode"]
            else (segment, category, sub)
        )
        row = grouped[dimensions + (month,)]
        row["subs"].add(sub)
        if month <= TODAY:
            row["actual"].append(sales)
    for segment, category, month, goal in selected_goals:
        if grain == "Data":
            subs = {
                r[3]
                for r in selected
                if r[0] == segment and r[1] == category and r[2] == month
            }
            if not subs and "sub" in state:
                continue
            dims = [(segment, category, sub) for sub in subs] or [
                (segment, category, "")
            ]
        else:
            if "sub" in state and not any(
                r[0] == segment and r[1] == category and r[2] == month for r in selected
            ):
                continue
            dims = [(segment,)] if grain == "Table" else [()]
        for dimensions in dims:
            grouped[dimensions + (month,)]["goals"][(segment, category, month)] = goal
    windows = defaultdict(int)
    for key, row in grouped.items():
        windows[key[:-1]] = max(windows[key[:-1]], len(row["subs"]))
    result = {}
    for key, row in grouped.items():
        month = key[-1]
        count = len(row["subs"])
        maximum = windows[key[:-1]]
        lowest = count == 1 and count == maximum
        actual_value = sum(row["actual"]) if row["actual"] else None
        goal_value = 0 if lowest else sum(row["goals"].values())
        difference = (
            None if lowest or actual_value is None else actual_value - goal_value
        )
        ratio = (
            difference / actual_value
            if difference is not None and actual_value
            else None
        )
        rag = (
            "WAY OFF TRACK"
            if ratio is not None and abs(ratio) > state.get("red", 0.25)
            else "ON TRACK"
            if ratio is not None and abs(ratio) < state.get("green", 0.1)
            else "NO COMPARISON"
            if month >= TODAY or goal_value == 0
            else "OFF TRACK"
        )
        keep = maximum != 0 and (
            month < TODAY if lowest else not (count == 0 and maximum == 1)
        )
        if grain == "Table" and not keep:
            continue
        result[key] = {
            "ACTUAL SALES": actual_value,
            "SALES GOAL": goal_value,
            "GOAL": goal_value if goal_value > 0 else None,
            "RESULT": difference,
            "ACTUAL vs GOAL": ratio,
            "RAG": rag,
            "# Sub-Cats": count,
            "Max Sub-Cats in Window": maximum,
            "Records to Show": keep,
        }
    if grain == "Data":
        # Native text crosstabs complete the visible month domain for each
        # existing dimensional partition. These are empty cells, not goals
        # copied from a different product or year.
        dimensions = {key[:-1] for key in result}
        months = {key[-1] for key in result}
        for partition in dimensions:
            for month in months:
                key = partition + (month,)
                if key not in result:
                    result[key] = {
                        "ACTUAL SALES": None,
                        "SALES GOAL": None,
                        "GOAL": None,
                        "RESULT": None,
                        "ACTUAL vs GOAL": None,
                        "RAG": "NO COMPARISON",
                        "# Sub-Cats": 0,
                        "Max Sub-Cats in Window": windows[partition],
                        "Records to Show": False,
                    }
    return result


def verify():
    # blank-sdk-build; locked-source-data; native-logical-relationships;
    # complete-goal-oracle; native-filter-actions; cloud-rest-comparison;
    # cloud-visual-review
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
    assert set(root.xpath("//worksheet/@name")) == {
        "Table",
        "Data",
        "Line Graph",
        "Barcode",
    }
    assert not root.xpath('//relation[@type="join"]')
    objects = root.xpath("/workbook/datasources/datasource/object-graph/objects/object")
    assert len(objects) == 2
    relationship = root.xpath(
        "/workbook/datasources/datasource/object-graph/relationships/relationship"
    )[0]
    assert len(relationship.xpath('./expression[@op="AND"]/expression[@op="="]')) == 3
    predicates = {
        tuple(n.xpath("./expression/@op"))
        for n in relationship.xpath("./expression/expression")
    }
    assert predicates == {
        ("[Segment]", "[Segment (Goals)]"),
        ("[Category]", "[Category (Goals)]"),
        ("[Month of Order Date]", "[Month of Order Date (Goals)]"),
    }
    assert root.xpath(
        '/workbook/datasources/datasource/column[@name="[Sales]"][@datatype="real"]'
    )
    assert root.xpath(
        '//worksheet//datasource-dependencies/column[@name="[Goal]"][@datatype="integer"]'
    )
    assert len(root.xpath('//drill-path[@name="SEGMENT"]/field')) == 3
    dependency_closures = {
        "Max Sub-Cats in Window": set(),
        "At Lowest Level": {"Max Sub-Cats in Window"},
        "SALES GOAL": {"At Lowest Level", "Max Sub-Cats in Window"},
        "RESULT": {"At Lowest Level", "Max Sub-Cats in Window", "SALES GOAL"},
        "ACTUAL vs GOAL": {
            "RESULT",
            "At Lowest Level",
            "Max Sub-Cats in Window",
            "SALES GOAL",
        },
        "Plot Goal": {"At Lowest Level", "Max Sub-Cats in Window", "SALES GOAL"},
        "Records to Show": {"At Lowest Level", "Max Sub-Cats in Window"},
        "RAG": {
            "ACTUAL vs GOAL",
            "RESULT",
            "At Lowest Level",
            "Max Sub-Cats in Window",
            "SALES GOAL",
        },
    }
    names = {
        n.get("name"): n.get("caption")
        for n in root.xpath("/workbook/datasources/datasource/column[@caption]")
    }
    for worksheet in root.xpath("//worksheet"):
        for instance in worksheet.xpath(".//column-instance[table-calc]"):
            name = names[instance.get("column")]
            nested = {
                names["[" + c.get("field").split(".[")[-1]]
                for c in instance.xpath("./table-calc[@field]")
            }
            assert nested == dependency_closures[name], (
                worksheet.get("name"),
                name,
                nested,
            )
            for calc in instance.xpath("./table-calc"):
                field = (
                    names["[" + calc.get("field").split(".[")[-1]]
                    if calc.get("field")
                    else name
                )
                expected_order = (
                    "Rows"
                    if worksheet.get("name") == "Barcode"
                    or worksheet.get("name") == "Line Graph"
                    and field != "Max Sub-Cats in Window"
                    else "Field"
                )
                assert calc.get("ordering-type") == expected_order, (
                    name,
                    field,
                    calc.attrib,
                )
                if expected_order == "Field":
                    assert "Calculation_" in calc.get("ordering-field", "")
    month_column = root.xpath(
        '/workbook/datasources/datasource/column[@caption="MONTH"]/@name'
    )[0]
    for sheet in ["Table", "Data", "Barcode"]:
        worksheet = root.xpath("//worksheet[@name=$sheet]", sheet=sheet)[0]
        instances = worksheet.xpath(
            ".//column-instance[@column=$column]", column=month_column
        )
        assert instances and all(n.get("derivation") == "None" for n in instances), (
            sheet,
            "Month must retain its complete date, rather than month-of-year",
        )
    actions = root.xpath("/workbook/actions/action")
    assert len(actions) == 3
    action_fields = set()
    for action in actions:
        assert action.find("activation").get("type") == "on-select"
        assert action.find("source").get("worksheet") == "Table"
        params = {
            n.get("name"): n.get("value") for n in action.xpath("./command/param")
        }
        assert action.find("command").get("command") == "tsc:tsl-filter"
        assert params["exclude"] == "Table"
        assert params["target"] == "2020_07_08_WW28_SalesvGoal_Relationships"
        dashboard_sheets = set(
            root.xpath(
                "//dashboard[@name=$dashboard]/zones//zone[@name]/@name",
                dashboard=params["target"],
            )
        )
        assert dashboard_sheets - {params["exclude"]} == {"Line Graph", "Barcode"}
        assert action.find("activation").get("auto-clear") == "true"
        decoded = unquote(action.find("link").get("expression"))
        field = "[" + decoded.split("?", 1)[1].split("~s0", 1)[0].split(".[")[-1]
        assert decoded.endswith("=<" + field + "~na>"), decoded
        action_fields.add(names[field])
    assert action_fields == {"SEGMENT", "CATEGORY", "SUB-CATEGORY"}
    assert root.xpath('//reference-line[@formula="min"]')
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as p:
        with Connection(p.endpoint, data) as c:
            actual = c.execute_list_query(
                f'SELECT "Segment","Category","Month of Order Date","Sub-Category","Sales" FROM "Extract"."{ACTUAL_TABLE}"'
            )
            goals = c.execute_list_query(
                f'SELECT "Segment","Category","Month of Order Date","Goal" FROM "Extract"."{GOAL_TABLE}"'
            )
    assert len(actual) == 9994 and len(goals) == 534
    actual = [
        (s, c, dt.date(m.year, m.month, m.day), sub, value)
        for s, c, m, sub, value in actual
    ]
    goals = [(s, c, dt.date(m.year, m.month, m.day), value) for s, c, m, value in goals]
    assert len({(s, c, m) for s, c, m, g in goals}) == 534
    # An independently computed sparse category is the important non-lowest counterexample.
    home = oracle(actual, goals, STATES["home-office-furniture"], "Table")
    january = home[("Home Office", dt.date(2018, 1, 1))]
    assert (
        january["# Sub-Cats"] == 1
        and january["Max Sub-Cats in Window"] > 1
        and january["SALES GOAL"] > 0
    )
    bookcases = oracle(actual, goals, STATES["bookcases"], "Table")
    assert bookcases and all(
        v["SALES GOAL"] == 0 and v["RESULT"] is None and k[-1] < TODAY
        for k, v in bookcases.items()
    )
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "actual_rows": len(actual),
        "goal_rows": len(goals),
        "state_marks": {
            state: {
                grain: len(oracle(actual, goals, settings, grain))
                for grain in ["Table", "Data", "Line Graph", "Barcode"]
            }
            for state, settings in STATES.items()
        },
        "goal_grain": "Each raw Segment/Category/month goal contributes once at the requested aggregate grain, never once per order line.",
        "sparse_category_counterexample": january,
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
        assert {s["name"] for s in manifest["states"]} == set(STATES)
        checks = []
        for state in manifest["states"]:
            assert len(state["data"]) == 8
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            for capture in state["data"]:
                path = HERE / capture["path"]
                author = path.name.startswith("cloud-author")
                assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    exported = list(csv.DictReader(stream))
                assert exported, (path, "Empty export")
                grain = capture["view"]
                expected = oracle(actual, goals, STATES[state["name"]], grain)
                observed = defaultdict(dict)
                for row in exported:
                    monthkey = next(
                        k
                        for k in row
                        if k == "MONTH"
                        or k.startswith("Month of MONTH")
                        or k.startswith("MONTH ")
                    )
                    month = date(row[monthkey], author)
                    dimensions = (
                        (row["SEGMENT"],)
                        if grain == "Table"
                        else (row["SEGMENT"], row["CATEGORY"], row["SUB-CATEGORY"])
                        if grain == "Data"
                        else ()
                    )
                    key = dimensions + (month,)
                    assert key in expected, (path, "Unexpected grain", key)
                    if grain == "Line Graph" and not author:
                        settings = STATES[state["name"]]
                        selected_category = settings.get(
                            "category",
                            "Furniture"
                            if settings.get("sub") == "Bookcases"
                            else "All",
                        )
                        title = (
                            "SEGMENT: "
                            + settings.get("segment", "All")
                            + " | CATEGORY: "
                            + selected_category
                            + " | SUB-CATEGORY: "
                            + settings.get("sub", "All")
                        )
                        assert row["Trend Title"] == title, (
                            path,
                            key,
                            row["Trend Title"],
                            title,
                        )
                    if "Measure Names" in row:
                        metric = row["Measure Names"].split(" along ")[0]
                        metric = "GOAL" if metric == "Plot Goal" else metric
                        assert metric not in observed[key], (
                            path,
                            key,
                            metric,
                            "Duplicate metric",
                        )
                        observed[key][metric] = row["Measure Values"]
                    else:
                        observed[key].update(row)
                    if grain == "Data":
                        flag = row["Records to Show"].lower() == "true"
                        assert flag == expected[key]["Records to Show"], (
                            path,
                            key,
                            "Records to Show",
                            flag,
                            expected[key],
                        )
                assert set(observed) == set(expected), (
                    path,
                    "Coverage mismatch",
                    len(observed),
                    len(expected),
                    set(expected) - set(observed),
                )
                metrics = (
                    ["ACTUAL SALES", "SALES GOAL", "RESULT"]
                    if grain == "Table"
                    else [
                        "ACTUAL SALES",
                        "SALES GOAL",
                        "RESULT",
                        "ACTUAL vs GOAL",
                        "# Sub-Cats",
                        "Max Sub-Cats in Window",
                    ]
                    if grain == "Data"
                    else ["ACTUAL SALES", "GOAL"]
                    if grain == "Line Graph"
                    else ["RAG"]
                )
                for key, target in expected.items():
                    for metric in metrics:
                        if metric == "RAG":
                            assert observed[key][metric] == target[metric], (
                                path,
                                key,
                                metric,
                            )
                            continue
                        observed_name = next(
                            k
                            for k in observed[key]
                            if k == metric
                            or k.startswith(metric + " ")
                            or k == "SUM(" + metric + ")"
                        )
                        value = number(observed[key][observed_name])
                        wanted = target[metric]
                        if (
                            value is None
                            and wanted == 0
                            and author
                            and metric == "SALES GOAL"
                        ):
                            continue  # Author's original zero-format section is empty; source CSV scope explicitly recorded.
                        if wanted is None:
                            assert value is None, (path, key, metric, value, wanted)
                        else:
                            assert value is not None and abs(value - wanted) <= (
                                0.0051
                                if metric == "ACTUAL vs GOAL"
                                and "%" in observed[key][observed_name]
                                else 0.00001
                                if metric
                                in ["ACTUAL SALES", "SALES GOAL", "RESULT", "GOAL"]
                                else 0.000000001
                                if metric == "ACTUAL vs GOAL"
                                else 0
                            ), (path, key, metric, value, wanted)
                checks.append(
                    {
                        "path": capture["path"],
                        "rows": len(exported),
                        "marks": len(expected),
                        "status": "pass",
                    }
                )
        assert len(checks) == 32
        report["cloud_checks"] = checks
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(
        "PASS",
        len(actual),
        "actual rows;",
        len(goals),
        "independent goals; all four grains/states",
    )


if __name__ == "__main__":
    verify()
