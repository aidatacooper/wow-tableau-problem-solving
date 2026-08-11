"""From-scratch acceptance and round-trip verification for WW32."""

from hashlib import sha256
from pathlib import Path
import sys
from zipfile import ZipFile

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
LAB_ROOT = ITERATION_DIR.parents[1]
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_analyzer import analyze_workbook  # noqa: E402
from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2019-08-09-ww32-step-area-chart-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "2019-08-09-ww32-step-area-chart-replicated-workbook.twbx"
LOCKED_HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
AUTHOR_TWB = (
    LAB_ROOT
    / "dataset"
    / "workbooks"
    / "tableau-a671a1f433d4dcca"
    / "workbook.twb"
)
EXPECTED_HYPER_SHA256 = (
    "9042a661caa6195146adc567c7eaaf8a4471f920946ed9bb96b2a8f1cfc57748"
)


def load_twbx(path: Path) -> tuple[etree._Element, bytes]:
    with ZipFile(path) as archive:
        twb_name = next(name for name in archive.namelist() if name.endswith(".twb"))
        hyper_name = next(name for name in archive.namelist() if name.endswith(".hyper"))
        return etree.fromstring(archive.read(twb_name)), archive.read(hyper_name)


def canonical(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n")


def assert_acceptance(root: etree._Element) -> None:
    worksheets = root.findall("./worksheets/worksheet")
    assert [worksheet.get("name") for worksheet in worksheets] == ["Viz"]
    viz = worksheets[0]
    panes = viz.findall("table/panes/pane")
    assert len(panes) == 3
    assert [pane.find("mark").get("class") for pane in panes] == [
        "Area",
        "Area",
        "Line",
    ]
    assert "Multiple Values" in (viz.findtext("table/rows") or "")
    assert "tdy:" in (viz.findtext("table/cols") or "")
    assert viz.findtext("table/view/slices/column", "").endswith(
        ".[:Measure Names]"
    )
    assert len(viz.findall("table/view/filter/groupfilter/groupfilter")) == 2
    assert (
        viz.findtext("layout-options/title/formatted-text/run")
        == "WHEN DID 2018 CATEGORY SALES DROP AND RISE THE MOST?"
    )
    line_encodings = panes[2].find("encodings")
    assert line_encodings.find("color").get("column").split("].[")[-1].startswith(
        "usr:"
    )
    assert line_encodings.find("size") is not None
    assert len(line_encodings.findall("text")) == 5
    assert (
        len(
            viz.findall(
                ".//column-instance[@column='[WW32_Colour_Diff]']/table-calc"
            )
        )
        == 7
    )

    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.findall("./datasources/datasource/column[calculation]")
    }
    assert "FIXED" in formulas["Sales In Month"]
    assert "LOOKUP" in formulas["Sales Next Value"]
    assert "WINDOW_MAX" in formulas["Max Diff"]
    assert "WINDOW_MIN" in formulas["Min Diff"]
    assert root.find(
        "./dashboards/dashboard[@name='2019_08_07_WW32_Step_Area-Chart']"
    ) is not None
    assert len(root.findall(".//metadata-record[@class='column']")) == 21


def assert_source_independence(generated_root: etree._Element) -> None:
    build_source = (ITERATION_DIR / "build_replication.py").read_text(
        encoding="utf-8"
    )
    assert "open_existing" not in build_source
    assert "tableau-a671a1f433d4dcca" not in build_source
    assert "2019_08_07_WW32_Step_Area_Chart.twbx" not in build_source

    author_root = etree.parse(str(AUTHOR_TWB)).getroot()
    generated_worksheets = {
        canonical(worksheet)
        for worksheet in generated_root.findall("./worksheets/worksheet")
    }
    author_worksheets = {
        canonical(worksheet)
        for worksheet in author_root.findall("./worksheets/worksheet")
    }
    assert generated_worksheets.isdisjoint(author_worksheets)


def main() -> None:
    twb_root = etree.parse(str(OUTPUT_TWB)).getroot()
    assert_acceptance(twb_root)
    assert_source_independence(twb_root)

    twbx_root, packaged_hyper = load_twbx(OUTPUT_TWBX)
    assert_acceptance(twbx_root)
    assert sha256(LOCKED_HYPER.read_bytes()).hexdigest() == EXPECTED_HYPER_SHA256
    assert sha256(packaged_hyper).hexdigest() == EXPECTED_HYPER_SHA256

    roundtrip = ITERATION_DIR / "outputs" / ".roundtrip.twbx"
    TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
    roundtrip_root, roundtrip_hyper = load_twbx(roundtrip)
    assert_acceptance(roundtrip_root)
    assert sha256(roundtrip_hyper).hexdigest() == EXPECTED_HYPER_SHA256
    roundtrip.unlink()

    report = analyze_workbook(OUTPUT_TWB)
    assert any(item.canonical == "Step Area" for item in report.detected)
    print(
        "PASS: WW32 from-scratch lineage, structure, locked Hyper, "
        "analyzer, and round-trip"
    )


if __name__ == "__main__":
    main()
