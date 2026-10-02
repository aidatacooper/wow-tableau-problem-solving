"""Compare actual Cloud LOD-sheet CSV exports to independent Hyper state oracle."""
from pathlib import Path
from hashlib import sha256
import csv,json,math
HERE=Path(__file__).resolve().parent
def verify():
    oracle=json.loads((HERE/'evidence/functional-verification.json').read_text())
    checks=[]
    for suffix,state in [('', 'all'),('-consumer','consumer'),('-consumer-east-no-furniture','consumer-hide-furniture-east'),('-consumer-east-tc-late-filter','consumer-hide-furniture-east')]:
        expected={(r['Region'],r['Category']):r for r in next(s['rows'] for s in oracle['states'] if s['state']==state)}
        exported={}
        for role in ['author','replica']:
            p=HERE/f'outputs/cloud-{role}-dashboard{suffix}.csv'
            with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            assert len(rows)==len(expected)
            actual={}
            for row in rows:
                key=row['Region'],row['Category'];assert key in expected and key not in actual
                actual[key]=row
                numeric=float(row['Sales'].replace(',',''));assert math.isclose(numeric,expected[key]['Sales'],abs_tol=1e-6)
                percent=float(row['LOD - % of Sales'].rstrip('%'))/100
                assert abs(percent-expected[key]['Percent'])<=0.00050001
            assert set(actual)==set(expected)
            exported[role]=actual
            checks.append({'role':role,'state':state,'file':p.relative_to(HERE).as_posix(),'sha256':sha256(p.read_bytes()).hexdigest(),'rows':len(rows),'Sales_tolerance':1e-6,'percent_tolerance':0.00050001,'source_scope':'LODs worksheet only, 1-decimal formatted percent'})
        for key in expected:
            assert exported['author'][key]['LOD - % of Sales']==exported['replica'][key]['LOD - % of Sales']
            assert math.isclose(float(exported['author'][key]['Sales'].replace(',','')),float(exported['replica'][key]['Sales'].replace(',','')),abs_tol=1e-6)
    report={'status':'pass','tc_late_filter_render':'Manual review of author/replica consumer-east-tc-late-filter PNGs observes Technology37.9%, OfficeSupplies29.5% with Furniture hidden, matching the independent Consumer/East baseline; CSV still covers LODs only.','scope':'Actual dashboard REST CSV exports select LODs only. Table Calcs is validated by native calculation/filter artifact contracts and independent Hyper oracle; these CSV exports do not prove Table Calcs rendered values.','checks':checks,'browser_interaction_executed':False}
    (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: WW07 eight actual Cloud LODs CSV exports match independent Hyper in four requests; Table Calcs CSV not covered')
    return report
if __name__=='__main__':verify()
