"""Independent raw-input oracle plus generated-workbook contract verification.

The Python oracle does not import the builder. A small fail-closed Tableau
expression parser translates the GENERATED formulas to Hyper SQL. This tests
calculation semantics locally, not Tableau rendering or live action dispatch.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
TABLE = '"Extract"."Extract"'
PERIODS = ("Month", "Quarter", "Year")
TOKEN = re.compile(
    r"\s*(\[[^\]]+\](?:\.\[[^\]]+\])?|'(?:''|[^'])*'|>=|<=|<>|[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|[{}():,=<>/+*-])"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


class Formula:
    """Restricted recursive parser: reject unsupported expressions rather than guess."""

    def __init__(self, text, resolve, table=TABLE):
        self.tokens = []
        while text.strip():
            match = TOKEN.match(text)
            assert match, f"Unsupported Tableau syntax: {text[:100]}"
            self.tokens.append(match.group(1))
            text = text[match.end() :]
        self.tokens.append("<EOF>")
        self.i, self.resolve, self.table = 0, resolve, table

    def pop(self, expected=None):
        token = self.tokens[self.i]
        if expected is not None:
            assert token.upper() == expected, (token, expected)
        self.i += 1
        return token

    def peek(self):
        return self.tokens[self.i].upper()

    def complete(self):
        result = self.expr()
        self.pop("<EOF>")
        return result

    def expr(self, precedence=0):
        token = self.pop()
        upper = token.upper()
        if upper == "IF":
            parts = []
            while True:
                condition = self.expr()
                self.pop("THEN")
                value = self.expr()
                parts.append(f"WHEN {condition} THEN {value}")
                if self.peek() != "ELSEIF":
                    break
                self.pop()
            fallback = "NULL"
            if self.peek() == "ELSE":
                self.pop()
                fallback = self.expr()
            self.pop("END")
            left = f"(CASE {' '.join(parts)} ELSE {fallback} END)"
        elif upper == "CASE":
            value = self.expr()
            parts = []
            while self.peek() == "WHEN":
                self.pop()
                choice = self.expr()
                self.pop("THEN")
                result = self.expr()
                parts.append(f"WHEN {choice} THEN {result}")
            fallback = "NULL"
            if self.peek() == "ELSE":
                self.pop()
                fallback = self.expr()
            self.pop("END")
            left = f"(CASE {value} {' '.join(parts)} ELSE {fallback} END)"
        elif token == "{":
            self.pop("FIXED")
            self.pop(":")
            aggregate = self.expr()
            self.pop("}")
            left = f"(SELECT {aggregate} FROM {self.table})"
        elif token == "(":
            left = self.expr()
            self.pop(")")
        elif token.startswith("["):
            left = self.resolve(token)
        elif token.startswith("'") or re.fullmatch(r"\d+(?:\.\d+)?", token):
            left = token
        elif upper in {"SUM", "COUNTD", "MAX", "MIN", "ATTR", "DATE", "DATETRUNC"}:
            self.pop("(")
            args = [self.expr()]
            while self.peek() == ",":
                self.pop()
                args.append(self.expr())
            self.pop(")")
            if upper == "COUNTD":
                left = f"COUNT(DISTINCT {args[0]})"
            elif upper == "DATE":
                left = f"CAST({args[0]} AS DATE)"
            elif upper == "DATETRUNC":
                assert len(args) == 2
                left = f"DATE_TRUNC({args[0]}, {args[1]})"
            else:
                left = f"{'MIN' if upper == 'ATTR' else upper}({args[0]})"
        else:
            raise AssertionError(f"Unsupported expression token: {token}")
        operators = {
            "OR": 1,
            "AND": 2,
            "=": 3,
            "<": 3,
            ">": 3,
            ">=": 3,
            "<=": 3,
            "<>": 3,
            "+": 4,
            "-": 4,
            "*": 5,
            "/": 5,
        }
        while operators.get(self.peek(), 0) > precedence:
            op = self.pop().upper()
            right = self.expr(operators[op])
            left = f"({left} {op} {right})"
        return left


class GeneratedModel:
    def __init__(self, root, period):
        self.ds = next(
            x
            for x in root.findall("datasources/datasource")
            if x.get("name") != "Parameters"
        )
        self.columns = {x.get("name"): x for x in self.ds.findall("column")}
        self.physical = {
            x.findtext("local-name"): x.findtext("remote-name")
            for x in self.ds.findall('.//metadata-record[@class="column"]')
        }
        self.by_caption = {
            x.get("caption", x.get("name").strip("[]")): x.get("name")
            for x in self.columns.values()
        }
        self.sets = {}
        params = root.find("datasources/datasource[@name='Parameters']")
        self.parameters = {
            f"[Parameters].{x.get('name')}": literal(period)
            for x in params.findall("column")
        }

    def field(self, name):
        if name in self.parameters:
            return self.parameters[name]
        if name in self.sets:
            return self.sets[name]
        if name in self.physical and name not in self.columns:
            return '"' + self.physical[name].replace('"', '""') + '"'
        column = self.columns[name]
        calc = column.find("calculation")
        if calc is not None:
            return Formula(calc.get("formula"), self.field).complete()
        return '"' + name.strip("[]").replace('"', '""') + '"'

    def sql(self, caption):
        return self.field(self.by_caption[caption])

    def rank(self, connection):
        results = {}
        for group in self.ds.findall("group"):
            end = group.find("groupfilter")
            order = end.find("groupfilter")
            level = order.find("groupfilter").get("level")
            assert end.get("units") == "records" and end.get("count") == "5"
            assert order.get("direction") == "DESC"
            measure = Formula(order.get("expression"), self.field).complete()
            category = self.field(level)
            rows = connection.execute_list_query(
                f"SELECT {category}, {measure} AS v FROM {TABLE} GROUP BY {category} ORDER BY v DESC, {category}"
            )
            assert len(rows) == 17 and all(v is not None for _, v in rows)
            chosen = rows[:5] if end.get("end") == "top" else rows[-5:]
            assert end.get("end") in {"top", "bottom"}
            names = [name for name, _ in chosen]
            results[group.get("caption")] = names
            self.sets[group.get("name")] = (
                f"({category} IN ({', '.join(map(literal, names))}))"
            )
        return results


def raw_oracle(rows, period):
    """Pure Python calendar and fsum implementation, independent of TWB formulas."""
    latest = max(date for date, _, _ in rows)
    if period == "Month":
        start = latest.replace(day=1)
    elif period == "Quarter":
        start = dt.date(latest.year, 3 * ((latest.month - 1) // 3) + 1, 1)
    else:
        start = dt.date(latest.year, 1, 1)
    values = defaultdict(list)
    for date, category, profit in rows:
        if start <= date <= latest:
            values[category].append(profit)
    profits = {name: math.fsum(value) for name, value in values.items()}
    assert len(profits) == 17
    descending = sorted(profits, key=lambda n: (-profits[n], n))
    top, bottom = descending[:5], descending[-5:]
    middle = descending[5:-5]
    bars = {
        name: {
            "value": profits[name],
            "group": "Top 5" if name in top else "Bottom 5",
            "members": 1,
        }
        for name in top + bottom
    }
    bars["Everyone Else"] = {
        "value": math.fsum(profits[n] for n in middle) / len(middle),
        "group": "Everything Else",
        "members": len(middle),
    }
    return {
        "start": start.isoformat(),
        "latest": latest.isoformat(),
        "total": math.fsum(profits.values()),
        "top": top,
        "bottom": bottom,
        "middle": middle,
        "profits": profits,
        "bars": bars,
        "boundary_gaps": {
            "top": profits[descending[4]] - profits[descending[5]],
            "bottom": profits[descending[-6]] - profits[descending[-5]],
        },
    }


def close(actual, expected):
    if expected is None:
        assert actual is None, (actual, expected)
    elif isinstance(expected, (int, float)):
        assert actual is not None and math.isclose(
            float(actual), expected, rel_tol=1e-10, abs_tol=1e-7
        ), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def structure(root):
    sheets = {w.get("name"): w for w in root.findall("worksheets/worksheet")}
    assert set(sheets) == {"Period KPIs", "Profit Performers"}
    params = root.findall("datasources/datasource[@name='Parameters']/column")
    assert (
        len(params) == 1
        and params[0].get("caption") == "Period"
        and params[0].get("value") == '"Month"'
    )
    members = params[0].xpath(".//member/@value")
    assert set(members) == {'"Month"', '"Quarter"', '"Year"'}, members
    chart = sheets["Profit Performers"]
    assert not chart.xpath(".//filter"), (
        "Unexpected filter changes ranking/grouping order"
    )
    assert not root.xpath("./datasources/datasource/filter"), (
        "Unexpected datasource filter changes FIXED anchor"
    )
    model = GeneratedModel(root, "Month")

    def ref(caption):
        return model.by_caption[caption].strip("[]")

    assert ref("Display Category") in chart.findtext("table/rows")
    sort = chart.find(".//computed-sort")
    assert sort is not None and sort.get("direction") == "DESC"
    assert ref("Display Category") in sort.get("column") and ref(
        "Average Profit"
    ) in sort.get("using")
    panes = chart.findall("table/panes/pane")
    assert len(panes) == 2
    for pane, side in zip(panes, ("Left", "Right")):
        assert pane.find("mark").get("class") == "GanttBar"
        assert ref("Zero") in pane.get("x-axis-name")
        assert ref("Average Profit") in pane.find("encodings/size").get("column")
        assert ref("Performance Group") in pane.find("encodings/color").get("column")
        labels = pane.xpath("./encodings/text/@column")
        assert (
            len(labels) == 2
            and any(ref(f"{side} Profit") in x for x in labels)
            and any(ref(f"{side} Category") in x for x in labels)
        )
        assert pane.xpath(
            f'./style/style-rule[@element="datalabel"]/format[@attr="text-align" and @value="{side.lower()}"]'
        )
        assert not pane.xpath("./encodings/lod"), (
            "Detail would split the grouped average"
        )
    assert chart.xpath('.//encoding[@fold="true" and @synchronized="true"]')
    kpi = sheets["Period KPIs"]
    kpi_filters = kpi.findall(".//filter")
    assert len(kpi_filters) == 1 and kpi_filters[0].get("column").endswith(
        "[:Measure Names]"
    )
    kpi_members = kpi_filters[0].xpath('.//groupfilter[@function="member"]/@member')
    assert len(kpi_members) == 3
    for name in PERIODS:
        assert any("sum:" + ref(name) + ":" in item for item in kpi_members)
    for sheet in sheets.values():
        assert sheet.xpath('./table/tooltip-style[@tooltip-mode="none"]'), (
            "Tooltips must be disabled"
        )
    dash = root.find("dashboards/dashboard")
    assert (
        dash.find("size").get("maxwidth") == "700"
        and dash.find("size").get("maxheight") == "800"
    )
    actions = root.findall("actions/edit-parameter-action")
    assert len(actions) == 1
    action = actions[0]
    assert action.find("activation").get("type") == "on-select"
    assert action.find("source").get("worksheet") == "Period KPIs"
    assert action.find("source").get("dashboard") == dash.get("name")
    assert action.find("agg-type").get("type") == "attr"
    assert action.find("clear-option").get("type") == "do-nothing"
    action_params = {
        p.get("name"): p.get("value") for p in action.findall("params/param")
    }
    assert action_params["source-field"].endswith("[:Measure Names]")
    assert action_params["target-parameter"] == f"[Parameters].{params[0].get('name')}"
    assert not root.xpath("./actions/action"), "No unintended dashboard filter action"


def compare_generated(root, connection, oracle, period):
    model = GeneratedModel(root, period)
    close(
        connection.execute_scalar_query(
            f"SELECT SUM({model.sql(period)}) FROM {TABLE}"
        ),
        oracle["total"],
    )
    sets = model.rank(connection)
    assert set(sets["Top 5"]) == set(oracle["top"])
    assert set(sets["Bottom 5"]) == set(oracle["bottom"])
    captions = [
        "Display Category",
        "Performance Group",
        "Average Profit",
        "Left Profit",
        "Left Category",
        "Right Profit",
        "Right Category",
    ]
    expressions = [model.sql(name) for name in captions]
    query = f'SELECT {", ".join(expressions)}, COUNT(DISTINCT "Sub-Category") FROM {TABLE} GROUP BY 1, 2 ORDER BY 3 DESC'
    actual = connection.execute_list_query(query)
    assert len(actual) == 11
    for name, group, value, lp, lc, rp, rc, count in actual:
        expected = oracle["bars"][name]
        close(value, expected["value"])
        close(group, expected["group"])
        close(count, expected["members"])
        close(lp, value if value < 0 else None)
        close(lc, name if value >= 0 else None)
        close(rp, value if value >= 0 else None)
        close(rc, name if value < 0 else None)
    # The middle aggregate is a mean; using a sum would fail the comparison above.
    assert actual == sorted(actual, key=lambda r: -r[2])
    return [
        {"category": r[0], "group": r[1], "profit": r[2], "member_count": r[7]}
        for r in actual
    ]


def main():
    artifact = HERE / "outputs/replicated-workbook.twbx"
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    source = HERE / lock["extracted_data"][0]["file"]
    assert sha(source) == lock["extracted_data"][0]["sha256"]
    with ZipFile(artifact) as package:
        root = etree.fromstring(
            package.read(next(n for n in package.namelist() if n.endswith(".twb")))
        )
        hypers = [n for n in package.namelist() if n.endswith(".hyper")]
        assert len(hypers) == 1 and hashlib.sha256(
            package.read(hypers[0])
        ).hexdigest() == sha(source)
        connection = root.find(".//named-connection/connection")
        assert (
            connection.get("dbname") == hypers[0]
            and connection.get("schema") == "Extract"
        )
    structure(root)
    evidence = {
        "artifact_sha256": sha(artifact),
        "method": "Independent Python raw-input oracle versus generated Tableau formulas translated to Hyper SQL; no Desktop/Cloud runtime claim.",
        "scenarios": {},
        "pending": [
            "Desktop load",
            "live KPI actions and clear selection",
            "visual labels and no-tooltip behavior",
            "corpus Desktop regression",
            "Cloud comparison if requested",
        ],
    }
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,
        Connection(process.endpoint, str(source)) as conn,
    ):
        rows = [
            (dt.date(d.year, d.month, d.day), n, float(p))
            for d, n, p in conn.execute_list_query(
                f'SELECT "Order Date", "Sub-Category", "Profit" FROM {TABLE}'
            )
        ]
        assert len(rows) == 9994
        assert min(d for d, _, _ in rows) == dt.date(2018, 1, 3)
        assert max(d for d, _, _ in rows) == dt.date(2021, 12, 30)
        for period in PERIODS:
            oracle = raw_oracle(rows, period)
            assert len(set(oracle["profits"].values())) == 17, (
                "Ties require explicit review, not an invented tie-breaker"
            )
            bars = compare_generated(root, conn, oracle, period)
            evidence["scenarios"][period] = {**oracle, "generated_bars": bars}
        # All KPIs stay visible and unchanged regardless of the selected period.
        for selected in PERIODS:
            model = GeneratedModel(root, selected)
            for kpi in PERIODS:
                close(
                    conn.execute_scalar_query(
                        f"SELECT SUM({model.sql(kpi)}) FROM {TABLE}"
                    ),
                    evidence["scenarios"][kpi]["total"],
                )
        # Shift the max date to a different year and a non-quarter-end month.
        # This catches hardcoded December/2021 and rolling-window definitions.
        fixture = "WITH fixture(\"Order Date\", \"Sub-Category\", \"Profit\") AS (VALUES (DATE '2022-12-31', 'A', 100.0), (DATE '2023-01-01', 'A', 1.0), (DATE '2023-02-01', 'A', 2.0), (DATE '2023-03-31', 'A', 3.0), (DATE '2023-04-01', 'A', 4.0), (DATE '2023-05-15', 'A', 5.0)) "
        model = GeneratedModel(root, "Month")
        for period, expected in zip(PERIODS, (5.0, 9.0, 15.0)):
            sql = model.sql(period).replace(TABLE, "fixture")
            close(
                conn.execute_scalar_query(f"{fixture} SELECT SUM({sql}) FROM fixture"),
                expected,
            )
        # Mutation tests: plausible defects must be caught by an independent oracle.
        mutations = [
            ("wrong-period", "Quarter", "[Month]"),
            ("wrong-denominator", "Average Profit", "SUM([Selected Profit])"),
        ]
        for mutation, caption, formula in mutations:
            changed = copy.deepcopy(root)
            ds = next(
                x
                for x in changed.findall("datasources/datasource")
                if x.get("name") != "Parameters"
            )
            target = ds.find(f"column[@caption='{caption}']/calculation")
            fields = {x.get("caption"): x.get("name") for x in ds.findall("column")}
            for name, internal in fields.items():
                formula = formula.replace(f"[{name}]", internal)
            target.set("formula", formula)
            try:
                compare_generated(
                    changed, conn, evidence["scenarios"]["Quarter"], "Quarter"
                )
            except AssertionError:
                pass
            else:
                raise AssertionError(f"Mutation escaped detection: {mutation}")
        changed = copy.deepcopy(root)
        changed.find(
            "datasources/datasource/group[@caption='Bottom 5']/groupfilter"
        ).set("end", "top")
        try:
            compare_generated(changed, conn, evidence["scenarios"]["Month"], "Month")
        except AssertionError:
            pass
        else:
            raise AssertionError("Wrong bottom-set mutation escaped detection")
    # Synthetic ties: five records, not five dense ranks. Tie membership is not
    # deterministic in the author's contract; require all strict winners and
    # only cutoff-tied candidates, and never claim a Tableau runtime tie verdict.
    scores = [100, 90, 80, 70, 60, 60, 50, 40, 30, 20, 10, -10, -10, -20, -30, -40, -50]
    for values in (scores, [-v for v in scores]):
        ordered = sorted(values, reverse=True)
        cutoff = ordered[4]
        strict = [v for v in values if v > cutoff]
        eligible = [v for v in values if v >= cutoff]
        assert len(strict) < 5 < len(eligible)
        assert len(ordered[:5]) == 5
    evidence["mutation_tests"] = [
        "wrong period rejected",
        "sum instead of middle mean rejected",
        "bottom selecting top rejected",
    ]
    evidence["synthetic_calendar_fixture"] = {
        "max_date": "2023-05-15",
        "expected_month": 5,
        "expected_quarter": 9,
        "expected_year": 15,
        "status": "passed",
    }
    evidence["tie_policy"] = (
        "No ties in any actual period. Native end count=5 units=records; no explicit secondary key in author or replica. Synthetic cutoff review confirms why dense-rank<=5 differs; runtime tie choice pending."
    )
    evidence["acceptance_ids"] = [
        "latest-calendar-periods",
        "all-period-kpis",
        "dynamic-top-bottom-five",
        "middle-seven-average",
        "signed-labels-and-sorting",
        "kpi-action-contract",
        "ties-and-filter-order",
        "packaged-data-integrity",
    ]
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/local-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    for period, scenario in evidence["scenarios"].items():
        print(
            f"{period}: total={scenario['total']:.8f}; top={scenario['top']}; bottom={scenario['bottom']}; middle mean={scenario['bars']['Everyone Else']['value']:.8f}"
        )
    print(
        "PASS: 8 local acceptance contracts, 3 independent numerical scenarios, 3 defect mutations. Desktop/live interactions/visual acceptance PENDING."
    )


if __name__ == "__main__":
    main()
