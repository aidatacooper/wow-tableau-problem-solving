"""Independently verify the WW22 "structure the unstructured" Airbnb workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Re-implements the article's regular-expression bedroom extraction in Python,
recomputes the price bins, and checks the native workbook contracts.

Automated acceptance IDs:
  - ww22-bedroom-regex
  - ww22-bedroom-groups
  - ww22-price-bins
  - ww22-histogram
  - ww22-map
  - ww22-interactions
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
    "ww22-bedroom-regex",
    "ww22-bedroom-groups",
    "ww22-price-bins",
    "ww22-histogram",
    "ww22-map",
    "ww22-interactions",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "Can You Find a Place to Stay?"
TABLE = TableName("Extract", "Extract")
BIN_SIZE = 100

CLEAN_RE = re.compile(
    r"\s+\b(?:BR|br|BDRM|bdrm|beds|bed|bd|rooms|Room|bed |BEDS|bedroom"
    r"|-bedroom|bedrooms)\b"
)
EXTRACT_RE = re.compile(r"(\d+ ?(Bedroom))")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(description: str) -> str:
    return CLEAN_RE.sub(" Bedroom ", description)


def group(description: str) -> str | None:
    if "studio" in clean(description).lower():
        return "Studio"
    match = EXTRACT_RE.search(clean(description))
    return match.group(1) if match else None


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
            f'SELECT "name","description","price" FROM {TABLE}'
        )
    assert len(rows) == 1189, "row count changed"
    groups = collections.Counter()
    bins = collections.Counter()
    matched = 0
    for _name, description, price in rows:
        size = group(description)
        groups[size] += 1
        if size is not None:
            matched += 1
        bins[(price // BIN_SIZE) * BIN_SIZE] += 1
    # The article's grouped labels roll 5+ bedrooms into one bucket.
    rolled = collections.Counter()
    for label, count in groups.items():
        if label is None:
            rolled["Other"] += count
        elif label == "Studio" or label.endswith("Bedroom") and label.split()[0] in {
            "1", "2", "3", "4"
        }:
            key = label.replace("Bedroom", "Bedrooms")
            rolled[key] += count
        else:
            rolled["More Than 5 Bedrooms"] += count
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "matched_rows": matched,
        "raw_groups": {k or "Other": v for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))},
        "rolled_groups": dict(sorted(rolled.items())),
        "price_bins": {str(k): v for k, v in sorted(bins.items())},
        "avg_price": round(sum(price for _n, _d, price in rows) / len(rows), 3),
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


def labelled(reference: str, names: dict) -> str:
    if not reference:
        return ""
    parts = re.findall(r"\[([^\]]+)\]", reference)
    for token in reversed(parts):
        if token.startswith("federated."):
            continue
        match = re.match(
            r"^(?:usr|sum|avg|attr|none|io|mn|yr|dy|cnt|cum|ctd):(.*?):(?:qk|nk|ok)$",
            token,
        )
        if match:
            return names.get(f"[{match.group(1)}]", match.group(1))
        return names.get(f"[{token}]", token)
    return ""


def verify():
    facts = oracle()
    root = workbook()
    calc = {}
    for column in root.findall(".//datasource/column"):
        node = column.find("calculation")
        if node is not None:
            calc[column.get("caption")] = node.get("formula") or ""
    names = captions(root)

    # --- ww22-bedroom-regex -------------------------------------------------
    cleaned = calc["Step 1 - Clean Up Bedroom"]
    assert "REGEXP_REPLACE" in cleaned and "description" in cleaned
    for token in ("bedroom", "bdrm", "bed", "rooms", "BDRM", "beds"):
        assert token in cleaned, token
    sizes = calc["Step 2 - Group Sizes"]
    assert "CONTAINS" in sizes and "studio" in sizes
    assert "REGEXP_EXTRACT" in sizes and "(\\d+ ?(Bedroom))" in sizes
    assert facts["matched_rows"] == facts["rows"], facts

    # --- ww22-bedroom-groups ------------------------------------------------
    # add_group writes a <calculation class='categorical-bin'> column whose
    # <bin value> is the group label and whose <value> children are the source
    # members.
    group_column = next(
        (
            column
            for column in root.findall(".//datasource/column")
            if column.get("caption") == "Step 2 - Group Sizes (group)"
        ),
        None,
    )
    assert group_column is not None, "bedroom group missing"
    bins = {
        (bin_el.get("value") or "").strip('"'): [
            (value.text or "").strip('"') for value in bin_el.findall("value")
        ]
        for bin_el in group_column.findall("calculation/bin")
    }
    for label in ("Studio", "1 Bedroom", "2 Bedrooms", "3 Bedrooms", "4 Bedrooms"):
        assert label in bins, (label, list(bins))
    assert sorted(bins["More Than 5 Bedrooms"]) == sorted(
        [
            "5 Bedroom", "6 Bedroom", "7 Bedroom", "8 Bedroom",
            "9 Bedroom", "10 Bedroom", "12 Bedroom", "16 Bedroom",
        ]
    ), bins["More Than 5 Bedrooms"]
    rolled = facts["rolled_groups"]
    assert rolled.get("Studio") == 503, rolled
    assert rolled.get("More Than 5 Bedrooms") == 89, rolled

    def resolve(formula: str) -> str:
        """Normalize internal calculation names and qualified parameters."""
        text = re.sub(r"\[Parameters\]\.\[Parameter \d+\]", "[Bin Size]", formula)

        def replace(match):
            token = match.group(1)
            return f"[{names.get('[' + token + ']', token)}]"

        return re.sub(r"\[([^\]]+)\]", replace, text)

    # --- ww22-price-bins ----------------------------------------------------
    assert resolve(calc["Price per Night Min"]) == (
        "FLOOR([price]/[Bin Size])*[Bin Size]"
    ), resolve(calc["Price per Night Min"])
    assert resolve(calc["Price per Night Max"]) == (
        "[Price per Night Min]+[Bin Size]"
    ), resolve(calc["Price per Night Max"])
    assert calc["# of Listings"] == "COUNTD([name])"
    assert resolve(calc["Window Avg Price"]) == (
        "WINDOW_SUM(SUM([price])) / WINDOW_SUM([# of Listings])"
    ), resolve(calc["Window Avg Price"])
    assert facts["price_bins"]["0"] == 572, facts["price_bins"]
    assert facts["price_bins"]["100"] == 425, facts["price_bins"]

    # --- ww22-histogram -----------------------------------------------------
    histo = root.find(".//worksheets/worksheet[@name='histo']")
    assert histo is not None, "missing histo worksheet"
    cols = histo.findtext("table/cols") or ""
    rows = histo.findtext("table/rows") or ""
    assert "Price per Night Min" in cols or any(
        labelled(ref, names) == "Price per Night Min"
        for ref in re.findall(r"\[[^\]]+\]", cols)
    ), cols
    assert "# of Listings" in rows or any(
        labelled(ref, names) == "# of Listings"
        for ref in re.findall(r"\[[^\]]+\]", rows)
    ), rows
    pane = histo.find("table/panes/pane")
    assert pane.find("mark").get("class") == "Bar"
    assert pane.find("encodings/lod") is not None, "average price is not on Detail"
    ref_line = histo.find(".//reference-line")
    assert ref_line is not None and ref_line.get("formula") == "average"
    assert ref_line.get("label") == "Avg: <Value>"
    histo_filters = histo.findall(".//view/filter")
    assert any(
        f.get("class") == "categorical"
        and any(
            "Studio" in (m.get("member") or "")
            for m in f.findall(".//groupfilter")
        )
        for f in histo_filters
    ), "bedroom filter missing on histo"

    # --- ww22-map -----------------------------------------------------------
    assert "MAKEPOINT" in calc["Listing Location"]
    map_sheet = root.find(".//worksheets/worksheet[@name='map']")
    assert map_sheet is not None, "missing map worksheet"
    assert map_sheet.find(".//mapsources/mapsource[@name='Tableau']") is not None
    map_pane = map_sheet.find("table/panes/pane")
    assert map_pane.find("encodings/lod") is not None, "listing_url not on Detail"
    map_layer = map_sheet.find(".//style-rule[@element='map-layer']")
    assert map_layer is not None and any(
        f.get("id") == "Area Code Boundaries" and f.get("value") == "true"
        for f in map_layer.findall("format")
    ), "Area Code Boundaries layer missing"

    # --- ww22-interactions --------------------------------------------------
    filters = [
        a for a in root.findall(".//actions/action")
        if a.find("command") is not None
        and a.find("command").get("command") == "tsc:tsl-filter"
    ]
    assert len(filters) == 2, f"expected two filter actions, got {len(filters)}"
    sources = {a.find("source").get("worksheet") for a in filters}
    assert sources == {"histo", "map"}, sources
    url_actions = [
        a for a in root.findall(".//actions/action")
        if a.find("link") is not None and "listing_url" in (a.find("link").get("expression") or "")
    ]
    assert url_actions, "listing URL action missing"
    assert url_actions[0].get("caption") == "See the listing"
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"

    evidence = {
        "scope": "Locked-extract oracle plus native histogram/map workbook contracts.",
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
