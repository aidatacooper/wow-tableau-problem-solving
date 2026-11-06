"""Compare Cloud exports with one another and the independent locked-data oracle."""
import csv, hashlib, json
from pathlib import Path
from verify_replication import oracle

HERE=Path(__file__).resolve().parent
def main():
    facts=oracle()
    rows=lambda name:list(csv.DictReader((HERE/'outputs'/name).open(encoding='utf-8-sig',newline='')))
    author=rows('cloud-author-chart.csv')
    replica=rows('cloud-replica-chart.csv')
    a={}
    for row in author:
        name=row['Product Name']
        a.setdefault(name,{})[row['Measure Names']]=row['Measure Values']
        assert row['In / Out of Top 50 Sales by Product']=='In'
        assert row['In / Out of Unprofitable Products']=='In'
        assert (row['Higher than Avg Customer Count']=='True')==(name not in facts['below_average'])
    b={}
    for row in replica:
        b.setdefault(row['Product Name'],{}).update({k:v for k,v in row.items() if v})
    assert set(a)==set(b)==facts['answer']
    for name, row in b.items():
        assert int(row['Customer Count Per Product'])==int(a[name]['Customer Count Per Product'].replace(',',''))==facts['customer_counts'][name]
        assert (row['Higher than Avg Customer Count']=='True')==(name not in facts['below_average'])
        for measure in ('Sales','Profit'):
            expected=facts[measure.lower()][name]
            assert abs(float(a[name][measure].replace(',',''))-expected)<.011
            displayed=float(row[measure].replace('$','').replace(',','').replace('K','').replace('(','-').replace(')',''))*1000
            assert abs(displayed-expected)<=500.01,(name,measure,displayed,expected)
    sha=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text())
    assert sha==cloud['source_hashes']['replica']
    result={'result':'PASS','products':len(b),'artifact_sha256':sha,'scope':'Original author and replica product domains, sets, customer counts, above-average flag, sales/profit; replica currency uses nearest $K display precision.'}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS Cloud: 13 products, memberships, customer counts, sales/profit')
if __name__=='__main__': main()
