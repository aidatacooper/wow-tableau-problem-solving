"""Independent raw-row oracle plus generated-workbook semantic checks.

This does not execute Tableau/VizQL. Desktop/Cloud rendering and interaction
acceptance remain pending even when every local check passes.
"""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile
from lxml import etree as ET
from tableauhyperapi import Connection, HyperProcess, Telemetry
from cwtwb.validator import validate_against_schema

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE / "outputs/replicated-workbook.twbx"
EVIDENCE = HERE / "evidence"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(actual, expected):
    assert abs(float(actual) - float(expected)) < 0.000001, (actual, expected)


def definitions(root):
    source = next(d for d in root.findall("datasources/datasource") if d.get("name") != "Parameters")
    columns = {c.get("caption", c.get("name").strip("[]")): c for c in source.findall("column")}
    names = {c.get("name"): "[" + caption + "]" for caption, c in columns.items()}
    names["[Parameters].[Parameter 1]"] = "[pTopN]"
    formulas = {}
    for caption, col in columns.items():
        calc = col.find("calculation")
        if calc is not None:
            formula = calc.get("formula")
            for original, readable in sorted(names.items(), key=lambda x: -len(x[0])):
                formula = formula.replace(original, readable)
            formulas[caption] = formula
    return source, columns, formulas


