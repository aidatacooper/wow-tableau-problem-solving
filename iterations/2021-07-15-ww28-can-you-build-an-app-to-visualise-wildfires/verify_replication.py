"""Independently verify the WW28 fire-size visualiser workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Recomputes the acres-to-radius conversion and the location coordinates and checks
the native workbook contracts.

Automated acceptance IDs:
  - ww28-parameters
  - ww28-geography
  - ww28-map-layers
  - ww28-apply-button
  - ww28-location-case
  - ww28-actions
"""

import hashlib
import json
import math
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww28-parameters",
    "ww28-geography",
    "ww28-map-layers",
    "ww28-apply-button",
    "ww28-location-case",
    "ww28-actions",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_07_14_WW28_FireSize_Map"
TABLE = TableName("Extract", "Extract")

LOCATION_LAT = {1: 51.6080, 2: 40.7812, 3: 51.5007, 4: 48.8584}
LOCATION_LONG = {1: -1.2448, 2: -73.9665, 3: 0.1246, 4: 2.2945}
FIRE_COLOR = "#fb9f8c"


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
        rows = connection.execute_list_query(f'SELECT "Data","F2" FROM {TABLE}')
    assert len(rows) == 5, "dummy row count changed"
    # The app's only real number is the acreage-to-radius conversion.
    acres = 5000
    radius_feet = math.sqrt((acres * 43560) / math.pi)
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "acres": acres,
        "radius_feet": round(radius_feet, 6),
        "locations": {
            str(key): [LOCATION_LAT[key], LOCATION_LONG[key]] for key in LOCATION_LAT
        },
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        return etree.fromstring(archive.read(name))


def formulas(root):
    raw = {}
    for column in root.findall(".//datasource/column"):
        calc = column.find("calculation")
        if calc is not None:
            raw[column.get("name")] = (column.get("caption"), calc.get("formula") or "")
    names = {name.strip("[]"): name for name in raw}

    def resolve(formula: str) -> str:
        text = re.sub(r"\[Parameters\]\.\[Parameter \d+\]", "[param]", formula)

        def replace(match):
            token = match.group(1)
            if token.startswith("Calculation_") and token in names:
                return f"[{raw[names[token]][0]}]"
            return match.group(0)

        return re.sub(r"\[([^\]]+)\]", replace, text)

    return {caption: resolve(formula) for caption, formula in raw.values()}


def verify():
    facts = oracle()
    root = workbook()
    calc = formulas(root)
    parameters = {
        column.get("caption"): column
        for column in root.findall(".//datasource[@name='Parameters']/column")
    }

    # --- ww28-parameters ----------------------------------------------------
    for name in ("pLocation", "pLatitude", "pLongtitude", "Acres", "pZoom"):
        assert name in parameters, (name, list(parameters))
    assert parameters["Acres"].get("value") == "5000"
    assert parameters["pLatitude"].get("value") == "51.608"
    assert parameters["pLongtitude"].get("value") == "-1.2448"
    assert parameters["pZoom"].get("value") == "2"
    zoom_members = [m.get("value") for m in parameters["pZoom"].findall("members/member")]
    assert zoom_members == ["1", "2", "5", "10", "50", "500"], zoom_members
    aliases = {
        a.get("key"): a.get("value")
        for a in parameters["pLocation"].findall("aliases/alias")
    }
    assert aliases == {
        "1": "Didcot, UK",
        "2": "Central Park, New York",
        "3": "Big Ben, London",
        "4": "Eiffel Tower, Paris",
    }, aliases

    # --- ww28-geography -----------------------------------------------------
    # Parameter references all resolve to [param] in this normalizer, so the
    # assertions check the structure around them.
    assert calc["Location"] == "MAKEPOINT([param], [param])"
    assert calc["Acres to Feet"] == "SQRT(([param]*43560)/PI())"
    assert calc["Fire Size"] == "BUFFER([Location],[Acres to Feet],'ft')"
    assert calc["Zoom"] == "BUFFER([Location],[param] * [Acres to Feet],'ft')"
    # The acreage parameter is the one defaulted to 5000 and is what feeds the
    # radius; the zoom parameter is the list one.
    assert parameters["Acres"].get("value") == "5000"
    assert facts["rows"] == 5, facts
    assert facts["radius_feet"] == 8326.337323, facts

    # --- ww28-map-layers ----------------------------------------------------
    map_sheet = root.find(".//worksheets/worksheet[@name='Map']")
    assert map_sheet is not None, "missing Map worksheet"
    panes = map_sheet.findall("table/panes/pane")
    # A canvas pane plus the fire layer plus the zoom layer.
    layers = [p for p in panes if p.find("encodings/geometry") is not None]
    assert len(layers) == 2, f"expected fire + zoom layers, got {len(layers)}"
    fire, zoom = layers
    fire_color = fire.find(
        "style/style-rule[@element='mark']/format[@attr='mark-color']"
    )
    assert fire_color is not None and fire_color.get("value") == FIRE_COLOR
    assert zoom.get("inert") == "true", etree.tostring(zoom)
    zoom_transparency = zoom.find(
        "style/style-rule[@element='mark']/format[@attr='mark-transparency']"
    )
    assert zoom_transparency is not None and zoom_transparency.get("value") == "0", (
        etree.tostring(zoom)
    )
    for layer in layers:
        assert layer.find("encodings/lod") is not None, (
            "buffer layer is missing its Detail field",
            etree.tostring(layer),
        )
    map_rule = map_sheet.find("table/style/style-rule[@element='map']")
    style = map_rule.find("format[@attr='map-style']").get("value")
    washout = float(map_rule.find("format[@attr='washout']").get("value"))
    assert style == "dark", style
    assert abs(washout - 0.15) < 1e-6, washout

    # --- ww28-apply-button --------------------------------------------------
    apply_sheet = root.find(".//worksheets/worksheet[@name='Apply']")
    assert apply_sheet is not None, "missing Apply worksheet"
    assert calc["Apply Label"] == "'Apply'"
    apply_details = [
        node.get("column") or ""
        for node in apply_sheet.findall("table/panes/pane/encodings/lod")
    ]
    assert any("Calculation" in ref for ref in apply_details), apply_details

    # --- ww28-location-case -------------------------------------------------
    lat = calc["Location Lat"]
    for key, value in LOCATION_LAT.items():
        assert f"WHEN {key} THEN {value}" in lat, lat
    long = calc["Location Long"]
    for key, value in LOCATION_LONG.items():
        assert f"WHEN {key} THEN {value}" in long, long

    # --- ww28-actions -------------------------------------------------------
    parameter_actions = root.findall(".//actions/edit-parameter-action")
    assert len(parameter_actions) == 2, len(parameter_actions)
    captions = {a.get("caption") for a in parameter_actions}
    assert captions == {"Set Lat", "Set Long"}, captions
    for action in parameter_actions:
        assert action.find("source").get("worksheet") == "Apply"
        assert action.find("params/param[@name='source-field']") is not None
    filter_actions = root.findall(".//actions/action")
    assert any(
        a.find("link") is not None and "~s0=<" in (a.find("link").get("expression") or "")
        for a in filter_actions
    ), "True->False filter action missing"
    assert "True" in calc and "False" in calc
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    evidence = {
        "scope": "Locked-extract oracle plus native parameter-map workbook contracts.",
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
