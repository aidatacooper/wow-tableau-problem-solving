"""Strictly compare the actual subcategory-only Cloud CSV exports."""
from pathlib import Path
import csv,hashlib,json
from datetime import datetime
HERE=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify():
    oracle=json.loads((HERE/"evidence/data-contract.json").read_text(encoding="utf-8"))
    receipt=json.loads((HERE/"evidence/cloud-verification.json").read_text(encoding="utf-8"))
    assert digest(HERE/"outputs/replicated-workbook.twbx")==receipt["source_hashes"]["replica"],"Workbook changed since export"
    assert {s["name"] for s in receipt["states"]}==set(oracle["states"]), "Incomplete captures"
    report={"status":"passed","replica_sha256":receipt["source_hashes"]["replica"],"csv_scope":"Author dashboard CSV Bar by Sub Cat ONLY. Replica independently exports weekly, monthly and entire dot matrix, plus marginal subcategory bars. Map and year-selector independently checked via Hyper plus PNG and artifact contracts.","checks":[]}
    for state in receipt["states"]:
        model=oracle["states"][state["name"]]
        for entry in state["data"]:
            path=HERE/entry["path"];assert digest(path)==entry["sha256"]
            rows=list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
            assert rows,(state["name"],entry["role"],entry["view"])
            if entry["role"]=="replica" and entry["view"]=="Sales By Week ":
                expected=model["weekly"];actual={str(datetime.strptime(row["Order Date Week"],"%d %B %Y").date()):float(row["Sales"].replace(",","")) for row in rows};scope="entire replica weekly area data; author paired CSV still subcategory bars only"
            elif entry["role"]=="replica" and entry["view"]=="Sales by Month":
                expected=model["monthly"];actual={datetime.strptime(row["Month, Year of Order Date"],"%B %Y").strftime("%Y-%m"):float(row["Sales"].replace(",","")) for row in rows};scope="entire replica monthly bars data; author paired CSV still subcategory bars only"
            elif entry["role"]=="replica" and entry["view"]=="Dot by Sub Cat ":
                expected=model["subcategory_month"];actual={row["Sub-Category"]+"|"+datetime.strptime(row["Month, Year of Order Date"],"%B %Y").strftime("%Y-%m"):float(row["Sales"].replace(",","")) for row in rows};scope="entire replica subcategory/month dot matrix; author paired CSV still subcategory bars only"
            else:
                expected=model["subcategory"];actual={row["Sub-Category"]:float(row["Sales"].replace("$","").replace(",","")) for row in rows};scope="Bar by Sub Cat only"
            assert len(rows)==len(expected);assert set(actual)==set(expected)
            tolerance=.500001 if entry["role"]=="author" else .000001
            errors={key:abs(actual[key]-expected[key]) for key in expected}
            assert max(errors.values())<=tolerance,(state["name"],entry["role"],entry["view"],max(errors.values()))
            report["checks"].append({"state":state["name"],"role":entry["role"],"view":entry["view"],"scope":scope,"rows":len(rows),"max_sales_error":max(errors.values()),"tolerance":tolerance,"sha256":entry["sha256"]})
    (HERE/"evidence/cloud-data-comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PASS four actual filter states, complete replica weekly/monthly/matrix/bar exports and author Bar-only exports")
if __name__=="__main__":verify()
