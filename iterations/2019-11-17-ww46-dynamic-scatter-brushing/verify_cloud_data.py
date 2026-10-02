"""Validate captured REST evidence, with explicit exported-sheet coverage."""
from pathlib import Path
from hashlib import sha256
import csv,json,math,sys
HERE=Path(__file__).resolve().parent

def number(value):
    value=str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    return float(value)

def verify(write=False,strict_workbook=False):
    report=json.loads((HERE/"evidence/cloud-verification.json").read_text())
    oracle=json.loads((HERE/"evidence/data-contract.json").read_text())
    assert report["acceptance_scope"]=="cloud_rest_and_artifact_contracts" and report["browser_interaction_executed"] is False
    if strict_workbook:assert sha256((HERE/"outputs/replicated-workbook.twbx").read_bytes()).hexdigest()==report["source_hashes"]["replica"]
    result={"acceptance_scope":report["acceptance_scope"],"source_hashes":report["source_hashes"],"browser_interaction_executed":False,"states":[]}
    for state in report["states"]:
        for role,image in state["views"].items():assert sha256((HERE/image["path"]).read_bytes()).hexdigest()==image["sha256"]
        by_role={}
        for export in state["data"]:
            path=HERE/export["path"];assert sha256(path.read_bytes()).hexdigest()==export["sha256"]
            by_role[export["role"]]=list(csv.DictReader(path.open(encoding="utf-8-sig")))
        level=state["parameters"].get("Set Level of Detail","Customer")
        if state["parameters"].get("Set X-Axis") == "Profit":
            result["states"].append({"name":state["name"],"evaluated":False,"reason":"Profit is not an allowed axis in author's implemented workbook; invalid historical REST state is excluded from acceptance."})
            continue
        expected=oracle["lod_states"][level]["mark_count"]
        for role,rows in by_role.items():
            assert len(rows)==1 and rows[0]["In / Out of Selected LOD"]=="Out"
            total_name="Total # LOD" if role=="author" else "LOD Total"
            share_name="% of Total # LOD" if role=="author" else "LOD Share"
            selected_name="# LOD Selected" if role=="author" else "LOD Selected"
            assert number(rows[0][total_name])==expected,(state["name"],role,rows[0][total_name],expected)
            assert number(rows[0][share_name])==100 and number(rows[0][selected_name])==0
        result["states"].append({"name":state["name"],"parameters":state["parameters"],"evaluated":True,"exported_sheet":"LOD Bars","rows":1,"expected_lod_count":expected,"checks":["complete Out count","100% total share","zero selected membership"],"not_exported":["Scatter coordinates","X Bars","Y Bars"],"independent_coverage":"data-contract.json covers all 48 axis/LOD combinations and set partitions independently; this CSV alone does not validate scatter/X/Y rendered values."})
    target=HERE/"evidence/cloud-data-comparison.json"
    if write:target.write_text(json.dumps(result,indent=2),encoding="utf8")
    else:assert json.loads(target.read_text())==result
    return result

if __name__=="__main__":
    verify(write="--write" in sys.argv,strict_workbook="--strict-workbook" in sys.argv)
    print("PASS: captured REST export hashes and explicitly scoped numerical comparisons; PNGs hash-bound, browser events not executed")
