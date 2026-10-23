import csv,datetime as dt,hashlib,json
from collections import defaultdict
from pathlib import Path
from tableauhyperapi import Connection,HyperProcess,Telemetry
from verify_replication import MISC_MEMBERS
HERE=Path(__file__).resolve().parent
def exported(role,state):
    result={}
    for r in csv.DictReader((HERE/'outputs'/f'cloud-{role}-data-{state}.csv').open(encoding='utf-8-sig')):
        m=dt.datetime.strptime(r['Month of Order Date'],'%B %Y').strftime('%Y-%m')
        v=r['Measure Values'].replace(',','')
        result[(m,r['Sub-Category (group)'],r['Measure Names'].split(' along ')[0])]=float(v) if v else None
    return result
def main():
    item=json.loads((HERE/'inputs/source-lock.json').read_text())['extracted_data'][0]
    source=HERE/item['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,Connection(hp.endpoint,str(source)) as c:
        rows=c.execute_list_query('SELECT "Order Date","Sub-Category","Sales" FROM "Extract"."Extract"')
    sales=defaultdict(float)
    for d,g,s in rows:sales[(f'{d.year:04d}-{d.month:02d}','Misc' if g in MISC_MEMBERS else g)]+=s
    months=sorted({m for m,g in sales});groups=sorted({g for m,g in sales})
    checks=0
    for state,prior,post in [('default',3,3),('one-one',1,1),('six-six',6,6)]:
        expected={}
        for g in groups:
            for i,m in enumerate(months):
                values=[sales[(t,g)] for t in months[max(0,i-prior+1):i+post+1] if (t,g) in sales]
                expected[(m,g,'Sales')]=sales.get((m,g))
                expected[(m,g,'Moving Avg')]=sum(values)/len(values) if values else None
        for m in months:
            domain=[expected[(m,g,'Moving Avg')] for g in groups if expected[(m,g,'Moving Avg')] is not None]
            for g in groups:
                expected[(m,g,'Window Max Avg')]=max(domain)
                expected[(m,g,'Window Min Avg')]=min(domain)
        a=exported('author',state);b=exported('replica',state)
        assert set(a)==set(b)==set(expected),(state,len(a),len(b),len(expected))
        for k,v in expected.items():
            assert (a[k] is None)==(b[k] is None)==(v is None),(state,k,a[k],b[k],v)
            if v is not None:
                assert abs(a[k]-b[k])<.011,(state,k,a[k],b[k])
                assert abs(b[k]-v)<.011,(state,k,b[k],v)
            checks+=1
    h=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    assert h==json.loads((HERE/'evidence/cloud-verification.json').read_text())['source_hashes']['replica']
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps({'result':'PASS','artifact_sha256':h,'measure_checks':checks,'states':3,'scope':'Original author and replica Data CSV versus independent monthly source oracle; Tableau densifies 48 months x 13 groups with null sales, WINDOW_AVG ignores nulls in the calendar window.'},indent=2)+'\n')
    print('PASS Moving Cloud',checks,'measure cells')
if __name__=='__main__':main()
