"""Verify native heatmap contracts and recompute every cell from locked raw rows."""

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import calendar
import csv
import json

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_15_WW29_Heatmap_Intermediate"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def oracle(records, filters=None):
    filters = filters or {}
    rows = [
        row
        for row in records
        if (
            not filters.get("Year Order Date")
            or str(row[0].year) == filters["Year Order Date"]
        )
        and (
            not filters.get("Month Order Date")
            or calendar.month_name[row[0].month] == filters["Month Order Date"]
        )
    ]
    groups = defaultdict(list)
    for day, quantity, sales, profit in rows:
        for key in (
            (str(day.year), calendar.month_name[day.month]),
            (str(day.year), "Total"),
            ("Total", calendar.month_name[day.month]),
            ("Total", "Total"),
        ):
            groups[key].append((quantity, sales, profit))
    years = sorted({str(row[0].year) for row in rows})
    months = [calendar.month_name[m] for m in sorted({row[0].month for row in rows})]
    result = {}
    for (year, month), values in groups.items():
        quantity = sum(v[0] for v in values) / len(values)
        label = (
            quantity
            if year == "Total"
            or month == "Total"
            or len(years) == 1
            or len(months) == 1
            else None
        )
        result[(year, month)] = {
            "quantity": quantity,
            "total_label": label,
            "cell_label": None,
            "profit_ratio": sum(v[2] for v in values) / sum(v[1] for v in values),
            "row_count": len(values),
        }
    for (year, month), values in result.items():
        components = [
            v["quantity"]
            for (y, m), v in result.items()
            if y != "Total"
            and m != "Total"
            and (year == "Total" or y == year)
            and (month == "Total" or m == month)
        ]
        values["visual_average"] = sum(components) / len(components)
    return result


def numeric(text, expected):
    if not text.strip():
        assert expected is None, (text, expected)
        return
    assert expected is not None
    clean = text.replace(",", "").replace("%", "").strip()
    scale = 100 if "%" in text else 1
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    assert (
        abs(float(clean) / scale - expected) <= 0.501 * 10 ** (-decimals) / scale + 1e-8
    ), (text, expected)


