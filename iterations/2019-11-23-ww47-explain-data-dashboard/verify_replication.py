# quarterly-trends
# year-comparison
# order-jitter
# saved-explanations
# locked-data
"""Validate public construction, data provenance, workbook contracts and data oracle."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json,tempfile
from lxml import etree
from cwtwb import TWBEditor
from verify_data import verify as verify_data
HERE=Path(__file__).resolve().parent

def load(path):
    with ZipFile(path) as archive:
        names=archive.namelist();assert len(names)==len(set(names))
        twb=[n for n in names if n.endswith(".twb")];assert len(twb)==1
        lock=json.loads((HERE/"inputs/source-lock.json").read_text())
        for item in lock["extracted_data"]:
            source=HERE/item["file"];assert sha256(source.read_bytes()).hexdigest()==item["sha256"]
            if source.suffix==".hyper":
                name=next(n for n in names if Path(n).name==source.name)
                assert sha256(archive.read(name)).hexdigest()==item["sha256"]
        return etree.fromstring(archive.read(twb[0]))

def contract(root):
    ds=root.find("./datasources/datasource[@caption]")
    fields={c.get("caption") or c.get("name").strip("[]"):c for c in ds.findall("column")}
    def formula(name):return fields[name].find("calculation").get("formula")
    assert "MAX(YEAR" in formula("Latest Year") and "[Order Date]" in formula("Sales This Year")
    assert "RANDOM" not in formula("Jitter") and "7919" in formula("Jitter")
    sheets={s.get("name"):s for s in root.findall("./worksheets/worksheet")}
    assert set(sheets)=={"Trend","This Year v Last Year Bars","Jitter Dot Plot","Average Value of Records","Average Sales by Category"}
    assert sheets["Trend"].find(".//style-rule[@element='axis']/encoding[@range-type='independent']") is not None
    assert sheets["Trend"].find(".//mark").get("class")=="Line"
    assert "qk" in sheets["Trend"].findtext("table/cols")
    assert sheets["This Year v Last Year Bars"].find(".//mark").get("class")=="Bar"
    assert len(sheets["This Year v Last Year Bars"].findall(".//reference-line"))==1
    for name in ["Jitter Dot Plot","Average Value of Records"]:
        assert sheets[name].find(".//mark").get("class")=="Circle"
        assert any("Order ID" in e.get("column","") for e in sheets[name].findall(".//column-instance"))
        assert len(sheets[name].findall(".//reference-line"))==1
    assert "avg:Sales" in sheets["Average Value of Records"].findtext("table/cols")
    assert "avg:Sales" in sheets["Average Sales by Category"].findtext("table/rows")
    assert len(root.findall("./dashboards/dashboard"))==2
    primary=root.find("./dashboards/dashboard[@name='2019_11_20_WW47_High_Level_Sales']")
    for name,x,w in [("Trend","800","29500"),("This Year v Last Year Bars","30300","28600"),("Jitter Dot Plot","58900","40300")]:
        zone=primary.find(".//zone[@name='"+name+"']")
        assert zone.get("x")==x and zone.get("w")==w and zone.get("y")=="13750",zone.attrib
    for d in root.findall("./dashboards/dashboard"):assert d.find("size").get("maxwidth")=="1000" and d.find("size").get("maxheight")=="800"

# case-functional-contract: explicit assertions, independent data and SDK round-trip.
def main():
    path=HERE/"outputs/replicated-workbook.twbx"
    contract(load(path))
    with tempfile.TemporaryDirectory(prefix="wow-contract-") as directory:
        other=Path(directory)/"roundtrip.twbx"
        TWBEditor.open_existing(path).save(other,validate=False)
        contract(load(other))
    verify_data()
    # cloud-rest-data-contract: validate committed capture hashes and actual exported-sheet scope.
    if (HERE/"evidence/cloud-data-comparison.json").exists():
        from verify_cloud_data import verify as verify_cloud
        verify_cloud()
    print("PASS: locked Hyper, worksheet/dashboard contracts, independent full data oracle, SDK round-trip. Actions checked structurally; browser events not executed.")

if __name__=="__main__":main()
