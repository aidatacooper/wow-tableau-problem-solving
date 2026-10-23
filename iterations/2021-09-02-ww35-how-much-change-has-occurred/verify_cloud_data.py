import csv,hashlib,json
from pathlib import Path
from verify_replication import oracle,label_percent
HERE=Path(__file__).resolve().parent
def main():
    facts=oracle();expected={r['sub_category']:r for r in facts['chart']}
    data=list(csv.DictReader((HERE/'outputs/cloud-replica-viz-default.csv').open(encoding='utf-8-sig')))
    domain=set();ordered=[];checks=0
    for r in data:
        cat=r['Sub-Category'];period=r.get('Dot Period') or r.get('Bar Period');year='2021' if period=='Current (2021)' else '2020'
        if cat not in ordered:ordered.append(cat)
        assert year in ('2020','2021');domain.add((cat,year));e=expected[cat]
        assert abs(float(r['Sales'].replace(',',''))-e['sales_'+year])<.011
        if r['% Difference']:assert int(r['% Difference'].replace('%',''))==label_percent(e['pct_difference'])
        for field in ['2021 Sales (discrete)','2021 Sales']:
            if r[field]:assert abs(float(r[field].replace('$','').replace(',',''))-e['sales_2021'])<=.501
        checks+=1
    assert domain=={(c,y) for c in expected for y in ('2020','2021')}
    assert ordered==[r['sub_category'] for r in facts['chart']]
    h=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    assert h==json.loads((HERE/'evidence/cloud-verification.json').read_text())['source_hashes']['replica']
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps({'result':'PASS','artifact_sha256':h,'export_rows':checks,'category_years':len(domain),'scope':'17 categories x 2 years, exact sales to cents, rounded current-year headers, signed percent change and descending order versus locked-data oracle. Original author dashboard rendered unchanged; hidden Viz not exported.'},indent=2)+'\n')
    print('PASS Sales Cloud',len(domain),'category-years')
if __name__=='__main__':main()
