"""Compare the complete cloud custom-axis CSV with author currency rounding."""
from pathlib import Path
import csv, json, hashlib
ROOT = Path(__file__).resolve().parent

def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows=list(csv.DictReader(handle))
    result={}
    for row in rows:
        key=row["Month Order Date"]
        if key in result: raise AssertionError("Duplicate month: " + key)
        result[key]=row
    return result

def main():
    a=ROOT/"outputs/cloud-author.csv"; b=ROOT/"outputs/cloud-replica.csv"
    author=read(a); replica=read(b); differences=[]
    for key in sorted(set(author)&set(replica)):
        for field in ("Colour:Circle", "Order Date Display"):
            if author[key][field]!=replica[key][field]: differences.append([key,field,author[key][field],replica[key][field]])
        sales=lambda v: float(v.replace("$", "").replace(",", ""))
        if abs(sales(author[key]["Sales"])-sales(replica[key]["Sales"]))>0.500001: differences.append([key,"Sales",author[key]["Sales"],replica[key]["Sales"]])
    same=set(author)==set(replica)
    result={"scope":"24 custom-axis month marks, source integer currency rounding tolerance 0.5; hover actions not tested", "author_rows":len(author),"replica_rows":len(replica),"keys_equal":same,"differences":differences,"pass":same and len(author)==24 and not differences,"source_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (a,b)}}
    (ROOT/"evidence/cloud-data-comparison.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    if not result["pass"]: raise SystemExit(1)
if __name__=="__main__": main()
