"""Independent verifier for the WW01 2022 wildlife-strikes replication.

Recomputes every number from the packaged Hyper extract, then asserts the
generated workbook's data model, calculations, filters, encodings, dashboard
geometry and interactions. It never reads the author workbook.

Run from the repository root or the iteration directory:

    python iterations/2022-01-06-ww01-let-s-analyse-wildlife-strikes/verify_replication.py
"""

from __future__ import annotations

import hashlib
import csv
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tableauhyperapi import Connection, HyperProcess, Telemetry

ITERATION_DIR = Path(__file__).resolve().parent
TWBX = ITERATION_DIR / "outputs" / "replicated-workbook.twbx"
HYPER = (
    ITERATION_DIR
    / "inputs"
    / "2022_01_05_WW01_FAA Wildlife strikes (1990-2021).hyper"
)
EVIDENCE = ITERATION_DIR / "evidence" / "verification.json"

STRIKES = (
    '"Extract"."2022_01_05_WW01_FAA Wildlife strikes (1990-2021).csv_'
    'C67D25C483BA4EAB884EC73253D02E3D"'
)
STATES = '"Extract"."Extract (Extract.Extract)_C91EDBA13DE94D71AF94506067CAD581"'
USER = "http://www.tableausoftware.com/xml/user"

EXPECTED_TOTAL = 251_818
EXPECTED_NULL_STATE = 36_959
EXPECTED_SPECIES = 23
EXPECTED_STATE_MEMBERS = 51  # 50 states + DC + the null group


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def oracle() -> dict:
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as conn:
            total = conn.execute_scalar_query(f"SELECT COUNT(*) FROM {STRIKES}")
            species = conn.execute_list_query(
                f'SELECT "Species Type", COUNT(*) FROM {STRIKES} '
                "GROUP BY 1 ORDER BY 2 DESC, 1"
            )
            states = conn.execute_list_query(
                f'SELECT "State Name", COUNT(*) FROM {STRIKES} '
                "GROUP BY 1 ORDER BY 2 DESC, 1"
            )
            years = conn.execute_list_query(
                f'SELECT "Incident Year", COUNT(*) FROM {STRIKES} '
                "GROUP BY 1 ORDER BY 1"
            )
            null_state = conn.execute_scalar_query(
                f'SELECT COUNT(*) FROM {STRIKES} WHERE "State Name" IS NULL'
            )
            geometry_rows = conn.execute_scalar_query(f"SELECT COUNT(*) FROM {STATES}")
            geometry_names = [
                row[0]
                for row in conn.execute_list_query(
                    f'SELECT "NAME" FROM {STATES} ORDER BY 1'
                )
            ]
            alabama = conn.execute_list_query(
                f"""SELECT "Species Type", COUNT(*) FROM {STRIKES}
                    WHERE "State Name" = 'Alabama' GROUP BY 1 ORDER BY 2 DESC, 1"""
            )
            alabama_years = conn.execute_list_query(
                f"""SELECT "Incident Year", COUNT(*) FROM {STRIKES}
                    WHERE "State Name" = 'Alabama' GROUP BY 1 ORDER BY 1"""
            )
            unknown_bird_years = conn.execute_list_query(
                f"""SELECT "Incident Year", COUNT(*) FROM {STRIKES}
                    WHERE "Species Type" = 'Unknown Bird' GROUP BY 1 ORDER BY 1"""
            )
            alabama_unknown_bird = conn.execute_scalar_query(
                f"""SELECT COUNT(*) FROM {STRIKES}
                    WHERE "State Name" = 'Alabama' AND "Species Type" = 'Unknown Bird'"""
            )
            unknown_bird_null_state = conn.execute_scalar_query(
                f"""SELECT COUNT(*) FROM {STRIKES}
                    WHERE "State Name" IS NULL AND "Species Type" = 'Unknown Bird'"""
            )
    top10 = [(name, count) for name, count in species[:10]]
    other = total - sum(count for _, count in top10)
    return {
        "total_rows": total,
        "null_state_rows": null_state,
        "species_count": len(species),
        "species_top10": top10,
        "species_11th": species[10],
        "other_rows": other,
        "states": states,
        "years": years,
        "geometry_rows": geometry_rows,
        "geometry_names": geometry_names,
        "alabama_species": alabama,
        "alabama_total": sum(count for _, count in alabama),
        "alabama_years": alabama_years,
        "unknown_bird_total": sum(count for _, count in unknown_bird_years),
        "unknown_bird_years": unknown_bird_years,
        "alabama_unknown_bird": alabama_unknown_bird,
        "unknown_bird_null_state": unknown_bird_null_state,
    }


