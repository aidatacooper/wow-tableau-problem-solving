"""Verify WW36's hover Set Action and three reference lines."""

from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
import re

from lxml import etree


HERE = Path(__file__).resolve().parent


def check_action_contract(root: etree._Element) -> None:
    """Validate declared hover behavior without claiming the event was executed."""
    datasource = next(ds for ds in root.findall("datasources/datasource") if ds.get("name") != "Parameters")
    ds_name = datasource.get("name")
    columns = {column.get("caption"): column for column in datasource.findall("column") if column.get("caption")}
    month = columns["Month Order Date"].get("name")
    selected = columns["Selected Date"].get("name")
    sales_ref = columns["Sales Ref"].get("name")
    group = datasource.find("group[@caption='Selected Date Set']")
    assert group is not None
    assert group.find("groupfilter[@function='empty-level']").get("member") == month
    assert columns["Month Order Date"].get("datatype") == "date"
    normalize = lambda value: re.sub(r"\s+", "", value)
    assert normalize(columns["Selected Date"].find("calculation").get("formula")) == normalize(f"IF {group.get('name')} THEN {month} END")
    assert normalize(columns["Sales Ref"].find("calculation").get("formula")) == normalize(f"IF {month} = {selected} THEN [Sales] END")

    actions = root.findall("actions/edit-group-action[@caption='Select Date']")
    assert len(actions) == 1
    action = actions[0]
    source = action.find("source")
    assert source.attrib == {"dashboard": "WW36 Custom Axis Tracker", "type": "sheet", "worksheet": "Custom Axis"}
    assert action.find("activation").get("type") == "on-hover"
    params = {item.get("name"): item.get("value") for item in action.findall("params/param")}
    assert params == {"selection-clear-set-option": "exclude-all", "target-group": f"[{ds_name}].{group.get('name')}"}
    axis = root.find("worksheets/worksheet[@name='Custom Axis']")
    dependencies = axis.find(f"table/view/datasource-dependencies[@datasource='{ds_name}']")
    month_instance = dependencies.find(f"column-instance[@column='{month}']")
    assert month_instance is not None
    month_ref = f"[{ds_name}].{month_instance.get('name')}"
    assert axis.findtext("table/cols") == month_ref

    lines = root.findall("worksheets/worksheet[@name='Line Chart']/table/panes/pane/reference-line")
    vertical = next(line for line in lines if selected.strip("[]") in line.get("value-column", ""))
    horizontal = next(line for line in lines if sales_ref.strip("[]") in line.get("value-column", ""))
    assert vertical.get("axis-column") == month_ref
    assert vertical.get("formula") == "min" and vertical.get("scope") == "per-pane"
    assert horizontal.get("axis-column") == f"[{ds_name}].[sum:Sales:qk]"
    assert horizontal.get("formula") == "average" and horizontal.get("scope") == "per-pane"


def reject_broken_action_mappings(root: etree._Element) -> int:
    """Ensure wrong event/source/target/member/axis declarations fail the contract."""
    mutations = [
        ("actions/edit-group-action/source", "worksheet", "Line Chart"),
        ("actions/edit-group-action/source", "dashboard", "Unrelated Dashboard"),
        ("actions/edit-group-action/activation", "type", "on-select"),
        ("actions/edit-group-action/params/param[@name='target-group']", "value", "[OtherDatasource].[OtherSet]"),
        ("datasources/datasource/group[@caption='Selected Date Set']/groupfilter", "member", "[Sales]"),
        ("worksheets/worksheet[@name='Line Chart']/table/panes/pane/reference-line[@id='refline1']", "axis-column", "[Wrong].[sum:Sales:qk]"),
    ]
    for path, attribute, value in mutations:
        broken = deepcopy(root)
        broken.find(path).set(attribute, value)
        try:
            check_action_contract(broken)
        except AssertionError:
            continue
        raise AssertionError(f"Broken action contract was accepted: {path}/{attribute}")
    return len(mutations)


def check(root: etree._Element) -> None:
    check_action_contract(root)
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
    assert lines[0].get("label") == "$<Value> in Sales"
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


# cloud-rest-action-contract: bound source/month/set/clear/reference-line contract.
# case-functional-contract: explicit assertions plus independent data and SDK round-trip.
def main() -> None:
    twb = HERE / "outputs" / "2019-09-09-ww36-custom-axis-tracker-replicated-workbook.twb"
    twbx = HERE / "outputs" / "replicated-workbook.twbx"
    check(etree.parse(str(twb)).getroot())
    with ZipFile(twbx) as archive:
        assert any(name.endswith(".hyper") for name in archive.namelist())
        root = etree.fromstring(archive.read(next(name for name in archive.namelist() if name.endswith(".twb"))))
        check(root)
        mutations = reject_broken_action_mappings(root)
    print(f"PASS: WW36 declared hover-set/reference-line contracts; {mutations} broken mappings rejected; browser event not executed")


if __name__ == "__main__":
    main()
