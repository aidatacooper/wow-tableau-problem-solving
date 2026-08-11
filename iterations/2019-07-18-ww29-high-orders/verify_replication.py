"""Deterministic acceptance and round-trip checks for 2019 WW29."""

from pathlib import Path
import sys
import tempfile
import zipfile

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2019-07-18-ww29-high-orders-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "2019-07-18-ww29-high-orders-replicated-workbook.twbx"


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
    fields = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("caption")
    }
    required = {
        "Count Orders per Segment",
        "Count Days Per Segment",
        "Overall Avg Orders Per Day Per Segment",
        "Count Orders per Segment per Month",
        "Count Days Per Segment Per Month",
        "Avg Orders Per Day Per Segment Per Month",
        "% Difference",
        "Difference",
        "COLOUR:Difference",
    }
    assert required <= set(fields)
    assert "{FIXED [Segment]" in fields["Count Orders per Segment"].find(
        "calculation"
    ).get("formula")
    assert "MONTH([Order Date])" in fields[
        "Count Orders per Segment per Month"
    ].find("calculation").get("formula")

    worksheet = root.find(
        "./worksheets/worksheet[@name='Higher Orders by Month']"
    )
    assert worksheet is not None
    assert worksheet.find(".//mark").get("class") == "GanttBar"
    assert worksheet.find(".//encodings/size") is not None
    assert worksheet.find(".//encodings/color") is not None
    assert worksheet.find(".//encodings/text") is not None
    reference_line = worksheet.find(".//reference-line")
    assert reference_line is not None
    assert reference_line.get("scope") == "per-pane"
    assert reference_line.get("label-type") == "value"
    assert reference_line.get("axis-column") != reference_line.get("value-column")

    dashboard = root.find("./dashboards/dashboard[@name='WW29 Higher Orders']")
    assert dashboard is not None
    assert dashboard.find(".//zone[@name='Higher Orders by Month']") is not None


def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww29-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
