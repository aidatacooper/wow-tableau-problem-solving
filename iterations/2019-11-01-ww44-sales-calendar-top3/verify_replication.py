from pathlib import Path
from zipfile import ZipFile

from lxml import etree


HERE = Path(__file__).resolve().parent
PREFIX = "2019-11-01-ww44-sales-calendar-top3-replicated-workbook"


def check(root):
    worksheets = {node.get("name") for node in root.xpath("./worksheets/worksheet")}
    assert {"Title", "Front"} <= worksheets
    formulas = {
        node.get("caption"): node.find("calculation").get("formula")
        for node in root.xpath(".//column[calculation]")
        if node.get("caption")
    }
    assert "FIXED YEAR" in formulas["Total Monthly Sales"]
    assert "WEEK([Order Date])" in formulas["Total Weekly Sales"]
    assert "'MONTHS'" in formulas["Group By Date"] and "'WEEKS'" in formulas["Group By Date"]
    assert root.xpath(".//groupfilter")
    assert root.xpath(".//dashboard[@name='WW44 Sales Calendar']")
    date_options = root.xpath("./datasources/datasource/date-options")
    assert date_options and date_options[0].get("start-of-week") == "sunday"


def main():
    check(etree.parse(str(HERE / "outputs" / f"{PREFIX}.twb")).getroot())
    with ZipFile(HERE / "outputs" / f"{PREFIX}.twbx") as archive:
        assert any(name.endswith(".hyper") for name in archive.namelist())
        twb_name = next(name for name in archive.namelist() if name.endswith(".twb"))
        check(etree.fromstring(archive.read(twb_name)))
    print("PASS: WW44 sales calendar top-three highlight")


if __name__ == "__main__":
    main()
