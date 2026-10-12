"""Independently verify the WW24 John Snow cholera outbreak workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Re-implements the haversine distance oracle in Python, recomputes every pump's
average distance and the number of deaths inside it, and checks the native
map / bar / action contracts.

Automated acceptance IDs:
  - ww24-distance-model
  - ww24-bars
  - ww24-map-layers
  - ww24-selection
  - ww24-unhighlight
"""

import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "ww24-distance-model",
    "ww24-bars",
    "ww24-map-layers",
    "ww24-selection",
    "ww24-unhighlight",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_06_15_WW24_Cholera_Outbreak_Map"

PUMPS_TABLE = "water_pumps.csv_9B7DA11BB1144B19BDD982A9268B75E0"
DEATHS_TABLE = "deaths_individual.csv_162009320E3A4F70866D724FA8898FC7"
AGG_TABLE = "deaths_aggregate.csv_1892F1A4B2974F6F83AF8CAD9933D259"

# Tableau's DISTANCE(...,'m') uses the WGS84 Vincenty inverse formula; the
# author's rounded labels match it exactly, while the simpler spherical law of
# cosines is a metre off on pumps 2-6.
WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563

EXPECTED_AVG = [119, 248, 297, 335, 260, 231, 421, 278]
EXPECTED_COUNT = [259, 242, 252, 258, 228, 251, 256, 279]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance(a, b):
    """WGS84 Vincenty inverse distance in metres between (lon, lat) pairs."""
    a_axis = WGS84_A
    b_axis = (1 - WGS84_F) * WGS84_A
    longitude_delta = math.radians(b[0] - a[0])
    u1 = math.atan((1 - WGS84_F) * math.tan(math.radians(a[1])))
    u2 = math.atan((1 - WGS84_F) * math.tan(math.radians(b[1])))
    sin_u1, cos_u1 = math.sin(u1), math.cos(u1)
    sin_u2, cos_u2 = math.sin(u2), math.cos(u2)
    lam = longitude_delta
    lam_prev = 2 * math.pi
    sigma = 0.0
    cos_sq_alpha = 0.0
    cos_2sigma_m = 0.0
    sin_sigma = 0.0
    cos_sigma = 1.0
    for _ in range(200):
        sin_lam, cos_lam = math.sin(lam), math.cos(lam)
        sin_sigma = math.hypot(
            cos_u2 * sin_lam, cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lam
        )
        if sin_sigma == 0:
            return 0.0
        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cos_u1 * cos_u2 * sin_lam / sin_sigma
        cos_sq_alpha = 1 - sin_alpha ** 2
        cos_2sigma_m = (
            cos_sigma - 2 * sin_u1 * sin_u2 / cos_sq_alpha
            if cos_sq_alpha != 0
            else 0.0
        )
        c = WGS84_F / 16 * cos_sq_alpha * (4 + WGS84_F * (4 - 3 * cos_sq_alpha))
        lam_prev = lam
        lam = longitude_delta + (1 - c) * WGS84_F * sin_alpha * (
            sigma
            + c * sin_sigma * (
                cos_2sigma_m
                + c * cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
            )
        )
        if abs(lam - lam_prev) < 1e-12:
            break
    u_sq = cos_sq_alpha * (a_axis ** 2 - b_axis ** 2) / b_axis ** 2
    big_a = 1 + u_sq / 16384 * (
        4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq))
    )
    big_b = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sigma = big_b * sin_sigma * (
        cos_2sigma_m
        + big_b / 4 * (
            cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
            - big_b / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2)
            * (-3 + 4 * cos_2sigma_m ** 2)
        )
    )
    return b_axis * big_a * (sigma - delta_sigma)


