"""WW06 Cloud REST and artifact contracts; browser clicks are not executed."""
from hashlib import sha256
import ast
import json
from pathlib import Path
import tempfile
from urllib.parse import quote, unquote
from zipfile import ZipFile
from lxml import etree
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
OUTPUT_TWB = ITERATION_DIR / "outputs/2026-02-15-ww06-null-safe-averages-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs/replicated-workbook.twbx"


def load_root(path):
    if path.suffix == ".twbx":
        with ZipFile(path) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            twbs = [name for name in names if name.endswith(".twb")]
            assert len(twbs) == 1
            locked = json.loads((ITERATION_DIR / "inputs/source-lock.json").read_text())
            for data in locked["extracted_data"]:
                source = ITERATION_DIR / data["file"]
                assert sha256(source.read_bytes()).hexdigest() == data["sha256"]
                member = next(n for n in names if Path(n).name == source.name)
                assert sha256(archive.read(member)).hexdigest() == data["sha256"]
            return etree.fromstring(archive.read(twbs[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root):
    parameters = {c.get("caption"): c for c in root.findall("./datasources/datasource[@name='Parameters']/column")}
    for name, value in [("pMinDate", "#2025-07-11#"), ("pMaxDate", "#2025-07-23#")]:
        assert parameters[name].get("value") == value
    ds = root.find("./datasources/datasource[@caption]")
    assert ds.find("date-options").get("start-of-week") == "sunday"
    fields = {c.get("caption"): c for c in ds.findall("column") if c.get("caption")}
    def formula(name):
        return fields[name].find("calculation").get("formula")
    assert "ZN(COUNTD" in formula("#Orders in Date Range")
    assert fields["#Orders in Date Range"].get("datatype") == "integer"
    assert "' *'" not in formula("Number Prefix *")
    assert "'*'" in formula("Number Prefix *") and "=0" in formula("Number Prefix *")
    assert formula("Index").upper() == "INDEX()"
    assert formula("True") == "TRUE" and formula("False") == "FALSE"
    assert len(ds.findall("drill-paths/drill-path/field")) == 3

    table = root.find("./worksheets/worksheet[@name='Viz']")
    assert table is not None
    assert "wd:Order Date:ok" in table.findtext("table/cols")
    rows = table.findtext("table/rows")
    assert "none:Category:nk" in rows and "none:Sub-Category:nk" in rows
    assert "Manufacturer" not in rows  # Author initial hierarchy is collapsed here.
    assert table.find(".//mark").get("class") == "Square"
    subtotals = table.findall("table/subtotals/column")
    assert len(subtotals) == 2
    assert any("Category:nk" in c.text for c in subtotals)
    assert any("Sub-Category:nk" in c.text for c in subtotals)
    for field in ("#Orders", "#Orders in Date Range"):
        ci = table.find(".//column-instance[@column='" + fields[field].get("name") + "']")
        assert ci.get("visual-totals") == "Avg" and ":vtavg:" in ci.get("name")
    assert table.find(".//column-instance[@column='" + fields["Index"].get("name") + "']/table-calc") is not None
    assert table.find(".//column-instance[@column='" + fields["Tooltip - 0 orders"].get("name") + "']").get("derivation") == "User"
    palette = table.find("table/style/style-rule[@element='mark']/encoding[@attr='color']")
    assert palette.get("palette") == "red_blue_white_diverging_10_0"
    assert palette.get("include-totals") == "true" and palette.get("center") == "0.0"
    labels = "".join(table.xpath(".//customized-label/formatted-text/run/text()"))
    assert fields["Number Prefix *"].get("name").strip("[]") in labels

    apply_sheet = root.find("./worksheets/worksheet[@name='Apply Button Filter']")
    assert apply_sheet is not None
    date_filter = apply_sheet.find(".//filter")
    assert date_filter.get("context") == "true" and "tdy:" in date_filter.get("column")
    for name in ("Colour", "Min Date", "Max Date"):
        assert apply_sheet.find(".//column-instance[@column='" + fields[name].get("name") + "']").get("derivation") == "User"
    assert not apply_sheet.findall(".//column-instance[@derivation='Sum']")
    colour_ci = apply_sheet.find(".//column-instance[@column='" + fields["Colour"].get("name") + "']")
    apply_palette = ds.find("style/style-rule[@element='mark']/encoding[@field='" + colour_ci.get("name") + "']")
    assert {b.text for b in apply_palette.findall("map/bucket")} == {"true", "false"}

    # action-field-mapping-contract: every selected source value is bound to its correct target.
    actions = root.findall("./actions/edit-parameter-action")
    assert len(actions) == 2
    assert {action.get("caption") for action in actions} == {"Set Min Date", "Set Max Date"}
    for action in actions:
        assert action.find("activation").get("type") == "on-select"
        source = action.find("source")
        assert source.get("worksheet") == "Apply Button Filter"
        assert source.get("dashboard") == "2026_02_11_WW06_Averages_and_Nulls"
        assert action.find("agg-type").get("type") == "attr"
        assert action.find("clear-option").get("type") == "do-nothing"
        source_caption = "Min Date" if action.get("caption") == "Set Min Date" else "Max Date"
        target_caption = "pMinDate" if source_caption == "Min Date" else "pMaxDate"
        instance = apply_sheet.find(".//column-instance[@column='" + fields[source_caption].get("name") + "']")
        assert action.find("params/param[@name='source-field']").get("value") == "[" + ds.get("name") + "]." + instance.get("name")
        assert action.find("params/param[@name='target-parameter']").get("value") == "[Parameters]." + parameters[target_caption].get("name")
    assert formula("Min Date") == "MIN([Order Date])" and formula("Max Date") == "MAX([Order Date])"
    colour = formula("Colour")
    assert fields["Min Date"].get("name") in colour and fields["Max Date"].get("name") in colour
    assert parameters["pMinDate"].get("name") in colour and parameters["pMaxDate"].get("name") in colour
    deselect = root.find("./actions/action[@caption='Deselect Button']")
    assert deselect.find("activation").get("auto-clear") == "true"
    assert deselect.find("activation").get("type") == "on-select"
    assert deselect.find("source").get("worksheet") == "Apply Button Filter"
    target, payload = deselect.find("link").get("expression").split("?", 1)
    assert unquote(target) == "tsl:Apply Button Filter"
    destination, source_value = payload.split("~s0=", 1)
    assert unquote(destination) == "[" + ds.get("name") + "]." + fields["True"].get("name")
    assert source_value == "<[" + ds.get("name") + "]." + fields["False"].get("name") + "~na>"
    assert deselect.find("command/param[@name='target']").get("value") == "Apply Button Filter"
    assert deselect.find("command/param[@name='exclude']") is None
    assert len(root.findall("./actions/*")) == 3
    dashboard = root.find("./dashboards/dashboard[@name='2026_02_11_WW06_Averages_and_Nulls']")
    assert dashboard.find(".//zone[@name='Viz']") is not None
    assert dashboard.find(".//zone[@name='Apply Button Filter']") is not None
    assert dashboard.find("size").get("maxwidth") == "1366"
    matrix_zone = dashboard.find(".//zone[@name='Viz']/layout-cache")
    assert matrix_zone.get("type-h") == "cell", "Category filtering must preserve row height"
    assert matrix_zone.get("type-w") == "scalable", "All seven weekday columns must remain visible"
    row_height = table.find("table/style/style-rule[@element='cell']/format[@attr='height']")
    assert row_height.get("value") == "25"



# case-functional-contract: explicit assertions plus independent data and SDK round-trip.
def main():
    build_source = (ITERATION_DIR / "build_replication.py").read_text()
    ast.parse(build_source)
    assert 'TWBEditor("")' in build_source
    assert not any(token in build_source for token in ["lxml", "SubElement", "open_existing", "source_workbook"])
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))
    with tempfile.TemporaryDirectory(prefix="cwtwb-ww06-") as directory:
        roundtrip = Path(directory) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))
    # matrix-hyper-data-contract
    from verify_matrix_data import verify as verify_matrix
    verify_matrix(ITERATION_DIR / "evidence/matrix-data-contract.json")
    # apply-rest-data-contract
    from verify_cloud_data import verify
    verify(ITERATION_DIR / "evidence/cloud-data-comparison.json")
    print("PASS: from-scratch, locked Hyper, null-safe count, Sunday matrix, average subtotal, three action definitions and round-trip; action mappings checked structurally, browser clicks not executed")

if __name__ == "__main__":
    main()
