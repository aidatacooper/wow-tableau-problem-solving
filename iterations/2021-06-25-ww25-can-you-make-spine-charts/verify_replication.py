"""Independently verify the WW25 "Can You Make Spine Charts?" workbook.

Reads only the locked Hyper extract, the written case files and the built TWBX.
Re-implements the selected-university average, the overall average and the
min/max/quartile references in Python, then checks the native workbook
contracts.

Automated acceptance IDs:
  - ww25-parameter-selection
  - ww25-spine-values
  - ww25-reference-lines
  - ww25-legend
  - ww25-layout
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
    "ww25-parameter-selection",
    "ww25-spine-values",
    "ww25-reference-lines",
    "ww25-legend",
    "ww25-layout",
]
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
DASHBOARD_NAME = "2021_06_23_WW25_Spine_Chart"
TABLE = TableName("Extract", "Extract")

DEFAULT_UNIVERSITY = "The University of Liverpool"
LEGEND_UNIVERSITY = "Middlesex University"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


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
            f'SELECT "Question Number","University","% Agree" FROM {TABLE}'
        )

    by_question: dict[str, list[float]] = {}
    by_university: dict[tuple[str, str], list[float]] = {}
    for question, university, agree in rows:
        by_question.setdefault(question, []).append(agree)
        by_university.setdefault((question, university), []).append(agree)

    spine = {}
    for question, values in by_question.items():
        selected = by_university.get((question, DEFAULT_UNIVERSITY))
        overall = sum(values) / len(values)
        spine[question] = {
            "overall": round(overall, 4),
            "university": round(sum(selected) / len(selected), 4) if selected else None,
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "lower_quartile": round(percentile(values, 0.25), 4),
            "upper_quartile": round(percentile(values, 0.75), 4),
        }
    legend = {
        "avg": round(
            sum(by_university[(q, LEGEND_UNIVERSITY)][0] for q in by_question)
            / len(by_question),
            4,
        )
    }
    assert len(rows) == 10095, len(rows)
    assert len(by_question) == 27, len(by_question)
    assert legend["avg"] == 0.7476, legend
    return {
        "extract_sha256": item["sha256"],
        "rows": len(rows),
        "questions": sorted(by_question),
        "spine": spine,
        "legend_avg": legend["avg"],
        "default_university": DEFAULT_UNIVERSITY,
        "legend_university": LEGEND_UNIVERSITY,
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


def resolve(formula, names, parameters):
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

    def resolved(caption):
        return re.sub(r"\s+", " ", resolve(calc[caption], names, parameters)).strip()

    # --- ww25-parameter-selection ------------------------------------------
    param = root.find(
        ".//datasource[@name='Parameters']/column[@caption='pUniversity']"
    )
    assert param is not None, "pUniversity parameter missing"
    assert param.get("value") == f'"{DEFAULT_UNIVERSITY}"', param.get("value")
    members = [
        (m.get("value") or "").strip('"') for m in param.findall("members/member")
    ]
    assert DEFAULT_UNIVERSITY in members and LEGEND_UNIVERSITY in members, members[:5]
    assert resolved("University Avg") == (
        "AVG(IF [University] = [pUniversity] THEN [% Agree] END)"
    ), resolved("University Avg")
    assert resolved("Overall Avg") == "AVG([% Agree])", resolved("Overall Avg")
    assert resolved("Delta") == (
        "[University Avg Axis] - [Overall Avg Axis]"
    ), resolved("Delta")
    assert resolved("Colour") == "[Delta]>=0", resolved("Colour")
    assert resolved("Lower Quartile") == "PERCENTILE([% Agree],0.25)"
    assert resolved("Upper Quartile") == "PERCENTILE([% Agree],0.75)"

    # --- ww25-spine-values --------------------------------------------------
    assert len(facts["questions"]) == 27, facts["questions"]
    # The author's published screenshot: Q01 Liverpool 89.8%, overall 89.1%,
    # Delta +0.70%▲; Q02 Liverpool 82.4%, overall 84.7%, Delta 2.30%▼.
    assert facts["spine"]["Q01"]["university"] == 0.8983, facts["spine"]["Q01"]
    assert facts["spine"]["Q01"]["overall"] == 0.8913, facts["spine"]["Q01"]
    assert facts["spine"]["Q02"]["university"] == 0.8243, facts["spine"]["Q02"]
    assert facts["spine"]["Q02"]["overall"] == 0.8473, facts["spine"]["Q02"]
    assert facts["spine"]["Q01"]["min"] == 0.6 and facts["spine"]["Q01"]["max"] == 1.0
    assert facts["spine"]["Q01"]["lower_quartile"] == 0.8613
    assert facts["spine"]["Q01"]["upper_quartile"] == 0.9252

    # --- ww25-reference-lines ----------------------------------------------
    viz = root.find(".//worksheets/worksheet[@name='Viz']")
    assert viz is not None, "missing Viz worksheet"
    rows = viz.findtext("table/rows") or ""
    for pill in (
        "none:Question Number:nk",
        "none:Question Text:nk",
        "ok]",  # the discrete measure pills
    ):
        assert pill in rows, (pill, rows)
    cols = viz.findtext("table/cols") or ""
    assert cols.endswith("qk]"), cols
    pane = viz.find("table/panes/pane")
    assert pane.find("mark").get("class") == "Circle"
    color = pane.find("encodings/color")
    assert color is not None, etree.tostring(pane)
    token = re.search(r"\[(?:usr|none):([^:\]]+):(?:nk|qk|ok)\]", color.get("column"))
    assert token and names.get(f"[{token.group(1)}]") == "Colour", color.get("column")
    lod_labels = {
        names.get(f"[{m.group(1)}]", m.group(1))
        for node in pane.findall("encodings/lod")
        for m in [re.search(r"\[(?:avg|min|max|sum|usr):([^:\]]+):(?:qk|ok)\]", node.get("column") or "")]
        if m
    }
    for expected in ("% Agree", "Lower Quartile", "Upper Quartile"):
        assert expected in lod_labels, (expected, sorted(lod_labels))
    refs = viz.findall(".//reference-line")
    assert len(refs) >= 4, len(refs)
    formulas = [r.get("formula") for r in refs]
    assert "average" in formulas and "min" in formulas and "max" in formulas, formulas
    # The min/max pair and the quartile pair are bands (paired ids + fill).
    refband = viz.find(".//style-rule[@element='refband']")
    assert refband is not None, "reference band style missing"
    fills = [f for f in refband.findall("format") if f.get("attr") == "fill-color"]
    assert len(fills) >= 2, etree.tostring(refband)
    fill_ids = {f.get("id") for f in fills}
    paired = {
        line.get("paired-id") for line in refs if line.get("paired-id")
    }
    assert fill_ids <= paired, (fill_ids, paired)

    # --- ww25-legend --------------------------------------------------------
    assert resolved("Legend Avg") == (
        f"AVG(IF [University] = '{LEGEND_UNIVERSITY}' THEN [% Agree] END)"
    ), resolved("Legend Avg")
    assert resolved("Legend Colour") == (
        "[Legend Avg] - [Overall Avg Axis] >=0"
    ), resolved("Legend Colour")
    assert facts["legend_avg"] == 0.7476, facts["legend_avg"]
    legend = root.find(".//worksheets/worksheet[@name='Legend']")
    assert legend is not None, "missing Legend worksheet"
    legend_refs = legend.findall(".//reference-line")
    labels = {r.get("label") for r in legend_refs}
    assert {"Overall Avg", "Overall Min", "Overall Max"} <= labels, labels

    # --- ww25-layout --------------------------------------------------------
    dashboard = root.find(f".//dashboards/dashboard[@name='{DASHBOARD_NAME}']")
    assert dashboard is not None, "dashboard missing"
    zone_names = {
        z.get("name") for z in dashboard.findall(".//zones//zone") if z.get("name")
    }
    assert {"Viz", "Legend"} <= zone_names, zone_names
    size = dashboard.find("size")
    assert size.get("maxwidth") == "1366" and size.get("maxheight") == "900", \
        etree.tostring(size)

    evidence = {
        "scope": "Locked-extract oracle plus native parameter/reference/legend contracts.",
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
            "rows": result["facts"]["rows"],
            "questions": len(result["facts"]["questions"]),
            "Q01": result["facts"]["spine"]["Q01"],
            "Q02": result["facts"]["spine"]["Q02"],
            "legend_avg": result["facts"]["legend_avg"],
        },
        indent=2,
    ))
    print("PASS")
