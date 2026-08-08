"""Deterministic acceptance and round-trip checks for 2019 WW31."""

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
DASHBOARD = "2019 WW31 Music Data Hub & Spoke"
MAPS = {
    "Routes — North & South America",
    "Routes — Europe",
    "Routes — East Asia & Middle East",
}


def load_root(path: Path) -> etree._Element:
    if path.suffix == ".twbx":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            twbs = [name for name in names if name.lower().endswith(".twb")]
            assert len(twbs) == 1
            hypers = [name for name in names if name.lower().endswith(".hyper")]
            assert hypers == [
                "Data/Datasources/"
                "2019_07_31_PD25_WWPD_MusicData_Output.hyper"
            ]
            return etree.fromstring(archive.read(twbs[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root: etree._Element) -> None:
    expected = {
        "Ben Howard Summary",
        "Ed Sheeran Summary",
        "Monthly Concert Trend",
        *MAPS,
        "Fellow Artist Word Cloud",
    }
    actual = {node.get("name") for node in root.findall("./worksheets/worksheet")}
    assert actual == expected

    fields = {
        column.get("caption"): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("caption")
    }
    assert fields["Route"].get("datatype") == "spatial"
    assert "MAKELINE" in fields["Route"].find("calculation").get("formula")
    assert fields["Destination"].get("datatype") == "spatial"
    assert "MAKEPOINT" in fields["Destination"].find("calculation").get("formula")

    serialized = etree.tostring(root, encoding="unicode")
    assert "none:Location (group):nk" not in serialized
    assert "sum:Calculation_488922052502458368" not in serialized

    for name in MAPS:
        worksheet = root.find(f"./worksheets/worksheet[@name='{name}']")
        panes = worksheet.findall(".//panes/pane")
        assert len(panes) == 3
        geometries = [
            pane.find("encodings/geometry").get("column") for pane in panes[1:]
        ]
        assert all("[clct:" in geometry for geometry in geometries)
        assert geometries[0] != geometries[1]
        assert panes[1].find("encodings/size") is not None
        assert panes[2].find(
            "style/style-rule/format[@attr='has-stroke'][@value='true']"
        ) is not None
        assert "none:Artist:nk" in worksheet.findtext("table/cols")
        assert worksheet.findtext("table/cols").count(
            "Longitude (generated)"
        ) == 2
        assert worksheet.find(".//filter[@class='categorical']") is not None

    cloud = root.find(
        "./worksheets/worksheet[@name='Fellow Artist Word Cloud']"
    )
    assert cloud.find(".//mark").get("class") == "Text"
    assert cloud.find(".//encodings/size") is not None
    assert cloud.find(".//encodings/text") is not None

    dashboard = root.find(f"./dashboards/dashboard[@name='{DASHBOARD}']")
    assert dashboard is not None
    zones = {zone.get("name") for zone in dashboard.findall(".//zone[@name]")}
    assert expected <= zones

    actions = root.findall("./actions/action")
    assert len(actions) == 2
    for action in actions:
        assert action.find("activation").get("type") == "on-hover"
        command = action.find("command")
        assert command.get("command") == "tsc:tsl-filter"
        target = command.find("param[@name='target']")
        assert target is not None
        assert target.get("value") == DASHBOARD
        exclude = command.find("param[@name='exclude']")
        assert exclude is not None
        assert "Fellow Artist Word Cloud" not in exclude.get("value")


def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww31-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
