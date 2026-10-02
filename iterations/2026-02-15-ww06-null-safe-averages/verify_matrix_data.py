"""Independent locked-Hyper matrix input calculations; no matrix REST CSV claim."""
from pathlib import Path
from hashlib import sha256
from datetime import date, datetime, timezone
from collections import defaultdict
import json
from tableauhyperapi import HyperProcess, Connection, Telemetry
BASE = Path(__file__).resolve().parent

def verify(output):
    lock = json.loads((BASE / "inputs/source-lock.json").read_text())["extracted_data"][0]
    path = BASE / lock["file"]
    assert sha256(path.read_bytes()).hexdigest() == lock["sha256"]
    states = []
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process, Connection(process.endpoint, str(path)) as conn:
        raw = conn.execute_list_query('SELECT "Category", "Sub-Category", "Order Date", "Order ID" FROM "Extract"."Extract"')
        for name, lo, hi, category in [("default", date(2025,7,11), date(2025,7,23), None), ("short-date-range", date(2025,7,14), date(2025,7,18), None), ("furniture-only", date(2025,7,11), date(2025,7,23), "Furniture")]:
            domains = defaultdict(set)
            groups = defaultdict(set)
            for cat, sub, day, oid in raw:
                if category and cat != category: continue
                domains[cat].add(sub)
                day = date.fromisoformat(str(day))
                weekday = (day.weekday()+1)%7
                if lo <= day <= hi and oid is not None: groups[(cat,sub,weekday)].add(oid)
            rows = []
            for cat, subs in sorted(domains.items()):
                for sub in sorted(subs):
                    vals = [len(groups[(cat,sub,w)]) for w in range(7)]
                    rows.append({"category":cat,"sub_category":sub,"Sunday_first_counts":vals,"labels":["*0" if v==0 else str(v) for v in vals]})
                averages = [sum(len(groups[(cat,sub,w)]) for sub in subs)/len(subs) for w in range(7)]
                rows.append({"category":cat,"subtotal":"Avg.","Sunday_first_average":averages,"formatted":["*0.00" if v==0 else f"{v:.2f}" for v in averages]})
            where = f""""Order Date" >= DATE '{lo}' AND "Order Date" <= DATE '{hi}' """
            if category: where += " AND \"Category\" = 'Furniture'"
            query = f"""SELECT "Category", "Sub-Category", MOD(EXTRACT(DOW FROM "Order Date")::int,7), COUNT(DISTINCT "Order ID") FROM "Extract"."Extract" WHERE {where} GROUP BY 1,2,3"""
            sql = {(c,s,int(w)):int(n) for c,s,w,n in conn.execute_list_query(query)}
            assert all(sql.get(key,0)==len(value) for key,value in groups.items())
            assert all(len(groups[key])==value for key,value in sql.items())
            states.append({"name":name,"min_date":str(lo),"max_date":str(hi),"category":category,"rows":rows,"independent_SQL_vs_Python_equal":True,"sql":query})
    result = {"acceptance_scope":"cloud_rest_and_artifact_contracts","browser_interaction_executed":False,"checked_at":datetime.now(timezone.utc).isoformat(),"hyper_sha256":lock["sha256"],"passed":True,"scope":"Independent Hyper COUNTD conditional/date/Category and Sunday-first mean-of-detail calculations. Matrix visual equality separately documented in visual-review.json; no matrix CSV exported.","states":states}
    Path(output).write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__ == "__main__":
    verify(BASE / "evidence/matrix-data-contract.json")
