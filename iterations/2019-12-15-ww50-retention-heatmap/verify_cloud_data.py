"""Compare actual Cloud data exports with full independent cohort oracle."""
from pathlib import Path
from datetime import datetime
import csv,hashlib,json
HERE=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
def date(value):return str(datetime.strptime(value,"%m/%d/%Y").date())
def number(value):return float(value.replace(",","").replace("%",""))
def verify():
    oracle=json.loads((HERE/"evidence/data-contract.json").read_text(encoding="utf-8"));receipt=json.loads((HERE/"evidence/cloud-verification.json").read_text(encoding="utf-8"))
    assert digest(HERE/"outputs/replicated-workbook.twbx")==receipt["source_hashes"]["replica"],"Workbook changed after capture"
    assert {s["name"] for s in receipt["states"]}=={"default","period-ten","period-eighteen"}, "Incomplete captures"
    all_cells={(c["cohort"],c["week"]):c for c in oracle["all_cells"]}
    report={"status":"passed","replica_sha256":receipt["source_hashes"]["replica"],"denominator_diagnosis":"Author and replica BAN actual denominator is sum of deduplicated cohort sizes. Row-repeated denominator rejected.","csv_scope":"Author Data full1431cohort/week cells?4measures; replica Heat Map entire visible matrix; replica Bar marginal histogram; dashboard and BAN CSV headline only.","checks":[]}
    for state in receipt["states"]:
        period=int(state["parameters"].get("Time Period",26));model=oracle["periods"][str(period)]
        for entry in state["data"]:
            path=HERE/entry["path"];assert digest(path)==entry["sha256"]
            records=rows(path);assert records,(state["name"],entry["role"],entry["view"])
            if entry["role"]=="author" and entry["view"]=="Data":
                for row in records:
                    cohort=date(row["Cohort"]);actual_date=date(row["order_week"]);week=(datetime.fromisoformat(actual_date)-datetime.fromisoformat(cohort)).days//7;cell=all_cells[(cohort,week)];name=row["Measure Names"]
                    expected=cell["returning_customers"] if name=="Customer Count" else week if name=="Min. Week Index" else cell["retention"] if name=="% of Customers" else all_cells.get((cohort,period),{}).get("returning_customers",0)
                    assert abs(number(row["Measure Values"])-expected)<1e-8
                    assert number(row["New Customers"])==cell["new_customers"]
                scope="author all1431cohort/week pairs?4measures"
            elif entry["role"]=="replica" and entry["view"]=="Heat Map":
                expected={(c["cohort"],c["week"]):c for c in model["matrix"]};actual={(date(r["Cohort"]),int(number(r["Week Index"]))):r for r in records}
                assert len(records)==len(actual)==len(expected);assert set(actual)==set(expected)
                for key,cell in expected.items():
                    row=actual[key];assert number(row["Customer Count"])==cell["returning_customers"] and number(row["New Customers"])==cell["new_customers"]
                    assert abs(number(row["% of Customers"])/100-cell["retention"])<=.000500001
                scope="replica complete visible heatmap matrix"
            elif entry["role"]=="author" and entry["view"]=="BAN:Data":
                values={r["Measure Names"]:number(r["Measure Values"]) for r in records};assert values["Customer Count"]==model["ban"]["returning_customers"] and values["New Customers"]==model["ban"]["new_customers"];assert abs(values["% BAN"]-model["ban"]["retention"])<1e-8;scope="author underlying BAN measures"
            elif entry["role"]=="replica" and entry["view"]=="Bar":
                expected={c["cohort"]:c for c in model["bars"]};actual={date(r["Cohort"]):r for r in records};assert set(actual)==set(expected)
                for key,cell in expected.items():
                    row=actual[key];assert number(row["Customer Count"])==cell["returning_customers"] and number(row["New Customers"])==cell["new_customers"];assert abs(number(row["% of Customers"])/100-cell["retention"])<=.000500001
                scope="replica complete marginal histogram"
            else:
                assert len(records)==1;row=records[0];assert number(row["Count Customers at Time Period Param"])==model["ban"]["returning_customers"] and number(row.get("New Customers",row.get("Sum of New Customers")))==model["ban"]["new_customers"];assert abs(number(row["% BAN"])/100-model["ban"]["retention"])<=.000500001;scope="BAN only"
            report["checks"].append({"state":state["name"],"role":entry["role"],"view":entry["view"],"rows":len(records),"scope":scope,"sha256":entry["sha256"]})
    (HERE/"evidence/cloud-data-comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PASS complete author data, all replica matrices/marginals and BAN exports")
if __name__=="__main__":verify()