def inspect_contract(root):
    source, columns, formulas = definitions(root)
    param = root.find("datasources/datasource[@name='Parameters']/column[@caption='pTopN']")
    assert param is not None and param.get("value") == "5" and param.get("datatype") == "integer"
    assert dict(param.find("range").attrib) == {"granularity": "1", "max": "17", "min": "1"}
    group = source.find("group[@name='[Top Sub-Categories]']")
    end = group.find("groupfilter")
    assert end.get("count") == "[Parameters].[Parameter 1]" and end.get("end") == "top"
    order = end.find("groupfilter")
    assert order.get("direction") == "DESC" and order.get("expression").upper() == "SUM([SALES])"
    assert order.find("groupfilter").get("level") == "[Sub-Category]"
    expected = {
        "Total Sales": "{FIXED : SUM([Sales])}",
        "Group Order": "IF [Top Sub-Categories] THEN 0 ELSE 1 END",
        "Sales Group": "IF [Top Sub-Categories] THEN 'IN TOP ' + STR([pTopN]) ELSE 'ALL ELSE' END",
        "Top Share": "IF MIN([Group Order]) = 0 THEN SUM([Sales]) / MIN([Total Sales]) END",
        "Pie Label": "IF MIN([Group Order]) = 0 THEN STR(INT(ROUND([Top Share] * 100, 0))) + '%' + CHAR(10) + 'TOP ' + STR([pTopN]) END",
        "Contribution Caption": "'TOP ' + STR([pTopN]) + '  ·  ' + STR(INT(ROUND(SUM(IF [Top Sub-Categories] THEN [Sales] ELSE 0 END) / MIN([Total Sales]) * 100, 0))) + '% OF SALES'",
        "Sales Rank": "RANK(SUM([Sales]), 'desc')", "Outer Axis": "MIN(0)",
        "Category Count": "{FIXED : COUNTD([Sub-Category])}",
        "Rank Prefix": "IF SIZE() = MIN([Category Count]) THEN '#' + STR(INT([Sales Rank])) + ' · ' ELSE '' END",
        "Inner Axis": "MIN(0)", "Bar Width": "MIN(1)",
    }
    for caption, expected_formula in expected.items():
        assert formulas[caption] == expected_formula, (caption, formulas[caption])
    mapping = dict(re.findall(r"WHEN '([^']+)' THEN '([^']+)'", formulas["Ordered Sub-Category"]))
    assert len(mapping) == 17
    pie = root.find("worksheets/worksheet[@name='Contribution Pie']")
    panes = pie.findall("table/panes/pane")
    assert len(panes) == 3
    for pane in panes[1:]:
        assert pane.find("mark").get("class") == "Pie"
        assert pane.find("encodings/wedge-size").get("column").endswith(".[sum:Sales:qk]")
        assert columns["Sales Group"].get("name").strip("[]") in pane.find("encodings/lod").get("column")
    assert columns["Ordered Sub-Category"].get("name").strip("[]") in panes[1].find("encodings/color").get("column")
    assert columns["Group Order"].get("name").strip("[]") in panes[2].find("encodings/color").get("column")
    assert panes[2].find("style/style-rule[@element='mark']/format[@attr='mark-labels-show']").get("value") == "false"
    summary = root.find("worksheets/worksheet[@name='Contribution Summary']")
    assert summary is not None and not summary.findall(".//filter")
    assert columns["Contribution Caption"].get("name").strip("[]") in summary.find(".//encodings/text").get("column")
    label_style = {f.get("attr"): f.get("value") for f in panes[2].findall("style/style-rule[@element='datalabel']/format")}
    assert label_style["text-align"] == label_style["vertical-align"] == "center"
    assert "+" in pie.findtext("table/rows")
    assert float(panes[1].find("style/style-rule[@element='mark']/format[@attr='size']").get("value")) > float(panes[2].find("style/style-rule[@element='mark']/format[@attr='size']").get("value"))
    table = root.find("worksheets/worksheet[@name='Highlight Table']")
    row_text = table.findtext("table/rows")
    assert row_text.index(columns["Group Order"].get("name").strip("[]")) < row_text.index(columns["Sales Group"].get("name").strip("[]")) < row_text.index("Sub-Category")
    assert table.find(".//shelf-sort-v2").get("direction") == "DESC"
    assert "Sub-Category" in table.find(".//shelf-sort-v2").get("dimension-to-sort")
    subtotal = table.find("table/subtotals/column")
    assert columns["Sales Group"].get("name").strip("[]") in subtotal.text
    assert table.find(".//column-instance[@column='[Sales]'][@visual-totals='Sum']") is not None
    rank = table.find(".//column-instance[@column='" + columns["Sales Rank"].get("name") + "']/table-calc")
    assert rank.get("ordering-type") == "Field"
    assert [x.get("field").split("].", 1)[1] for x in rank] == [columns[c].get("name") for c in ["Group Order", "Sales Group", "Sub-Category"]]
    rank_prefix = table.find(".//column-instance[@column='" + columns["Rank Prefix"].get("name") + "']/table-calc")
    assert rank_prefix.get("ordering-type") == "Field"
    assert [x.get("field").split("].", 1)[1] for x in rank_prefix] == [columns[c].get("name") for c in ["Group Order", "Sales Group", "Sub-Category"]]
    nested_rank = table.find(".//column-instance[@column='" + columns["Rank Prefix"].get("name") + "']/table-calc[@field]")
    assert nested_rank.get("field").endswith("." + columns["Sales Rank"].get("name"))
    assert nested_rank.get("ordering-type") == "Field"
    assert [x.get("field").split("].", 1)[1] for x in nested_rank] == [columns[c].get("name") for c in ["Group Order", "Sales Group", "Sub-Category"]]
    label_runs = table.findall("table/panes/pane/customized-label/formatted-text/run")
    assert any(columns["Rank Prefix"].get("name").strip("[]") in (r.text or "") for r in label_runs)
    assert not any(columns["Sales Rank"].get("name").strip("[]") in (r.text or "") for r in label_runs)
    dashboard = root.find("dashboards/dashboard")
    size = dashboard.find("size")
    assert size.get("maxwidth") == "1400" and size.get("maxheight") == "900"
    assert dashboard.find(".//zone[@type-v2='paramctrl']") is not None
    action = root.find("actions/action")
    assert action.find("activation").get("type") == "on-hover"
    assert action.find("activation").get("auto-clear") == "true"
    assert action.find("source").get("dashboard") == dashboard.get("name")
    assert action.find("command").get("command") == "tsc:brush"
    attrs = {n.get("name"): n.get("value") for n in action.findall("command/param")}
    assert attrs == {"field-captions": "Sales Group", "target": dashboard.get("name"), "exclude": "Contribution Summary"}
    assert [n.get("name") for n in action.findall("source/exclude-sheet")] == ["Contribution Summary"]
    # Same color for each sales category in ring and table.
    palettes = source.findall("style/style-rule/encoding[@attr='color']")
    def palette_for(caption):
        token = columns[caption].get("name").strip("[]")
        node = next(x for x in palettes if token in x.get("field"))
        return {x.findtext("bucket").strip('"'): x.get("to") for x in node.findall("map")}
    colors, ring_colors = palette_for("Sub-Category"), palette_for("Ordered Sub-Category")
    assert len(set(colors.values())) == 17
    assert all(colors[category] == ring_colors[key] for category, key in mapping.items())
    return mapping


def mutation_checks(root):
    checks = []
    mutations = {
        "fixed-top-count": lambda r: r.find(".//group/groupfilter").set("count", "5"),
        "wrong-wedge-measure": lambda r: r.find(".//encodings/wedge-size").set("column", "[bad].[sum:Wrong:qk]"),
        "wrong-denominator": lambda r: r.find("datasources/datasource/column[@caption='Top Share']/calculation").set("formula", "SUM([Sales]) / 1"),
        "select-instead-of-hover": lambda r: r.find("actions/action/activation").set("type", "on-select"),
        "partitioned-rank": lambda r: r.find("worksheets/worksheet[@name='Highlight Table']//column-instance/table-calc").set("ordering-type", "Rows"),
        "subtotal-rank-visible": lambda r: r.find("datasources/datasource/column[@caption='Rank Prefix']/calculation").set("formula", "STR(RANK(SUM([Sales])))"),
        "nested-rank-partition": lambda r: r.find("worksheets/worksheet[@name='Highlight Table']//column-instance/table-calc[@field]").set("ordering-type", "Rows"),
        "clipped-pie-label-enabled": lambda r: r.find("worksheets/worksheet[@name='Contribution Pie']/table/panes/pane[@id='2']/style/style-rule[@element='mark']/format[@attr='mark-labels-show']").set("value", "true"),
    }
    for name, mutate in mutations.items():
        changed = deepcopy(root)
        mutate(changed)
        try:
            inspect_contract(changed)
        except AssertionError:
            checks.append(name)
        else:
            raise AssertionError("Verifier failed to reject mutation: " + name)
    return checks


