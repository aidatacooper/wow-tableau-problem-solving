"""Independently verify the Hans Rosling scatter from the locked extracts.

The verifier reads only the locked Hyper extract, the written case files and the
built TWBX. It never opens the author workbook or imports the builder. It
recomputes the year/income/life-expectancy/population/region facts straight from
the four physical tables and checks the native workbook contracts that carry
them.

Automated acceptance IDs:
  - rosling-country-facts
  - rosling-log-income-axis
  - rosling-region-highlight
"""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry, TableName

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "rosling-country-facts",
    "rosling-log-income-axis",
    "rosling-region-highlight",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_03_17_Hans_Rosling"

LE_TABLE = "Extract (Extract.Extract)_1A34BF9035E143049C56F3B620E979E3"
POP_TABLE = "Extract (Extract.Extract)_0243FA6460B04031BAB2F3510CA4ACE1"
INC_TABLE = "Extract (Extract.Extract)_B6DF8AE667624AD89112BA1378751D0A"
REGION_TABLE = "list-of-countries-etc_9E3A85DC981044D1ACD35A49A8CDC359"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle():
    """Recompute the raw country/year facts from the locked Hyper extract."""
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    path = HERE / item["file"]
    assert digest(path) == item["sha256"], "locked extract hash changed"

    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,
        Connection(hp.endpoint, str(path)) as connection,
    ):
        query = lambda sql: connection.execute_list_query(sql)

        def facts(table):
            return {
                (country, year): value
                for country, year, value in query(
                    f'SELECT "country","Pivot Field Names","Pivot Field Values" '
                    f'FROM {TableName("Extract", table)}'
                )
            }

        life = facts(LE_TABLE)
        population = facts(POP_TABLE)
        income = facts(INC_TABLE)
        regions = {
            name: region
            for name, region in query(
                f'SELECT "name","eight_regions" FROM {TableName("Extract", REGION_TABLE)}'
            )
        }

    # Every country/year cell appears once per measure table.
    for table, values in (("life", life), ("population", population), ("income", income)):
        assert len(values) == 41070, f"{table} cell count changed"

    # The measure tables share the same country/year keys.
    assert set(life) == set(population) == set(income)
    assert len(life) == 185 * 222

    # Year domain and the article's upper bound.
    years = {year for _, year in life}
    assert min(years) == 1800 and max(years) == 2021

    # A representative modern year: every mapped country has all three facts.
    mapped = {
        country
        for country, _ in life
        if country in regions and regions[country]
    }
    assert len(mapped) == 185
    sample = [
        (country, year, income[(country, year)], life[(country, year)], population[(country, year)])
        for (country, year) in income
        if year == 2019 and country in mapped
    ]
    assert len(sample) == 185
    missing_life = 0
    for country, year, inc, life_exp, pop in sample:
        assert inc is not None and inc > 0, f"{country} income missing"
        assert pop is not None and pop > 0, f"{country} population missing"
        # Life expectancy is null for a handful of countries even in a modern
        # year; when present it must sit in a plausible human range.
        if life_exp is None:
            missing_life += 1
        else:
            assert 20 <= life_exp <= 90, f"{country} life expectancy {life_exp}"
    assert missing_life <= 5, f"too many null life-expectancy cells: {missing_life}"

    # The log axis is what makes the story readable: income spans three orders
    # of magnitude in 2019.
    incomes_2019 = [inc for _, year, inc, _, _ in sample]
    assert max(incomes_2019) / min(incomes_2019) > 100

    # Region assignment is total over the mapped countries.
    assert all(regions[country] for country in mapped)

    return {
        "extract_sha256": item["sha256"],
        "cell_count": len(life),
        "year_min": min(years),
        "year_max": max(years),
        "mapped_countries": len(mapped),
        "income_ratio_2019": max(incomes_2019) / min(incomes_2019),
        "region_count": len(set(regions.values())),
    }


def workbook():
    assert OUTPUT.is_file(), f"missing output: {OUTPUT}"
    with ZipFile(OUTPUT) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".twb"))
        root = etree.fromstring(archive.read(name))
    return root


def worksheet(root, name):
    node = root.find(f".//worksheets/worksheet[@name='{name}']")
    assert node is not None, f"missing worksheet {name}"
    return node


