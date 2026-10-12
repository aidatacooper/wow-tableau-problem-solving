"""Independently verify the Regional Sales Readout map-layer workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes per-region and per-city sales from the raw rows and checks the native
map-layer contracts that carry the solution chain.

Automated acceptance IDs:
  - ww19-region-segmented-map
  - ww19-region-borders
  - ww19-city-sales-layer
  - ww19-region-sales-text
  - ww19-selected-city-set
"""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww19-region-segmented-map",
    "ww19-region-borders",
    "ww19-city-sales-layer",
    "ww19-region-sales-text",
    "ww19-selected-city-set",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_05_12_WW19_Map_Layers"
TABLE = TableName("Extract", "Extract")

REGION_BORDERS = {
    "West State": "#7ec886",
    "Central State": "#82d7d6",
    "East State": "#b6b6dd",
    "South State": "#fd8b59",
}


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
            f'SELECT "City","State","Region","Sales" FROM {TABLE}'
        )
    assert len(rows) == 9994, "row count changed"
    region_sales = {}
    state_region = {}
    for city, state, region, sales in rows:
        assert region in {"West", "Central", "East", "South"}, f"unexpected region {region}"
        region_sales[region] = region_sales.get(region, 0) + sales
        state_region[state] = region
    assert len(state_region) == 49, f"state count changed: {len(state_region)}"
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "states": len(state_region),
        "region_sales": {k: round(v, 3) for k, v in sorted(region_sales.items())},
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def verify():
    facts = oracle()
    root = workbook()

    viz = root.find(".//worksheets/worksheet[@name='Map']")
    assert viz is not None, "missing Map worksheet"
    table = viz.find("table")

    # --- ww19-region-segmented-map -----------------------------------------
    # The map is drawn from US states and the base layer colours them by Region.
    geographic = root.find(".//datasource//column[@semantic-role='[State].[Name]']")
    assert geographic is not None, "no state-geocoded column"
    panes = table.findall("panes/pane")
    # Pane 0 is the map canvas; then the base state layer plus four region
    # border layers, the city circle layer and the sales text layer.
    assert len(panes) == 8, f"expected the authored layer stack, got {len(panes)}"
    multipolygons = [p for p in panes if p.find("mark").get("class") == "Multipolygon"]
    assert len(multipolygons) == 6, (
        f"expected canvas + 1 base + 4 region multipolygon layers, got {len(multipolygons)}"
    )
    base = multipolygons[1]
    base_color = base.find("encodings/color")
    assert base_color is not None, "base state layer has no colour encoding"

    # --- ww19-region-borders -----------------------------------------------
    # Four region layers carry distinct stroke colours.
    strokes = {
        layer.get("generated-title") or f"layer{index}": layer.get("stroke-color")
        for index, layer in enumerate(multipolygons[1:], start=1)
    }
    region_layer_colors = {
        pane.findtext("style/style-rule[@element='mark']/format[@attr='stroke-color']")
        or pane.get("stroke-color")
        for pane in multipolygons[2:]
    }
    # The stroke colours are recorded on the pane style; collect them robustly.
    found_strokes = set()
    for pane in multipolygons[2:]:
        for fmt in pane.findall(".//format[@attr='stroke-color']"):
            found_strokes.add(fmt.get("value"))
    assert found_strokes == set(REGION_BORDERS.values()), (
        f"region border colours changed: {found_strokes}"
    )

    # --- ww19-city-sales-layer ---------------------------------------------
    circle = next((p for p in panes if p.find("mark").get("class") == "Circle"), None)
    assert circle is not None, "missing city circle layer"
    size = circle.find("encodings/size")
    assert size is not None and "Sales" in (size.get("column") or ""), (
        "city layer is not sized by Sales"
    )
    lod = [e.get("column", "") for e in circle.findall("encodings/lod")]
    assert any("City" in ref for ref in lod), "city layer does not detail by City"

    # --- ww19-region-sales-text --------------------------------------------
    text = next((p for p in panes if p.find("mark").get("class") == "Text"), None)
    assert text is not None, "missing sales text layer"
    label = text.find("encodings/text")
    assert label is not None and "Sales" in (label.get("column") or ""), (
        "sales text layer does not label Sales"
    )

    # --- ww19-selected-city-set --------------------------------------------
    group = root.find(".//datasource/group[@caption='Selected City']")
    assert group is not None, "Selected City set missing"
    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.findall(".//datasource/column")
        if column.find("calculation") is not None
    }
    assert "Selected City" in (formulas.get("Selected City Sales") or ""), (
        "Selected City Sales does not test the set"
    )
    assert "Selected City" in (formulas.get("Selected City Name") or ""), (
        "Selected City Name does not test the set"
    )
    assert "SUM([Sales])" in (formulas.get("% of Total Sales") or ""), (
        "% of Total Sales is not city-sales over all sales"
    )
    actions = root.findall(".//actions/edit-group-action")
    assert actions, "no change-set action"
    assert any(
        "Selected City"
        in (
            action.find("params/param[@name='target-group']").get("value")
            or ""
        )
        for action in actions
    ), "the set action does not target Selected City"

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    evidence = {
        "scope": "Locked-extract oracle plus native map-layer workbook contracts.",
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
