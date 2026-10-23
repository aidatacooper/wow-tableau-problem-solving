"""Independently verify the WW31 needle-in-the-haystack workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the top-50 / unprofitable / below-average-customer-count
intersection from the raw rows and checks the native workbook contracts.

Automated acceptance IDs:
  - ww31-filter-field
  - ww31-top50-set
  - ww31-unprofitable-set
  - ww31-customer-average
  - ww31-thirteen-products
  - ww31-chart-layout
  - ww31-dashboard
"""

import collections
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww31-filter-field",
    "ww31-top50-set",
    "ww31-unprofitable-set",
    "ww31-customer-average",
    "ww31-thirteen-products",
    "ww31-chart-layout",
    "ww31-dashboard",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_08_04_WW31_Unprofitable_High_Sales"
TABLE = TableName("Extract", "Extract")
TOP_N = 50
EXPECTED_ANSWER_COUNT = 13

EXPECTED = {
    "Cisco TelePresence System EX90 Videoconferencing Unit",
    "GBC DocuBind P400 Electric Binding System",
    "High Speed Automatic Electric Letter Opener",
    "Lexmark MX611dhe Monochrome Laser Printer",
    "Martin Yale Chadless Opener Electric Letter Opener",
    "Riverside Palais Royal Lawyers Bookcase, Royale Cherry Finish",
    "Bretford Rectangular Conference Table Tops",
    "Cubify CubeX 3D Printer Double Head Print",
    "Chromcraft Bull-Nose Wood Oval Conference Tables & Bases",
    "Bush Advantage Collection Racetrack Conference Table",
    "Tennsco Single-Tier Lockers",
    "Chromcraft Round Conference Tables",
    "Cubify CubeX 3D Printer Triple Head Print",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute every WW31 measure straight from the locked extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            f'SELECT "Product Name","Customer ID","Sales","Profit" FROM {TABLE}'
        )
    assert len(rows) == 9994, "row count changed"

    sales = collections.defaultdict(float)
    profit = collections.defaultdict(float)
    customers = collections.defaultdict(set)
    for product, customer, value, margin in rows:
        sales[product] += value
        profit[product] += margin
        customers[product].add(customer)

    products = len(sales)
    counts = {name: len(ids) for name, ids in customers.items()}
    average = sum(counts.values()) / products
    top = {
        name
        for name, _ in sorted(sales.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]
    }
    unprofitable = {name for name, value in profit.items() if value < 0}
    answer = top & unprofitable
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "products": products,
        "average_customers": round(average, 6),
        "top50": top,
        "unprofitable": unprofitable,
        "answer": answer,
        "below_average": {name for name in answer if counts[name] < average},
        "sales": {name: round(sales[name], 2) for name in answer},
        "profit": {name: round(profit[name], 2) for name in answer},
        "customer_counts": {name: counts[name] for name in answer},
        "top50_threshold": round(sorted(sales.values(), reverse=True)[TOP_N - 1], 2),
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root):
    """Map display name -> (datatype, role, formula) for datasource columns."""
    result = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is None:
            continue
        key = column.get("caption") or column.get("name", "").strip("[]")
        result[key] = (
            column.get("datatype"),
            column.get("role"),
            (calc.get("formula") or "").replace("&gt;", ">").replace("&lt;", "<"),
        )
    return result


def sets(root):
    """Map caption -> the datasource <group> element that defines a set."""
    found = {}
    for group in root.findall(".//datasource/group"):
        caption = group.get("caption") or group.get("name", "").strip("[]")
        found[caption] = group
    return found


def normalize(formula, mapping):
    """Rewrite generated calculation names back to display names."""
    text = formula
    for local, display in mapping.items():
        text = text.replace(local, f"[{display}]")
    return re.sub(r"\s+", " ", text).strip()


def check_filter_field(root, facts):
    """The brief allows exactly one filter field, and it is the intersection."""
    view = root.find(".//worksheet/table/view")
    assert view is not None, "Chart worksheet has no view"
    filters = view.findall("filter")
    assert len(filters) == 1, f"expected 1 filter, found {len(filters)}"
    (only,) = filters
    assert only.get("class") == "categorical", "the single filter must be categorical"
    column = only.get("column", "")
    assert "Products to Include" in column or "Calculation_" in column, column
    groups = only.findall("groupfilter")
    assert groups, "filter has no groupfilter"
    members = [g.get("member") for g in groups]
    assert members == ["true"], f"filter must keep the true members, got {members}"
    slices = view.findall("slices/column")
    assert [node.text for node in slices] == [column], "the single filter must be the only slice"
    return {
        "filters": len(filters),
        "column": column,
        "members": members,
    }


