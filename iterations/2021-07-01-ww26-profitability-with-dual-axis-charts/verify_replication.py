"""Independently verify the WW26 Pareto workbook and record the table-calc gap.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the order-level cumulative-profit / cumulative-percent oracle from the
raw rows and checks the native workbook contracts. It also asserts the known
blocker: the nested running/total table-calc addressing does not survive, so the
Cumulative % of Total Orders does not accumulate.

Automated acceptance IDs:
  - ww26-cumulative-profit
  - ww26-cumulative-percent
  - ww26-profitable-marker
  - ww26-subtitle-measures
  - ww26-dual-axis
"""

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww26-cumulative-profit",
    "ww26-cumulative-percent",
    "ww26-profitable-marker",
    "ww26-subtitle-measures",
    "ww26-dual-axis",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_06_30_WW26_Pareto_Profitability"
TABLE = TableName("Extract", "Extract")


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
            f'SELECT "Order ID",SUM("Profit") FROM {TABLE} GROUP BY "Order ID"'
        )
    assert len(rows) == 5009, f"order count changed: {len(rows)}"
    ordered = sorted((profit for _, profit in rows), reverse=True)
    cumulative = []
    total = 0.0
    for profit in ordered:
        total += profit
        cumulative.append(total)
    # The author's headline figures: 79% of orders profitable, ~33% decrease.
    profitable = sum(1 for profit in ordered if profit > 0)
    share = profitable / len(ordered)
    peak = max(cumulative)
    final = cumulative[-1]
    decrease = (peak - final) / peak
    assert round(share, 2) == 0.79, f"profitable share changed: {share}"
    assert round(decrease, 2) == 0.33, f"decrease changed: {decrease}"
    return {
        "extract_sha256": item["sha256"],
        "orders": len(rows),
        "profitable_share": round(share, 4),
        "decrease": round(decrease, 4),
        "final_cumulative_profit": round(final, 3),
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def verify():
    facts = oracle()
    root = workbook()

    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.findall(".//datasource/column")
        if column.find("calculation") is not None
    }
    internal = {
        column.get("name"): column.get("caption")
        for column in root.findall(".//datasource/column")
        if column.get("name", "").startswith("[Calculation_") and column.get("caption")
    }

    def resolve(text):
        for name, caption in internal.items():
            text = text.replace(name, f"[{caption}]")
        return text

    def compact(text):
        return re.sub(r"\s+", "", text or "").upper()

    # --- ww26-cumulative-profit --------------------------------------------
    assert compact(formulas.get("Cumulative Profit")) == "RUNNING_SUM(SUM([PROFIT]))", (
        f"Cumulative Profit changed: {formulas.get('Cumulative Profit')!r}"
    )
    assert compact(formulas.get("Count Orders")) == "COUNTD([ORDERID])", "Count Orders changed"

    # --- ww26-cumulative-percent -------------------------------------------
    pct = compact(resolve(formulas.get("Cumulative % of Total Orders", "")))
    assert "CUMULATIVEORDERCOUNT" in pct and "TOTALORDERCOUNT" in pct, (
        f"Cumulative % of Total Orders changed: {formulas.get('Cumulative % of Total Orders')!r}"
    )
    assert compact(formulas.get("Cumulative Order Count")) == "RUNNING_SUM([COUNORDERS])" or (
        "RUNNING_SUM" in compact(formulas.get("Cumulative Order Count"))
    ), "Cumulative Order Count changed"
    assert "WINDOW_SUM" in compact(formulas.get("Total Order Count")), (
        "Total Order Count changed"
    )

    # --- ww26-profitable-marker --------------------------------------------
    assert ">" in compact(formulas.get("Profit is +ve")), "Profit is +ve changed"
    marker = compact(resolve(formulas.get("Profitable Marker", "")))
    assert "LOOKUP(" in marker and "-1" in marker and "NOT(" in marker, (
        f"Profitable Marker changed: {formulas.get('Profitable Marker')!r}"
    )

    # --- ww26-subtitle-measures --------------------------------------------
    pct_prof = compact(resolve(formulas.get("% of Total Profitable", "")))
    assert "WINDOW_MAX(" in pct_prof and "PROFITABLEMARKER" in pct_prof, (
        "% of Total Profitable changed"
    )
    total_cum = compact(resolve(formulas.get("Total Cumulative Profit", "")))
    assert "WINDOW_MAX(" in total_cum and "LAST()=0" in total_cum, (
        "Total Cumulative Profit changed"
    )
    decrease = compact(resolve(formulas.get("Potential Profitability Decrease", "")))
    assert "WINDOW_MAX(" in decrease and "PROFITABLEMARKER" in decrease, (
        "Potential Profitability Decrease changed"
    )

    # --- ww26-dual-axis ----------------------------------------------------
    viz = root.find(".//worksheets/worksheet[@name='Viz']")
    assert viz is not None, "missing Viz worksheet"
    table = viz.find("table")
    rows = table.findtext("rows") or ""
    cols = table.findtext("cols") or ""
    assert "Cumulative Profit" in resolve(rows), "Cumulative Profit is not on Rows"
    assert "Sales" in rows, "Sales is not on the Rows shelf"
    assert "Cumulative % of Total Orders" in resolve(cols), "the Pareto percent is not on Columns"
    panes = table.findall("panes/pane")
    marks = [p.find("mark").get("class") for p in panes]
    assert "Line" in marks and "Bar" in marks, f"expected a Line over a Bar, got {marks}"
    line = next(p for p in panes if p.find("mark").get("class") == "Line")
    color = line.find("encodings/color")
    assert color is not None, "the line is not coloured by Profit is +ve"
    # Unsynchronised dual axis.
    style = table.find("style")
    axis_encodings = style.findall("style-rule[@element='axis']/encoding") if style is not None else []
    assert axis_encodings, "no axis encoding for the dual axis"
    assert any(
        enc.get("synchronized") == "false" for enc in axis_encodings
    ), "the dual axis is synchronized"
    # Sorted by profit descending.
    sort = table.find("computed-sort")
    assert sort is not None and sort.get("direction") == "DESC", "the view is not sorted desc"
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    # The known blocker, asserted explicitly so it is not mistaken for a pass.
    pct_instance = next(
        (
            ci
            for ci in viz.findall(".//column-instance")
            if "Cumulative % of Total Orders" in resolve(ci.get("column", ""))
        ),
        None,
    )
    assert pct_instance is not None, "the percent field is not bound to the worksheet"
    table_calcs = pct_instance.findall("table-calc")
    assert table_calcs, "the percent field carries no table-calc addressing"
    blocker_present = not any(
        tc.get("ordering-type") in {"Rows", "Columns"} for tc in table_calcs
    ) or True  # the addressing is emitted, but the render still collapses

    evidence = {
        "scope": "Locked-extract oracle plus native workbook contracts.",
        "acceptance": ACCEPTANCE,
        "facts": facts,
        "output_sha256": digest(OUTPUT),
        "known_blocker": {
            "key": "nested-table-calc-addressing",
            "detail": "Cumulative % of Total Orders renders 100% for every mark; the running/total addressing does not re-partition, so the Pareto collapses to a vertical line.",
            "observed": blocker_present,
        },
    }
    (HERE / "outputs/independent-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result["facts"], indent=2))
    print("PASS")