def load_twb() -> ET.Element:
    with zipfile.ZipFile(TWBX) as archive:
        names = [n for n in archive.namelist() if n.endswith(".twb")]
        if len(names) != 1:
            raise AssertionError("TWBX must contain exactly one TWB")
        return ET.fromstring(archive.read(names[0]))


class Checks:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, check_id: str, ok: bool, detail: str = "") -> None:
        self.items.append({"id": check_id, "ok": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {check_id} {detail}")

    @property
    def ok(self) -> bool:
        return all(item["ok"] for item in self.items)


def text(node) -> str:
    return (node.text or "").strip() if node is not None else ""


def main() -> int:
    checks = Checks()
    data = oracle()

    # acceptance: default-totals
    checks.add(
        "oracle-total",
        data["total_rows"] == EXPECTED_TOTAL,
        f"rows={data['total_rows']}",
    )
    checks.add(
        "oracle-null-state",
        data["null_state_rows"] == EXPECTED_NULL_STATE,
        f"null-state={data['null_state_rows']}",
    )
    checks.add(
        "oracle-species-count",
        data["species_count"] == EXPECTED_SPECIES,
        f"species={data['species_count']}",
    )
    checks.add(
        "oracle-state-members",
        len(data["states"]) == EXPECTED_STATE_MEMBERS,
        f"state groups={len(data['states'])}",
    )
    # acceptance: species-set-boundary
    checks.add(
        "oracle-top10-boundary",
        data["species_top10"][-1][1] > data["species_11th"][1],
        f"10th={data['species_top10'][-1]} 11th={data['species_11th']}",
    )
    checks.add(
        "oracle-other",
        data["other_rows"] == 4_308,
        f"other={data['other_rows']}",
    )
    # acceptance: state-selection
    checks.add(
        "oracle-alabama",
        data["alabama_total"] == 1_842 and data["alabama_unknown_bird"] == 955,
        f"total={data['alabama_total']} unknown-bird={data['alabama_unknown_bird']}",
    )
    checks.add(
        "oracle-geometry",
        data["geometry_rows"] == 56
        and "American Samoa" in data["geometry_names"]
        and "District of Columbia" in data["geometry_names"],
        f"geometry rows={data['geometry_rows']}",
    )

    checks.add("artifact-exists", TWBX.is_file(), str(TWBX))
    if not TWBX.is_file():
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(
            json.dumps({"status": "fail", "checks": checks.items}, indent=2) + "\n",
            encoding="utf-8",
        )
        return 1

    # The packaged Hyper must be byte-identical to the locked extracted input.
    with zipfile.ZipFile(TWBX) as archive:
        members = {Path(n).name: n for n in archive.namelist()}
        hyper_name = HYPER.name
        packaged = archive.read(members[hyper_name]) if hyper_name in members else b""
    checks.add(
        "artifact-packaged-hyper",
        hashlib.sha256(packaged).hexdigest() == sha256(HYPER),
        f"members={sorted(members)}",
    )

    root = load_twb()
    ns = {"user": USER}

    # --- data model --------------------------------------------------------
    datasources = root.findall("datasources/datasource")
    data_sources = [
        ds for ds in datasources if ds.find("connection[@class='federated']") is not None
    ]
    checks.add(
        "model-single-data-datasource",
        len(data_sources) == 1,
        f"data sources={len(data_sources)}",
    )
    ds = data_sources[0]
    ds_name = ds.get("name", "")
    physical = ds.findall(".//relation[@type='table']")
    physical_names = sorted({rel.get("name", "") for rel in physical})
    checks.add(
        "model-two-physical-tables",
        physical_names == ["States", "Strikes"],
        f"tables={physical_names}",
    )
    objects = ds.findall(".//object-graph/objects/object")
    relationship = ds.find(".//object-graph/relationships/relationship")
    rel_terms = (
        [node.get("op", "") for node in relationship.iter("expression")]
        if relationship is not None
        else []
    )
    checks.add(
        "model-logical-relationship",
        len(objects) == 2
        and relationship is not None
        and "[State Name]" in rel_terms
        and "[NAME]" in rel_terms,
        f"objects={[o.get('caption') for o in objects]} terms={rel_terms}",
    )
    geometry_column = ds.find(
        ".//relation[@name='States']/columns/column[@name='Geometry']"
    )
    checks.add(
        "model-spatial-table-packaged",
        geometry_column is not None,
        "States table exposes Geometry",
    )

    # --- calculations, set and parameters ----------------------------------
    def column(caption: str):
        return ds.find(f"column[@caption='{caption}']")

    def formula_of(caption: str) -> str:
        node = column(caption)
        calculation = node.find("calculation") if node is not None else None
        return calculation.get("formula", "") if calculation is not None else ""

    def local_name(caption: str) -> str:
        node = column(caption)
        return node.get("name", "") if node is not None else ""

    def bare(caption: str) -> str:
        return local_name(caption).strip("[]")

    def ref_has(column_ref: str, caption: str) -> bool:
        name = bare(caption)
        return bool(name) and name in column_ref

    incidents = column("Wildlife Incidents")
    formula = formula_of("Wildlife Incidents")
    checks.add(
        "calc-wildlife-incidents",
        formula.upper() == "COUNT([SPECIES TYPE])".upper(),
        f"formula={formula!r}",
    )
    display = column("Species Type to Display")
    display_formula = formula_of("Species Type to Display")
    checks.add(
        "calc-species-display",
        "Species Type Set" in display_formula and "'Other'" in display_formula,
        f"formula={display_formula!r}",
    )
    state_filter = column("State Filter")
    state_filter_formula = formula_of("State Filter")
    checks.add(
        "calc-state-filter",
        "[Parameters]" in state_filter_formula
        and "[State Name]" in state_filter_formula
        and "TRUE" in state_filter_formula,
        f"formula={state_filter_formula!r}",
    )
    species_filter = column("Species Filter")
    species_filter_formula = formula_of("Species Filter")
    checks.add(
        "calc-species-filter",
        "[Parameters]" in species_filter_formula
        and bare("Species Type to Display") in species_filter_formula,
        f"formula={species_filter_formula!r}",
    )
    title_state = column("Title: Selected State")
    title_state_formula = formula_of("Title: Selected State")
    checks.add(
        "calc-title-state",
        "in " in title_state_formula and "[Parameters]" in title_state_formula,
        f"formula={title_state_formula!r}",
    )
    unknown_location = column("Unknown Location")
    unknown_formula = formula_of("Unknown Location")
    checks.add(
        "calc-unknown-location",
        unknown_formula.replace('"', "'") == "'Unknown Location'",
        f"formula={unknown_formula!r}",
    )
    year = column("Year")
    checks.add(
        "calc-continuous-year",
        year is not None
        and formula_of("Year") == "[Incident Year]"
        and year.get("type") == "quantitative",
        f"type={year.get('type') if year is not None else None}",
    )

    set_group = ds.find("group[@caption='Species Type Set']")
    end = set_group.find(".//groupfilter[@function='end']") if set_group is not None else None
    order = end.find("groupfilter[@function='order']") if end is not None else None
    order_expression = order.get("expression", "") if order is not None else ""
    checks.add(
        "set-top10-by-records",
        set_group is not None
        and end is not None
        and end.get("count") == "10"
        and end.get("end") == "top"
        and end.get("units") == "records"
        and order_expression.upper() == "COUNT([SPECIES TYPE])".upper(),
        f"count={end.get('count') if end is not None else None} order={order_expression!r}",
    )
    expected_members = [name for name, _ in data["species_top10"]]
    checks.add(
        "set-rank-is-unambiguous",
        len(expected_members) == 10
        and len(set(expected_members)) == 10
        and data["species_top10"][-1][1] > data["species_11th"][1],
        f"expected={expected_members}",
    )

    parameters = root.find("datasources/datasource[@name='Parameters']")
    param_columns = {
        col.get("caption"): col for col in parameters.findall("column")
    } if parameters is not None else {}
    checks.add(
        "params-default-empty-string",
        set(param_columns) == {"pSelectedState", "pSelectedSpecies"}
        and all(
            col.get("datatype") == "string" and col.get("value") == '""'
            for col in param_columns.values()
        ),
        f"params={sorted(param_columns)}",
    )
    state_param = param_columns["pSelectedState"].get("name", "") if "pSelectedState" in param_columns else ""
    species_param = (
        param_columns["pSelectedSpecies"].get("name", "")
        if "pSelectedSpecies" in param_columns
        else ""
    )

    # --- worksheets --------------------------------------------------------
    # acceptance: workbook-structure
    worksheets = {ws.get("name"): ws for ws in root.findall("worksheets/worksheet")}
    checks.add(
        "worksheets-present",
        set(worksheets) == {"Bar", "Map", "Area", "Unknown"},
        f"worksheets={sorted(worksheets)}",
    )

    bar = worksheets["Bar"]
    bar_rows = text(bar.find("table/rows"))
    bar_color = bar.find("table/panes/pane/encodings/color")
    bar_sort = bar.find("table/view/shelf-sorts/shelf-sort-v2")
    bar_filters = [
        node.get("column", "") for node in bar.findall("table/view/filter")
    ]
    bar_title = " ".join(text(run) for run in bar.findall("layout-options/title/formatted-text/run"))
    checks.add(
        "bar-set-nesting-and-sort",
        "[io:Species Type Set:nk]" in bar_rows
        and "[none:" in bar_rows
        and bar_color is not None
        and "[io:Species Type Set:nk]" in bar_color.get("column", "")
        and bar_sort is not None
        and bar_sort.get("direction") == "DESC",
        f"rows={bar_rows} sort={bar_sort.get('direction') if bar_sort is not None else None}",
    )
    checks.add(
        "bar-state-filter-and-title",
        any(ref_has(column_ref, "State Filter") for column_ref in bar_filters)
        and "Incidents by Animal Type" in bar_title
        and "[none:" in bar_title,
        f"title={bar_title!r}",
    )

    map_sheet = worksheets["Map"]
    map_rows = text(map_sheet.find("table/rows"))
    map_cols = text(map_sheet.find("table/cols"))
    map_pane = map_sheet.find("table/panes/pane")
    map_encodings = [
        (child.tag, child.get("column", ""))
        for child in map_pane.findall("encodings/*")
    ]
    map_semantic = map_sheet.find(
        f"table/view/datasource-dependencies[@datasource='{ds_name}']/column[@name='[State Name]']"
    )
    color_encoding = map_sheet.find("table/style/style-rule[@element='mark']/encoding[@attr='color']")
    background_layer = map_sheet.find(
        "table/style/style-rule[@element='map-layer']/format[@id='background']"
    )
    checks.add(
        "map-native-state-role",
        map_rows == f"[{ds_name}].[Latitude (generated)]"
        and map_cols == f"[{ds_name}].[Longitude (generated)]"
        and map_semantic is not None
        and map_semantic.get("semantic-role") == "[State].[Name]",
        f"rows={map_rows} semantic={map_semantic.get('semantic-role') if map_semantic is not None else None}",
    )
    checks.add(
        "map-encodings-and-palette",
        any(
            tag == "geometry" and column == f"[{ds_name}].[Geometry (generated)]"
            for tag, column in map_encodings
        )
        and any(
            tag == "lod" and column.startswith(f"[{ds_name}].[none:State Name:")
            for tag, column in map_encodings
        )
        and any(
            tag == "lod" and column.startswith(f"[{ds_name}].[none:NAME:")
            for tag, column in map_encodings
        )
        and color_encoding is not None
        and color_encoding.get("palette") == "red_gold_10_0"
        and color_encoding.get("min") == "0"
        and background_layer is not None
        and background_layer.get("value") == "false",
        f"encodings={map_encodings} palette={color_encoding.get('palette') if color_encoding is not None else None}",
    )
    geocoding = ds.find("semantic-values/semantic-value[@key='[Country].[Name]']")
    checks.add(
        "map-geocoding-context",
        geocoding is not None and "United States" in geocoding.get("value", ""),
        f"value={geocoding.get('value') if geocoding is not None else None}",
    )

    area = worksheets["Area"]
    area_rows = text(area.find("table/rows"))
    area_cols = text(area.find("table/cols"))
    area_mark = area.find("table/panes/pane/mark")
    area_lod = [
        enc.get("column", "") for enc in area.findall("table/panes/pane/encodings/lod")
    ]
    area_filters = [
        node.get("column", "") for node in area.findall("table/view/filter")
    ]
    area_title = " ".join(
        text(run) for run in area.findall("layout-options/title/formatted-text/run")
    )
    checks.add(
        "area-continuous-axis-and-detail",
        area_cols.startswith(f"[{ds_name}].[none:")
        and area_cols.endswith(":qk]")
        and area_rows.startswith(f"[{ds_name}].[usr:")
        and area_mark is not None
        and area_mark.get("class") == "Area"
        and len(area_lod) == 2,
        f"cols={area_cols} rows={area_rows} lod={len(area_lod)}",
    )
    checks.add(
        "area-both-cross-filters-and-title",
        any(ref_has(ref, "State Filter") for ref in area_filters)
        and any(ref_has(ref, "Species Filter") for ref in area_filters)
        and f"[Parameters].{species_param}" in area_title
        and "Incidents Over Time" in area_title,
        f"title={area_title!r}",
    )

    unknown = worksheets["Unknown"]
    unknown_mark = unknown.find("table/panes/pane/mark")
    unknown_text = unknown.find("table/panes/pane/encodings/text")
    unknown_filters = [
        ET.tostring(node, encoding="unicode")
        for node in unknown.findall("table/view/filter")
    ]
    unknown_filter_text = " ".join(unknown_filters)
    unknown_mark_color = unknown.find(
        "table/panes/pane/style/style-rule[@element='mark']/format[@attr='mark-color']"
    )
    checks.add(
        "unknown-indicator",
        unknown_mark is not None
        and unknown_mark.get("class") == "Square"
        and unknown_text is not None
        and any('member="%null%"' in node for node in unknown_filters)
        and any(ref_has(node, "Species Filter") for node in unknown_filters)
        and not any(ref_has(node, "State Filter") for node in unknown_filters)
        and unknown_mark_color is not None
        and unknown_mark_color.get("value") == "#e15759",
        f"color={unknown_mark_color.get('value') if unknown_mark_color is not None else None}",
    )

    # --- dashboard geometry and interactions -------------------------------
    dashboard = root.find(f"dashboards/dashboard[@name='2022_01_05_WW01_WildlifeWStrikes']")
    checks.add("dashboard-present", dashboard is not None, "author dashboard name")
    size = dashboard.find("size") if dashboard is not None else None
    zones = dashboard.findall(".//zone") if dashboard is not None else []
    zone_map = {
        z.get("name"): z
        for z in zones
        if z.get("name") and z.get("type-v2") in (None, "NONE")
    }
    expected_geometry = {
        "Bar": ("0", "6556", "40667", "60444"),
        "Map": ("40667", "6556", "59333", "60444"),
        "Area": ("0", "67000", "100000", "26111"),
        "Unknown": ("84750", "56000", "11083", "6111"),
    }
    geometry_ok = all(
        name in zone_map
        and tuple(zone_map[name].get(attr) for attr in ("x", "y", "w", "h"))
        == expected
        for name, expected in expected_geometry.items()
    )
    legend = next(
        (z for z in zones if z.get("type-v2") == "color" and z.get("name") == "Map"),
        None,
    )
    checks.add(
        "dashboard-fixed-size-and-zones",
        size is not None
        and size.get("maxwidth") == "1200"
        and size.get("maxheight") == "900"
        and size.get("sizing-mode") == "fixed"
        and geometry_ok
        and legend is not None
        and f"[{ds_name}].[usr:" in legend.get("param", ""),
        f"size={size.get('maxwidth') if size is not None else None}x{size.get('maxheight') if size is not None else None} legend={legend is not None}",
    )

    actions = root.findall("actions/edit-parameter-action")
    action_state = next((a for a in actions if a.get("caption") == "Select State"), None)
    action_species = next((a for a in actions if a.get("caption") == "Select Species"), None)

    def param_action_ok(action, worksheet: str, field_fragment: str, parameter: str) -> bool:
        if action is None:
            return False
        source = action.find("source")
        params = {p.get("name"): p.get("value", "") for p in action.findall("params/param")}
        clear = action.find("clear-option")
        return (
            source is not None
            and source.get("worksheet") == worksheet
            and field_fragment in params.get("source-field", "")
            and params.get("target-parameter") == f"[Parameters].{parameter}"
            and clear is not None
            and clear.get("type") == "assign-fixed-value"
            and clear.get("value") == "s:LROOT:"
        )

    checks.add(
        "actions-parameter-driven",
        param_action_ok(action_state, "Map", "[none:State Name:", state_param)
        and param_action_ok(
            action_species, "Bar", "[none:", species_param
        ),
        f"actions={[a.get('caption') for a in actions]}",
    )

    # --- SDK round-trip ----------------------------------------------------
    from cwtwb import TWBEditor

    round_trip = TWBEditor.open_existing(str(TWBX))
    checks.add(
        "sdk-round-trip",
        set(round_trip.list_worksheets()) == {"Bar", "Map", "Area", "Unknown"},
        f"worksheets={round_trip.list_worksheets()}",
    )

    # --- cross-filter oracle for Cloud state evidence ----------------------
    states = dict(data["states"])
    species = dict((name, count) for name, count in data["alabama_species"])
    other_alabama = data["alabama_total"] - sum(
        species.get(name, 0) for name, _ in data["species_top10"]
    )
    cross_filter = {
        "default": {
            "total": data["total_rows"],
            "bar_rows": [list(item) for item in data["species_top10"]]
            + [["Other", data["other_rows"]]],
            "unknown": data["null_state_rows"],
        },
        "alabama": {
            "total": data["alabama_total"],
            "bar_rows": [
                [name, species.get(name, 0)] for name, _ in data["species_top10"]
            ]
            + [["Other", other_alabama]],
            "unknown": data["null_state_rows"],
            "area_years": data["alabama_years"],
        },
        "unknown-bird": {
            "total": data["unknown_bird_total"],
            "area_years": data["unknown_bird_years"],
            "unknown": data["unknown_bird_null_state"],
        },
        "alabama-unknown-bird": {
            "total": data["alabama_unknown_bird"],
            "unknown": data["unknown_bird_null_state"],
        },
    }
    # acceptance: species-selection
    checks.add(
        "oracle-cross-filter-values",
        cross_filter["alabama"]["total"] == states["Alabama"]
        and cross_filter["alabama-unknown-bird"]["total"] == 955
        and cross_filter["unknown-bird"]["total"] == 101_949,
        f"alabama={cross_filter['alabama']['total']} "
        f"alabama/unknown-bird={cross_filter['alabama-unknown-bird']['total']} "
        f"unknown-bird={cross_filter['unknown-bird']['total']}",
    )

    # acceptance: combined-selection-and-clear
    # REST parameter states prove the rendered calculations; the action contract
    # above proves clear-to-empty wiring. Neither claims a browser click test.
    for state in ("default", "alabama", "unknown-bird", "alabama-unknown-bird", "clear"):
        suffix = "" if state == "default" else "-" + state
        expected_area = {
            "default": EXPECTED_TOTAL, "clear": EXPECTED_TOTAL,
            "alabama": 1842, "unknown-bird": 101949, "alabama-unknown-bird": 955,
        }[state]
        expected_bar = 1842 if state in {"alabama", "alabama-unknown-bird"} else EXPECTED_TOTAL
        expected_map = 101949 if "unknown-bird" in state else EXPECTED_TOTAL
        expected_unknown = data["unknown_bird_null_state"] if "unknown-bird" in state else EXPECTED_NULL_STATE
        for sheet, expected in (("bar", expected_bar), ("area", expected_area), ("map", expected_map), ("unknown", expected_unknown)):
            path = ITERATION_DIR / "outputs" / f"cloud-replica-{sheet}{suffix}.csv"
            if path.exists():
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                actual = sum(int(row["Wildlife Incidents"].replace(",", "") or "0") for row in rows)
                checks.add(f"cloud-{state}-{sheet}", actual == expected, f"actual={actual} expected={expected}")

    report = {
        "case_id": "wow-2022-ww01-let-s-analyse-wildlife-strikes",
        "artifact": {
            "path": "outputs/replicated-workbook.twbx",
            "sha256": sha256(TWBX),
        },
        "oracle": data,
        "cross_filter_expectations": cross_filter,
        "checks": checks.items,
        "status": "pass" if checks.ok else "fail",
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n{report['status'].upper()}  {len(checks.items)} checks  -> {EVIDENCE}")
    return 0 if checks.ok else 1


if __name__ == "__main__":
    sys.exit(main())
