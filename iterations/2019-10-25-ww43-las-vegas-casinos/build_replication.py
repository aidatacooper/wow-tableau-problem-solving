from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor

H = next((HERE / "inputs").glob("*.hyper"))
O = HERE / "outputs"


def style_map(e):
    ws = e._find_worksheet("Map")
    table = ws.find("table")
    pane = table.find("panes/pane")
    color = pane.find("encodings/color").get("column")
    style = table.find("style")
    if style is None:
        from lxml import etree

        style = etree.Element("style")
        table.insert(1, style)
    from lxml import etree

    rule = etree.SubElement(style, "style-rule", element="mark")
    etree.SubElement(
        rule,
        "encoding",
        attr="color",
        field=color,
        palette="purple_10_0",
        reverse="true",
        type="interpolated",
    )


def package_shape_assets(path: Path) -> None:
    """Package the authored map-pin shape without reading the source workbook."""
    from lxml import etree

    def mutate(raw: bytes) -> bytes:
        root = etree.fromstring(raw)
        worksheet = root.xpath(".//worksheet[@name='Map']")[0]
        pane = worksheet.find("./table/panes/pane")
        pane.find("mark").set("class", "Shape")
        size = pane.find("encodings/size")
        if size is None or not size.get("column"):
            raise ValueError(
                "Map size encoding is required for selected-casino shape mapping"
            )
        style = worksheet.find("./table/style")
        rule = style.find("style-rule[@element='mark']")
        for old in rule.findall("encoding[@attr='shape']"):
            rule.remove(old)
        encoding = etree.SubElement(
            rule, "encoding", attr="shape", field=size.get("column"), type="shape"
        )
        for target, bucket in (
            (":filled/circle", "false"),
            ("Maps/Map Pin.png", "true"),
        ):
            mapping = etree.SubElement(encoding, "map", to=target)
            etree.SubElement(mapping, "bucket").text = f'"{bucket}"'
        for connection in root.xpath('.//connection[@class="hyper"]'):
            connection.set("dbname", "2019_10_23_WW43_Las Vegas Casinos.hyper")
        return etree.tostring(
            root, xml_declaration=True, encoding="utf-8", pretty_print=False
        )

    asset = HERE / "inputs" / "ww43-map-pin.png"
    if not asset.exists():
        raise FileNotFoundError(asset)
    if path.suffix.lower() == ".twb":
        path.write_bytes(mutate(path.read_bytes()))
        return
    with ZipFile(path, "r") as source:
        entries = {name: source.read(name) for name in source.namelist()}
    workbook_name = next(name for name in entries if name.endswith(".twb"))
    entries[workbook_name] = mutate(entries[workbook_name])
    entries["Maps/Map Pin.png"] = asset.read_bytes()
    with ZipFile(path, "w", ZIP_DEFLATED) as target:
        for name, data in entries.items():
            target.writestr(name, data)


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(H), table_name="Extract")
    e.add_parameter(
        "Selected Casino",
        datatype="string",
        default_value="Mandalay Bay Resort & Casino",
        domain_type="any",
    )
    e.add_parameter(
        "How many Miles?",
        datatype="real",
        default_value="2.0",
        domain_type="range",
        min_value="0.5",
        max_value="10.0",
        granularity="0.5",
    )
    e.add_calculated_field(
        "Is Selected Casino?",
        "[name] = [Parameters].[Selected Casino]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Selected Casino Lat",
        "{ FIXED : MIN(IIF([Is Selected Casino?], [latitude], NULL)) }",
        datatype="real",
    )
    e.add_calculated_field(
        "Selected Casino Long",
        "{ FIXED : MIN(IIF([Is Selected Casino?], [longitude], NULL)) }",
        datatype="real",
    )
    e.add_calculated_field(
        "Distance (miles)",
        "DISTANCE(MAKEPOINT([Selected Casino Lat],[Selected Casino Long]), MAKEPOINT([latitude],[longitude]), 'miles')",
        datatype="real",
    )
    e.add_calculated_field(
        "Distance (metres)",
        "DISTANCE(MAKEPOINT([Selected Casino Lat],[Selected Casino Long]), MAKEPOINT([latitude],[longitude]), 'meters')",
        datatype="real",
    )
    e.add_calculated_field(
        "Within specified miles?",
        "[Distance (miles)] <= [Parameters].[How many Miles?]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field("Count Casinos", "COUNTD([name])", datatype="integer")
    e.add_calculated_field(
        "Dynamic Title",
        "'Show me all casinos within ' + STR(INT([Parameters].[How many Miles?])) + ' miles of'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Dynamic Casino Title",
        "[Parameters].[Selected Casino] + '..'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Count Within",
        'STR(COUNTD(IF [Within specified miles?] AND NOT [Is Selected Casino?] THEN [name] END)) + " casinos within " + STR(INT([Parameters].[How many Miles?])) + " miles"',
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_worksheet("Title")
    e.configure_chart("Title", mark_type="Text", label="Dynamic Title")
    e.add_worksheet("Casino Title")
    e.configure_chart("Casino Title", mark_type="Text", label="Dynamic Casino Title")
    e.add_worksheet("Count")
    e.configure_chart("Count", mark_type="Text", label="Count Within")
    e.add_worksheet("Map")
    e.configure_chart(
        "Map",
        mark_type="Circle",
        columns=["AVG(longitude)"],
        rows=["AVG(latitude)"],
        detail="name",
        color="SUM(Distance (metres))",
        size="Is Selected Casino?",
        tooltip=["name", "SUM(Distance (miles))"],
        filters=[{"column": "Within specified miles?", "values": ["true"]}],
    )
    e.add_worksheet("Data")
    e.configure_chart(
        "Data",
        mark_type="Text",
        columns=["name"],
        rows=["SUM(Distance (miles))"],
        color="Within specified miles?",
    )
    e.configure_worksheet_style(
        "Title", pane_datalabel_style={"font-size": "15", "font-family": "Tableau Book"}
    )
    e.configure_worksheet_style(
        "Casino Title",
        pane_datalabel_style={"font-size": "22", "font-family": "Tableau Book"},
    )
    e.configure_worksheet_style(
        "Count", pane_datalabel_style={"font-size": "12", "font-family": "Tableau Book"}
    )
    e.add_dashboard(
        "WW43 Las Vegas Casinos",
        width=350,
        height=800,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "worksheet",
                    "name": "Title",
                    "fit": "entire",
                    "show_title": False,
                    "fixed_size": 28,
                },
                {
                    "type": "worksheet",
                    "name": "Casino Title",
                    "fit": "entire",
                    "show_title": False,
                    "fixed_size": 48,
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 70,
                    "children": [
                        {
                            "type": "paramctrl",
                            "parameter": "How many Miles?",
                            "mode": "compact",
                            "fixed_size": 150,
                        },
                        {
                            "type": "text",
                            "text": "Click on a Casino to change\nactive Casino",
                            "font_size": "9",
                            "bold": True,
                            "color": "#555555",
                            "weight": 1,
                        },
                    ],
                },
                {
                    "type": "color",
                    "worksheet": "Map",
                    "field": "SUM(Distance (metres))",
                    "show_title": True,
                    "fixed_size": 55,
                },
                {
                    "type": "worksheet",
                    "name": "Count",
                    "fit": "entire",
                    "show_title": False,
                    "fixed_size": 38,
                },
                {
                    "type": "worksheet",
                    "name": "Map",
                    "fit": "entire",
                    "show_title": False,
                    "weight": 1,
                },
                {
                    "type": "text",
                    "text": "#WORKOUTWEDNESDAY  |  2019  |  WEEK 43",
                    "font_size": "8",
                    "bold": True,
                    "fixed_size": 32,
                },
            ],
        },
        worksheet_names=["Title", "Casino Title", "Count", "Map"],
    )
    e.add_dashboard_action(
        "WW43 Las Vegas Casinos",
        "parameter",
        "Map",
        source_field="name",
        target_parameter="Selected Casino",
        aggregation="attr",
        caption="Select Casino",
    )
    style_map(e)
    O.mkdir(exist_ok=True)
    e.save(p, validate=False)
    package_shape_assets(p)
    return p


if __name__ == "__main__":
    for n in (
        "2019-10-25-ww43-las-vegas-casinos-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(O / n))
