"""Verify six chart grains, preserved input and public builder contracts."""
from pathlib import Path
from zipfile import ZipFile
import ast, hashlib, json
from lxml import etree
from sales_oracle import compute
HERE=Path(__file__).resolve().parent
def verify():
    # acceptance: source-integrity
    lock=json.loads((HERE/"inputs/source-lock.json").read_text(encoding="utf-8"))
    for source in lock["extracted_data"]:assert hashlib.sha256((HERE/source["file"]).read_bytes()).hexdigest()==source["sha256"]
    # acceptance: independent-sdk-build
    tree=ast.parse((HERE/"build_replication.py").read_text(encoding="utf-8"))
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="TWBEditor" and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=="" for n in ast.walk(tree))
    assert not any(isinstance(n,ast.Attribute) and n.attr.startswith("_") for n in ast.walk(tree))
    with ZipFile(HERE/"outputs/replicated-workbook.twbx") as package:
        root=etree.fromstring(package.read(next(n for n in package.namelist() if n.endswith(".twb"))))
    # acceptance: six-sheet-grains
    sheets={n.get("name"):n for n in root.findall("./worksheets/worksheet")}
    assert len(sheets)==6
    for name,mark in [("Sales By Week ","Area"),("Year Filter","Circle"),("Sales by Month","Bar"),("Dot by Sub Cat ","Circle"),("Bar by Sub Cat","Bar"),("Map","Multipolygon")]:assert sheets[name].find(".//mark").get("class")==mark
    assert "[my:" in etree.tostring(sheets["Dot by Sub Cat "],encoding="unicode")
    assert sheets["Bar by Sub Cat"].find(".//shelf-sort-v2") is not None
    # acceptance: independent-six-grain-data
    result=compute()
    stored=json.loads((HERE/"evidence/data-contract.json").read_text(encoding="utf-8"))
    assert stored==result
    assert len(result["states"]["default"]["subcategory"])==17
    assert len(result["states"]["default"]["monthly"])==48
    assert len(result["states"]["default"]["state"])==49
    # acceptance: year-filter-and-highlight-actions
    actions=root.findall("./actions/action")
    assert any(a.find("./command").get("command")=="tsc:tsl-filter" and a.find("./source").get("worksheet")=="Year Filter" and a.find("./activation").get("type")=="on-select" for a in actions), "Year filter action not yet installed"
    assert any(a.find("./command").get("command")=="tsc:brush" and a.find("./activation").get("type")=="on-hover" for a in actions), "Hover highlight action not yet installed"
    highlight=next(a for a in actions if a.find("./command").get("command")=="tsc:brush")
    assert {e.get("name") for e in highlight.findall("./source/exclude-sheet")}=={"Map","Sales By Week ","Year Filter"}
    exclusions=next(e.get("value") for e in highlight.findall("./command/param") if e.get("name")=="exclude")
    assert set(exclusions.split(","))=={"Map","Sales By Week ","Year Filter"}
    assert all(a.find("./activation").get("auto-clear")=="true" for a in actions)
    assert len(root.findall(".//color-palette[@type='ordered-sequential']"))==4
    print("PASS: preserved source, public builder, six chart grains, four data states and action contracts")
if __name__=="__main__":verify()
