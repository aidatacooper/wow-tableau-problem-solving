# dynamic-scatter
# set-action-brushing
# top-x-axis
# locked-data
"""Validate public construction, data provenance, workbook contracts and data oracle."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json,tempfile,re
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
    params={c.get("caption"):c for c in root.findall("./datasources/datasource[@name='Parameters']/column")}
    for name,value in [("Set Level of Detail",'"Customer"'),("Set X-Axis",'"Quantity"'),("Set Y-Axis",'"Discount"')]:assert params[name].get("value")==value
    assert len(params["Set Level of Detail"].findall("members/member"))==3
    for axis in ["X","Y"]:
        assert len(params[f"Set {axis}-Axis"].findall("members/member"))==4
        assert "COUNTD" in formula(f"{axis}-Axis") and "SUM" in formula(f"{axis}-Axis")
    assert "Customer Name" in formula("LOD") and fields["Manufacturer"].find("calculation").get("class")=="categorical-bin"
    grouping=fields["Manufacturer"].find("calculation")
    assert grouping.get("default") is None
    def decode_literal(value):return re.sub(r"\\(.)",r"\1",value[1:-1])
    serialized={decode_literal(bin.get("value")):[decode_literal(v.text) for v in bin.findall("value")] for bin in grouping.findall("bin")}
    assert serialized==json.loads((HERE/"inputs/manufacturer-groups.json").read_text()), "Serialized group literals must preserve quotes, hash, percent and original bin mapping"
    group=ds.find("group[@caption='Selected LOD']");assert group is not None
    scatter=root.find("./worksheets/worksheet[@name='Scatter']")
    axes=scatter.findall(".//style-rule[@element='axis']/encoding")
    assert any(a.get("fold")=="true" and a.get("synchronized")=="true" and a.get("scope")=="cols" for a in axes)
    assert any(a.get("major-show")=="false" and a.get("minor-show")=="false" and a.get("class")=="0" for a in axes)
    assert len(scatter.findall(".//mark[@class='Circle']"))==2
    for name in ["LOD Bars","X Bars","Y Bars"]:
        sheet=root.find(f"./worksheets/worksheet[@name='{name}']");assert sheet.find(".//mark").get("class")=="Bar"
        assert sheet.find(".//column-instance/table-calc") is not None
        assert all("io:Selected LOD:nk" in calc.get("ordering-field", "") for calc in sheet.findall(".//column-instance/table-calc"))
        prefix=name.split()[0]
        assert "WINDOW_SUM" in formula(prefix+" Share")
        axis=sheet.find(".//style-rule[@element='axis']/encoding[@range-type='fixed']")
        assert axis.get("min")=="0" and axis.get("max")=="1"
        assert "WINDOW_MAX" in formula(prefix+" Selected")
    action=root.find("./actions/edit-group-action")
    assert action.find("activation").get("type")=="on-select"
    assert action.find("source").get("worksheet")=="Scatter"
    assert action.find("params/param[@name='selection-clear-set-option']").get("value")=="exclude-all"
    assert action.find("params/param[@name='target-group']").get("value").endswith(".[Selected LOD]")
    dashboard=root.find("./dashboards/dashboard");assert dashboard.find("size").get("maxwidth")=="1000"
    assert {z.get("name") for z in dashboard.findall(".//zone") if z.get("name")}=={"Scatter","LOD Bars","X Bars","Y Bars"}

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