def verify(workbook_path=None, evidence_path=None):
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    data = HERE / item["file"]
    assert digest(data) == item["sha256"]
    workbook = Path(workbook_path or HERE / "outputs/replicated-workbook.twbx")
    with ZipFile(workbook) as z:
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
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
        Connection(process.endpoint, str(data)) as connection,
    ):
        table = next(
            t
            for s in connection.catalog.get_schema_names()
            for t in connection.catalog.get_table_names(s)
        )
        records = connection.execute_list_query(
            'SELECT "Order Date","Quantity","Sales","Profit" FROM ' + str(table)
        )
    assert len(records) == 9994
    expected = oracle(records)
    assert len(expected) == 65
    assert sum(row[1] for row in records) == 37873
    hover_cases = []
    for selected_months, selected_years, expected_count in [
        (set(), set(), 0),
        ({"January"}, {"2019"}, 1),
        ({"January", "February"}, {"2018", "2019"}, 4),
    ]:
        selected = {
            key: values["quantity"]
            for key, values in expected.items()
            if "Total" not in key
            and key[0] in selected_years
            and key[1] in selected_months
        }
        assert len(selected) == expected_count
        hover_cases.append(
            {
                "months": sorted(selected_months),
                "years": sorted(selected_years),
                "expected_interior_labels": len(selected),
                "evaluation": "Independent set-membership formula oracle, no event executed",
            }
        )
    worksheet = root.find("worksheets/worksheet[@name='Chart-Int']")
    assert worksheet is not None
    dependencies = worksheet.find("table/view/datasource-dependencies")
    columns = {
        c.get("caption", c.get("name").strip("[]")): c
        for c in dependencies.findall("column")
    }
    names = {c.get("name"): caption for caption, c in columns.items()}

    def formula(caption):
        value = columns[caption].find("calculation").get("formula")
        for local, display in names.items():
            value = value.replace(local, "[" + display + "]")
        return value

    assert (
        formula("Total Label")
        == "IF [Size of Years]=1 OR [Size of Months]=1 THEN AVG([Quantity]) END"
    )
    assert (
        formula("Cell Label")
        == "IF ATTR([Hover Month Set]) AND ATTR([Hover Year Set]) AND [Size of Months]>1 AND [Size of Years]>1 THEN AVG([Quantity]) END"
    )
    assert formula("Profit Ratio") == "SUM([Profit])/SUM([Sales])"
    assert formula("Month Order Date") == "DATENAME('month',[Order Date])"
    assert formula("Year Order Date") == "YEAR([Order Date])"
    assert formula("Size of Years") == "SIZE()"
    assert formula("Size of Months") == "SIZE()"
    for caption in ("Total Label", "Cell Label"):
        instance = dependencies.find(
            "column-instance[@column='%s']" % columns[caption].get("name")
        )
        addressing = instance.findall("table-calc")
        assert len(addressing) == 3 and addressing[0].get("ordering-type") == "Rows"
        for size, dimension in (
            ("Size of Years", "Year Order Date"),
            ("Size of Months", "Month Order Date"),
        ):
            calculation = next(
                t
                for t in addressing
                if t.get("field", "").endswith("." + columns[size].get("name"))
            )
            assert calculation.get("ordering-type") == "Field"
            assert columns[dimension].get("name").strip("[]") in calculation.get(
                "ordering-field"
            )
    quantity = dependencies.find("column-instance[@column='[Quantity]']")
    assert (
        quantity.get("derivation") == "Avg" and quantity.get("visual-totals") == "Avg"
    )
    assert ":vtavg:" in quantity.get("name")
    assert worksheet.find("table/rows").get("total") == "true"
    assert worksheet.find("table/cols").get("total") == "true"
    pane = worksheet.find("table/panes/pane")
    assert pane.find("mark").get("class") == "Square"
    assert pane.find("mark-sizing").get("mark-sizing-setting") == "marks-scaling-off"
    assert len(pane.findall("encodings/text")) == 2
    assert "Total Label" not in "".join(
        pane.find("customized-label").itertext()
    )  # field tokens, not literal captions
    encoding = worksheet.find(
        "table/style/style-rule[@element='mark']/encoding[@attr='color']"
    )
    assert encoding.get("include-totals") == "true"
    groups = root.findall("datasources/datasource/group")
    for name, dimension in (
        ("Hover Month Set", "Month Order Date"),
        ("Hover Year Set", "Year Order Date"),
    ):
        group = next(g for g in groups if g.get("caption") == name)
        empty = group.find("groupfilter")
        assert empty.get("function") == "empty-level"
        assert empty.get("member") == columns[dimension].get("name")
    actions = root.findall("actions/edit-group-action")
    assert len(actions) == 2 and len({a.get("name") for a in actions}) == 2
    targets = set()
    for action in actions:
        assert action.find("activation").get("type") == "on-hover"
        assert action.find("source").get("dashboard") == DASHBOARD
        assert action.find("source").get("worksheet") == "Chart-Int"
        params = {p.get("name"): p.get("value") for p in action.findall("params/param")}
        assert params["selection-clear-set-option"] == "exclude-all"
        mode = action.find("add-or-remove-marks")
        assert (
            mode.get("value") if mode is not None else params.get("add-or-remove-marks")
        ) == "assign"
        assert params["target-group"].endswith(".[Hover Month Set]") or params[
            "target-group"
        ].endswith(".[Hover Year Set]")
        targets.add(params["target-group"].rsplit(".", 1)[-1])
    assert targets == {"[Hover Month Set]", "[Hover Year Set]"}
    dashboard = root.find("dashboards/dashboard[@name='%s']" % DASHBOARD)
    assert dashboard.find("size").get("maxwidth") == "900"
    assert dashboard.find("size").get("maxheight") == "500"
    for zone in dashboard.findall("zones//zone"):
        assert 0 <= int(zone.get("x")) <= 100000 and 0 <= int(zone.get("y")) <= 100000
        assert int(zone.get("x")) + int(zone.get("w")) <= 100001
        assert int(zone.get("y")) + int(zone.get("h")) <= 100001
    cloud_checks = []
    manifest = HERE / "evidence/cloud-verification.json"
    if manifest.exists() and workbook_path is None:
        report = json.loads(manifest.read_text(encoding="utf-8"))
        assert report["source_hashes"]["replica"] == digest(workbook)
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert report["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert not report["browser_interaction_executed"]
        assert len(report["states"]) == 4
        for state in report["states"]:
            state_expected = oracle(records, state.get("filters"))
            for exported in state["views"].values():
                assert digest(HERE / exported["path"]) == exported["sha256"]
            for exported in state["data"]:
                path = HERE / exported["path"]
                assert digest(path) == exported["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                assert rows, exported
                seen = set()
                for row in rows:
                    year = row.get("Year Order Date", "").strip()
                    month = row.get("Month Order Date", "").strip()
                    year = (
                        "Total"
                        if year.lower() == "all" or "total" in year.lower()
                        else year
                    )
                    month = (
                        "Total"
                        if month.lower() == "all" or "total" in month.lower()
                        else month
                    )
                    key = (year, month)
                    assert key in state_expected, (exported, row)
                    values = state_expected[key]
                    quantity_column = next(
                        (
                            k
                            for k in row
                            if k in ("Avg. Quantity", "AVG(Quantity)", "Quantity")
                        ),
                        None,
                    )
                    assert quantity_column, row
                    numeric(row[quantity_column], values["visual_average"])
                    for caption, metric in (
                        ("Total Label", "total_label"),
                        ("Cell Label", "cell_label"),
                        ("Profit Ratio", "profit_ratio"),
                    ):
                        assert caption in row, (exported, row)
                        numeric(row[caption], values[metric])
                    seen.add(key)
                assert set(state_expected) == seen, (
                    exported,
                    set(state_expected) - seen,
                )
                cloud_checks.append(
                    {
                        "state": state["name"],
                        "role": exported["role"],
                        "cells_checked": len(seen),
                        "total_cells_exported": sum("Total" in key for key in seen),
                        "scope": "All exported heatmap cells checked against raw data; totals included only when present in REST CSV. Stored empty sets and filter states do not execute hover.",
                    }
                )
    result = {
        "status": "passed",
        "artifact_sha256": digest(workbook),
        "raw_rows": len(records),
        "grid_cells": 48,
        "total_cells": 17,
        "acceptance_ids": [
            "ww29-heatmap-oracle",
            "ww29-independent-size-addressing",
            "ww29-hover-action-contract",
            "ww29-native-totals",
            "ww29-cloud-matrix",
        ],
        "oracle": [
            {"year": y, "month": m, **values}
            for (y, m), values in sorted(expected.items())
        ],
        "synthetic_hover_scope": "Independent formula oracle: selected month AND year shows just their cell for full grid; cleared sets suppress all interior labels; SIZE=1 suppresses Cell Label and enables Total Label. No browser event execution claimed.",
        "hover_formula_cases": hover_cases,
        "cloud_checks": cloud_checks,
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    Path(evidence_path or HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "oracle"}, indent=2))
    return result


if __name__ == "__main__":
    verify()
