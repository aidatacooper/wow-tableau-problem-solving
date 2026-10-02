"""Compare actual dashboard KPI export scope to independent Hyper results."""
from pathlib import Path
from hashlib import sha256
import csv,json,re
HERE=Path(__file__).resolve().parent
def number(value):
    text=str(value).strip();negative='\u25bc' in text or '-' in text
    parsed=float(re.sub(r'[^0-9.]','',text))
    if '%' in text:parsed/=100
    if 'K' in text:parsed*=1000
    return -parsed if negative else parsed

def verify(strict_workbook=False):
    cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
    if strict_workbook:assert sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()==cloud['source_hashes']['replica']
    oracle=json.loads((HERE/'evidence/data-contract.json').read_text(encoding='utf-8'))['kpis']
    expected={'Profit % Increase':oracle['profit']['increase'],'PR % Increase':oracle['profit_ratio']['increase']}
    for metric,name in [('sales','Sales'),('profit','Profit'),('profit_ratio','Profit Ratio')]:
        for year,key in [('CY','current'),('PY','prior')]:expected['Total '+name+' '+year]=oracle[metric][key]
    report={'status':'passed','csv_scope':'Author dashboard exports Profit % Increase only (one row). Replica dashboard export includes eight dependent aggregate KPI columns. Only this actual scope is claimed; monthly trend and 17-point scatter numerical contracts use locked Hyper plus XML/PNG evidence.','browser_events_executed':False,'exports':{}}
    for role in ['author','replica']:
        path=HERE/('outputs/cloud-'+role+'-dashboard.csv');data=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
        assert len(data)==1
        values={k:number(v) for k,v in data[0].items() if k in expected}
        assert 'Profit % Increase' in values
        if role=='author':assert values.keys()=={'Profit % Increase'}
        else:assert values.keys()==expected.keys()
        differences={}
        for key,value in values.items():
            tolerance=.00051 if '%' in key or 'Ratio' in key else 50.001
            error=abs(value-expected[key]);assert error<=tolerance,(role,key,error)
            differences[key]={'displayed':value,'oracle':expected[key],'absolute_error':error,'format_tolerance':tolerance}
        report['exports'][role]={'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'columns':list(data[0]),'comparisons':differences}
    (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('WW11 actual author delta and eight replica KPI aggregates verified')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--strict-workbook',action='store_true');verify(p.parse_args().strict_workbook)
