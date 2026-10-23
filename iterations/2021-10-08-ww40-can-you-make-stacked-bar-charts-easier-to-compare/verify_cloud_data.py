"""Check WW40 Cloud state exports against independent locked-extract arithmetic."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,hashlib
from verify_replication import oracle
HERE=Path(__file__).resolve().parent
SELECTIONS={'default':'Office Supplies','furniture':'Furniture','technology':'Technology'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(text):
    t=text.strip().replace('$','').replace(',','')
    return float(t[:-1])*1000 if t.endswith('K') else float(t)
def verify():
    lock=json.loads((HERE/"inputs/source-lock.json").read_text(encoding="utf8"))
    for record in lock["extracted_data"]:
        assert digest(HERE/record["file"])==record["sha256"],"locked extract changed"
    rows,sums,counts,_=oracle()
    cell_counts=Counter(('A-M' if state[0].upper() in 'ABCDEFGHIJKLM' else 'N-Z',cat) for state,cat,sale in rows)
    totals={g:sum(v for (group,cat),v in sums.items() if group==g) for g in ['A-M','N-Z']}
    current=digest(HERE/'outputs/replicated-workbook.twbx')
    cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf8'))
    manifest=json.loads((HERE/'evidence/replica-data-exports.json').read_text(encoding='utf8'))
    assert current==cloud['source_hashes']['replica']==manifest['artifact_sha256'],'stale artifact binding'
    assert {s['name'] for s in cloud['states']}==set(SELECTIONS),'incomplete image state capture'
    images=[]
    for state in cloud['states']:
        for role in ['author','replica']:
            image=state['views'][role];assert digest(HERE/image['path'])==image['sha256']
            images.append({'state':state['name'],'role':role,**image})
    records=[r for r in manifest['exports'] if r['view']=='Chart']
    assert {r['state'] for r in records}==set(SELECTIONS) and len(records)==3,'incomplete CSV states'
    checks=0;result=[]
    for record in records:
        state=record['state'];selected=SELECTIONS[state]
        assert record['parameters'].get('pSelectedCategpry','Office Supplies')==selected
        path=HERE/record['path'];assert digest(path)==record['sha256']
        exported=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        keys=[(r['State Group'],r['Category']) for r in exported]
        assert len(keys)==6 and set(keys)==set(sums),f'{state}: wrong group/category domain'
        group_order=defaultdict(list)
        for row in exported:
            key=(row['State Group'],row['Category']);group_order[key[0]].append(key[1])
            assert abs(number(row['Sales'])-sums[key])<=500,f'{state} {key}: wrong sales'
            assert abs(number(row['Total Sales per State Group'])-totals[key[0]])<=500,f'{state} {key}: wrong total'
            assert number(row['Sort'])==(0 if key[1]==selected else cell_counts[key]),f'{state} {key}: wrong dynamic sort'
            assert row['True']=='True' and row['False']=='False'
            checks+=5
        expected=sorted(counts,key=lambda cat:0 if cat==selected else -counts[cat])
        assert all(order==expected and order[-1]==selected for order in group_order.values()),f'{state}: wrong stack order'
        result.append({'state':state,'selected_category':selected,'order_top_to_bottom':expected,'cells':6})
    report={'result':'PASS','status':'PASS','artifact_sha256':current,'source_hashes':cloud['source_hashes'],'checks':checks,'states':result,'tolerance':{'currency':500,'explanation':'Cloud CSV displays rounded whole $K; Sort and booleans compare exactly.'},'scope':'Replica six group/category cells and total/Sort/boolean values in all three states against independent raw Hyper oracle. Original author exposes dashboard only; six images reviewed separately. No browser click claim.','csv_sources':records,'images':images}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(f'PASS: {checks} checks across 3 states, 18 category cells, selected category at bottom in both groups')
    return report
if __name__=='__main__':verify()
