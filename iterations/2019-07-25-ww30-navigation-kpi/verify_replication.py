"""Deterministic acceptance and round-trip checks for 2019 WW30."""

from pathlib import Path
import sys
import tempfile
import zipfile
from hashlib import sha256

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ITERATION_DIR.parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


OUTPUT_TWB = ITERATION_DIR / "outputs" / "2019-07-25-ww30-navigation-kpi-replicated-workbook.twb"
OUTPUT_TWBX = ITERATION_DIR / "outputs" / "replicated-workbook.twbx"
EXPECTED_NAVIGATION = {
    "Customers": "Customer Sales",
    "Products": "Product Sales",
    "Orders": "Order Sales",
    "Cities": "City Sales",
}


def load_root(path: Path) -> etree._Element:
    if path.suffix == ".twbx":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            twbs = [name for name in names if name.lower().endswith(".twb")]
            assert len(twbs) == 1
            hypers = [name for name in names if name.lower().endswith(".hyper")]
            assert len(hypers) == 1 and Path(hypers[0]).name == 'Orders (Sample - Superstore).hyper'
            assert sha256(archive.read(hypers[0])).digest() == sha256((ITERATION_DIR / "inputs" / 'Orders (Sample - Superstore).hyper').read_bytes()).digest()
            return etree.fromstring(archive.read(twbs[0]))
    return etree.parse(str(path)).getroot()


def assert_acceptance(root: etree._Element) -> None:
    expected_sheets = {
        "Customers",
        "Products",
        "Orders",
        "Cities",
        "by Customer",
        "by Product",
        "by Order",
        "by City",
    }
    worksheets = {node.get("name") for node in root.findall("./worksheets/worksheet")}
    assert worksheets == expected_sheets

    expected_dashboards = {
        "4 Box KPI",
        "Customer Sales",
        "Product Sales",
        "Order Sales",
        "City Sales",
    }
    dashboards = {node.get("name") for node in root.findall("./dashboards/dashboard")}
    assert dashboards == expected_dashboards

    for sheet in ("Customers", "Products", "Orders", "Cities"):
        worksheet = root.find(f"./worksheets/worksheet[@name='{sheet}']")
        assert worksheet.find(".//mark").get("class") == "Square"
        assert worksheet.find(".//encodings/text") is not None

    for sheet in ("by Customer", "by Product", "by Order", "by City"):
        worksheet = root.find(f"./worksheets/worksheet[@name='{sheet}']")
        assert worksheet.find(".//mark").get("class") == "Bar"
        assert worksheet.find(".//encodings/text") is not None
        pane = worksheet.find("table/panes/pane")
        assert len(pane.findall("customized-label/formatted-text/run")) == 3
        assert pane.find("style/style-rule[@element='cell']/format[@attr='text-align'][@value='left']") is not None
        assert worksheet.find("table/style/style-rule[@element='cell']/format[@attr='height']").get("value") in {"30", "33"}
        assert worksheet.find("table/style/style-rule[@element='axis']/format[@attr='display'][@value='false']") is not None

    actions = root.findall("./actions/nav-action")
    assert len(actions) == 4
    actual_navigation = {}
    for action in actions:
        source = action.find("source")
        assert source.get("dashboard") == "4 Box KPI"
        assert source.get("type") == "sheet"
        assert action.find("activation").get("type") == "on-select"
        target = action.find("./params/param[@name='sheet']")
        assert source.get("worksheet") not in actual_navigation, "Each KPI must map once"
        assert target.get("value") in dashboards
        target_name = target.get("value")
        target_window = root.find(f"./windows/window[@class='dashboard'][@name='{target_name}']/simple-id")
        assert target_window is not None and target_window.get("uuid")
        actual_navigation[source.get("worksheet")] = target.get("value")
    assert actual_navigation == EXPECTED_NAVIGATION

    main = root.find("./dashboards/dashboard[@name='4 Box KPI']")
    assert {
        zone.get("name") for zone in main.findall(".//zone[@name]")
    } >= {"Customers", "Products", "Orders", "Cities"}

    main_id = root.find("./windows/window[@class='dashboard'][@name='4 Box KPI']/simple-id").get("uuid")
    for dashboard in expected_dashboards - {"4 Box KPI"}:
        node = root.find(f"./dashboards/dashboard[@name='{dashboard}']")
        button = node.find(".//zone[@type='dashboard-object']/button")
        assert button is not None
        assert button.get("action") == f"tabdoc:goto-sheet window-id=\"{main_id}\""
        assert "GO BACK" in "".join(button.itertext())
        expected_color = {"Customer Sales": "#57a337", "Product Sales": "#fc719e", "Order Sales": "#8076ba", "City Sales": "#1ba3c6"}[dashboard]
        assert button.find("button-visual-state/format[@attr='background-color']").get("value").lower() == expected_color
        zone = next(z for z in node.findall(".//zone[@name]") if z.get("name").startswith("by "))
        cache = zone.find("layout-cache")
        assert cache.get("type-h") == "cell" and cache.get("type-w") == "scalable", "Details must scroll naturally and fit only width"


# case-functional-contract: explicit assertions plus independent data and SDK round-trip.
def main() -> None:
    for output in (OUTPUT_TWB, OUTPUT_TWBX):
        assert output.exists()
        assert_acceptance(load_root(output))

    with tempfile.TemporaryDirectory(prefix="cwtwb-ww30-") as temp_dir:
        roundtrip = Path(temp_dir) / "roundtrip.twbx"
        TWBEditor.open_existing(OUTPUT_TWBX).save(roundtrip, validate=False)
        assert_acceptance(load_root(roundtrip))

    print("PASS: acceptance and round-trip checks")


if __name__ == "__main__":
    main()
