"""Deterministic acceptance and round-trip checks for this replication."""

from pathlib import Path
import sys
import tempfile
import zipfile

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2026-02-02-ww04-dynamic-moving-average-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "replicated-workbook.twbx"


def load_root(path: Path) -> etree._Element:
    if path.suffix == ".twbx":
        with zipfile.ZipFile(path) as archive:
            twb_names = [name for name in archive.namelist() if name.lower().endswith(".twb")]
            assert len(twb_names) == 1
            return etree.fromstring(archive.read(twb_names[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root: etree._Element) -> None:
    parameter_columns = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource[@name='Parameters']/column")
    }
    assert set(parameter_columns) >= {"pTimePortion", "pTimeFrame", "pMoveAvg"}
    assert parameter_columns["pTimePortion"].get("value") == '"month"'
    assert parameter_columns["pTimeFrame"].get("value") == "24"
    assert parameter_columns["pMoveAvg"].get("value") == "3"

    datasource_columns = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("caption")
    }
    for name in ("Display Date", "Moving Average", "Latest Date", "Date to Display"):
        assert name in datasource_columns

    formulas = {
        name: datasource_columns[name].find("calculation").get("formula")
        for name in ("Display Date", "Moving Average", "Latest Date", "Date to Display")
    }
    assert "DATETRUNC" in formulas["Display Date"]
    assert "WINDOW_AVG" in formulas["Moving Average"]
    assert "WINDOW_MAX" in formulas["Latest Date"]
    assert "DATEADD" in formulas["Date to Display"]

    worksheet = root.find("./worksheets/worksheet[@name='Dynamic Moving Average']")
    assert worksheet is not None
    axis_panes = worksheet.findall(".//pane[@id]")
    assert len(axis_panes) == 2
    assert all(pane.find("mark").get("class") == "Line" for pane in axis_panes)
    assert worksheet.find(".//filter") is not None
    date_filter = worksheet.find(".//filter")
    assert date_filter.find("groupfilter").get(
        "{http://www.tableausoftware.com/xml/user}ui-domain"
    ) == "relevant"
    assert worksheet.find(".//column-instance[@derivation='Day-Trunc']") is not None

    dashboard = root.find("./dashboards/dashboard[@name='Dynamic Moving Average Dashboard']")
    assert dashboard is not None
    assert len(dashboard.findall(".//zone[@type-v2='paramctrl']")) == 3
    assert dashboard.find(".//zone[@name='Dynamic Moving Average']") is not None


def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with zipfile.ZipFile(OUTPUT_TWBX) as archive:
        names = archive.namelist()
        assert any(name.lower().endswith(".hyper") for name in names)

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww04-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        editor = TWBEditor.open_existing(OUTPUT_TWBX)
        editor.save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
