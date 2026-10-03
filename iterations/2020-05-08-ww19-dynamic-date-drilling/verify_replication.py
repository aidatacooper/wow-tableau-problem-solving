"""Independent Sunday-week interval and complete plotted-sales oracle."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
from datetime import date, datetime, timedelta
import ast
import csv
import json
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry
HERE = Path(__file__).resolve().parent
STATES = {'default': 0, 'daily': 1, 'reset': 0}
SELECTED = [date(2019,11,2), date(2019,11,3), date(2019,11,6)]


def sunday(day):
    return day - timedelta(days=(day.weekday()+1)%7)


def selection_interval(selected):
    return sunday(min(selected)), sunday(max(selected))+timedelta(days=6)


def parse_date(raw, day_first=False):
    raw=raw.strip().replace('Week of ', '')
    formats = (['%d/%m/%Y', '%m/%d/%Y'] if day_first else ['%m/%d/%Y', '%d/%m/%Y']) + ['%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %I:%M:%S %p', '%d/%m/%Y %H:%M:%S']
    for fmt in formats:
        try:
            return datetime.strptime(raw,fmt).date()
        except ValueError:
            pass
    raise ValueError(raw)


def numeric(raw):
    return float(raw.replace('$','').replace(',',''))


def verify():
    # blank-sdk-build; locked-source-data; native-calculations-actions;
    # independent-complete-data-oracle; cloud-rest-comparison; cloud-visual-review
    source=(HERE/'build_replication.py').read_text(encoding='utf-8-sig')
    assert 'TWBEditor("")' in source
    assert not any(isinstance(n,ast.Attribute) and n.attr.startswith('_') for n in ast.walk(ast.parse(source)))
    lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
    item=lock['extracted_data'][0];data=HERE/item['file']
    assert sha256(data.read_bytes()).hexdigest()==item['sha256']
    artifact=HERE/'outputs/replicated-workbook.twbx';digest=sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        assert sha256(z.read(next(n for n in z.namelist() if n.endswith('.hyper')))).hexdigest()==item['sha256']
    columns={c.get('caption'):c for c in root.xpath('/workbook/datasources/datasource/column[@caption]')}
    dates=columns['Date to Plot'];formula=dates.find('calculation').get('formula')
    assert 'DATETRUNC' in formula and "'day'" in formula and "'week'" in formula and "'sunday'" in formula
    assert dates.get('datatype')=='datetime'
    group=root.xpath('//datasource/group[@caption="Selected Dates"]')[0]
    assert {m.get('member') for m in group.xpath('.//groupfilter[@function="member"]')}=={'#'+d.isoformat()+' 00:00:00#' for d in SELECTED}
    assert '{FIXED:MIN(IF' in columns['Min Date'].find('calculation').get('formula')
    assert "DATEADD('week',1" in columns['Max Date'].find('calculation').get('formula')
    assert '>=' in columns['Dates To Include'].find('calculation').get('formula')
    setactions=root.xpath('/workbook/actions/edit-group-action')
    assert len(setactions)==1
    action=setactions[0]
    assert action.find('activation').get('type')=='on-select'
    assert action.find('source').get('worksheet')=='Chart'
    params={p.get('name'):p.get('value') for p in action.findall('params/param')}
    assert params['add-or-remove-marks']=='assign' and params['selection-clear-set-option']=='do-nothing'
    assert params['target-group'].endswith('.[Selected Dates]')
    actions=root.xpath('/workbook/actions/edit-parameter-action')
    assert len(actions)==2 and {a.find('source').get('worksheet') for a in actions}=={'Chart','Reset'}
    target='[Parameters].'+columns['Drill Down'].get('name')
    for action in actions:
        assert action.find('activation').get('type')=='on-select'
        assert action.xpath('./params/param[@name="target-parameter"]')[0].get('value')==target
    assert columns['Set Drill Down Level'].find('calculation').get('formula')=='1'
    assert columns['Reset'].find('calculation').get('formula')=='0'
    chart=root.xpath('//worksheet[@name="Chart"]')[0]
    assert chart.xpath('./table/panes/pane/mark[@class="Line"]')
    assert chart.xpath('./table/panes/pane/reference-line[@formula="average" and @scope="per-table"]')
    assert len(chart.xpath('./table/view/filter')) == 1
    assert columns['Dates To Include'].get('name')[1:-1] in chart.xpath('./table/view/filter')[0].get('column')
    assert root.xpath('//worksheet[@name="Reset"]/table/view/filter')
    title = root.xpath('//worksheet[@name="Title"]')[0]
    binding = title.xpath('./table/panes/pane/encodings/text')[0].get('column')
    runs = title.xpath('./table/panes/pane/customized-label/formatted-text/run')
    assert len(runs) == 1 and runs[0].text == '<' + binding + '>'
    assert 'COUNTD(' in columns['Complete Title'].find('calculation').get('formula')
    for name in ['Total Sales','Avg Sales']:
        assert columns[name].find('calculation/table-calc') is not None
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,Connection(hp.endpoint,str(data)) as connection:
        rows=connection.execute_list_query('SELECT "Order Date","Sales" FROM "Extract"."Extract"')
    raw=[(date(dt.year,dt.month,dt.day),sales) for dt,sales in rows]
    assert all(d.year==2019 for d,_ in raw)
    # Explicit independent simulated native selection cases: one week, disjoint
    # weeks, one day and multiple days all expand to inclusive Sunday/Saturday.
    scenarios={
        'single-week':([date(2019,11,3)],(date(2019,11,3),date(2019,11,9))),
        'disjoint-weeks':([date(2019,10,27),date(2019,11,10)],(date(2019,10,27),date(2019,11,16))),
        'single-day':([date(2019,11,5)],(date(2019,11,3),date(2019,11,9))),
        'multi-day':([date(2019,11,5),date(2019,11,15)],(date(2019,11,3),date(2019,11,16))),
    }
    for selected,wanted in scenarios.values():
        assert selection_interval(selected)==wanted
    oracle={}
    for state,level in STATES.items():
        lower,upper=selection_interval(SELECTED) if level else (min(sunday(d) for d,_ in raw),max(sunday(d) for d,_ in raw)-timedelta(days=1))
        grouped=defaultdict(float)
        for day,sales in raw:
            if lower<=day<=upper:
                grouped[day if level else sunday(day)]+=sales
        oracle[state]={'level':level,'lower':lower.isoformat(),'upper':upper.isoformat(),'values':{d.isoformat():v for d,v in sorted(grouped.items())},'total':sum(grouped.values()),'average':sum(grouped.values())/len(grouped)}
    report={'status':'pass','artifact_sha256':digest,'source_rows':len(rows),'states':oracle,'independent_selection_cases':{name:{'first':wanted[0].isoformat(),'last':wanted[1].isoformat()} for name,(_,wanted) in scenarios.items()},'browser_interaction_executed':False,'scope':'All plotted weekly/day sales marks. REST uses author stored date-set membership and Drill Down parameter states; disjoint and day selections are independently simulated plus action contracts, not browser executions.'}
    cloudpath=HERE/'evidence/cloud-verification.json'
    if cloudpath.exists():
        cloud=json.loads(cloudpath.read_text(encoding='utf-8'));provenance=json.loads((HERE/'evidence/export-provenance.json').read_text(encoding='utf-8'))
        assert cloud['source_hashes']['replica']==digest and cloud['source_hashes']['author']==provenance['comparison_sha256']
        assert provenance['original_sha256']==lock['locked_original_sha256']
        assert {s['name'] for s in cloud['states']}==set(STATES)
        checks=[]
        for state in cloud['states']:
            wanted=oracle[state['name']]
            for image in state['views'].values():
                assert sha256((HERE/image['path']).read_bytes()).hexdigest()==image['sha256']
            for capture in state['data']:
                path=HERE/capture['path'];assert sha256(path.read_bytes()).hexdigest()==capture['sha256']
                with path.open(encoding='utf-8-sig',newline='') as f:
                    exported=list(csv.DictReader(f))
                assert exported,(path,'Empty CSV');found={}
                for row in exported:
                    dt=parse_date(row['Date to Plot'], day_first=capture['role']=='author').isoformat()
                    assert dt in wanted['values'],(path,dt)
                    value=numeric(row['Sales']);assert abs(value-wanted['values'][dt])<=0.51,(path,dt,value,wanted['values'][dt])
                    found[dt]=value
                    for key,metric in [('Total Sales','total'),('Avg Sales','average')]:
                        if row.get(key) and row[key]!='Null':
                            assert abs(numeric(row[key])-wanted[metric])<=0.51,(path,key,row[key],wanted[metric])
                assert set(found)==set(wanted['values']),(path,len(found),len(wanted['values']))
                checks.append({'path':capture['path'],'status':'pass','marks':len(found)})
        assert len(checks)==6
        report['cloud_checks']=checks
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2),encoding='utf-8')
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',len(rows),'rows;', {k:len(v['values']) for k,v in oracle.items()},'marks')


if __name__=='__main__':
    verify()
