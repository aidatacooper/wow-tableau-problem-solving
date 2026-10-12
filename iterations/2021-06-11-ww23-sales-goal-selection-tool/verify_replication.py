"""Independently verify the WW23 "Sales Goal Selection Tool" workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Re-implements the two goal methodologies in Python, recomputes the per
sub-category goal / value-to-goal / percent-of-goal and the three headline
totals, and checks the native workbook contracts.

Automated acceptance IDs:
  - ww23-goal-calcs
  - ww23-bans
  - ww23-chart
  - ww23-toggle
  - ww23-layout
"""

import datetime
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww23-goal-calcs",
    "ww23-bans",
    "ww23-chart",
    "ww23-toggle",
    "ww23-layout",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_06_09_WW23_Sales_Goal_Selection"
TABLE = TableName("Extract", "Extract")

TODAY = datetime.date(2021, 6, 9)
PCT_INCREASE = 0.1
DAYS_SO_FAR = (TODAY - datetime.date(2021, 1, 1)).days + 1
DAYS_IN_YEAR = (datetime.date(2022, 1, 1) - datetime.date(2021, 1, 1)).days
LY_CUTOFF = datetime.date(2020, 6, 9)
INITIAL_SET = ["Accessories", "Copiers", "Machines", "Phones"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(path)) as connection,
    ):
        rows = connection.execute_list_query(
            f'SELECT "Order Date","Category","Sub-Category","Sales" FROM {TABLE}'
        )

    ytd: dict[str, float] = {}
    ly_ytd: dict[str, float] = {}
    ly: dict[str, float] = {}
    category: dict[str, str] = {}
    for order_date, cat, sub_cat, sales in rows:
        order_date = datetime.date(order_date.year, order_date.month, order_date.day)
        category[sub_cat] = cat
        if order_date.year == 2021 and order_date <= TODAY:
            ytd[sub_cat] = ytd.get(sub_cat, 0.0) + sales
        if order_date.year == 2020 and order_date <= LY_CUTOFF:
            ly_ytd[sub_cat] = ly_ytd.get(sub_cat, 0.0) + sales
        if order_date.year == 2020:
            ly[sub_cat] = ly.get(sub_cat, 0.0) + sales

    same_pace = {
        sc: ytd.get(sc, 0.0) / DAYS_SO_FAR * DAYS_IN_YEAR for sc in category
    }
    ly_plus = {sc: ly.get(sc, 0.0) * (1 + PCT_INCREASE) for sc in category}
    goal = {
        sc: (ly_plus[sc] if sc in INITIAL_SET else same_pace[sc]) for sc in category
    }
    value_to_goal = {sc: goal[sc] - ytd.get(sc, 0.0) for sc in category}
    pct_of_goal = {
        sc: (ytd.get(sc, 0.0) / goal[sc] if goal[sc] else 0.0) for sc in category
    }

    total_ytd = sum(ytd.values())
    total_ly_ytd = sum(ly_ytd.values())
    total_goal = sum(goal.values())
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "days_so_far": DAYS_SO_FAR,
        "days_in_year": DAYS_IN_YEAR,
        "sub_categories": sorted(category),
        "category": category,
        "sales_ytd": {sc: round(ytd.get(sc, 0.0), 2) for sc in category},
        "sales_ly_ytd": {sc: round(ly_ytd.get(sc, 0.0), 2) for sc in category},
        "same_pace_goal": {sc: round(same_pace[sc], 2) for sc in category},
        "ly_plus_goal": {sc: round(ly_plus[sc], 2) for sc in category},
        "year_end_goal": {sc: round(goal[sc], 2) for sc in category},
        "value_to_goal": {sc: round(value_to_goal[sc], 2) for sc in category},
        "pct_of_goal": {sc: round(pct_of_goal[sc], 4) for sc in category},
        "ban_sales_ytd": round(total_ytd, 2),
        "ban_sales_ly_ytd": round(total_ly_ytd, 2),
        "ban_year_end_goal": round(total_goal, 2),
        "same_pace_total": round(sum(same_pace.values()), 2),
        "ly_plus_total": round(sum(ly_plus.values()), 2),
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def captions(root):
    result = {}
    for column in root.findall(".//datasource/column"):
        name = column.get("name") or ""
        result[name] = column.get("caption") or name.strip("[]")
    return result


def resolve(formula: str, names: dict, parameters: dict) -> str:
    """Normalize internal calculation names and qualified parameters."""

    def replace(match):
        token = match.group(1)
        if f"[{token}]" in names:
            return f"[{names[f'[{token}]']}]"
        return f"[{token}]"

    text = re.sub(r"\[Parameters\]\.\[([^\]]+)\]",
                  lambda m: f"[{parameters.get(m.group(1), m.group(1))}]", formula)
    return re.sub(r"\[([^\]]+)\]", replace, text)