def verify():
    EVIDENCE.mkdir(exist_ok=True)
    raw = next((HERE / "inputs").glob("*.hyper"))
    with zipfile.ZipFile(ARTIFACT) as archive:
        root = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith(".twb"))))
        hyper_name = next(n for n in archive.namelist() if n.endswith(".hyper"))
        packaged = archive.read(hyper_name)
    assert hashlib.sha256(packaged).hexdigest() == sha(raw)
    schema = validate_against_schema(root)
    assert schema.schema_available and not schema.errors, schema.errors
    mapping = inspect_contract(root)
    with tempfile.TemporaryDirectory(prefix="ww41-oracle-") as temp, HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, str(raw)) as connection:
            # Oracle is an independent decimal accumulation over unaggregated rows.
            rows = connection.execute_list_query('SELECT "Sub-Category", "Sales" FROM "Extract"."Extract"')
        totals = defaultdict(Decimal)
        for category, sales in rows:
            assert category is not None and sales is not None
            totals[category] += Decimal(str(sales))
        ranked = sorted(totals, key=lambda category: (-totals[category], category))
        assert len(rows) == 9994 and len(ranked) == 17
        total = sum(totals.values())
        close(total, Decimal('2297200.8603'))
        assert ranked == sorted(mapping, key=mapping.get)
        packaged_path = Path(temp) / "generated.hyper"
        packaged_path.write_bytes(packaged)
        with Connection(hp.endpoint, str(packaged_path)) as generated:
            # The supported generated plan was checked above: SUM Sales, DESC,
            # dynamic Top N by Sub-Category, unfiltered FIXED denominator.
            actual = generated.execute_list_query('SELECT "Sub-Category", SUM("Sales"), RANK() OVER (ORDER BY SUM("Sales") DESC) FROM "Extract"."Extract" GROUP BY "Sub-Category" ORDER BY SUM("Sales") DESC')
        assert [r[0] for r in actual] == ranked
        for index, (category, amount, rank) in enumerate(actual, 1):
            close(amount, totals[category])
            assert rank == index
        scenarios = []
        for n in range(1, 18):
            expected_top = sum(totals[c] for c in ranked[:n])
            actual_top = sum(amount for _, amount, rank in actual if rank <= n)
            actual_rest = sum(amount for _, amount, rank in actual if rank > n)
            close(actual_top, expected_top)
            close(actual_rest, total - expected_top)
            close(actual_top + actual_rest, total)
            close(actual_top / float(total), expected_top / total)
            assert len([rank for _, _, rank in actual if rank <= n]) == n
            # Both hover sources carry exactly this group and therefore have
            # the same selected membership; empty ALL ELSE at N=17 is omitted.
            selected_top = ranked[:n]
            selected_rest = ranked[n:]
            assert set(selected_top).isdisjoint(selected_rest)
            assert len(selected_top) + len(selected_rest) == 17
            scenarios.append({"top_n": n, "top_members": selected_top,
                "rest_members": selected_rest, "top_sales": float(expected_top),
                "rest_sales": float(total - expected_top), "top_fraction": float(expected_top / total),
                "display_percent": int((expected_top / total * 100).quantize(Decimal('1'))),
                "group_count": 1 if n == 17 else 2})
    oracle = {"input_sha256": sha(raw), "rows": len(rows), "total_sales": float(total),
        "subcategories": [{"name": category, "rank": i, "sales": float(totals[category]), "fraction": float(totals[category] / total)} for i, category in enumerate(ranked, 1)], "scenarios": scenarios}
    (EVIDENCE / "numerical-oracle.json").write_text(json.dumps(oracle, indent=2) + "\n", encoding="utf8")
    report = {"status": "local-pass-runtime-pending", "workbook_sha256": sha(ARTIFACT),
        "checks": ["locked-data", "parameter-domain", "all-top-n-numerics", "sales-proportional-pies", "grouped-ranked-subtotals", "group-hover-contract", "matching-colors", "dashboard-contract", "xsd"],
        "scenarios": len(scenarios), "mutation_checks": mutation_checks(root),
        "limits": "SQL evaluates a checked subset of workbook semantics; not Tableau/VizQL execution.",
        "pending": ["desktop-load", "runtime-parameter-and-hover", "cloud-visual-review", "desktop-corpus", "independent-review"]}
    (EVIDENCE / "local-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": report["status"], "scenarios": 17, "total_sales": oracle["total_sales"], "default_top_sales": scenarios[4]["top_sales"], "default_top_fraction": scenarios[4]["top_fraction"], "mutations_rejected": len(report["mutation_checks"])}, indent=2))


if __name__ == "__main__":
    verify()