def verify():
    facts = oracle()
    root = workbook()

    scatter = worksheet(root, "Scatter")
    assert scatter.find(".//mark[@class='Circle']") is not None, "scatter mark changed"

    # The three measures come from the normalized facts table; the axes are
    # explicit dimension-typed fields so the view renders (see analysis.md).
    datasource = next(
        (
            node
            for node in root.findall(".//datasource")
            if node.find("connection[@class='federated']") is not None
        ),
        None,
    )
    assert datasource is not None, "federated datasource missing"
    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in datasource.findall("column")
        if column.find("calculation") is not None
    }
    assert formulas["Income Axis"] == "[Income]"
    assert formulas["Life Expectancy Axis"] == "[Life Expectancy]"
    assert formulas["Has Region"] == "NOT ISNULL([Region])"

    # The normalized extract is a single physical table; the workbook must not
    # depend on the multi-table relationship path that Cloud refuses to load.
    relations = root.findall(".//object-graph/objects/object")
    assert len(relations) == 1, "expected a single normalized extract object"
    object_graph = root.find(".//object-graph")
    assert not object_graph.findall("relationships/relationship"), (
        "normalized extract must not declare logical relationships"
    )
    maps = root.findall(".//datasource/connection[@class='federated']/cols/map")
    assert {m.get("key") for m in maps} >= {
        "[Country]",
        "[Year]",
        "[Life Expectancy]",
        "[Income]",
        "[Population]",
        "[Region]",
    }, "normalized columns are not mapped"

    # The scatter plots income (x) against life expectancy (y) at country grain.
    caption_by_calc = {
        column.get("name", "").strip("[]"): column.get("caption")
        for column in datasource.findall("column")
        if column.get("name", "").startswith("[Calculation_")
    }

    def shelf_captions(text):
        import re

        found = set()
        for token in re.findall(r"Calculation_[0-9A-F]+", text or ""):
            caption = caption_by_calc.get(token)
            if caption:
                found.add(caption)
        return found

    rows = scatter.findtext(".//rows") or ""
    cols = scatter.findtext(".//cols") or ""
    assert "Life Expectancy Axis" in shelf_captions(rows), "life expectancy is not on rows"
    assert "Income Axis" in shelf_captions(cols), "income is not on columns"
    encodings = scatter.find(".//encodings")
    assert encodings.find("size") is not None, "population size encoding missing"
    assert encodings.find("color") is not None, "region color encoding missing"
    assert encodings.find("lod") is not None, "country detail encoding missing"

    # rosling-log-income-axis: the income axis carries a logarithmic scale.
    scale = scatter.find(".//style-rule[@element='axis']/encoding[@scale='log']")
    assert scale is not None, "income axis is not logarithmic"

    # rosling-country-facts: the scatter is restricted to mapped countries and
    # to the selected year, and the year card echoes the parameter.
    filters = scatter.findall(".//filter")
    assert filters, "scatter has no filters"
    filtered = {
        caption_by_calc.get(token)
        for f in filters
        for token in __import__("re").findall(r"Calculation_[0-9A-F]+", f.get("column", ""))
    }
    assert "Has Region" in filtered, "null-region exclusion missing"
    assert "Selected Year" in filtered, "year selection missing"
    # The year card echoes the parameter value through the Year Label field.
    year_card = worksheet(root, "Year")
    year_text = etree.tostring(year_card).decode()
    year_label = next(
        (
            column
            for column in datasource.findall("column")
            if column.get("caption") == "Year Label"
        ),
        None,
    )
    assert year_label is not None, "year label field missing"
    assert "Parameters" in (year_label.find("calculation").get("formula") or ""), (
        "year label is not parameter-driven"
    )
    assert year_label.get("name", "").strip("[]") in year_text, (
        "year card does not render the year label"
    )

    # rosling-region-highlight: a highlight action sources Region into Scatter.
    actions = root.findall(".//actions/action")
    highlights = [
        action
        for action in actions
        if (action.find("command") is not None and action.find("command").get("command") == "tsc:brush")
    ]
    assert highlights, "no highlight action"
    assert any(
        action.find("source").get("worksheet") == "Region"
        and action.find("source").get("dashboard") == DASHBOARD_NAME
        and "Region"
        in (
            action.find("command/param[@name='field-captions']").get("value")
            or ""
        )
        for action in highlights
    ), "highlight action does not source Region"
    target = highlights[0].find("command/param[@name='target']").get("value") or ""
    assert target == DASHBOARD_NAME, "highlight action target changed"

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
