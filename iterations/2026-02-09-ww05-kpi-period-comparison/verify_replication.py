"""Deterministic acceptance and round-trip checks for WW05."""

from pathlib import Path
import sys
import tempfile
import zipfile

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "replicated-workbook.twbx"
REQUIRED_CALCULATIONS = {
    "Today Last Month",
    "Today Last Year",
    "Recent | Prior  Mth | Prior Yr",
    "Profit Ratio",
    "PR - Recent",
    "PR - Not Recent",
    "X-Axis",
    "PR - Today",
    "PR - Yesterday",
    "PR Difference",
    "PR Direction Up",
    "PR Direction Down",
}


def load_root(path: Path) -> etree._Element:
    if path.suffix == ".twbx":
        with zipfile.ZipFile(path) as archive:
            twbs = [name for name in archive.namelist() if name.lower().endswith(".twb")]
            assert len(twbs) == 1
            return etree.fromstring(archive.read(twbs[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root: etree._Element) -> None:
    parameter = root.find("./datasources/datasource[@name='Parameters']/column[@caption='pToday']")
    assert parameter is not None
    assert parameter.get("value") == "#2025-02-04#"

    columns = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("caption")
    }
    assert REQUIRED_CALCULATIONS <= set(columns)
    assert "FIXED" in columns["PR - Today"].find("calculation").get("formula")
    assert "FIXED" in columns["PR - Yesterday"].find("calculation").get("formula")
    assert "DATEDIFF" in columns["X-Axis"].find("calculation").get("formula")

    trend = root.find("./worksheets/worksheet[@name='Period Trend']")
    assert trend is not None
    axis_panes = trend.findall(".//pane[@id]")
    assert len(axis_panes) == 2
    assert all(pane.find("mark").get("class") == "Line" for pane in axis_panes)
    assert trend.find(".//filter") is not None
    assert all(pane.find(".//encodings/color") is not None for pane in axis_panes)

    kpi = root.find("./worksheets/worksheet[@name='KPI Summary']")
    assert kpi is not None
    assert kpi.find(".//mark").get("class") == "Text"
    kpi_xml = etree.tostring(kpi, encoding="unicode")
    for name in ("PR - Today", "PR Difference", "PR Direction Up", "PR Direction Down"):
        internal_name = columns[name].get("name")
        assert internal_name in kpi_xml

    dashboard = root.find("./dashboards/dashboard[@name='KPI Trend Monitor']")
    assert dashboard is not None
    assert dashboard.find(".//zone[@name='Period Trend']") is not None
    assert dashboard.find(".//zone[@name='KPI Summary']") is not None
    assert dashboard.find(".//zone[@type-v2='paramctrl']") is not None


def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with zipfile.ZipFile(OUTPUT_TWBX) as archive:
        names = archive.namelist()
        assert any(name.lower().endswith(".hyper") for name in names)

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww05-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
