"""Independent month pair aggregates, KPI health and serialized tooltips."""
from collections import defaultdict
from datetime import date
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import math
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE=Path(__file__).resolve().parent
# Acceptance: blank-sdk-build, locked-extract, independent-metric-oracle,
# artifact-contract, cloud-rest-states.
STATES=[('default',date(2019,11,1)),('december',date(2019,12,1)),('january',date(2019,1,1))]


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))) as c:
        table=next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        facts=c.execute_list_query('SELECT "Order Date", "Sub-Category", "Order ID", "Sales", "Quantity" FROM '+str(table))
    grouped=defaultdict(list)
    for d,sub,order,sales,qty in facts:
        grouped[d.year,d.month,sub.upper()].append((order,float(sales),int(qty)))
    categories=sorted({r[1].upper() for r in facts}); states=[]
    for state, current in STATES:
        previous=date(current.year if current.month>1 else current.year-1,current.month-1 if current.month>1 else 12,1); values=[]
        for sub in categories:
            record={'subcategory':sub};score=0
            for prefix,index in [('Sales',1),('Orders',0),('Qty',2)]:
                totals=[]
                for when,d in [('Current',current),('Previous',previous)]:
                    rows=grouped[d.year,d.month,sub]
                    value=len({r[0] for r in rows}) if prefix=='Orders' else math.fsum(r[index] for r in rows) if prefix=='Sales' else sum(r[index] for r in rows)
                    record[f'{prefix} {when} Month']=value;totals.append(value)
                assert totals[1]>0
                ratio=totals[0]/totals[1];healthy=int(ratio>=1);record[f'% {prefix}']=ratio;record[f'{prefix} Indicator']=healthy;score+=healthy
            record['% Overall Score']=score/3;record['Overall Score']=score;record['Overall Indicator']='●' if score<3 else '';values.append(record)
        states.append({'name':state,'current':current.isoformat(),'previous':previous.isoformat(),'values':values})
    assert len(facts)==9994 and len(categories)==17
    return {'row_count':len(facts),'states':states}


def number(text):
    raw=text.strip().replace('$','').replace(',','')
    return float(raw.rstrip('%'))/(100 if raw.endswith('%') else 1)


def verify_cloud(data):
    checks=[]
    required={f'{prefix} {when} Month' for prefix in ['Sales','Orders','Qty'] for when in ['Current','Previous']}|{'% Sales','% Orders','% Qty','Sales Indicator','Orders Indicator','Qty Indicator','% Overall Score'}
    for state in data['states']:
        suffix='' if state['name']=='default' else '-'+state['name'];expected={v['subcategory']:v for v in state['values']}
        for role in ['author','replica']:
            path=HERE/f'outputs/cloud-{role}-chart{suffix}.csv'
            if not path.exists():continue
            rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')));coverage=set();subseen=set()
            for row in rows:
                sub=next((v.strip().upper() for k,v in row.items() if ('Sub-Cat' in k or 'Sub-Category' in k) and v.strip().upper() in expected),None)
                assert sub,(path,row);subseen.add(sub)
                for field in required:
                    raw=row.get(field,'').strip()
                    if not raw:continue
                    actual=number(raw)
                    if field.startswith('%') and raw.endswith('%'):
                        numeric=raw[:-1];precision=len(numeric.split('.')[-1]) if '.' in numeric else 0
                        tolerance=0.5*10**(-precision)/100+1e-8
                    else:
                        tolerance=0.5000001 if field.startswith('Sales ') else 1e-8
                    assert abs(actual-expected[sub][field])<=tolerance,(path,sub,field,actual,expected[sub][field]);coverage.add((sub,field))
                if row.get('Overall Indicator','').strip():assert expected[sub]['Overall Indicator']=='●'
            assert subseen==set(expected) and coverage=={(s,f) for s in expected for f in required},(path,len(coverage),len(required)*17,set(required)-{f for s,f in coverage})
            checks.append({'role':role,'state':state['name'],'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'subcategories':17,'metric_cells_verified':len(coverage)})
    if (HERE/'evidence/cloud-verification.json').exists():
        assert len(checks)==6
        assert json.loads((HERE/'evidence/cloud-verification.json').read_text())['source_hashes']['replica']==sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    if checks:(HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','scope':'All 17 subcategories, six month-specific totals, three ratios, three indicators and overall score for all three month pairs; no button CSV.','checks':checks},indent=2)+'\n')


def verify():
    output=HERE/'outputs/replicated-workbook.twbx';lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for filename,digest in lock['data_files'].items():
            assert sha256((HERE/filename).read_bytes()).hexdigest()==digest
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==Path(filename).name))).hexdigest()==digest
    assert root.xpath('worksheets/worksheet/@name')==['Viz'];size=root.find('dashboards/dashboard/size');assert size.get('maxwidth')=='600' and size.get('maxheight')=='800'
    table=root.find('worksheets/worksheet/table');assert table.xpath('panes/pane/mark/@class')==['Bar','Bar','Bar','Text']
    assert not table.xpath('.//encodings/*[contains(@column,":Measure Names") or contains(@column,"Multiple Values")]')
    assert len(table.xpath('panes/pane/customized-tooltip/formatted-text'))==4
    assert table.xpath('panes/pane/customized-label/formatted-text/run[@fontcolor="#ff003b"]')
    assert table.find('cols').text.count(' + ')==3 and ' * ' not in table.find('cols').text
    ds=next(d for d in root.findall('datasources/datasource') if d.get('name')!='Parameters');cols={c.get('caption',c.get('name').strip('[]')):c for c in ds.findall('column')}
    formulas={k:c.find('calculation').get('formula') for k,c in cols.items() if c.find('calculation') is not None}
    for field,local in [(k,c.get('name')) for k,c in cols.items()]:
        formulas={k:v.replace(local,'['+field+']') for k,v in formulas.items()}
    assert formulas['Orders Current Month']=='COUNTD(IF [Order Date MY]=[Current Month] THEN [Order ID] END)'
    assert formulas['Previous Month']=="DATE(DATEADD('month',-1,[Current Month]))"
    assert formulas['Overall Score']=='[Sales Indicator]+[Orders Indicator]+[Qty Indicator]'
    param=root.find('datasources/datasource[@name="Parameters"]/column');assert param.get('value')=='#2019-11-01#' and param.get('param-domain-type')=='list' and len(param.findall('members/member'))==48
    data=oracle();data.update({'status':'pass','artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False,'tooltip_scope':'Serialized text/field runs only; browser hover not executed.'})
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(data,indent=2)+'\n');verify_cloud(data)
    print('PASS: WW06 17 subcategories, three independent month pairs and one-sheet KPI/tooltip contracts')
    return data


if __name__=='__main__':verify()
