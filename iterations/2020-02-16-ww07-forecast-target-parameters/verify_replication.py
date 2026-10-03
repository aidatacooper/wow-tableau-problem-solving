"""Independent category forecast/target states and parameter action contracts."""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import math
import re
from urllib.parse import unquote
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE=Path(__file__).resolve().parent
# Acceptance: blank-sdk-build, locked-extract, independent-metric-oracle,
# artifact-contract, cloud-rest-states.
STATES=[
    ('default','',''),
    ('technology-forecast','Technology_70000:',''),
    ('negative-forecast','Furniture_-25000:',''),
    ('custom-target','','Office Supplies_310000:Technology_280000:'),
    ('combined','Technology_70000:Furniture_-25000:','Office Supplies_310000:Technology_280000:'),
    ('reset','',''),
]
DEFAULT_TARGETS={'Furniture':270000,'Office Supplies':260000,'Technology':250000}


def parse_list(text):
    values={}
    for token in text.split(':'):
        if not token:continue
        category,number=token.rsplit('_',1)
        if category not in values:values[category]=int(number)
    return values


def set_category(text, category, value, forecast=True):
    if value==0 or (not forecast and value<0):return ''
    tokens=[t for t in text.split(':') if t and not t.startswith(category+'_')]
    return ':'.join(tokens+[f'{category}_{value}'])+':'


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))) as c:
        table=next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        facts=c.execute_list_query('SELECT "Order Date", "Category", "Sales" FROM '+str(table))
    grouped=defaultdict(list)
    for d,category,sales in facts:
        if d.year==2019:grouped[category].append(float(sales))
    sales={k:math.fsum(v) for k,v in grouped.items()};assert set(sales)==set(DEFAULT_TARGETS)
    states=[]
    for name,forecast_list,target_list in STATES:
        fc=parse_list(forecast_list);targets=parse_list(target_list);values=[]
        for category in sorted(sales,key=lambda k:-sales[k]):
            actual=sales[category];target=targets.get(category) or DEFAULT_TARGETS[category];forecast=actual+fc[category] if category in fc else None
            values.append({'category':category,'Sales':actual,'Target':target,'Forecast':forecast,'Sales v Target Diff':(actual-target)/target,'Forecast v Target Diff':(forecast-target)/target if forecast is not None else None})
        states.append({'name':name,'forecast_list':forecast_list,'target_list':target_list,'values':values})
    first=set_category('','Technology',70000);second=set_category(first,'Furniture',-25000);third=set_category(second,'Technology',10000)
    assert parse_list(third)=={'Furniture':-25000,'Technology':10000}
    assert set_category(third,'Technology',0)=='' and set_category('', 'Furniture',-1,forecast=False)==''
    assert len(facts)==3312
    return {'row_count':len(facts),'sales_year':2019,'states':states,'replacement_sequence':{'first':first,'second':second,'third':third,'reset':''}}


def number(raw):
    text=raw.strip().replace(',','').replace('$','').replace('▲','').replace('▼','-').strip('() ')
    return float(text.rstrip('%'))/(100 if text.endswith('%') else 1)


