"""Deterministic acceptance and round-trip checks for WW06."""

from pathlib import Path
import sys
import tempfile
import zipfile

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2026-02-15-ww06-null-safe-averages-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "2026-02-15-ww06-null-safe-averages-replicated-workbook.twbx"


def load_root(path: Path) -> etree._Element:
    if path.suffix == ".twbx":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            twbs = [name for name in names if name.lower().endswith(".twb")]
            assert len(twbs) == 1
            assert any(name.lower().endswith(".hyper") for name in names)
            return etree.fromstring(archive.read(twbs[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root: etree._Element) -> None:
    parameters = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource[@name='Parameters']/column")
    }
    assert set(parameters) >= {"pMinDate", "pMaxDate"}
    assert parameters["pMinDate"].get("value") == "#2025-07-11#"
    assert parameters["pMaxDate"].get("value") == "#2025-07-23#"
    assert len([name for name in parameters if name == "pMinDate"]) == 1

    fields = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("caption")
    }
    for name in (
        "#Orders",
        "#Orders in Date Range",
        "Index",
        "Number Prefix *",
        "Tooltip - 0 orders",
        "Min Date",
        "Max Date",
        "Colour",
        "True",
        "False",
    ):
        assert name in fields
    assert "ZN(COUNTD" in fields["#Orders in Date Range"].find("calculation").get("formula")
    assert fields["Index"].find("calculation").get("formula").upper() == "INDEX()"

    table = root.find("./worksheets/worksheet[@name='Null-safe Average']")
    assert table is not None
    table_xml = etree.tostring(table, encoding="unicode")
    for name in ("Category", "Sub-Category", "Manufacturer"):
        assert f"[{name}]" in table_xml
    assert "visual-totals=\"Avg\"" in table_xml
    assert "INDEX()" in table_xml
    assert table.find(".//mark").get("class") == "Square"

    apply_sheet = root.find("./worksheets/worksheet[@name='Apply Button']")
    assert apply_sheet is not None
    date_filter = apply_sheet.find(".//filter")
    assert date_filter is not None
    assert date_filter.get("context") == "true"
    assert "tdy:" in date_filter.get("column")
    assert apply_sheet.find(".//column-instance[@derivation='Day-Trunc']") is not None
    apply_instances = {
        instance.get("column"): instance
        for instance in apply_sheet.findall(".//column-instance")
    }
    for name in ("Colour", "Min Date", "Max Date"):
        local_name = fields[name].get("name")
        assert apply_instances[local_name].get("derivation") == "User"
    assert not apply_sheet.findall(".//column-instance[@derivation='Sum']")

    tooltip_local_name = fields["Tooltip - 0 orders"].get("name")
    tooltip_instance = table.find(
        f".//column-instance[@column='{tooltip_local_name}']"
    )
    assert tooltip_instance is not None
    assert tooltip_instance.get("derivation") == "User"

    colour_ref = apply_instances[fields["Colour"].get("name")].get("name")
    palette = root.find(
        ".//style-rule[@element='mark']/encoding[@attr='color']"
        f"[@field='[{root.find('./datasources/datasource[@caption]').get('name')}].{colour_ref}']"
    )
    assert palette is not None
    assert {bucket.text for bucket in palette.findall("map/bucket")} == {
        "true",
        "false",
    }

    actions = root.findall("./actions/edit-parameter-action")
    assert len(actions) == 2
    assert {action.get("caption") for action in actions} == {"Set Min Date", "Set Max Date"}

    dashboard = root.find("./dashboards/dashboard[@name='Null-safe Average Dashboard']")
    assert dashboard is not None
    assert dashboard.find(".//zone[@name='Null-safe Average']") is not None
    assert dashboard.find(".//zone[@name='Apply Button']") is not None


def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww06-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
