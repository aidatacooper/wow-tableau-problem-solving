"""Verify WW36's hover Set Action and three reference lines."""

from pathlib import Path
from zipfile import ZipFile

from lxml import etree


HERE = Path(__file__).resolve().parent


def check(root: etree._Element) -> None:
    names = {worksheet.get("name") for worksheet in root.xpath("./worksheets/worksheet")}
    assert {"Line Chart", "Custom Axis", "Data"} <= names
    assert root.xpath("./dashboards/dashboard[@name='WW36 Custom Axis Tracker']")

    formulas = {
        column.get("caption"): column.find("calculation").get("formula")
        for column in root.xpath(".//column[calculation]")
    }
    assert "DATE(DATETRUNC('month', [Order Date]))" in formulas["Month Order Date"]
    assert "{ FIXED : MAX([Order Date]) }" in formulas["Max Date Month"]
    local_names = {
        column.get("caption"): column.get("name")
        for column in root.xpath(".//column[@caption]")
    }
    assert "[Selected Date Set]" in formulas["Selected Date"]
    assert local_names["Selected Date"] in formulas["Sales Ref"]
    assert "WINDOW_MAX" in formulas["Max Sales in Window"]

    selected_set = root.xpath(".//datasources/datasource/group[@caption='Selected Date Set']")
    assert len(selected_set) == 1
    assert selected_set[0].xpath("./groupfilter[@function='empty-level']")

    custom_axis = root.xpath(".//worksheet[@name='Custom Axis']")[0]
    assert custom_axis.findtext("table/rows") in (None, "")
    assert custom_axis.xpath(".//pane[@selection-relaxation-option='selection-relaxation-allow']")
    assert custom_axis.xpath("./table/style/style-rule[@element='axis']/format[@attr='display' and @value='false']")
    assert custom_axis.xpath("./table/style/style-rule[@element='cell']/format[@attr='height' and @value='60']")
    tooltip_runs = custom_axis.xpath(".//pane/customized-tooltip/formatted-text/run")
    assert len(tooltip_runs) == 4
    assert tooltip_runs[0].get("bold") == "true" and tooltip_runs[0].get("fontsize") == "9"
    assert tooltip_runs[1].text == "\u00c6\n"
    assert tooltip_runs[2].text == "Sales:\t"
    assert tooltip_runs[2].get("fontcolor") == "#666666"
    pane_formats = {
        (item.getparent().get("element"), item.get("attr")): item.get("value")
        for item in custom_axis.xpath(".//pane/style/style-rule/format")
    }
    assert pane_formats[("cell", "text-align")] == "center"
    assert pane_formats[("cell", "vertical-align")] == "center"
    assert pane_formats[("datalabel", "color")] == "#898989"
    assert pane_formats[("datalabel", "font-size")] == "8"
    assert pane_formats[("mark", "mark-color")] == "#499894"
    assert pane_formats[("mark", "size")] == "0.31784531474113464"
    assert pane_formats[("mark", "mark-labels-cull")] == "false"

    lines = root.xpath(".//worksheet[@name='Line Chart']//reference-line")
    assert len(lines) == 3
    assert {line.get("formula") for line in lines} == {"max", "min", "average"}
    selected_date_token = local_names["Selected Date"].strip("[]")
    sales_ref_token = local_names["Sales Ref"].strip("[]")
    assert any(selected_date_token in line.get("value-column", "") for line in lines)
    assert any(sales_ref_token in line.get("value-column", "") for line in lines)
    assert [line.get("z-order") for line in lines] == ["1", "2", "3"]
    detail_columns = {
        item.get("column")
        for item in root.xpath(".//worksheet[@name='Line Chart']//pane/encodings/lod")
    }
    assert {line.get("value-column") for line in lines} <= detail_columns
    assert lines[0].get("label-type") == "custom"
    assert lines[0].get("label") == "<Value> in Sales"
    assert lines[0].get("probability") is None
    assert lines[1].get("probability") is None
    refline_formats = {
        (item.get("id"), item.get("attr")): item.get("value")
        for item in root.xpath(
            ".//worksheet[@name='Line Chart']/table/style/"
            "style-rule[@element='refline']/format"
        )
    }
    for reference_id in ("refline0", "refline1", "refline2"):
        assert refline_formats[(reference_id, "line-pattern-only")] == "dotted"
        assert refline_formats[(reference_id, "stroke-color")] == "#499894"
        assert refline_formats[(reference_id, "line-visibility")] == "on"
    assert refline_formats[("refline1", "stroke-size")] == "2"
    assert refline_formats[("refline0", "font-family")] == "Tableau Medium"
    line_mark_formats = {
        item.get("attr"): item.get("value")
        for item in root.xpath(
            ".//worksheet[@name='Line Chart']//pane/style/"
            "style-rule[@element='mark']/format"
        )
    }
    assert line_mark_formats["mark-color"] == "#499894"
    assert line_mark_formats["mark-markers-mode"] == "all"
    line_tooltip = root.xpath(
        ".//worksheet[@name='Line Chart']//customized-tooltip/formatted-text/run"
    )
    assert len(line_tooltip) == 4
    dashboard = root.xpath("./dashboards/dashboard[@name='WW36 Custom Axis Tracker']")[0]
    assert dashboard.xpath(".//zone[@name='Custom Axis' and @show-title='false']")
    assert dashboard.xpath(".//zone[@name='Line Chart' and @show-title='false']")

    action = root.xpath(".//actions/edit-group-action[@caption='Select Date']")
    assert len(action) == 1
    assert action[0].xpath("./activation[@type='on-hover']")
    assert action[0].xpath("./source[@worksheet='Custom Axis']")
    parameters = {item.get("name"): item.get("value") for item in action[0].xpath("./params/param")}
    assert parameters["selection-clear-set-option"] == "exclude-all"
    assert parameters["target-group"].endswith("[Selected Date Set]")


def main() -> None:
    twb = HERE / "outputs" / "2019-09-09-ww36-custom-axis-tracker-replicated-workbook.twb"
    twbx = HERE / "outputs" / "2019-09-09-ww36-custom-axis-tracker-replicated-workbook.twbx"
    check(etree.parse(str(twb)).getroot())
    with ZipFile(twbx) as archive:
        assert any(name.endswith(".hyper") for name in archive.namelist())
        check(etree.fromstring(archive.read(next(name for name in archive.namelist() if name.endswith(".twb")))))
    print("PASS: WW36 hover set action and tracking reference lines")


if __name__ == "__main__":
    main()