def oracle():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(path)) as connection,
    ):
        pumps = connection.execute_list_query(
            f'SELECT "PumpID","Location","PumpLon","PumpLat" '
            f'FROM {TableName("Extract", PUMPS_TABLE)} ORDER BY 1'
        )
        deaths = connection.execute_list_query(
            f'SELECT "DeathID","DeathLon","DeathLat" '
            f'FROM {TableName("Extract", DEATHS_TABLE)} ORDER BY 1'
        )
        aggregates = connection.execute_list_query(
            f'SELECT "LocID","Deaths","DeathLon","DeathLat" '
            f'FROM {TableName("Extract", AGG_TABLE)} ORDER BY 1'
        )

    avg = {}
    within = {}
    for pump_id, _location, pump_lon, pump_lat in pumps:
        distances = [
            distance((pump_lon, pump_lat), (lon, lat)) for _d, lon, lat in deaths
        ]
        average = sum(distances) / len(distances)
        avg[pump_id] = average
        within[pump_id] = sum(1 for value in distances if value <= average)

    assert len(pumps) == 8, len(pumps)
    assert len(deaths) == 489, len(deaths)
    assert len(aggregates) == 250, len(aggregates)
    assert sum(count for _l, count, _lon, _lat in aggregates) == 489

    return {
        "extract_sha256": item["sha256"],
        "pumps": len(pumps),
        "individual_deaths": len(deaths),
        "aggregated_locations": len(aggregates),
        "avg_distance": {pid: round(avg[pid], 1) for pid in sorted(avg)},
        "avg_distance_label": {pid: round(avg[pid]) for pid in sorted(avg)},
        "deaths_within": {pid: within[pid] for pid in sorted(within)},
        "pump_locations": {
            pid: location for pid, location, _lon, _lat in pumps
        },
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
    import re

    def replace(match):
        token = match.group(1)
        if f"[{token}]" in names:
            return f"[{names[f'[{token}]']}]"
        return f"[{token}]"

    text = re.sub(
        r"\[Parameters\]\.\[([^\]]+)\]",
        lambda m: f"[{parameters.get(m.group(1), m.group(1))}]",
        formula,
    )
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
        import re

        return re.sub(r"\s+", " ", resolve(calc[caption], names, parameters)).strip()

    # --- ww24-distance-model ------------------------------------------------
    assert facts["pumps"] == 8 and facts["individual_deaths"] == 489, facts
    assert facts["aggregated_locations"] == 250, facts
    assert facts["avg_distance_label"] == {
        pid: value for pid, value in enumerate(EXPECTED_AVG, start=1)
    }, facts["avg_distance_label"]
    assert facts["deaths_within"] == {
        pid: value for pid, value in enumerate(EXPECTED_COUNT, start=1)
    }, facts["deaths_within"]

    assert resolved("Distance Pump to Death") == (
        "DISTANCE([Pump Location], [Individual Death Location],'m')"
    ), resolved("Distance Pump to Death")
    assert resolved("Avg Distance") == (
        "{FIXED [PumpID]: AVG([Distance Pump to Death])}"
    ), resolved("Avg Distance")
    assert resolved("Number Deaths within Avg Distance") == (
        "SUM(INT([Distance Pump to Death] <= [Avg Distance]))"
    ), resolved("Number Deaths within Avg Distance")
    assert "MAKEPOINT([PumpLat],[PumpLon])" == resolved("Pump Location")
    assert "MAKEPOINT([DeathLat],[DeathLon])" == resolved("Individual Death Location")

    # --- ww24-bars ----------------------------------------------------------
    for sheet, measure in (
        ("Avg Distance to Pump", "Avg Distance"),
        ("Total Deaths within Avg Distance", "Number Deaths within Avg Distance"),
    ):
        node = root.find(f".//worksheets/worksheet[@name='{sheet}']")
        assert node is not None, f"missing {sheet}"
        rows = node.findtext("table/rows") or ""
        cols = node.findtext("table/cols") or ""
        assert "none:PumpID" in rows, rows
        measure_ref = next(
            (k for k, v in names.items() if v == measure), None
        )
        assert measure_ref and measure_ref[1:-1] in cols, (measure, cols)
        pane = node.find("table/panes/pane")
        assert pane.find("mark").get("class") == "Bar", etree.tostring(pane)
        color = pane.find("encodings/color")
        assert color is not None, etree.tostring(pane)
        import re as _re

        match = _re.search(r"\[(?:none|usr|sum|attr):([^:\]]+):(?:nk|qk|ok)\]",
                           color.get("column") or "")
        assert match, color.get("column")
        assert names.get(f"[{match.group(1)}]", match.group(1)) == "Is Selected Pump?", \
            (match.group(1), color.get("column"))
        # The selected bar is black; the rest match the sheet background.
        palette = root.find(
            ".//datasource/style/style-rule[@element='mark']/encoding[@attr='color']"
        )
        if palette is None:
            palette = next(
                (
                    enc
                    for enc in root.findall(
                        ".//style-rule[@element='mark']/encoding[@attr='color']"
                    )
                    if "Is Selected Pump?" in (enc.get("field") or "")
                ),
                None,
            )
        assert palette is not None, "selected-pump palette missing"
        mapping = {
            (m.findtext("bucket") or "").strip('"'): m.get("to")
            for m in palette.findall("map")
        }
        assert mapping.get("true") == "#000000", mapping
        assert mapping.get("false") == "#f5f1f0", mapping

    # --- ww24-map-layers ----------------------------------------------------
    map_sheet = root.find(".//worksheets/worksheet[@name='Map']")
    assert map_sheet is not None, "missing Map worksheet"
    panes = map_sheet.findall("table/panes/pane")
    # The native-layer model writes a base Multipolygon pane followed by the
    # four declared layers.
    assert len(panes) == 5, [p.find("mark").get("class") for p in panes]
    marks = [p.find("mark").get("class") for p in panes[1:]]
    assert marks == ["Heatmap", "Automatic", "Circle", "Circle"], marks
    titles = [p.get("generated-title") for p in panes]
    assert "Pump Buffer" in titles and "Pumps" in titles and "Deaths Agg" in titles, titles
    # The buffer layer carries the BUFFER geometry; the others carry their own.
    geometry_refs = [
        g.get("column")
        for g in (p.find("encodings/geometry") for p in panes)
        if g is not None
    ]
    assert any(ref and "Calculation" in ref for ref in geometry_refs), geometry_refs
    assert resolved("Pump Buffer") == (
        "BUFFER([Selected Pump Location],[Selected Pump Avg Distance],'m')"
    ), resolved("Pump Buffer")
    assert map_sheet.find(".//mapsources/mapsource[@name='Tableau']") is not None
    map_rule = map_sheet.find(".//style-rule[@element='map']")
    assert map_rule is not None, "map style rule missing"
    settings = {f.get("attr"): f.get("value") for f in map_rule.findall("format")}
    assert settings.get("map-style") == "normal", settings

    # --- ww24-selection -----------------------------------------------------
    assert resolved("Is Selected Pump?") == "[PumpID]=[pSelectedPump]"
    assert resolved("Selected Pump Avg Distance") == (
        "{FIXED :SUM( IF [Is Selected Pump?] THEN [Avg Distance] END)}"
    ), resolved("Selected Pump Avg Distance")
    assert "IIF([Is Selected Pump?],[PumpLat],NULL)" in resolved("Selected Pump Lat")
    assert "IIF([Is Selected Pump?],[PumpLon],NULL)" in resolved("Selected Pump Long")
    param = root.find(".//datasource[@name='Parameters']/column[@caption='pSelectedPump']")
    assert param is not None and param.get("value") == "1", \
        etree.tostring(param) if param is not None else None
    param_ref = param.get("name")
    actions = root.findall(".//actions/edit-parameter-action")
    assert len(actions) == 3, f"expected three parameter actions, got {len(actions)}"
    for action in actions:
        assert action.find("activation").get("type") == "on-select"
        target = action.find("params/param[@name='target-parameter']")
        assert target is not None and target.get("value") == f"[Parameters].{param_ref}", \
            etree.tostring(action)
        source = action.find("params/param[@name='source-field']")
        assert source is not None and "PumpID" in source.get("value"), \
            etree.tostring(action)

    # --- ww24-unhighlight ---------------------------------------------------
    filters = [
        a for a in root.findall(".//actions/action")
        if a.find("command") is not None
        and a.find("command").get("command") == "tsc:tsl-filter"
    ]
    assert len(filters) == 3, f"expected three filter actions, got {len(filters)}"
    sources = {a.find("source").get("worksheet") for a in filters}
    assert sources == {
        "Map", "Avg Distance to Pump", "Total Deaths within Avg Distance"
    }, sources
    for action in filters:
        assert "Unhighlight" in (action.get("caption") or ""), action.get("caption")
    # Both "True" and "False" are bound on Detail so the click can be mapped.
    for sheet in (
        "Avg Distance to Pump",
        "Total Deaths within Avg Distance",
    ):
        node = root.find(f".//worksheets/worksheet[@name='{sheet}']")
        deps = next(
            (
                d
                for d in node.findall("table/view/datasource-dependencies")
                if (d.get("datasource") or "").startswith("federated.")
            ),
            None,
        )
        assert deps is not None, sheet
        detail = set()
        for ci in deps.findall("column-instance"):
            raw = ci.get("column") or ""
            match = _re.search(
                r"\[(?:none|usr|sum|attr):([^:\]]+):(?:nk|qk|ok)\]", raw
            )
            token = match.group(1) if match else raw.strip("[]")
            detail.add(names.get(f"[{token}]", token))
        assert "True" in detail, (sheet, sorted(detail))

    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zone_names = {
        z.get("name") for z in dashboard.findall(".//zones//zone") if z.get("name")
    }
    assert {
        "Map", "Avg Distance to Pump", "Total Deaths within Avg Distance"
    } <= zone_names, zone_names

    evidence = {
        "scope": "Locked-extract haversine oracle plus native map/bar/action contracts.",
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
                "pumps", "individual_deaths", "aggregated_locations",
                "avg_distance_label", "deaths_within",
            )
        },
        indent=2,
    ))
    print("PASS")
