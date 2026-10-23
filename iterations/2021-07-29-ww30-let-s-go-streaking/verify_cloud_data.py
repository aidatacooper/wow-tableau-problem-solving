import csv,datetime as dt,hashlib,json
from pathlib import Path
from verify_replication import oracle
HERE=Path(__file__).resolve().parent
def read(name,author=False):
    result={}
    for r in csv.DictReader((HERE/'outputs'/name).open(encoding='utf-8-sig')):
        month=dt.datetime.strptime(r['Order Date Month' if author else 'Month of Order Date'],'%m/%d/%Y' if author else '%B %Y').strftime('%Y-%m')
        measure=r['Measure Names'].split(' along ')[0]
        value=r['Measure Values'].replace(',','')
        result[(r['Sub-Category'],month,measure)]=None if not value else float(value)
    return result
def main():
    a=read('cloud-author-chart.csv',True);b=read('cloud-replica-chart.csv')
    assert set(b)<=set(a),(len(a),len(b))
    for c,m,n in set(a)-set(b):assert a[(c,m,'Sales')] is None,(c,m)
    for k in b:
        assert (a[k] is None)==(b[k] is None),(k,a[k],b[k])
        if a[k] is not None:assert abs(a[k]-b[k])<.011,(k,a[k],b[k])
    facts=oracle()
    for category,f in facts['sub_categories'].items():
        assert {v for (c,m,n),v in b.items() if c==category and n=='Longest Streak'}=={f['longest_streak']}
        peaks={m:v for (c,m,n),v in b.items() if c==category and n=='Sales of Month with Longest Streak' and v is not None}
        assert set(peaks)=={p['month'] for p in f['peaks']}
        for p in f['peaks']:assert abs(peaks[p['month']]-p['sales'])<.011
    h=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    assert h==json.loads((HERE/'evidence/cloud-verification.json').read_text())['source_hashes']['replica']
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps({'result':'PASS','artifact_sha256':h,'measure_checks':len(b),'categories':17,'scope':'All author and replica month/category/measure values, nulls, streaks and peaks; independent locked-data longest/peak oracle.'},indent=2)+'\n')
    print('PASS Streak Cloud',len(b),'measure cells')
if __name__=='__main__':main()
