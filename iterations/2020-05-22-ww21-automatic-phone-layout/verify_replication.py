"""Independent raw-data oracle for every annual/monthly/product mark."""

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
import ast
import calendar
import csv
import json
import re
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
SHEETS = {
    "Sales Summary",
    "Sales Line",
    "Top 10 Products by Sales",
    "Profit Summary",
    "Profit Line",
    "Top & Bottom 10 Products by Profit",
}


def number(value):
    text = (
        value.strip()
        .replace(",", "")
        .replace("$", "")
        .replace("?", "")
        .replace("?", "-")
    )
    multiplier = 1000000 if text.endswith("M") else 1000 if text.endswith("K") else 1
    return float(text.rstrip("%MK")) * multiplier / (100 if "%" in text else 1)


def verify():
    # blank-sdk-build; locked-source-data; native-calculations-actions;
    # independent-complete-data-oracle; cloud-rest-comparison; cloud-visual-review
    source = (HERE / "build_replication.py").read_text(encoding="utf-8-sig")
    assert 'TWBEditor("")' in source
    assert not any(
        isinstance(n, ast.Attribute) and n.attr.startswith("_")
        for n in ast.walk(ast.parse(source))
    )
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    item = lock["extracted_data"][0]
    data = HERE / item["file"]
    assert sha256(data.read_bytes()).hexdigest() == item["sha256"]
    artifact = HERE / "outputs/replicated-workbook.twbx"
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as package:
        root = etree.fromstring(
            package.read(next(n for n in package.namelist() if n.endswith(".twb")))
        )
        assert (
            sha256(
                package.read(
                    next(n for n in package.namelist() if n.endswith(".hyper"))
                )
            ).hexdigest()
            == item["sha256"]
        )
    assert {n.get("name") for n in root.xpath("//worksheet")} == SHEETS
    year_members = root.xpath(
        '//worksheet//filter[contains(@column,"yr:Order Date:ok")]//groupfilter[@function="member"]'
    )
    assert year_members and all(
        n.get("member") in {"2017", "2018", "2019"} for n in year_members
    )
    year_colors = root.xpath(
        '//datasource/style//encoding[contains(@field,"yr:Order Date:ok")]//bucket'
    )
    assert year_colors and all(n.text in {"2018", "2019"} for n in year_colors)
    phone = root.xpath('//devicelayout[@name="Phone"]')[0]
    assert (
        phone.get("auto-generated") == "true"
        and phone.find("size").get("sizing-mode") == "vscroll"
    )
    assert SHEETS <= {n.get("name") for n in phone.xpath(".//zone[@name]")}
    assert root.xpath('//dashboard/size[@maxwidth="1200"][@maxheight="800"]')
    for heading in ["SALES", "PROFIT"]:
        assert root.xpath(
            '//dashboard/zones//formatted-text/run[@fontalignment="0"][text()=$heading]',
            heading=heading,
        )
    combined = root.xpath(
        '//datasource/group[@caption="Top & Bottom Products by Profit"]/groupfilter[@function="union"]'
    )[0]
    assert len(combined.findall("groupfilter")) == 2
    bottom = root.xpath(
        '//datasource/group[@caption="Bottom 10 Products by Profit"]/groupfilter'
    )[0]
    assert bottom.get("end") == "bottom" and bottom.get("count") == "10"
    profit_group = root.xpath(
        "/workbook/datasources/datasource/column[@caption='Profit Group']"
    )[0]
    assert profit_group.find("calculation").get("formula") == (
        "IF [Top 10 Products by Profit] THEN 'Top 10' ELSE 'Bottom 10' END"
    )
    profit_sheet = root.xpath(
        '//worksheet[@name="Top & Bottom 10 Products by Profit"]'
    )[0]
    group_instance = profit_sheet.xpath(
        ".//column-instance[@column=$base]", base=profit_group.get("name")
    )[0].get("name")
    assert group_instance in profit_sheet.find("table/rows").text
    assert profit_sheet.xpath(
        './/format[@attr="text-orientation"][@value="-90"][contains(@field,$group)]',
        group=group_instance,
    )
    for sheet in ["Top 10 Products by Sales", "Top & Bottom 10 Products by Profit"]:
        assert root.xpath('//worksheet[@name="' + sheet + '"]//filter[@context="true"]')
        assert root.xpath(
            '//worksheet[@name=$sheet]//format[@attr="mark-color"][@value="#000000"]',
            sheet=sheet,
        )
    for metric in ["Sales", "Profit"]:
        sheet = root.xpath('//worksheet[@name="' + metric + ' Summary"]')[0]
        base = root.xpath(
            "/workbook/datasources/datasource/column[@caption=$name]",
            name=metric + " Year Change",
        )[0].get("name")
        change_instance = sheet.xpath(".//column-instance[@column=$base]", base=base)[
            0
        ].get("name")
        assert any(
            n.get("column").endswith("." + change_instance)
            for n in sheet.xpath("./table/panes/pane/encodings/text")
        )
        calculations = sheet.xpath(".//column-instance/table-calc")
        assert calculations and all(
            c.get("ordering-type") == "Field" for c in calculations
        )
        assert any(
            "yr:Order Date:ok" in c.get("ordering-field", "") for c in calculations
        )
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, data) as connection:
            table = connection.catalog.get_table_names("Extract")[0]
            raw = connection.execute_list_query(
                'SELECT "Order Date", "Product Name", "Sales", "Profit" FROM '
                + str(table)
            )
    annual = defaultdict(lambda: [0.0, 0.0])
    monthly = defaultdict(lambda: [0.0, 0.0])
    products = defaultdict(lambda: [0.0, 0.0])
    for date, product, sales, profit in raw:
        annual[date.year][0] += sales
        annual[date.year][1] += profit
        if date.year in [2018, 2019]:
            monthly[(date.year, date.month)][0] += sales
            monthly[(date.year, date.month)][1] += profit
            products[product][0] += sales
            products[product][1] += profit
    assert len(monthly) == 24
    sales_top = sorted(products, key=lambda p: (-products[p][0], p))[:10]
    profit_top = sorted(products, key=lambda p: (-products[p][1], p))[:10]
    profit_bottom = sorted(products, key=lambda p: (products[p][1], p))[:10]
    assert len(set(profit_top + profit_bottom)) == 20
    annual_expected = {
        year: {
            "sales": annual[year][0],
            "profit": annual[year][1],
            "sales_change": (annual[year][0] - annual[year - 1][0])
            / abs(annual[year - 1][0]),
            "profit_change": (annual[year][1] - annual[year - 1][1])
            / abs(annual[year - 1][1]),
        }
        for year in [2018, 2019]
    }
    report = {
        "status": "pass",
        "artifact_sha256": digest,
        "source_rows": len(raw),
        "annual": annual_expected,
        "monthly": {str(k): v for k, v in monthly.items()},
        "top_sales": {p: products[p][0] for p in sales_top},
        "extreme_profit": {p: products[p][1] for p in profit_top + profit_bottom},
        "phone_layout_scope": "Native automatic Phone/vscroll artifact contract only; no browser or mobile rendering executed.",
        "source_scope": "Donna full annual 2018/2019 product dashboard, not official YTD/customer brief.",
    }
    manifest_path = HERE / "evidence/cloud-verification.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        provenance = json.loads(
            (HERE / "evidence/export-provenance.json").read_text(encoding="utf-8")
        )
        assert manifest["source_hashes"]["replica"] == digest
        assert manifest["source_hashes"]["author"] == provenance["comparison_sha256"]
        assert provenance["original_sha256"] == lock["locked_original_sha256"]
        assert {s["name"] for s in manifest["states"]} == {"default"}
        checks = []
        for state in manifest["states"]:
            for image in state["views"].values():
                assert (
                    sha256((HERE / image["path"]).read_bytes()).hexdigest()
                    == image["sha256"]
                )
            assert {c["view"] for c in state["data"]} == SHEETS
            for capture in state["data"]:
                path = HERE / capture["path"]
                assert sha256(path.read_bytes()).hexdigest() == capture["sha256"]
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    exported = list(csv.DictReader(stream))
                assert exported, (path, "Empty data export")
                view = capture["view"]
                metric = "Sales" if "Sales" in view else "Profit"
                index = 0 if metric == "Sales" else 1
                if "Products" in view:
                    expected = (
                        report["top_sales"]
                        if metric == "Sales"
                        else report["extreme_profit"]
                    )
                    found = {}
                    for row in exported:
                        product = row["Product Name"]
                        assert product in expected, (path, product)
                        if metric == "Profit" and path.name.startswith("cloud-replica"):
                            assert row["Profit Group"] == (
                                "Top 10" if product in profit_top else "Bottom 10"
                            ), (path, product, row)
                        key = next(
                            k for k in row if k == metric or k == "SUM(" + metric + ")"
                        )
                        assert abs(number(row[key]) - expected[product]) <= 0.51, (
                            path,
                            product,
                            row,
                        )
                        found[product] = row
                    assert set(found) == set(expected)
                elif "Line" in view:
                    found = {}
                    for row in exported:
                        yearkey = next(k for k in row if "Year" in k or "YEAR" in k)
                        monthkey = next(k for k in row if "Month" in k or "MONTH" in k)
                        year = int(row[yearkey])
                        monthtext = row[monthkey]
                        month = (
                            int(monthtext)
                            if monthtext.isdigit()
                            else next(
                                n
                                for n in range(1, 13)
                                if calendar.month_name[n]
                                .lower()
                                .startswith(monthtext.lower())
                            )
                        )
                        key = next(
                            k for k in row if k == metric or k == "SUM(" + metric + ")"
                        )
                        assert (
                            abs(number(row[key]) - monthly[(year, month)][index])
                            <= 0.51
                        )
                        found[(year, month)] = row
                    assert set(found) == set(monthly)
                else:
                    found = {}
                    for row in exported:
                        yearkey = next(k for k in row if "Year" in k or "YEAR" in k)
                        year = int(row[yearkey])
                        assert year in annual_expected, (path, year)
                        key = next(
                            k for k in row if k == metric or k == "SUM(" + metric + ")"
                        )
                        changekey = next(
                            k
                            for k in row
                            if "Change" in k or "%" in k or "Difference" in k
                        )
                        assert (
                            abs(
                                number(row[key]) - annual_expected[year][metric.lower()]
                            )
                            <= 0.51
                        )
                        assert (
                            abs(
                                number(row[changekey])
                                - annual_expected[year][metric.lower() + "_change"]
                            )
                            <= 0.0051
                        )
                        found[year] = row
                    assert set(found) == {2018, 2019}
                checks.append(
                    {
                        "path": capture["path"],
                        "view": view,
                        "rows": len(exported),
                        "status": "pass",
                    }
                )
        assert len(checks) == 12
        report["cloud_checks"] = checks
        (HERE / "evidence/cloud-data-comparison.json").write_text(
            json.dumps({"status": "pass", "checks": checks}, indent=2), encoding="utf-8"
        )
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        "PASS",
        len(raw),
        "raw rows; 24 monthly pairs; 2 annual comparisons; 10 sales + 20 profit products",
    )


if __name__ == "__main__":
    verify()