def check_top50_set(root):
    """Top 50 is a native set ranked by SUM(Sales) over Product Name."""
    groups = sets(root)
    assert "Top 50 Sales by Product" in groups, sorted(groups)
    group = groups["Top 50 Sales by Product"]
    end = group.find("groupfilter")
    assert end is not None and end.get("function") == "end", "top-N set needs an end filter"
    assert end.get("count") == str(TOP_N), end.get("count")
    assert end.get("end") == "top", end.get("end")
    assert end.get("units") == "records", end.get("units")
    order = end.find("groupfilter")
    assert order is not None and order.get("function") == "order", "missing order filter"
    assert order.get("direction") == "DESC", order.get("direction")
    expression = re.sub(r"\s+", "", order.get("expression", "")).upper()
    assert expression in {"SUM([SALES])", "SUM(SALES)"}, expression
    level = order.find("groupfilter")
    assert level is not None and level.get("function") == "level-members"
    assert level.get("level", "").strip("[]") == "Product Name", level.get("level")
    return {
        "caption": group.get("caption"),
        "count": end.get("count"),
        "expression": order.get("expression"),
        "level": level.get("level"),
    }


def unescape_member(literal: str) -> str:
    """Decode a Tableau set member literal (``"a\\"b"``) back to its value."""
    text = literal.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    out = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            out.append(text[index + 1])
            index += 2
            continue
        out.append(char)
        index += 1
    return "".join(out)


def check_unprofitable_set(root, facts):
    """The unprofitable set members equal the independently computed list."""
    groups = sets(root)
    assert "Unprofitable Products" in groups, sorted(groups)
    group = groups["Unprofitable Products"]
    members = {
        unescape_member(node.get("member", ""))
        for node in group.iter("groupfilter")
        if node.get("function") == "member"
    }
    assert members == facts["unprofitable"], (
        f"set drift: missing={sorted(facts['unprofitable'] - members)[:5]} "
        f"extra={sorted(members - facts['unprofitable'])[:5]}"
    )
    levels = {
        node.get("level", "")
        for node in group.iter("groupfilter")
        if node.get("function") in {"member", "level-members"}
    }
    assert levels == {"[Product Name]"}, levels
    return {"members": len(members), "levels": sorted(levels)}


def check_customer_average(root, facts):
    """The FIXED LoD chain matches the article, including the count of products."""
    calcs = formulas(root)
    mapping = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name")
        caption = column.get("caption")
        if name and caption:
            mapping[name] = caption
    expected = {
        "Customer Count Per Product": "{FIXED [Product Name] : COUNTD([Customer ID])}",
        "Count Products": "{FIXED : COUNTD([Product Name])}",
        "Avg Overall Customer Count": (
            "{FIXED: SUM([Customer Count Per Product])} / [Count Products]"
        ),
        "Higher than Avg Customer Count": (
            "AVG([Customer Count Per Product]) > SUM([Avg Overall Customer Count])"
        ),
    }
    seen = {}
    for name, want in expected.items():
        assert name in calcs, f"missing calculation '{name}'"
        datatype, role, formula = calcs[name]
        got = normalize(formula, mapping)
        assert got == want, f"{name}: {got!r} != {want!r}"
        seen[name] = {"datatype": datatype, "role": role, "formula": got}
    assert calcs["Customer Count Per Product"][0] == "integer"
    assert calcs["Count Products"][0] == "integer"
    assert calcs["Higher than Avg Customer Count"][0] == "boolean"
    # The average must reproduce the extract's own value.
    assert abs(facts["average_customers"] - 5.37642) < 1e-5, facts["average_customers"]
    return {"calculations": seen, "average_customers": facts["average_customers"]}


def check_thirteen_products(root, facts):
    """The boolean intersection resolves to the 13 products in the oracle."""
    assert facts["answer"] == EXPECTED, (
        f"oracle drift: missing={sorted(EXPECTED - facts['answer'])} "
        f"extra={sorted(facts['answer'] - EXPECTED)}"
    )
    assert len(facts["answer"]) == EXPECTED_ANSWER_COUNT
    calcs = formulas(root)
    assert "Products to Include" in calcs, "the intersection field is missing"
    datatype, role, formula = calcs["Products to Include"]
    assert datatype == "boolean", datatype
    assert role == "dimension", role
    terms = {token.strip() for token in formula.split(" AND ")}
    assert terms == {"[Top 50 Sales by Product]", "[Unprofitable Products]"}, terms
    return {
        "products": len(facts["answer"]),
        "formula": formula,
        "below_average": len(facts["below_average"]),
        "sales": facts["sales"],
        "profit": facts["profit"],
        "customer_counts": facts["customer_counts"],
    }


def local_captions(root):
    """Map a generated local column name to its display caption."""
    mapping = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name")
        if not name:
            continue
        mapping[name] = column.get("caption") or name.strip("[]")
    return mapping


