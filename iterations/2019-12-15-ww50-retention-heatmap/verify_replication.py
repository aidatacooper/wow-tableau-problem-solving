"""Independent data oracle and generated-artifact contracts."""
from pathlib import Path
from zipfile import ZipFile
import ast
import hashlib
import json
from lxml import etree
from cohort_oracle import compute
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/replicated-workbook.twbx"
def verify():
    # acceptance: source-integrity
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    for source in lock["extracted_data"]:
        assert hashlib.sha256((HERE / source["file"]).read_bytes()).hexdigest() == source["sha256"]
    # acceptance: independent-sdk-build
    tree = ast.parse((HERE / "build_replication.py").read_text(encoding="utf-8"))
    assert any(isinstance(n, ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="TWBEditor" and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=="" for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith("_") for n in ast.walk(tree))
    with ZipFile(OUTPUT) as package:
        root = etree.fromstring(package.read(next(name for name in package.namelist() if name.endswith(".twb"))))
        assert any(name.endswith(".hyper") for name in package.namelist())
    columns = {node.get("caption",node.get("name")): node for node in root.findall("./datasources/datasource/column")}
    # acceptance: parameter-domain
    parameter = columns["Time Period"]
    assert parameter.get("value")=="26"
    assert parameter.find("range").get("min")=="10" and parameter.find("range").get("max")=="26"
    # acceptance: cohort-and-denominator
    formulas = {key: node.find("calculation").get("formula") for key,node in columns.items() if node.find("calculation") is not None}
    assert "FIXED" in formulas["Cohort"] and "monday" in formulas["Cohort"]
    assert "FIXED" in formulas["New Customers"] and "COUNTD" in formulas["New Customers"]
    assert "SUM(" in formulas["% of Customers"]
    worksheets = {node.get("name"):node for node in root.findall("./worksheets/worksheet")}
    # acceptance: matrix-and-marginal-filter-contract
    for sheet,names in [("Heat Map",["FILTER:Complete Cohorts","FILTER:Weeks Index to Display"]),("Bar",["FILTER:Time Period"]),("BAN",["FILTER:Time Period"])]:
        xml = etree.tostring(worksheets[sheet],encoding="unicode")
        for name in names: assert name in xml, (sheet,name)
        assert worksheets[sheet].findall(".//filter"), sheet
    assert worksheets["Heat Map"].find(".//mark").get("class")=="Square"
    assert len(worksheets["Bar"].findall("./table/panes/pane"))==2
    # acceptance: all-period-independent-data
    result=compute()
    stored=json.loads((HERE / "evidence/data-contract.json").read_text(encoding="utf-8"))
    assert result==stored
    assert len(result["periods"])==17
    assert [(result["periods"][period]["cohorts"],result["periods"][period]["matrix_cells"]) for period in ["10","18","26"]]==[(43,387),(35,595),(27,675)]
    print("PASS: source, public builder, parameter/filter/layered contracts and all 17 independent data states")
if __name__=="__main__":verify()