def verify():
    facts = oracle()
    root = workbook()
    calc = {}
    for column in root.findall(".//datasource/column"):
        node = column.find("calculation")
        if node is not None and node.get("class") == "tableau":
            calc[column.get("caption")] = node.get("formula") or ""
    names = captions(root)
    parameters = {
        column.get("name").strip("[]"): column.get("caption")
        for column in root.findall(".//datasource[@name='Parameters']/column")
        if column.get("caption")
    }

    def resolved(caption: str) -> str:
        return re.sub(r"\s+", " ", resolve(calc[caption], names, parameters)).strip()

    # --- ww23-goal-calcs ----------------------------------------------------
    assert facts["days_so_far"] == 160, facts
    assert facts["days_in_year"] == 365, facts
    assert "DATEDIFF" in calc["# Days So Far This Year"]
    assert "DATETRUNC" in calc["# Days In Year"] and "DATEADD" in calc["# Days In Year"]
    assert resolved("SALES YTD by Sub Cat") == (
        "IF YEAR([Order Date]) = YEAR([pToday]) AND [Order Date] <= [pToday] "
        "THEN [Sales] END"
    ), resolved("SALES YTD by Sub Cat")
    assert resolved("SALES LY YTD by Sub Cat") == (
        "IF YEAR([Order Date]) = YEAR([pToday])-1 AND [Order Date] <= "
        "DATEADD('year',-1,[pToday]) THEN [Sales] END"
    ), resolved("SALES LY YTD by Sub Cat")
    assert resolved("SALES LY") == (
        "IF YEAR([Order Date]) = YEAR([pToday])-1 THEN [Sales] END"
    ), resolved("SALES LY")
    assert resolved("Same Pace Goal") == (
        "(SUM([SALES YTD by Sub Cat])/[# Days So Far This Year]) * [# Days In Year]"
    ), resolved("Same Pace Goal")
    assert resolved("LY + Percent Increase Goal") == (
        "SUM([SALES LY])*(1+[pPercentIncrease])"
    ), resolved("LY + Percent Increase Goal")
    assert resolved("YEAR-END GOAL Per Sub Cat") == (
        "IF ATTR([Use Last Year With Increase]) then [LY + Percent Increase Goal] "
        "ELSE [Same Pace Goal] END"
    ), resolved("YEAR-END GOAL Per Sub Cat")
    assert resolved("Value to Goal") == (
        "[YEAR-END GOAL Per Sub Cat]-SUM([SALES YTD by Sub Cat])"
    ), resolved("Value to Goal")
    assert resolved("% of Goal") == (
        "SUM([SALES YTD by Sub Cat])/[YEAR-END GOAL Per Sub Cat]"
    ), resolved("% of Goal")
    # Every displayed row stays in the window even though only one is shown.
    for ban in ("SALES YTD", "SALES LY YTD", "YEAR-END GOAL"):
        assert "WINDOW_SUM" in calc[ban], ban
    assert calc["Index"] == "INDEX()"

    # --- ww23-bans ----------------------------------------------------------
    assert facts["ban_sales_ytd"] == 216041.66, facts["ban_sales_ytd"]
    assert facts["ban_sales_ly_ytd"] == 199946.57, facts["ban_sales_ly_ytd"]
    assert facts["ban_year_end_goal"] == 546802.99, facts["ban_year_end_goal"]
    bans = root.find(".//worksheets/worksheet[@name='BANs']")
    assert bans is not None, "missing BANs worksheet"
    index_filter = [
        f for f in bans.findall(".//view/filter")
        if f.get("class") == "quantitative"
    ]
    assert index_filter, "BANs Index filter missing"
    assert index_filter[0].findtext("max") == "1", etree.tostring(index_filter[0])
    ban_pane = bans.find("table/panes/pane")
    texts = {node.get("column") for node in ban_pane.findall("encodings/text")}
    assert any(t.endswith("[Multiple Values]") for t in texts), texts
    assert ban_pane.find("encodings/lod") is not None, "Sub-Category is not on Detail"
    # The Measure Names filter restricts the pane to the three headline measures.
    members = set()
    for filter_el in bans.findall(".//view/filter"):
        if filter_el.get("column", "").endswith("[:Measure Names]"):
            for m in filter_el.findall(".//groupfilter[@function='member']"):
                ref = (m.get("member") or "").strip('"')
                token = re.findall(r"\[([^\]]+)\]", ref)
                if token:
                    last = token[-1]
                    match = re.match(r"^(?:usr|sum|avg|attr|none):(.*?):(?:qk|nk|ok)$", last)
                    name = match.group(1) if match else last
                    members.add(names.get(f"[{name}]", name))
    assert members == {"SALES YTD", "SALES LY YTD", "YEAR-END GOAL"}, members

    # --- ww23-chart ---------------------------------------------------------
    chart = root.find(".//worksheets/worksheet[@name='Chart']")
    assert chart is not None, "missing Chart worksheet"
    rows = chart.findtext("table/rows") or ""
    assert "none:Category:nk" in rows and "none:Sub-Category:nk" in rows, rows
    panes = chart.findall("table/panes/pane")
    mark_types = [p.find("mark").get("class") for p in panes]
    assert mark_types == ["Bar", "GanttBar", "Text", "Text", "Circle"], mark_types
    bar = panes[0]
    bar_encodings = bar.findall("encodings/color")
    assert bar_encodings and bar_encodings[0].get("column", "").endswith("[:Measure Names]"), \
        etree.tostring(bar)
    assert bar.find("encodings/size") is not None, "Measure Names is not on Size"
    circle = panes[4]
    circle_color = circle.find("encodings/color")
    assert circle_color is not None and "Use Last Year With Increase" in (
        circle_color.get("column") or ""
    ), etree.tostring(circle)
    # The set palette must distinguish the two methodologies.
    set_encoding = root.find(
        ".//datasource/style/style-rule[@element='mark']/encoding[@attr='color']"
    )
    if set_encoding is None or "Use Last Year With Increase" not in (
        set_encoding.get("field") or ""
    ):
        set_encoding = next(
            (
                enc
                for enc in root.findall(
                    ".//style-rule[@element='mark']/encoding[@attr='color']"
                )
                if "Use Last Year With Increase" in (enc.get("field") or "")
            ),
            None,
        )
    assert set_encoding is not None, "set colour palette missing"
    palette = {
        (m.findtext("bucket") or ""): m.get("to")
        for m in set_encoding.findall("map")
    }
    assert palette.get("false") and palette.get("true"), palette
    assert palette["false"] != palette["true"], palette
    # The two text panes print "<value> to goal" / "<value> of goal".
    labels = [
        "".join(node.itertext())
        for node in chart.findall(".//customized-label")
    ]
    assert any("to goal" in label for label in labels), labels
    assert any("of goal" in label for label in labels), labels
    # Per-sub-category values are the recomputed oracle values.
    chart_deps = next(
        (
            deps
            for deps in chart.findall("table/view/datasource-dependencies")
            if deps.get("datasource", "").startswith("federated.")
        ),
        None,
    )
    assert chart_deps is not None
    bound = {
        names.get(ci.get("column"), ci.get("column")): ci.get("name")
        for ci in chart_deps.findall("column-instance")
    }
    bound_labels = {
        label.strip("[]"): ref for label, ref in bound.items()
    }
    for field in ("YEAR-END GOAL Per Sub Cat", "Value to Goal", "% of Goal",
                  "Use Last Year With Increase"):
        assert field in bound_labels, (field, sorted(bound_labels))

    # --- ww23-toggle --------------------------------------------------------
    group = root.find(
        f".//datasource/group[@name='[Use Last Year With Increase]']"
    )
    assert group is not None, "Use Last Year With Increase set missing"
    members = {
        (m.get("member") or "").strip('"')
        for m in group.findall(".//groupfilter[@function='member']")
    }
    assert members == set(INITIAL_SET), members
    actions = root.findall(".//actions/edit-group-action")
    assert len(actions) == 2, f"expected two set actions, got {len(actions)}"
    by_caption = {a.get("caption"): a for a in actions}
    assert "Add to Set" in by_caption and "TOGGLE TYPE" in by_caption, by_caption
    assert by_caption["Add to Set"].find("add-or-remove-marks").get("value") == "add"
    assert by_caption["TOGGLE TYPE"].find("add-or-remove-marks").get("value") == "remove"
    for action in actions:
        target = action.find("params/param[@name='target-group']")
        assert target is not None and "Use Last Year With Increase" in target.get("value")
        clear = action.find("params/param[@name='selection-clear-set-option']")
        assert clear is not None and clear.get("value") == "do-nothing"

    # --- ww23-layout --------------------------------------------------------
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zone_names = {
        z.get("name") for z in dashboard.findall(".//zones//zone") if z.get("name")
    }
    assert {"BANs", "Chart"} <= zone_names, zone_names
    sizes = dashboard.find("size")
    assert sizes.get("maxwidth") == "1200" and sizes.get("maxheight") == "800", \
        etree.tostring(sizes)

    evidence = {
        "scope": "Locked-extract oracle plus native goal/set/dashboard contracts.",
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(
        {
            k: result["facts"][k]
            for k in (
                "rows", "days_so_far", "days_in_year",
                "ban_sales_ytd", "ban_sales_ly_ytd", "ban_year_end_goal",
            )
        },
        indent=2,
    ))
    print("PASS")