def verify_cloud(data):
    checks=[]
    for state in data['states']:
        suffix='' if state['name']=='default' else '-'+state['name'];expected={v['category']:v for v in state['values']}
        for role,kind in [('author','chart'),('replica','chart'),('author','labels')]:
            path=HERE/f'outputs/cloud-{role}-{kind}{suffix}.csv'
            if not path.exists():continue
            rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')));seen=set();coverage=set()
            for row in rows:
                category=row['Category'].strip();assert category in expected;seen.add(category)
                for field in ['Sales','Target','Forecast','Sales v Target Diff','Forecast v Target Diff']:
                    raw=row.get(field,'').strip();value=expected[category][field]
                    if value is None:
                        assert not raw,(path,category,field,raw)
                        coverage.add((category,field));continue
                    if not raw:continue
                    tolerance=0.0050001 if 'Diff' in field else 0.500001
                    assert abs(number(raw)-value)<=tolerance,(path,category,field,raw,value);coverage.add((category,field))
            assert seen==set(expected) and coverage=={(c,f) for c in expected for f in ['Sales','Target','Forecast','Sales v Target Diff','Forecast v Target Diff']},(path,coverage)
            checks.append({'role':role,'view_kind':kind,'state':state['name'],'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'categories_verified':3,'metric_cells_verified':15})
        label_path=HERE/f'outputs/cloud-replica-labels{suffix}.csv'
        if label_path.exists():
            rows=list(csv.DictReader(label_path.open(encoding='utf-8-sig',newline='')));assert len(rows)==3
            assert {row['Category'] for row in rows}==set(expected)
            for row in rows:
                value=expected[row['Category']]
                for field in ['Sales','Target','Forecast']:
                    raw=row[field].strip()
                    if value[field] is None:assert not raw
                    else:assert abs(number(raw)-value[field])<=0.500001,(label_path,row['Category'],field,raw,value[field])
                for prefix in ['Sales','Forecast']:
                    ratio=value[prefix+' v Target Diff'];raw=row[prefix+' Diff Text'].strip()
                    expected_text='' if ratio is None else (chr(0x25b2) if ratio>=0 else chr(0x25bc))+str(math.floor(abs(ratio)*100+0.5))+'%'
                    assert raw==expected_text,(label_path,row['Category'],prefix,raw,expected_text)
            checks.append({'role':'replica','view_kind':'labels','state':state['name'],'file':label_path.relative_to(HERE).as_posix(),'sha256':sha256(label_path.read_bytes()).hexdigest(),'rows':3,'categories_verified':3,'metric_cells_verified':15,'formatted_percent_labels_verified':6})
    if (HERE/'evidence/cloud-verification.json').exists():
        assert len(checks)==24
        assert json.loads((HERE/'evidence/cloud-verification.json').read_text())['source_hashes']['replica']==sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    if checks:(HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','scope':'Every category actual, forecast, target and both target differences and replica signedformattedpercentlabels in six parameter-list states; all24chart/labelCSVexports checked; selector/reset CSV excluded.','checks':checks},indent=2)+'\n')


def verify():
    output=HERE/'outputs/replicated-workbook.twbx';lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for filename,digest in lock['data_files'].items():
            assert sha256((HERE/filename).read_bytes()).hexdigest()==digest
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==Path(filename).name))).hexdigest()==digest
    assert root.xpath('worksheets/worksheet/@name')==['Forecast Select','Forecast Reset','Target Select','Target Reset','Viz','Labels'];size=root.find('dashboards/dashboard/size');assert size.get('maxwidth')=='1000' and size.get('maxheight')=='500'
    table=root.find('worksheets/worksheet[@name="Viz"]/table');assert table.xpath('panes/pane/mark/@class')==['Bar','GanttBar']
    assert table.xpath('panes/pane/view/breakdown/@value')==['off','off']
    assert table.xpath('panes/pane/encodings/size/@column')==table.xpath('panes/pane/encodings/color/@column')
    assert ':Measure Names' in table.xpath('panes/pane/encodings/size/@column')[0]
    assert not table.xpath('panes/pane/encodings/text')
    assert 'Multiple Values' in table.find('cols').text and ' + ' in table.find('cols').text
    assert len(table.xpath('view/filter[contains(@column,":Measure Names")]/groupfilter/groupfilter'))==2
    assert len(root.xpath('//encoding[@field=":Measure Names" or @field="[:Measure Names]"]/map'))>=2
    params={c.get('caption'):c.get('name') for c in root.xpath('datasources/datasource[@name="Parameters"]/column')}
    assert set(params)=={'Forecast Param','Forecast List','Target Param','Target List','Delimiter'}
    ds=next(d for d in root.findall('datasources/datasource') if d.get('name')!='Parameters');cols={c.get('caption',c.get('name').strip('[]')):c for c in ds.findall('column')}
    formulas={k:c.find('calculation').get('formula') for k,c in cols.items() if c.find('calculation') is not None}
    assert 'ROUND(ABS(' in formulas['Sales Diff Text'] and 'ISNULL(' in formulas['Forecast Diff Text']
    for prefix in ['Forecast','Target']:
        assert 'REGEXP_REPLACE' in formulas[f'Add To {prefix} List']
        assert formulas[f'{prefix} List Reset']=="''"
        for source,field in [(f'{prefix} Select',f'Add To {prefix} List'),(f'{prefix} Reset',f'{prefix} List Reset')]:
            actions=root.xpath('actions/edit-parameter-action[source/@worksheet=$s]',s=source);assert len(actions)==1;action=actions[0]
            assert action.find('activation').get('type')=='on-select'
            assert cols[field].get('name').strip('[]') in action.find('params/param[@name="source-field"]').get('value')
            assert action.find('params/param[@name="target-parameter"]').get('value')=='[Parameters].'+params[f'{prefix} List']
            assert action.find('params/param[@name="clear-value"]') is None
        action=root.xpath('actions/action[source/@worksheet=$s]',s=f'{prefix} Select')[0]
        assert action.find('activation').get('auto-clear')=='true'
        link=unquote(action.find('link').get('expression'));assert cols['True'].get('name') in link and cols['False'].get('name') in link
        assert action.find('command/param').get('value')==f'{prefix} Select'
    assert formulas['2019 Orders']=='YEAR([Order Date])=2019'
    data=oracle();data.update({'status':'pass','artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False,'action_scope':'Serialized select sources, parameter targets, reset empty fields and self-filter clearing; no browser event execution.'})
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(data,indent=2)+'\n');verify_cloud(data)
    print('PASS: WW07 six fact-level forecast/target states, replacement/reset logic and all action contracts')
    return data


if __name__=='__main__':verify()
