"""Verify WW35's independent parameter-driven drill behavior."""

from pathlib import Path
from zipfile import ZipFile
from lxml import etree


HERE = Path(__file__).resolve().parent


def check(root: etree._Element) -> None:
    assert root.xpath("./worksheets/worksheet[@name='Viz']")
    assert root.xpath("./dashboards/dashboard[@name='WW35 Drill Up and Down']")
    params = {c.get("caption") for c in root.xpath(".//datasource[@name='Parameters']/column")}
    assert {"Select Category", "Level Param"} <= params
    formulas = {c.get("caption"): c.find("calculation").get("formula") for c in root.xpath(".//column[calculation]")}
    assert "FIXED YEAR([Order Date]), [Category]" in formulas["Sales Per Year Per Category"]
    assert "[Parameters].[Parameter 2] = 2" in formulas["Level"]
    assert "[Sub-Category]" in formulas["Display"]
    viz = root.xpath("./worksheets/worksheet[@name='Viz']")[0]
    buckets = viz.xpath("./table/view/manual-sort/dictionary/bucket/text()")
    assert buckets == ['"Technology"', '"Office Supplies"', '"Furniture"']
    assert viz.xpath("./table/style/style-rule[@element='axis']/format[@attr='display'][@value='false']")


def main() -> None:
    twb = HERE / "outputs" / "2019-09-04-ww35-drill-up-down-parameter-actions-replicated-workbook.twb"
    twbx = HERE / "outputs" / "replicated-workbook.twbx"
    check(etree.parse(str(twb)).getroot())
    with ZipFile(twbx) as archive:
        inner = next(name for name in archive.namelist() if name.endswith(".twb"))
        assert any(name.endswith(".hyper") for name in archive.namelist())
        check(etree.fromstring(archive.read(inner)))
    print("PASS: WW35 parameter-driven category/sub-category drill")


if __name__ == "__main__":
    main()

