"""Independent date-window aggregates, ranks and classification for all three lists."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
from datetime import date, timedelta
import ast
import csv
import json
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
STATES = {'default': date(2019,5,8), 'monday': date(2019,5,6), 'year-end': date(2019,12,31)}


def verify():
    # blank-sdk-build; locked-superstore-data; native-84-day-weekday-window;
    # native-three-metric-ranking; native-average-bands; selected-date-arrow-rank;
    # independent-ranking-oracle; cloud-rest-three-lists; cloud-visual-review
    text = (HERE/'build_replication.py').read_text(encoding='utf-8')
    assert 'TWBEditor("")' in text
    assert not any(isinstance(n,ast.Attribute) and n.attr.startswith('_') for n in ast.walk(ast.parse(text)))
    lock=json.loads((HERE/'inputs/source-lock.json').read_text()); entry=lock['extracted_data'][0]; data=HERE/entry['file']
    assert sha256(data.read_bytes()).hexdigest()==entry['sha256']
    artifact=HERE/'outputs/replicated-workbook.twbx';digest=sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        assert sha256(z.read(next(n for n in z.namelist() if n.endswith('.hyper')))).hexdigest()==entry['sha256']
    columns={c.get('caption'):c for c in root.xpath('/workbook/datasources/datasource/column[@caption]')}
    parameter=columns['Order Date Parameter']
    assert parameter.get('datatype')=='date' and parameter.get('param-domain-type')=='any'
    assert parameter.get('value')=='#2019-05-08#'
    assert parameter.find('calculation').get('formula')=='#2019-05-08#'
    assert '-84' in columns['Dates to Include'].find('calculation').get('formula')
    assert 'DATENAME' in columns['Weekdays to Include'].find('calculation').get('formula')
    question_formula = columns['Question'].find('calculation').get('formula')
    assert all(token in question_formula for token in ('HOW DOES ', ' COMPARE TO THE PRIOR 12 ', 'MONTH(', 'DAY(', 'YEAR('))
    title = root.xpath('//worksheet[@name="Title"]')[0]
    title_binding = title.xpath('./table/panes/pane/encodings/text')[0].get('column')
    title_runs = title.xpath('./table/panes/pane/customized-label/formatted-text/run')
    assert len(title_runs) == 1 and title_runs[0].text == '<' + title_binding + '>'
    assert title_runs[0].get('fontsize') == '10'
    for metric in ['Sales','Orders','Qty']:
        color=columns['COLOUR:'+metric].find('calculation').get('formula')
        assert all(fn in color for fn in ['WINDOW_MAX','WINDOW_MIN','WINDOW_AVG'])
        assert 'RANK_UNIQUE' in columns['Selected Date '+metric+' Rank'].find('calculation').get('formula')
        sheet=root.xpath('//worksheet[@name="'+metric+' Rank"]')[0]
        assert sheet.xpath('./table/panes/pane/mark[@class="Square"]')
        assert len(sheet.xpath('./table/view/filter'))==2
        assert sheet.xpath('.//shelf-sort-v2[@direction="DESC"]')
        row_shelf=sheet.findtext('table/rows')
        assert ':Order Date:ok]' in row_shelf and '[mn:' not in row_shelf,row_shelf
        date_instances=[c for c in sheet.xpath('./table/view/datasource-dependencies/column-instance') if c.get('column') in ['[Order Date]',columns['Order Date Copy'].get('name')]]
        assert date_instances and all(c.get('derivation') in ['None','Attribute'] for c in date_instances)
        assert sheet.xpath('./table/style/style-rule/encoding[@palette="tableau-map-temperatur"]')
        assert sheet.xpath('./table/style/style-rule[@element="header"]/format[@attr="band-color" and @scope="rows" and @value="#d4d4d4"]')
        assert sheet.xpath('./table/style/style-rule[@element="table"]/format[@attr="band-level" and @scope="rows" and @value="3"]')
        assert sheet.xpath('./table/style/style-rule[@element="table"]/format[@attr="band-size" and @scope="rows" and @value="1"]')
        assert sheet.xpath('./table/style/style-rule[@element="label"]/format[@attr="font-weight" and @value="bold"]')
        for tc in sheet.xpath('./table/view/datasource-dependencies/column-instance/table-calc'):
            assert tc.get('ordering-type')=='Field'
            assert len(tc.findall('order'))==3
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp,Connection(hp.endpoint,str(data)) as c:
        rows=c.execute_list_query('SELECT "Order Date","Order ID","Sales","Quantity" FROM "Extract"."Extract"')
    oracle={}
    for state,target in STATES.items():
        grouped=defaultdict(lambda:{'Sales':0.0,'Orders':set(),'Qty':0})
        for dt,orderid,sales,qty in rows:
            dt=date(dt.year,dt.month,dt.day)
            if target-timedelta(days=84)<=dt<=target and dt.weekday()==target.weekday():
                grouped[dt]['Sales']+=sales;grouped[dt]['Orders'].add(orderid);grouped[dt]['Qty']+=qty
        assert grouped
        metrics={}
        for metric in ['Sales','Orders','Qty']:
            values={d:(len(v[metric]) if metric=='Orders' else v[metric]) for d,v in grouped.items()}
            average=sum(values.values())/len(values);maximum=max(values.values());minimum=min(values.values())
            ordered=sorted(values,key=lambda d:(-values[d],d))
            metrics[metric]=[{'date':d.isoformat(),'value':values[d],'rank':i+1,'color':1 if values[d]==maximum else 4 if values[d]==minimum else 2 if values[d]>=average else 3,'group':'ABOVE\nAVERAGE' if values[d]>=average else 'BELOW\nAVERAGE','selected':d==target,'average':average} for i,d in enumerate(ordered)]
        oracle[state]={'target':target.isoformat(),'weekday':target.strftime('%A').upper(),'metrics':metrics}
    report={'status':'pass','artifact_sha256':digest,'source_rows':len(rows),'states':oracle,'browser_interaction_executed':False,'scope':'Complete date-window Sales/COUNTD orders/quantity aggregates and ordinal rank ranges; tied rank uniqueness is checked without assuming tie-break date.'}
    cloudpath=HERE/'evidence/cloud-verification.json'
    if cloudpath.exists():
        cloud=json.loads(cloudpath.read_text());provenance=json.loads((HERE/'evidence/export-provenance.json').read_text())
        assert cloud['source_hashes']['replica']==digest and cloud['source_hashes']['author']==provenance['comparison_sha256']
        assert provenance['original_sha256']==lock['locked_original_sha256']
        assert {s['name'] for s in cloud['states']}==set(STATES)
        checks=[]
        for state in cloud['states']:
            for image in state['views'].values():assert sha256((HERE/image['path']).read_bytes()).hexdigest()==image['sha256']
            for capture in state['data']:
                metric=capture['view'].split()[0];wanted={r['date']:r for r in oracle[state['name']]['metrics'][metric]}
                path=HERE/capture['path'];assert sha256(path.read_bytes()).hexdigest()==capture['sha256']
                with path.open(encoding='utf-8-sig',newline='') as f:exported=list(csv.DictReader(f))
                assert exported,(path,'Empty CSV');found=set()
                for row in exported:
                    raw=row['Order Date'];dt=None
                    for fmt in ['%m/%d/%Y','%d/%m/%Y','%Y-%m-%d','%B %d, %Y','%b %d, %Y']:
                        try:
                            from datetime import datetime
                            dt=datetime.strptime(raw,fmt).date().isoformat();break
                        except ValueError:pass
                    assert dt in wanted,(path,raw)
                    expected=wanted[dt];found.add(dt)
                    valuefield={'Sales':'Sales','Orders':'# Orders','Qty':'Quantity'}[metric]
                    value=float(row[valuefield].replace(',','').replace('$',''))
                    assert abs(value-expected['value'])<=0.51,(path,dt,value,expected)
                    colorfield=next((k for k in row if k.startswith('COLOUR:') and row[k]),None)
                    if colorfield:assert int(row[colorfield])==expected['color'],(path,dt,row[colorfield],expected)
                    groupfield=next((k for k in row if 'Header' in k),None)
                    if groupfield:assert ' '.join(row[groupfield].split())==' '.join(expected['group'].split())
                    if 'Selected Date' in row:assert row['Selected Date']==('►' if expected['selected'] else '')
                    rankfield=next((k for k in row if k.startswith('Selected Date ') and 'Rank' in k),None)
                    if rankfield and row[rankfield] and row[rankfield]!='Null':
                        assert expected['selected'],(path,dt,'Rank only applies to selected date')
                        values=[r['value'] for r in wanted.values()]
                        first=1+sum(v>expected['value'] for v in values)
                        last=sum(v>=expected['value'] for v in values)
                        assert first<=int(row[rankfield])<=last,(path,dt,row[rankfield],first,last)
                assert found==set(wanted),(path,len(found),len(wanted))
                checks.append({'path':capture['path'],'status':'pass','dates':len(found)})
        assert len(checks)==18
        report['cloud_checks']=checks
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2),encoding='utf-8')
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',len(rows),'source rows;', {s:len(o['metrics']['Sales']) for s,o in oracle.items()},'dates per state')


if __name__=='__main__':
    verify()
