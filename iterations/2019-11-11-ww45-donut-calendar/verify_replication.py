"""Verification script for WW45 Donut Calendar replication."""

from pathlib import Path
from zipfile import ZipFile
from lxml import etree

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")

    with ZipFile(OUTPUT) as archive:
        twb_name = next(name for name in archive.namelist() if name.lower().endswith(".twb"))
        root = etree.fromstring(archive.read(twb_name))

    # acceptance: report-date-parameter
    params = root.xpath(".//datasource[@name='Parameters']//column[@caption='Report Date' or @name='[Report Date]']")
    assert len(params) == 1, "Report Date parameter not found"
    assert params[0].get("datatype") == "date", "Report Date parameter must be date type"
    assert "#2019-11-06#" in (params[0].get("value") or ""), "Report Date default must be 2019-11-06"

    # acceptance: fulfilment-calculations
    calc_fields = {
        col.get("caption") or col.get("name"): col.find("calculation").get("formula")
        for col in root.xpath(".//column[calculation]")
    }
    assert "Dates to Include" in calc_fields, "Missing Dates to Include calc"
    assert "Has Shipped?" in calc_fields, "Missing Has Shipped? calc"
    assert "% Shipped" in calc_fields, "Missing % Shipped calc"
    assert "Fully Shipped?" in calc_fields, "Missing Fully Shipped? calc"
    assert "LABEL Tick" in calc_fields, "Missing LABEL Tick calc"
    assert "LABEL % Shipped" in calc_fields, "Missing LABEL % Shipped calc"

    # acceptance: trailing-date-filter
    assert "DATEADD('day', -7" in calc_fields["Dates to Include"], "Dates to Include must check trailing 7 days"

    # acceptance: dual-axis-donut-calendar
    worksheets = {ws.get("name"): ws for ws in root.xpath("./worksheets/worksheet")}
    assert "Main" in worksheets, "Main worksheet not found"
    ws = worksheets["Main"]

    cols = ws.findtext("table/cols") or ""
    rows = ws.findtext("table/rows") or ""
    assert "Order Date" in cols or "none:Order Date" in cols, "Order Date must be in columns"
    assert "Region" in rows or "none:Region" in rows, "Region must be in rows"

    panes = ws.findall("table/panes/pane")
    assert len(panes) >= 2, "Main must configure dual-axis panes"
    mark_classes = [p.find("mark").get("class") for p in panes if p.find("mark") is not None]
    assert "Pie" in mark_classes, "Primary mark must be Pie for donut slice proportion"
    assert "Circle" in mark_classes, "Secondary mark must be Circle for donut hole"

    # acceptance: dashboard-composition
    dashboards = {d.get("name"): d for d in root.xpath("./dashboards/dashboard")}
    assert "2019_11_06_WW45_Donut_Calendar" in dashboards, "Dashboard 2019_11_06_WW45_Donut_Calendar not found"


if __name__ == "__main__":
    verify()
    print("PASS: WW45 Donut Calendar verified successfully")
