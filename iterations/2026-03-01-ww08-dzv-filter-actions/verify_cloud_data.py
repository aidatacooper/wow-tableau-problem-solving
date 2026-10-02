"""Compare every exported product pair to independently aggregated Hyper."""
from pathlib import Path
from hashlib import sha256
from collections import defaultdict
import csv,json,math
from tableauhyperapi import Connection,HyperProcess,Telemetry
HERE=Path(__file__).resolve().parent
def verify(strict_workbook=False):
    cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
    if strict_workbook:assert sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()==cloud['source_hashes']['replica']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))) as c:rows=c.execute_list_query('SELECT "State/Province","Product Name","Sales","Quantity","Customer Name" FROM "Extract"."Extract"')
    report={'status':'passed','csv_scope':'Customer Orders product Sales and Quantity; includes hidden default sheet CSV. Does not export KPI Profit/Ratio or map geometry/customer domain. Those use independent Hyper + XML/image evidence.','browser_events_executed':False,'states':[]}
    for suffix,state,customer in [('',None,None),('-california','California',None),('-texas','Texas',None),('-california-aaron','California','Aaron Hawkins')]:
        values=defaultdict(lambda:[0.,0])
        for st,p,s,q,name in rows:
            if (state is None or st==state) and (customer is None or name==customer):values[p][0]+=float(s);values[p][1]+=q
        expected={(p,'Sales'):v[0] for p,v in values.items()};expected.update({(p,'Quantity'):v[1] for p,v in values.items()})
        entry={'name':(state or 'default') + (':'+customer if customer else ''),'products':len(values),'measure_rows':len(expected),'exports':{}}
        for role in ['author','replica']:
            path=HERE/('outputs/cloud-'+role+'-dashboard'+suffix+'.csv')
            data=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
            actual={(r['Product Name'],r['Measure Names']):float(r['Measure Values'].replace(',','').replace('$','')) for r in data}
            assert actual.keys()==expected.keys()
            errors=[abs(v-actual[k]) for k,v in expected.items()]
            assert max(errors,default=0)<=0.00051
            entry['exports'][role]={'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'max_absolute_error':max(errors,default=0)}
        report['states'].append(entry)
    (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('WW08 all author/replica product pairs verified for four states')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--strict-workbook',action='store_true');verify(p.parse_args().strict_workbook)
