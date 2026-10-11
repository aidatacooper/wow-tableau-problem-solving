"""Independently verify the WW12 Comparative Quantity Analysis workbook.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the per-Sub-Category average quantity inclusive of manufacturer
straight from the raw rows and checks the native workbook contracts that carry
the INCLUDE/EXCLUDE LoD solution chain, the parameter action and the
no-FIXED-LoD challenge constraint.

Automated acceptance IDs:
  - ww12-include-lod-average
  - ww12-exclude-lod-variance
  - ww12-parameter-action
  - ww12-no-fixed-lod
  - ww12-selected-color
"""

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww12-include-lod-average",
    "ww12-exclude-lod-variance",
    "ww12-parameter-action",
    "ww12-no-fixed-lod",
    "ww12-selected-color",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_03_24_WW12_Comparative_Qty"
PARAMETER = "pSelectedSubCat"
DEFAULT_SUBCAT = "Fasteners"
TABLE = TableName("Extract", "Extract")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute the raw quantity facts from the locked Hyper extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"

    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        query = lambda sql: connection.execute_list_query(sql)
        rows = query(f'SELECT COUNT(*) FROM {TABLE}')[0][0]
        assert rows == 9994, f"row count changed: {rows}"

        # The article's "Avg Qty" is SUM(Quantity)/COUNTD(Manufacturer); the LoD
        # route is AVG over the {INCLUDE [Manufacturer]: SUM(Quantity)} grain.
        # The two must agree for every Sub-Category, which is why the author's
        # two solutions produce the same picture.
        direct = {
            sub: Decimal(str(value))
            for sub, value in query(
                f'SELECT "Sub-Category", '
                f'SUM("Quantity")*1.0/COUNT(DISTINCT "Manufacturer") '
                f"FROM {TABLE} GROUP BY 1"
            )
        }
        lod = {
            sub: Decimal(str(value))
            for sub, value in query(
                f"SELECT s, AVG(qty) FROM ("
                f'SELECT "Sub-Category" s, "Manufacturer" m, SUM("Quantity") qty '
                f"FROM {TABLE} GROUP BY 1,2) GROUP BY 1"
            )
        }
        raw_mean = {
            sub: Decimal(str(value))
            for sub, value in query(
                f'SELECT "Sub-Category", AVG("Quantity") FROM {TABLE} GROUP BY 1'
            )
        }

    assert set(direct) == set(lod) and len(direct) == 17, "Sub-Category domain changed"
    for sub in direct:
        # Allow the tiny rounding difference between the two aggregation paths.
        assert abs(direct[sub] - lod[sub]) < Decimal("0.001"), (
            f"INCLUDE LoD disagrees with SUM/COUNTD for {sub}"
        )

    selected = lod[DEFAULT_SUBCAT]
    variance = {sub: value - selected for sub, value in lod.items()}

    # Every manufacturer's grain rows are grouped correctly: the LoD average is
    # the mean over manufacturers, not the mean over raw order rows.
    assert any(abs(lod[sub] - raw_mean[sub]) > Decimal("1") for sub in lod), (
        "INCLUDE grain collapsed to the raw row grain"
    )

    return {
        "extract_sha256": item["sha256"],
        "rows": rows,
        "subcategories": len(lod),
        "avg_qty": {sub: float(value) for sub, value in lod.items()},
        "selected": DEFAULT_SUBCAT,
        "selected_avg": float(selected),
        "variance": {sub: float(value) for sub, value in variance.items()},
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        root = etree.fromstring(archive.read(name))
    return root


def datasource(root):
    return next(
        node
        for node in root.findall("datasources/datasource")
        if node.get("name") != "Parameters"
    )


def verify():
    facts = oracle()
    root = workbook()

    ds = datasource(root)
    formulas = {}
    internal = {}
    for column in ds.findall("column"):
        caption = column.get("caption") or column.get("name", "").strip("[]")
        internal[caption] = column.get("name")
        calculation = column.find("calculation")
        if calculation is not None:
            formulas[caption] = calculation.get("formula") or ""

    def local(name):
        return str(name).strip("[]")

    # --- ww12-no-fixed-lod: the challenge forbids FIXED LoDs ---------------
    joined = " ".join(formulas.values())
    assert not re.search(r"\{\s*FIXED", joined, re.IGNORECASE), (
        "workbook uses a FIXED LoD, which the challenge forbids"
    )

    # --- ww12-include-lod-average ------------------------------------------
    include = formulas.get("Qty Inc Manufacturer", "")
    assert re.fullmatch(
        r"\{\s*INCLUDE\s*\[Manufacturer\]\s*:\s*SUM\(\[Quantity\]\)\s*\}",
        include,
    ), f"INCLUDE LoD changed: {include!r}"
    assert "AVG(" in formulas.get("Avg Qty Inc Manufacturer", ""), (
        "Avg Qty Inc Manufacturer must average the INCLUDE field"
    )

    # --- ww12-exclude-lod-variance -----------------------------------------
    exclude = formulas.get("Overall Selected Qty Inc Manufacturer", "")
    assert "{EXCLUDE" in exclude and "AVG(" in exclude, (
        f"EXCLUDE LoD changed: {exclude!r}"
    )
    assert "[Sub-Category]" in exclude, "EXCLUDE LoD must exclude Sub-Category"
    assert local(internal["Is Selected Sub Cat"]) in exclude, (
        "EXCLUDE LoD must exclude Is Selected Sub Cat"
    )
    assert "AVG(" in formulas.get("Variance", ""), "Variance must average the INCLUDE field"

    # The two panes sit side by side on the column axis with independent
    # domains, one bar per Sub-Category on the shared row axis.
    viz = root.find(".//worksheets/worksheet[@name='Viz']")
    assert viz is not None, "missing Viz worksheet"
    table = viz.find("table")
    rows = (table.findtext("rows") or "").strip()
    cols = (table.findtext("cols") or "").strip()
    assert local(internal["Sub-Category"]) in rows, "Sub-Category is not on the row axis"
    assert local(internal["Avg Qty Inc Manufacturer"]) in cols, "avg measure missing from columns"
    assert local(internal["Variance"]) in cols, "variance measure missing from columns"
    panes = table.findall("panes/pane")
    assert len(panes) == 2, f"expected two panes, found {len(panes)}"
    for pane in panes:
        assert pane.find("mark").get("class") == "Bar", "both panes must be bar marks"
    pane_axes = [pane.get("x-axis-name") for pane in panes]
    assert any(local(internal["Avg Qty Inc Manufacturer"]) in (axis or "") for axis in pane_axes), (
        "avg pane axis missing"
    )
    assert any(local(internal["Variance"]) in (axis or "") for axis in pane_axes), (
        "variance pane axis missing"
    )

    # --- ww12-selected-color -----------------------------------------------
    # The Avg pane colours by the boolean Is Selected Sub Cat field and the
    # datasource palette distinguishes selected from unselected.
    avg_pane = next(
        pane
        for pane in panes
        if local(internal["Avg Qty Inc Manufacturer"]) in (pane.get("x-axis-name") or "")
    )
    color = avg_pane.find("encodings/color")
    assert color is not None, "avg pane has no colour encoding"
    assert local(internal["Is Selected Sub Cat"]) in color.get("column"), (
        "avg pane must colour by Is Selected Sub Cat"
    )
    palette = ds.find("style/style-rule[@element='mark']/encoding[@attr='color']")
    assert palette is not None, "boolean colour palette missing"
    buckets = {b.text for b in palette.findall("map/bucket")}
    assert buckets == {"true", "false"}, f"palette buckets changed: {buckets}"
    colors = {m.get("to") for m in palette.findall("map")}
    assert len(colors) == 2, "selected/unselected colours must differ"

    # The Variance pane colours continuously by the variance value.
    var_pane = next(
        pane
        for pane in panes
        if local(internal["Variance"]) in (pane.get("x-axis-name") or "")
    )
    var_color = var_pane.find("encodings/color")
    assert var_color is not None and local(internal["Variance"]) in var_color.get("column"), (
        "variance pane must colour by Variance"
    )
    continuous = table.find(
        "style/style-rule[@element='mark']/encoding[@attr='color'][@type='interpolated']"
    )
    assert continuous is not None, "continuous variance palette missing"

    # --- ww12-parameter-action ---------------------------------------------
    actions = root.find("actions")
    assert actions is not None, "no actions container"
    parameter_action = actions.find("edit-parameter-action")
    assert parameter_action is not None, "no parameter action"
    source = parameter_action.find("source")
    assert source.get("worksheet") == "Viz", "parameter action source changed"
    assert source.get("dashboard") == DASHBOARD_NAME, "parameter action dashboard changed"
    params = {
        p.get("name"): p.get("value") for p in parameter_action.findall("params/param")
    }
    assert local(internal["Sub-Category"]) in params.get("source-field", ""), (
        "parameter action must source Sub-Category"
    )
    assert params.get("target-parameter", "").endswith("Parameter 1]"), (
        "parameter action must target the pSelectedSubCat parameter"
    )

    # The Unhighlight filter action maps True to False so the default selection
    # highlight never overrides the authored colour encodings.
    filter_action = actions.find("action")
    assert filter_action is not None, "no filter action"
    command = filter_action.find("command")
    assert command.get("command") == "tsc:tsl-filter", "unhighlight action changed"
    assert command.find("param[@name='target']").get("value") == "Viz", (
        "unhighlight action target changed"
    )

    # The parameter default matches the article's starting comparison baseline.
    parameters = next(
        node for node in root.findall("datasources/datasource") if node.get("name") == "Parameters"
    )
    param_column = parameters.find(f"column[@caption='{PARAMETER}']")
    assert param_column is not None, "pSelectedSubCat parameter missing"
    assert param_column.get("value") == f'"{DEFAULT_SUBCAT}"', (
        f"parameter default changed: {param_column.get('value')}"
    )

    # The dashboard hosts the single sheet.
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    assert any(
        zone.get("name") == "Viz" for zone in dashboard.findall(".//zones//zone")
    ), "dashboard does not host Viz"

    evidence = {
        "scope": "Locked-extract oracle plus native workbook contracts.",
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
    print(json.dumps(result["facts"], indent=2))
    print("PASS")