def display_shelf(text: str, mapping, instances) -> str:
    """Replace generated instance/local names in a shelf expression with captions."""
    result = text
    for instance, caption in instances.items():
        result = result.replace(instance, f"[{caption}]")
    for local, caption in mapping.items():
        result = result.replace(local, f"[{caption}]")
    return result


def local_instances(root):
    """Map every generated column-instance name to its field caption."""
    captions = local_captions(root)
    mapping = {}
    for node in root.findall(".//column-instance"):
        instance = node.get("name")
        column = node.get("column")
        if instance and column in captions:
            mapping[instance] = captions[column]
    return mapping


def check_chart_layout(root):
    """Product Name on Rows; MIN(1) then SUM(Sales) on Columns with two panes."""
    worksheet = root.find(".//worksheet[@name='Chart']")
    assert worksheet is not None, "missing Chart worksheet"
    table = worksheet.find("table")
    mapping = local_captions(root)
    instances = local_instances(root)
    rows = display_shelf((table.findtext("rows") or "").strip(), mapping, instances)
    cols = display_shelf((table.findtext("cols") or "").strip(), mapping, instances)
    assert "Product Name" in rows, rows
    assert "MIN(1)" in cols and "Sales" in cols, cols
    # The label pane must come first so its text sits left of the sales bar.
    assert cols.index("MIN(1)") < cols.index("Sales"), cols
    panes = table.findall("panes/pane")
    assert len(panes) == 2, f"expected 2 panes, got {len(panes)}"
    label_pane, bar_pane = panes
    label_marks = [node.get("column", "") for node in label_pane.findall("encodings/text")]
    assert any("Product Name" in ref for ref in label_marks), label_marks
    assert any("Sub-Category" in ref for ref in label_marks), label_marks
    assert any("Category" in ref for ref in label_marks), label_marks
    assert label_pane.find("mark").get("class") == "Bar"
    bar_marks = [node.get("column", "") for node in bar_pane.findall("encodings/color")]
    assert bar_marks, "the sales pane must colour by the customer-count flag"
    assert "Calculation_" in bar_marks[0]
    axis = table.find("style/style-rule[@element='axis']")
    assert axis is not None, "chart has no axis style rule"
    fixed = [
        node
        for node in axis.findall("encoding")
        if node.get("range-type") == "fixed" and node.get("max") == "2"
    ]
    assert fixed, "the MIN(1) axis must be pinned to a fixed 0..2 range"
    return {"rows": rows, "cols": cols, "panes": len(panes)}


def check_dashboard(root):
    """The dashboard is the required 800x650 and hosts the Chart sheet."""
    dashboard = root.find(f".//dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, f"missing dashboard {DASHBOARD_NAME}"
    size = dashboard.find("size")
    assert size is not None
    assert (size.get("minwidth"), size.get("minheight")) == ("800", "650")
    assert (size.get("maxwidth"), size.get("maxheight")) == ("800", "650")
    zones = dashboard.findall(".//zone[@name='Chart']")
    assert zones, "the dashboard must place the Chart worksheet"
    window = root.find(f".//window[@class='dashboard'][@name='{DASHBOARD_NAME}']")
    assert window is not None, "the dashboard window is missing"
    viewpoint = window.find("viewpoints/viewpoint[@name='Chart']")
    assert viewpoint is not None, "the Chart viewpoint is missing"
    return {"size": "800x650", "zones": len(zones)}


CHECKS = {
    "ww31-filter-field": lambda root, facts: check_filter_field(root, facts),
    "ww31-top50-set": lambda root, facts: check_top50_set(root),
    "ww31-unprofitable-set": lambda root, facts: check_unprofitable_set(root, facts),
    "ww31-customer-average": lambda root, facts: check_customer_average(root, facts),
    "ww31-thirteen-products": lambda root, facts: check_thirteen_products(root, facts),
    "ww31-chart-layout": lambda root, facts: check_chart_layout(root),
    "ww31-dashboard": lambda root, facts: check_dashboard(root),
}


def main():
    facts = oracle()
    root = workbook()
    results = {}
    for name in ACCEPTANCE:
        detail = CHECKS[name](root, facts)
        results[name] = {"status": "pass", "detail": detail}
        print(f"PASS {name}")
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    payload = {
        "case_id": "wow-2021-ww31-can-you-find-the-needle-in-the-haystack",
        "workbook_sha256": digest(OUTPUT),
        "extract_sha256": facts["extract_sha256"],
        "oracle": {
            "rows": facts["rows"],
            "products": facts["products"],
            "average_customers": facts["average_customers"],
            "top50_threshold": facts["top50_threshold"],
            "unprofitable_products": len(facts["unprofitable"]),
            "answer": sorted(facts["answer"]),
            "below_average_in_answer": sorted(facts["below_average"]),
        },
        "acceptance": results,
    }
    (evidence / "functional-verification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {evidence / 'functional-verification.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
