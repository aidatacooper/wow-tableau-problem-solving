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
        expected={(row["order"],row["subcategory"]):row for row in oracle["orders"]}
        discrepancies={}
        for role,rows in by_role.items():
            actual={(r["Order ID"],r["Sub-Category"]):r for r in rows}
            assert len(rows)==len(actual)==len(expected)==9159
            assert set(actual)==set(expected)
            max_error=max(abs(number(actual[k]["Sales"])-expected[k]["sum_sales"]) for k in expected)
            assert max_error<=0.500001 if role=="author" else max_error<=0.000001,(role,max_error)
            discrepancies[role]=round(max_error,6)
        result["states"].append({"name":state["name"],"exported_sheet":"Jitter Dot Plot","rows":9159,"checks":["all order/subcategory identifiers","all horizontally plotted SUM(Sales) values"],"maximum_sales_error":discrepancies,"author_numeric_tolerance":0.500001,"author_formatting":"Author exports $ values rounded to whole dollars; replica retains decimals.","not_exported":["Trend quarter totals","This Year v Last Year Bars","saved explanation charts"],"jitter_policy":"Author unsupported RANDOM exports * in ATTR; deterministic replica jitter differs intentionally. Jitter is not used to certify sales values."})
    target=HERE/"evidence/cloud-data-comparison.json"
    if write:target.write_text(json.dumps(result,indent=2),encoding="utf8")
    else:assert json.loads(target.read_text())==result
    return result

if __name__=="__main__":
    verify(write="--write" in sys.argv,strict_workbook="--strict-workbook" in sys.argv)
    print("PASS: captured REST export hashes and explicitly scoped numerical comparisons; PNGs hash-bound, browser events not executed")
