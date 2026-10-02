"""Deterministic acceptance and round-trip checks for 2019 WW31."""

from pathlib import Path
import sys
import tempfile
import zipfile
from hashlib import sha256
from urllib.parse import unquote, quote

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2019-08-04-ww31-hub-spoke-map-replicated-workbook.twb"
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
            assert len(hypers) == 1 and Path(hypers[0]).name == '2019_07_31_PD25_WWPD_MusicData_Output.hyper'
            assert sha256(archive.read(hypers[0])).digest() == sha256((ITERATION_DIR / "inputs" / '2019_07_31_PD25_WWPD_MusicData_Output.hyper').read_bytes()).digest()
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
        (column.get("caption") or column.get("name", "").strip("[]")): column
        for column in root.findall("./datasources/datasource/column")
        if column.get("name")
    }
    assert fields["Route"].get("datatype") == "spatial"
    assert "MAKELINE" in fields["Route"].find("calculation").get("formula")
    assert fields["Destination"].get("datatype") == "spatial"
    assert "MAKEPOINT" in fields["Destination"].find("calculation").get("formula")

    assert fields["# Concerts"].find("calculation").get("formula") == "COUNTD([ConcertID])"
    assert fields["Monthly Concert Date"].find("calculation").get("formula") == "DATETRUNC('month',[Concert Date])"
    assert fields["Last Concert Month"].find("calculation").get("formula") == "{FIXED [Artist]:MAX(DATETRUNC('month',[Concert Date]))}"
    for field in ["Trend End Artist", "Trend End Concerts"]:
        assert "MIN(" in fields[field].find("calculation").get("formula")
        assert fields["Last Concert Month"].get("name") in fields[field].find("calculation").get("formula")
        assert "LAST()" not in fields[field].find("calculation").get("formula")
    trend = root.find("./worksheets/worksheet[@name='Monthly Concert Trend']")
    assert fields["Monthly Concert Date"].get("name").strip("[]") in trend.findtext("table/cols")
    axis = trend.find("table/style/style-rule[@element='axis']")
    assert axis.find("format[@attr='display'][@scope='cols'][@value='true']") is not None
    assert axis.find("format[@attr='display'][@scope='rows'][@value='false']") is not None
    limits = axis.find("encoding[@scope='rows']")
    assert limits.get("min") == "0" and limits.get("max") == "1200"
    text = "".join(trend.xpath(".//customized-label/formatted-text/run/text()"))
    assert fields["Trend End Artist"].get("name").strip("[]") in text
    assert fields["Trend End Concerts"].get("name").strip("[]") in text

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
        assert not any(pane.find("mark-sizing") is not None for pane in panes)
        assert panes[1].find("style/style-rule[@element='mark']/format[@attr='size']").get("value") == "1.0214917659759521"
        assert panes[2].find("style/style-rule[@element='mark']/format[@attr='size']").get("value") == "7.7539858818054199"
        assert panes[2].find(
            "style/style-rule/format[@attr='has-stroke'][@value='true']"
        ) is not None
        assert "none:Artist:nk" in worksheet.findtext("table/cols")
        assert worksheet.findtext("table/cols").count(
            "Longitude (generated)"
        ) == 2
        assert worksheet.find(".//filter[@class='categorical']") is not None
        size_scale = worksheet.find("table/style/style-rule[@element='mark']/encoding[@attr='size']")
        assert size_scale is not None and size_scale.get("type") == "rangesize"
        assert size_scale.get("max-size") == "1"
        assert size_scale.get("min") == "1"
        assert size_scale.get("min-size") == "0.00251905"
        assert size_scale.get("max") is None, "Author maximum value range is automatic"
        assert size_scale.get("field-type") == "quantitative"
        assert fields["# Concerts"].get("name").strip("[]") in size_scale.get("field")

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

    # action-field-mapping-contract: evaluate the serialized executable mapping, not captions only.
    actions = root.findall("./actions/action")
    assert len(actions) == 2
    ds = root.find("./datasources/datasource[@caption]")
    source_sheets = {"Ben Howard Summary": "Ben Howard", "Ed Sheeran Summary": "Ed Sheeran"}
    assert {action.find("source").get("worksheet") for action in actions} == set(source_sheets)
    for action in actions:
        activation = action.find("activation")
        assert activation.get("type") == "on-hover" and activation.get("auto-clear") == "true"
        source = action.find("source")
        assert source.get("dashboard") == DASHBOARD and source.get("type") == "sheet"
        source_name = source.get("worksheet")
        source_sheet = root.find("./worksheets/worksheet[@name='" + source_name + "']")
        assert source_sheets[source_name] in etree.tostring(source_sheet, encoding="unicode")
        command = action.find("command")
        assert command.get("command") == "tsc:tsl-filter"
        assert command.find("param[@name='target']").get("value") == DASHBOARD
        excluded = set(command.find("param[@name='exclude']").get("value").split(","))
        assert excluded == expected - {"Fellow Artist Word Cloud"}, "Only word cloud is an action target"
        link = action.find("link")
        assert link.get("url-escape") == "true" and link.get("include-null") == "true"
        target, payload = link.get("expression").split("?", 1)
        assert target == "tsl:" + DASHBOARD
        mappings = payload.split("&")
        assert len(mappings) == 2
        expected_map = {"[" + ds.get("name") + "]." + fields[name].get("name"): "<" + fields[name].get("name") + "~na>" for name in ("Artist", "Region")}
        actual_map = {}
        for mapping in mappings:
            target_field, value = mapping.split("~s0=", 1)
            actual_map[unquote(target_field)] = value
        assert actual_map == expected_map, "Both Artist and Region source/target fields must match"
        word = root.find("./worksheets/worksheet[@name='Fellow Artist Word Cloud']")
        dependencies = {column.get("name") for column in word.findall("table/view/datasource-dependencies/column")}
        assert fields["Artist"].get("name") in dependencies and fields["Region"].get("name") in dependencies


# case-functional-contract: explicit assertions plus independent data and SDK round-trip.
def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww31-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    # wordcloud-filter-data-contract
    from verify_filter_data import verify
    verify(ITERATION_DIR / "evidence/wordcloud-filter-data.json")
    print("PASS: independent locked data, chart and exact action mappings, Hyper Artist/Region filter aggregation/removal contracts, SDK round-trip; browser events not executed")


if __name__ == "__main__":
    main()
