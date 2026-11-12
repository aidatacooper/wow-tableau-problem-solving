"""Verify the WW50 drill-down workbook and its click-path semantics.

The check has three independent legs:

* the emitted XML declares the required parameters, calculations, shelves,
  filter, dashboard and parameter actions;
* the click path is simulated from the two emitted calculations, including the
  hard part of the challenge: selecting another Category clears the previous
  Sub-Category;
* an independent SQLite oracle over the packaged extract reproduces every
  monthly line-chart scope and the bar-chart totals.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile
import zipfile

from lxml import etree as E
from tableauhyperapi import Connection, HyperProcess, Telemetry


HERE = Path(__file__).resolve().parent
WORKBOOK = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD = "2021 Week 50 - Drill Down"
BAR = "Bar Chart"
LINE = "Line"

EXPECTED_FORMULAS = {
    "Sub Cat Display": 'IF [pSelectedCategory]=[Category] THEN [Sub-Category] ELSE "" END',
    "FILTER": '([pSelectedCategory]="") OR '
    '([pSelectedCategory]=[Category] AND [pSelectedSubCat]="") OR '
    '([pSelectedCategory]=[Category] AND [pSelectedSubCat]=[Sub-Category])',
    "Colour:Line": "[pSelectedCategory]",
    "TOOLTIP:Category": 'IF [pSelectedCategory]="" THEN "All" ELSE [pSelectedCategory] END',
    "TOOLTIP:SubCat": 'IF [pSelectedSubCat]="" THEN "All" ELSE [pSelectedSubCat] END',
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def load_root():
    with zipfile.ZipFile(WORKBOOK) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return E.fromstring(archive.read(name))


def main_datasource(root):
    for datasource in root.findall("datasources/datasource"):
        if datasource.find(".//connection[@class='hyper']") is not None:
            return datasource
    raise AssertionError("packaged Hyper datasource is missing")


def parameters(root):
    ds = root.find("datasources/datasource[@name='Parameters']")
    require(ds is not None, "Parameters datasource is missing")
    return {c.get("caption"): c for c in ds.findall("column") if c.get("caption")}


def instance_names(datasource, worksheet):
    dependencies = worksheet.find(
        f"table/view/datasource-dependencies[@datasource='{datasource.get('name')}']"
    )
    require(dependencies is not None, f"{worksheet.get('name')} has no datasource dependencies")
    return {ci.get("column"): ci.get("name") for ci in dependencies.findall("column-instance")}


def full(datasource, instance):
    return f"[{datasource.get('name')}].{instance}"


def normalize_formula(formula, params, columns):
    param_caption = {
        column.get("name", "").strip("[]"): caption
        for caption, column in params.items()
    }

    def replace_parameter(match):
        return f"[{param_caption.get(match.group(1), match.group(1))}]"

    text = re.sub(r"\[Parameters\]\.\[([^\]]+)\]", replace_parameter, formula)
    caption_by_name = {
        column.get("name", "").strip("[]"): (
            column.get("caption") or column.get("name", "").strip("[]")
        )
        for column in columns.values()
    }

    def replace_field(match):
        return f"[{caption_by_name.get(match.group(1), match.group(1))}]"

    return re.sub(r"\[([^\]]+)\]", replace_field, text)


def contracts(root):
    """Static contract for every automated acceptance scenario."""

    # acceptance: parameters
    params = parameters(root)
    require(set(params) == {"pSelectedCategory", "pSelectedSubCat"}, "exactly two selection parameters")
    for caption, column in params.items():
        require(column.get("datatype") == "string", f"{caption} must be a string parameter")
        require(column.get("value") == '""', f"{caption} must default to the empty string")
        require(column.get("param-domain-type") == "any", f"{caption} must accept any typed value")

    datasource = main_datasource(root)
    columns = {
        (c.get("caption") or c.get("name", "").strip("[]")): c
        for c in datasource.findall("column")
        if c.get("caption") or c.get("name")
    }

    # acceptance: drill-display, selection-filter
    for caption, expected in EXPECTED_FORMULAS.items():
        require(caption in columns, f"missing calculation {caption}")
        calculation = columns[caption].find("calculation")
        require(calculation is not None, f"{caption} is not calculated")
        actual = normalize_formula(calculation.get("formula", ""), params, columns)
        require(actual == expected, f"{caption} formula changed: {actual}")

    sheets = {ws.get("name"): ws for ws in root.findall("worksheets/worksheet")}
    require(set(sheets) == {BAR, LINE}, "exactly the two challenge worksheets")
    bar_instances = instance_names(datasource, sheets[BAR])
    line_instances = instance_names(datasource, sheets[LINE])
    for caption in ("Category", "Sub Cat Display", "Sales"):
        require(columns[caption].get("name") in bar_instances, f"bar field {caption} is unbound")
    for caption in ("Order Date", "Sales", "Colour:Line", "FILTER", "TOOLTIP:Category", "TOOLTIP:SubCat"):
        require(columns[caption].get("name") in line_instances, f"line field {caption} is unbound")

    # acceptance: bar-chart
    bar = sheets[BAR]
    bar_rows = bar.findtext("table/rows") or ""
    require(
        full(datasource, bar_instances[columns["Category"].get("name")]) in bar_rows
        and full(datasource, bar_instances[columns["Sub Cat Display"].get("name")]) in bar_rows,
        "bar chart must stack Category then Sub Cat Display on Rows",
    )
    require(
        full(datasource, bar_instances[columns["Sales"].get("name")]) in (bar.findtext("table/cols") or ""),
        "bar chart must put Sales on Columns",
    )
    bar_pane = bar.find("table/panes/pane")
    require(bar_pane.find("mark").get("class") == "Bar", "bar chart mark must be Bar")
    require(
        bar_pane.find("encodings/color").get("column")
        == full(datasource, bar_instances[columns["Category"].get("name")]),
        "bar colour must encode Category",
    )
    require(
        bar_pane.find("encodings/text").get("column")
        == full(datasource, bar_instances[columns["Sales"].get("name")]),
        "bar labels must show Sales",
    )
    sort = bar.find("table/view/shelf-sorts/shelf-sort-v2")
    require(sort is not None, "bar chart needs a descending shelf sort")
    require(sort.get("direction") == "DESC", "bar sort must be descending")
    require(
        sort.get("dimension-to-sort")
        == full(datasource, bar_instances[columns["Sub Cat Display"].get("name")]),
        "bar sort must address Sub Cat Display",
    )
    require(
        sort.get("measure-to-sort-by")
        == full(datasource, bar_instances[columns["Sales"].get("name")]),
        "bar sort must use Sales",
    )
    bar_style = bar.find("table/style")
    require(
        any(
            rule.get("element") == "axis"
            and any(f.get("attr") == "display" and f.get("value") == "false" for f in rule.findall("format"))
            for rule in bar_style.findall("style-rule")
        ),
        "bar axis must be hidden",
    )
    require(
        any(
            rule.get("element") == "worksheet"
            and any(
                f.get("attr") == "display-field-labels"
                and f.get("scope") == "rows"
                and f.get("value") == "false"
                for f in rule.findall("format")
            )
            for rule in bar_style.findall("style-rule")
        ),
        "bar row field labels must be hidden",
    )

    # acceptance: line-chart
    line = sheets[LINE]
    line_cols = line.findtext("table/cols") or ""
    require(
        full(datasource, line_instances[columns["Order Date"].get("name")]) in line_cols,
        "line chart must use continuous month-truncated Order Date",
    )
    require(
        full(datasource, line_instances[columns["Sales"].get("name")]) in (line.findtext("table/rows") or ""),
        "line chart must put Sales on Rows",
    )
    line_pane = line.find("table/panes/pane")
    require(line_pane.find("mark").get("class") == "Line", "line chart mark must be Line")
    require(
        line_pane.find("encodings/color").get("column")
        == full(datasource, line_instances[columns["Colour:Line"].get("name")]),
        "line colour must follow the selected Category parameter",
    )
    filters = line.findall("table/view/filter")
    require(len(filters) == 1, "line chart needs exactly one categorical filter")
    require(
        filters[0].get("column") == full(datasource, line_instances[columns["FILTER"].get("name")]),
        "line filter must bind the FILTER calculation",
    )
    require(filters[0].find("groupfilter").get("member") == "true", "line filter must keep FILTER = true")
    mark_formats = {
        f.get("attr"): f.get("value")
        for f in line_pane.findall("style/style-rule[@element='mark']/format")
    }
    require(mark_formats.get("mark-labels-mode") == "range", "line labels must use range mode")
    require(mark_formats.get("mark-labels-range-min") == "true", "line must label its minimum mark")
    require(mark_formats.get("mark-labels-range-max") == "true", "line must label its maximum mark")
    tooltip_columns = [e.get("column") for e in line_pane.findall("encodings/tooltip")]
    for caption in ("TOOLTIP:Category", "TOOLTIP:SubCat"):
        local_name = columns[caption].get("name", "").strip("[]")
        require(
            any(local_name in reference for reference in tooltip_columns),
            f"line tooltip must include {caption}",
        )

    # acceptance: dashboard-layout
    dashboards = root.findall("dashboards/dashboard")
    require(len(dashboards) == 1 and dashboards[0].get("name") == DASHBOARD, "one challenge dashboard")
    dashboard = dashboards[0]
    size = dashboard.find("size")
    require(
        size.get("maxwidth") == "500" and size.get("maxheight") == "600",
        "dashboard must be fixed at 500 x 600",
    )
    zones = dashboard.findall(".//zone")
    for name in (BAR, LINE):
        require(sum(z.get("name") == name for z in zones) == 1, f"dashboard must contain {name} once")
    require("Sales Drill Down" in "".join(dashboard.itertext()), "dashboard title is missing")

    # acceptance: parameter-actions
    actions = root.findall("actions/edit-parameter-action")
    require(len(actions) == 2, "exactly two parameter actions are required")
    targets = {}
    for action in actions:
        require(action.find("activation").get("type") == "on-select", "parameter action must fire on select")
        source = action.find("source")
        require(source.get("dashboard") == DASHBOARD and source.get("worksheet") == BAR, "action source")
        clear = action.find("clear-option")
        require(
            clear is not None
            and clear.get("type") == "assign-fixed-value"
            and clear.get("value") == "s:LROOT:",
            "clearing the click must reset the parameter to the empty string",
        )
        values = {p.get("name"): p.get("value") for p in action.findall("params/param")}
        targets[values["target-parameter"]] = values["source-field"]
    param_ref = {f"[Parameters].{column.get('name')}": caption for caption, column in params.items()}
    require(set(targets) == set(param_ref), "both parameters need an action")
    category_parameter = next(
        key for key, caption in param_ref.items() if caption == "pSelectedCategory"
    )
    subcategory_parameter = next(
        key for key, caption in param_ref.items() if caption == "pSelectedSubCat"
    )
    require(
        targets[category_parameter]
        == full(datasource, bar_instances[columns["Category"].get("name")]),
        "Category action must read the Category field",
    )
    require(
        targets[subcategory_parameter]
        == full(datasource, bar_instances[columns["Sub Cat Display"].get("name")]),
        "Sub Cat action must read the Sub Cat Display field",
    )
    return params, datasource, columns


def read_extract():
    with zipfile.ZipFile(WORKBOOK) as archive:
        hyper_name = next(n for n in archive.namelist() if n.lower().endswith(".hyper"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / Path(hyper_name).name
            path.write_bytes(archive.read(hyper_name))
            with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
                with Connection(process.endpoint, str(path)) as connection:
                    table = connection.catalog.get_table_names("Extract")[0]
                    rows = connection.execute_list_query(
                        f'SELECT "Order Date", "Category", "Sub-Category", "Sales" FROM {table}'
                    )
    require(len(rows) == 9994, "packaged extract must retain all 9,994 order lines")
    return rows


def subcat_display(category, subcategory, selected_category):
    return subcategory if selected_category == category else ""


def passes_filter(category, subcategory, selected_category, selected_subcategory):
    return (
        selected_category == ""
        or (selected_category == category and selected_subcategory == "")
        or (
            selected_category == category
            and selected_subcategory == subcategory
        )
    )


def monthly(rows):
    totals = {}
    for order_date, _category, _subcategory, sales in rows:
        key = (order_date.year, order_date.month)
        totals[key] = totals.get(key, 0.0) + float(sales)
    return totals


def close(left, right):
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=0.01)


def compare_scope(label, rows, selected_category, selected_subcategory, expected_sql):
    """Compare the emitted-formula scope with an independent SQL predicate."""
    selected = [
        row
        for row in rows
        if passes_filter(row[1], row[2], selected_category, selected_subcategory)
    ]
    database = sqlite3.connect(":memory:")
    database.execute("CREATE TABLE lines (ym TEXT, category TEXT, subcategory TEXT, sales REAL)")
    database.executemany(
        "INSERT INTO lines VALUES (?,?,?,?)",
        [
            (f"{row[0].year:04d}-{row[0].month:02d}", row[1], row[2], float(row[3]))
            for row in rows
        ],
    )
    expected_count, expected_sum = database.execute(
        f"SELECT COUNT(*), SUM(sales) FROM lines WHERE {expected_sql}"
    ).fetchone()
    expected_monthly = dict(
        database.execute(
            f"SELECT ym, SUM(sales) FROM lines WHERE {expected_sql} GROUP BY ym"
        ).fetchall()
    )
    database.close()

    actual_monthly = {
        f"{year:04d}-{month:02d}": value
        for (year, month), value in monthly(selected).items()
    }
    require(len(selected) == expected_count, f"{label}: line row scope count differs")
    require(
        close(sum(float(row[3]) for row in selected), expected_sum),
        f"{label}: line row scope sales differ",
    )
    require(set(actual_monthly) == set(expected_monthly), f"{label}: month domain differs")
    for month in expected_monthly:
        require(
            close(actual_monthly[month], expected_monthly[month]),
            f"{label}: monthly sales differ for {month}",
        )
    return {
        "rows": expected_count,
        "sales": round(expected_sum, 2),
        "months": len(expected_monthly),
        "monthly": {month: round(value, 2) for month, value in sorted(expected_monthly.items())},
    }


def data_oracle(rows):
    # acceptance: monthly-oracle, reset-semantics
    total = sum(float(row[3]) for row in rows)
    require(close(total, 2297200.86), "extract total sales changed")
    categories = {
        category: round(sum(float(row[3]) for row in rows if row[1] == category), 2)
        for category in sorted({row[1] for row in rows})
    }
    expected_categories = {
        "Furniture": 741999.7953,
        "Office Supplies": 719047.032,
        "Technology": 836154.033,
    }
    require(set(categories) == set(expected_categories), f"category domain changed: {categories}")
    for category, expected in expected_categories.items():
        require(
            close(categories[category], expected),
            f"category total changed for {category}: {categories[category]}",
        )

    states = {}
    states["default"] = compare_scope("default", rows, "", "", "1=1")
    states["category"] = compare_scope(
        "category", rows, "Furniture", "", "category = 'Furniture'"
    )
    states["subcategory"] = compare_scope(
        "subcategory",
        rows,
        "Furniture",
        "Bookcases",
        "category = 'Furniture' AND subcategory = 'Bookcases'",
    )
    states["reset"] = compare_scope(
        "reset", rows, "Technology", "", "category = 'Technology'"
    )

    # Simulate the actual parameter-action click path. The reset relies on
    # Sub Cat Display being blank for a Category that is not currently
    # selected: clicking Technology while Furniture/Bookcases is active writes
    # an empty Sub-Category in the same gesture.
    selected_category, selected_subcategory = "", ""
    selected_category, selected_subcategory = (
        "Furniture",
        subcat_display("Furniture", "", selected_category),
    )
    require(selected_subcategory == "", "clicking a collapsed Category must leave Sub-Category blank")
    selected_category, selected_subcategory = (
        selected_category,
        subcat_display("Furniture", "Bookcases", selected_category),
    )
    require(selected_subcategory == "Bookcases", "clicking a Sub-Category must set it")
    selected_category, selected_subcategory = (
        "Technology",
        subcat_display("Technology", "", selected_category),
    )
    require(
        (selected_category, selected_subcategory) == ("Technology", ""),
        "selecting another Category must clear the previous Sub-Category",
    )
    reset_rows = [
        row
        for row in rows
        if passes_filter(row[1], row[2], selected_category, selected_subcategory)
    ]
    require(len(reset_rows) == states["reset"]["rows"], "reset click path must show the new Category")
    require(
        close(sum(float(row[3]) for row in reset_rows), states["reset"]["sales"]),
        "reset click path must show the new Category sales",
    )
    return {
        "rows": len(rows),
        "total_sales": round(total, 2),
        "category_sales": categories,
        "states": states,
    }


def rejected(label, function):
    try:
        function()
    except AssertionError:
        return label
    raise AssertionError(f"mutation survived: {label}")


def mutations(root):
    killed = []

    def changed(label, mutate):
        mutant = deepcopy(root)
        mutate(mutant)
        killed.append(rejected(label, lambda: contracts(mutant)))

    def calculation(element, caption):
        return element.find(
            f"datasources/datasource/column[@caption='{caption}']/calculation"
        )

    changed(
        "subcat-display-always-on",
        lambda r: calculation(r, "Sub Cat Display").set(
            "formula", 'IF [Parameters].[Parameter 1]=[Category] THEN [Sub-Category] ELSE [Sub-Category] END'
        ),
    )
    changed(
        "filter-ignores-subcategory",
        lambda r: calculation(r, "FILTER").set(
            "formula",
            '([Parameters].[Parameter 1]="") OR ([Parameters].[Parameter 1]=[Category])',
        ),
    )
    changed(
        "line-filter-removed",
        lambda r: r.find("worksheets/worksheet[@name='Line']/table/view").remove(
            r.find("worksheets/worksheet[@name='Line']/table/view/filter")
        ),
    )
    changed(
        "action-does-not-clear",
        lambda r: r.find("actions/edit-parameter-action/clear-option").set(
            "type", "do-nothing"
        ),
    )
    changed(
        "wrong-action-source",
        lambda r: r.find("actions/edit-parameter-action/params/param[@name='source-field']").set(
            "value", "[missing].[none:Category:nk]"
        ),
    )
    changed(
        "bar-sort-ascending",
        lambda r: r.find("worksheets/worksheet[@name='Bar Chart']/table/view/shelf-sorts/shelf-sort-v2").set(
            "direction", "ASC"
        ),
    )
    changed(
        "line-uses-discrete-month",
        lambda r: setattr(
            r.find("worksheets/worksheet[@name='Line']/table/cols"),
            "text",
            r.findtext("worksheets/worksheet[@name='Line']/table/cols").replace(
                "tmn:Order Date:qk", "mn:Order Date:ok"
            ),
        ),
    )
    changed(
        "dashboard-wrong-size",
        lambda r: r.find("dashboards/dashboard/size").set("maxwidth", "800"),
    )
    return killed


def verify():
    require(WORKBOOK.is_file(), f"missing workbook: {WORKBOOK}")
    root = load_root()
    contracts(root)
    rows = read_extract()
    oracle = data_oracle(rows)
    killed = mutations(root)

    # acceptance: provenance
    provenance = json.loads((HERE / "outputs/build-provenance.json").read_text(encoding="utf-8"))
    digest = sha256(WORKBOOK.read_bytes()).hexdigest()
    require(provenance["workbook_sha256"] == digest, "build provenance must bind the current workbook")
    require(provenance["version"] == "0.29.0a2", "provenance must name the tested cwtwb release")

    report = {
        "workbook_sha256": digest,
        "sdk_version": provenance["version"],
        "raw_lines": oracle["rows"],
        "total_sales": oracle["total_sales"],
        "category_sales": oracle["category_sales"],
        "states": oracle["states"],
        "mutations_rejected": killed,
        "runtime_status": "Desktop load verified separately; Cloud REST states captured without browser interaction",
    }
    (HERE / "outputs/verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"PASS: {oracle['rows']} lines, {len(oracle['states'])} scopes, "
        f"{len(killed)} mutations rejected, SHA256 {digest}"
    )


if __name__ == "__main__":
    verify()
