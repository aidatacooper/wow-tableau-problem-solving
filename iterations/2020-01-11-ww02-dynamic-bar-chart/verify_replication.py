"""Independent nine-state Hyper oracle and serialized dashboard contracts."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import math
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance trace: blank-sdk-build, locked-superstore-source,
# nine-metric-date-states, selected-metric-labels, selector-action-contract,
# cloud-rest-states.
PERIODS = ['Last 12 Months', 'Last 13 Weeks', 'Last 14 Days']
MEASURES = [' Sales ', ' Profit Ratio ', ' Items Per Order ']


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(next((HERE/'inputs').glob('*.hyper')))) as c:
        table = next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        rows = c.execute_list_query('SELECT "Order Date", "Order ID", "Sales", "Profit", "Quantity" FROM '+str(table))
    states = []
    starts = [date(2019,1,1), date(2019,10,2), date(2019,12,18)]
    for period, start in zip(PERIODS, starts):
        groups = defaultdict(list)
        for order_date, order_id, sales, profit, quantity in rows:
            d = date(order_date.year, order_date.month, order_date.day)
            if d < start:
                continue
            bucket = d.replace(day=1) if period == PERIODS[0] else d-timedelta(days=(d.weekday()+1)%7) if period == PERIODS[1] else d
            groups[bucket].append((order_id,float(sales),float(profit),int(quantity)))
        values = []
        for bucket, facts in sorted(groups.items()):
            sales = math.fsum(r[1] for r in facts)
            profit = math.fsum(r[2] for r in facts)
            quantity = sum(r[3] for r in facts)
            orders = len({r[0] for r in facts})
            values.append({'date':bucket.isoformat(),'sales':sales,'profit_ratio':profit/sales,'items_per_order':quantity/orders,'orders':orders,'quantity':quantity})
        for measure, key in zip(MEASURES,['sales','profit_ratio','items_per_order']):
            states.append({'period':period,'measure':measure,'metric':key,'start':start.isoformat(),'bars':len(values),'values':values})
    assert len(rows) == 9994
    assert [states[i]['bars'] for i in [0,3,6]] == [12,14,13]
    return {'row_count':len(rows),'states':states,'week_start':'sunday','reference_today':'2020-01-01'}


def verify_cloud(data):
    """Chart CSVs cover every dated bar; Selector CSVs are not data proof."""
    checks=[]
    for state in data['states']:
        period=['months','weeks','days'][PERIODS.index(state['period'])]
        metric=['sales','profit-ratio','items-per-order'][MEASURES.index(state['measure'])]
        suffix='' if (period,metric)==('months','sales') else '-'+period+'-'+metric
        for role in ['author','replica']:
            path=HERE/f'outputs/cloud-{role}-chart{suffix}.csv'
            if not path.exists():continue
            with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            assert len(rows)==state['bars'],(path,len(rows),state['bars'])
            metric_column=next((k for k in rows[0] if k.strip()=='Measure to Show'),None)
            assert metric_column,(path,list(rows[0]))
            date_column=next((k for k in rows[0] if k.strip()=='Order Date Truncate'),None)
            assert date_column,(path,list(rows[0]))
            actual=[]
            expected_by_date={v['date']:v[state['metric']] for v in state['values']}
            for row in rows:
                raw=row[metric_column].replace(',','').replace('$','').strip()
                value=float(raw.rstrip('%'))/(100 if raw.endswith('%') else 1)
                raw_date=row[date_column].strip()
                bucket=None
                for fmt in ['%m/%d/%Y','%Y-%m-%d','%B %d, %Y','%b %d, %Y','%d/%m/%Y','%Y-%m-%d %H:%M:%S']:
                    try:bucket=datetime.strptime(raw_date,fmt).date().isoformat();break
                    except ValueError:pass
                assert bucket in expected_by_date,(path,'unknown date bucket',raw_date)
                assert math.isclose(value,expected_by_date[bucket],rel_tol=1e-8,abs_tol=0.005),(path,bucket,value,expected_by_date[bucket])
                active=['Label:Sales','Label:Profit Ratio','Label:Items Per Order'][MEASURES.index(state['measure'])]
                active_text=row[active].strip()
                assert active_text,(path,'missing selected metric label',bucket)
                for inactive in set(['Label:Sales','Label:Profit Ratio','Label:Items Per Order'])-{active}:
                    assert not row[inactive].strip(),(path,'inactive metric label unexpectedly populated',inactive)
                display=float(active_text.replace(',','').replace('$','').rstrip('%'))/(100 if active_text.endswith('%') else 1)
                tolerance=0.500001 if active=='Label:Sales' else 0.000500001 if active=='Label:Profit Ratio' else 0.0500001
                assert abs(display-expected_by_date[bucket])<=tolerance,(path,bucket,'formatted label',active_text)
                actual.append((bucket,value))
            assert {d for d,_ in actual}==set(expected_by_date),(path,'missing or duplicated date bucket')
            checks.append({'role':role,'period':state['period'],'measure':state['measure'],'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'bars_verified':state['bars']})
    if checks:
        if (HERE/'evidence/cloud-verification.json').exists():
            assert len(checks)==18,('Cloud acceptance requires author and replica for all nine states',len(checks))
            cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text())
            assert cloud['source_hashes']['replica']==sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','scope':'Every dated Chart bar in all captured states, independently matched to fact-level metric aggregates; Selector CSV is excluded. CSV ordering does not prove visible sort.','checks':checks,'browser_interaction_executed':False},indent=2)+'\n')
    return checks


def verify():
    output = HERE/'outputs/replicated-workbook.twbx'
    lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for item in lock['extracted_data']:
            p=HERE/item['file'];assert sha256(p.read_bytes()).hexdigest()==item['sha256']
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==p.name))).hexdigest()==item['sha256']
    assert root.xpath('worksheets/worksheet/@name')==['Chart','Selector']
    size=root.find('dashboards/dashboard/size');assert size.get('maxwidth')=='1100' and size.get('maxheight')=='800'
    ds=next(d for d in root.findall('datasources/datasource') if d.get('name')!='Parameters')
    fields={c.get('caption',c.get('name')):c for c in ds.findall('column')}
    formulas={k:c.find('calculation').get('formula') for k,c in fields.items() if c.find('calculation') is not None}
    for key,value in list(formulas.items()):
        for caption,col in fields.items():
            if col.get('caption'):value=value.replace(col.get('name'),'['+caption+']')
        formulas[key]=value
    compact=lambda s:''.join(s.split()).upper()
    assert compact(formulas['Profit Ratio'])=='SUM([PROFIT])/SUM([SALES])'
    assert compact(formulas['Items Per Order'])=='SUM([QUANTITY])/COUNTD([ORDERID])'
    assert 'REGEXP_REPLACE' in formulas['Label:Sales']
    assert fields['Label:Profit Ratio'].get('default-format')=='p0.0%'
    assert fields['Label:Items Per Order'].get('default-format')=='n#,##0.0;-#,##0.0'
    for p in PERIODS[:2]:assert p in formulas['Dates to Include'] and p in formulas['Order Date Truncate']
    chart=root.find('worksheets/worksheet[@name="Chart"]');assert chart.find('table/view/filter') is not None
    assert chart.find('table/panes/pane/mark').get('class')=='Bar'
    params={c.get('caption'):c for c in root.findall('datasources/datasource[@name="Parameters"]/column')}
    assert params['Today'].get('value')=='#2020-01-01#'
    assert params['Selected Measure'].get('value')=='" Sales "'
    assert params['Selected Measure'].get('param-domain-type')=='any'
    assert params['Date Period'].get('param-domain-type')=='list'
    assert [m.get('value').strip('"') for m in params['Date Period'].findall('members/member')]==PERIODS
    action=root.find('actions/edit-parameter-action');assert action.find('activation').get('type')=='on-select'
    assert action.find('source').get('worksheet')=='Selector'
    values={p.get('name'):p.get('value') for p in action.findall('params/param')}
    assert values['source-field']=='['+ds.get('name')+'].[:Measure Names]'
    assert values['target-parameter']=='[Parameters].'+params['Selected Measure'].get('name')
    reset=root.find('actions/action');assert reset.find('activation').get('auto-clear')=='true'
    assert reset.find('command/param[@name="target"]').get('value')=='Selector'
    selector=root.find('worksheets/worksheet[@name="Selector"]');assert len(selector.findall('table/panes/pane'))==3
    assert not selector.xpath('.//encoding[@fold="true"]')
    for pane,caption in zip(selector.findall('table/panes/pane'),MEASURES):
        assert fields[caption].get('name').strip('[]') in pane.get('x-axis-name')
    date_binding=chart.findtext('table/cols')
    assert 'mn:' not in date_binding and fields['Order Date Truncate'].get('name').strip('[]') in date_binding
    data=oracle();data.update({'status':'pass','artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False,'interaction_scope':'Artifact select/source/parameter target/keep-current and self-filter show-all contracts. REST exports do not execute browser clicks.'})
    (HERE/'evidence').mkdir(exist_ok=True)
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(data,indent=2)+'\n')
    verify_cloud(data)
    print('PASS: WW02 locked input, nine metric/time-window states and parameter/filter contracts')
    return data


if __name__=='__main__':verify()
