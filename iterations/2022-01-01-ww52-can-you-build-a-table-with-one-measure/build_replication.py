"""Build WW52 (one-measure table) from the locked Hyper through public cwtwb APIs.

The challenge is one measure rendering two different quantities: the detail
cells show SUM(Sales) while each Category subtotal row shows that category's
share of the month total.  A single calculated field decides per cell which of
the two to emit by asking how many marks share the cell's partition (SIZE()).
"""

from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
import json
import tempfile

import cwtwb
from cwtwb import TWBEditor, convert_workbook

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"

# Author number formats: currency for detail/grand-total cells, a signed
# percentage for the subtotal rows.  The percentage carries a negative value so
# the diverging palette paints it green; the ``0%;0%`` pattern hides the sign.
DETAIL_FORMAT = 'c"$"#,##0;-"$"#,##0'
SUBTOTAL_FORMAT = "*0%;0%"

SHEET = "Table"
DASHBOARD = "2021 Week 52 - Single Table One Measure"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    data = next((HERE / "inputs").glob("*.hyper"))

    editor = TWBEditor("")
    editor.set_hyper_connection(str(data), table_name="Extract")

    # SIZE() = 1 for an ordinary detail cell and also for the grand-total row;
    # it is > 1 for a Category subtotal row, whose partition holds one mark per
    # category.  That single test is what lets one measure carry both numbers.
    editor.add_calculated_field(
        "Size", "SIZE()", datatype="integer", table_calc={"ordering-type": "Rows"}
    )
    editor.add_calculated_field(
        "Custom Measure",
        "IF [Size] = 1 THEN SUM([Sales]) ELSE -SUM([Sales])/TOTAL(SUM([Sales])) END",
        datatype="real",
        table_calc={"ordering-type": "Rows"},
    )

    editor.add_worksheet(SHEET)
    editor.configure_chart(
        SHEET,
        mark_type="Square",
        columns=["MONTH(Order Date)"],
        rows=["Category", "Sub-Category"],
        color="Custom Measure",
        label="Custom Measure",
        # Both table calculations are addressed by Category, so a subtotal
        # row's partition is the three Category marks of that month and
        # TOTAL(SUM(Sales)) resolves to the month's grand total.
        table_calc_overrides={
            "Custom Measure": [
                {"ordering-field": "Category", "ordering-type": "Field"},
                {"field": "Size", "ordering-field": "Category", "ordering-type": "Field"},
            ]
        },
    )
    editor.set_worksheet_rich_title(
        SHEET, [{"text": "Can you build a table with one measure?", "fontalignment": 1}]
    )

    editor.configure_subtotals(
        SHEET,
        measure_fields=["Custom Measure"],
        aggregation="Automatic",
        subtotal_fields=["Category"],
        label="% of Total",
    )
    editor.configure_worksheet_style(
        SHEET,
        show_row_totals=True,
        hide_col_field_labels=True,
        cell_formats=[
            {"field": "Custom Measure", "attr": "text-format", "value": DETAIL_FORMAT},
            {
                "field": "Custom Measure",
                "attr": "text-format",
                "data_class": "total",
                "value": DETAIL_FORMAT,
            },
            {
                "field": "Custom Measure",
                "attr": "text-format",
                "data_class": "subtotal",
                "value": SUBTOTAL_FORMAT,
            },
            {"attr": "width", "value": 127},
        ],
        header_formats=[
            {
                "field": "Category",
                "attr": "total-label",
                "data_class": "total",
                "value": "Total",
            },
            # Tableau renders the subtotal label in the column *after* the
            # subtotaled dimension, so the format is scoped to Sub-Category.
            {
                "field": "Sub-Category",
                "attr": "total-label",
                "data_class": "subtotal",
                "value": "% of Total",
            },
        ],
        table_dividers=[{"scope": "cols", "div-level": 1}],
        color_style={
            "field": "Custom Measure",
            "palette": "green_blue_white_diverging_10_0",
            "center": 0.0,
            "include_totals": True,
        },
        pane_mark_style={"mark-labels-show": "true"},
    )

    def zone(kind, x, y, w, h, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1000 * 100000),
                "y": round(y / 600 * 100000),
                "w": round(w / 1000 * 100000),
                "h": round(h / 600 * 100000),
            },
            # The author's zones all carry a 4px inner margin.
            "style": {"margin": 4},
            **kwargs,
        }

    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=600,
        worksheet_names=[SHEET],
        layout={
            "type": "container",
            "direction": "floating",
            # The author's root layout zone carries an 8px margin.
            "style": {"margin": 8},
            "children": [
                zone("worksheet", 8, 8, 984, 520, name=SHEET, fit="entire"),
                zone(
                    "text",
                    8,
                    528,
                    328,
                    32,
                    runs=[
                        {
                            "text": "CHALLENGE BY : LUKE STANKE",
                            "font_name": "Tableau Medium",
                            "font_size": 8,
                            "font_alignment": 0,
                        }
                    ],
                ),
                zone(
                    "text",
                    336,
                    528,
                    328,
                    32,
                    runs=[
                        {
                            "text": "#WOW2021  |  WEEK 52",
                            "font_name": "Tableau Medium",
                            "font_size": 8,
                            "font_alignment": 1,
                        }
                    ],
                ),
                zone(
                    "text",
                    664,
                    528,
                    328,
                    32,
                    runs=[
                        {
                            "text": "RECREATED BY : CW TWB",
                            "font_name": "Tableau Medium",
                            "font_size": 8,
                            "font_alignment": 2,
                        }
                    ],
                ),
                zone(
                    "text",
                    8,
                    560,
                    984,
                    32,
                    runs=[
                        {
                            "text": "http://www.workout-wednesday.com/wow2021_w52/",
                            "font_size": 8,
                            "font_alignment": 1,
                            "hyperlink": 'tabdoc:load-url url="http://www.workout-wednesday.com/wow2021_w52/"',
                        }
                    ],
                ),
            ],
        },
    )

    output = OUTPUTS / "replicated-workbook.twbx"
    staged = OUTPUTS / "_staged.twbx"
    try:
        editor.save(staged)
        workbook = _place_totals_on_top(staged, output)
        provenance = {
            "version": version("cwtwb"),
            "module": str(Path(cwtwb.__file__).resolve()),
            "module_sha256": sha256(Path(cwtwb.__file__).read_bytes()).hexdigest(),
            "extract_sha256": sha256(data.read_bytes()).hexdigest(),
            "workbook_sha256": sha256(workbook.read_bytes()).hexdigest(),
            "authoring_route": "cwtwb_public_api_plus_native_json_on_top",
            "sheets": [SHEET],
            "dashboard": DASHBOARD,
        }
        (OUTPUTS / "build-provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )
        return workbook
    finally:
        staged.unlink(missing_ok=True)


def _place_totals_on_top(staged: Path, output: Path) -> Path:
    """Move the row totals above their group.

    ``cwtwb`` 0.29.0a2 writes ``<rows total="true">`` but exposes no API for
    Tableau's ``onTop`` attribute, which is what puts the grand total and the
    Category subtotals at the top of the table (the challenge's explicit
    requirement).  The documented native-JSON representation is used to set
    that one attribute on the worksheet we just authored; nothing from the
    author workbook is read or copied.
    """
    with tempfile.TemporaryDirectory() as scratch:
        document_path = Path(scratch) / "workbook.json"
        convert_workbook(staged, document_path, force=True)
        payload = json.loads(document_path.read_text(encoding="utf-8"))
        rows = _find_rows_shelf(payload["document"]["root"], SHEET)
        rows.setdefault("attributes", {})["onTop"] = "true"
        # Negative subtotal shares and positive dollars need separate ranges.
        # A symmetric range makes the small negative percentages almost white.
        for node in _iter_nodes(payload["document"]["root"]):
            attrs = node.get("attributes", {})
            if node.get("tag") == "encoding" and attrs.get("attr") == "color":
                attrs["symmetric"] = "false"
        document_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        convert_workbook(document_path, output, force=True)
    return output


def _find_rows_shelf(node: dict, worksheet_name: str) -> dict:
    """Return the ``rows`` shelf node of one worksheet in the native JSON tree."""
    for candidate in _iter_nodes(node):
        if candidate.get("tag") != "worksheet":
            continue
        if (candidate.get("attributes") or {}).get("name") != worksheet_name:
            continue
        for child in candidate.get("children", []):
            if child.get("tag") != "table":
                continue
            for grandchild in child.get("children", []):
                if grandchild.get("tag") == "rows":
                    return grandchild
    raise AssertionError(f"No rows shelf for worksheet '{worksheet_name}'")


def _iter_nodes(node: dict):
    yield node
    for child in node.get("children", []):
        yield from _iter_nodes(child)


if __name__ == "__main__":
    print(build())
