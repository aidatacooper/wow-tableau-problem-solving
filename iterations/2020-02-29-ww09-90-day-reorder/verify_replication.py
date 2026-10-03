"""Independently deduplicate orders, sequence customers and calculate reorders."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import ast
import csv
import json
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent


def number(text):
    return float(text.replace(',', '').replace('%', '')) / (100 if '%' in text else 1)


def tolerance(text):
    raw=text.replace(',','').replace('%','').strip()
    decimals=len(raw.split('.')[1]) if '.' in raw else 0
    return 0.5*10**(-decimals)/(100 if '%' in text else 1)+1e-8


def parse_date(text):
    if not text or text=='Null':return None
    for fmt in ['%m/%d/%Y','%d/%m/%Y','%Y-%m-%d','%B %d, %Y','%b %d, %Y']:
        try:return datetime.strptime(text,fmt).date().isoformat()
        except ValueError:pass
    raise AssertionError(('Unrecognized date export',text))


def verify():
    # blank-sdk-build; locked-superstore-orders; ordered-native-reorders;
    # first-order-exclusion; native-customer-timeline; global-reorder-kpis;
    # independent-reorder-oracle; cloud-rest-order-matrices; cloud-visual-review
    source = (HERE / 'build_replication.py').read_text(encoding='utf-8')
    assert 'TWBEditor("")' in source
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(ast.parse(source)))
    lock = json.loads((HERE / 'inputs/source-lock.json').read_text())
    data = HERE / lock['extracted_data'][0]['file']
    assert sha256(data.read_bytes()).hexdigest() == lock['extracted_data'][0]['sha256']
    artifact = HERE / 'outputs/replicated-workbook.twbx'
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root = etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        assert sha256(z.read(next(n for n in z.namelist() if n.endswith('.hyper')))).hexdigest() == lock['extracted_data'][0]['sha256']
    calcs = {c.get('caption'): c.find('calculation').get('formula') for c in root.xpath('/workbook/datasources/datasource/column[calculation][@caption]')}
    assert calcs['Previous Order Date'] == 'LOOKUP(ATTR([Order Date]),-1)'
    assert 'THEN NULL' in calcs['Reorder Within 90 Days'] and '<=90' in calcs['Reorder Within 90 Days']
    assert 'WINDOW_COUNT' in calcs['90-Day Reorder Rate'] and 'WINDOW_SUM' in calcs['90-Day Reorder Rate']
    table = root.xpath('//worksheet[@name="Table"]')[0]
    assert '[mn:' not in table.findtext('table/cols'),table.findtext('table/cols')
    assert '[mn:Order Date:' not in etree.tostring(root,encoding='unicode')
    assert len(table.xpath('./table/panes/pane')) == 2
    assert table.xpath('./table/panes/pane[@id="2" and @x-index="1"]')
    gantt = table.xpath('./table/panes/pane[mark[@class="GanttBar"]]')[0]
    days_column = root.xpath('/workbook/datasources/datasource/column[@caption="Days Since Previous Order"]')[0].get('name')
    assert calcs['Connection Duration'] in ('-[Days Since Previous Order]', '-' + days_column)
    assert gantt.xpath('./encodings/size') and gantt.xpath('./encodings/lod')
    assert gantt.xpath('./style/style-rule/format[@attr="mark-color" and @value="#cac4be"]')
    size_ref = gantt.find('encodings/size').get('column').split('.')[-1]
    size_column = table.xpath('./table/view/datasource-dependencies/column-instance[@name=$name]', name=size_ref)[0].get('column')
    assert root.xpath('/workbook/datasources/datasource/column[@name=$name and @caption="Connection Duration"]', name=size_column)
    assert len(table.xpath('./table/panes/pane/mark-sizing[@mark-sizing-setting="marks-scaling-off"]')) == 2
    assert len(table.xpath('./table/panes/pane[@selection-relaxation-option="selection-relaxation-disallow"]')) == 2
    assert table.xpath('./table/panes/pane[mark[@class="Shape"]]/style/style-rule/format[@attr="size" and @value="0.44977900385856628"]')
    assert root.xpath('/workbook/datasources/datasource/column[@caption="Reorder Within 90 Days" and @role="measure"]')
    assert root.xpath('/workbook/datasources/datasource/column[@caption="Previous Order Date" and @role="measure" and @type="ordinal"]')
    shapes = root.xpath('/workbook/datasources/datasource/style/style-rule/encoding[@attr="shape"]')
    assert shapes and all(s.get('type') == 'shape' for s in shapes), 'Native shape mappings require type=shape'
    assert all({m.findtext('bucket'):m.get('to') for m in s.findall('map')} == {'0':':filled/diamond','1':':filled/diamond','%null%':':filled/right-triangle'} for s in shapes)
    colors = root.xpath('/workbook/datasources/datasource/style/style-rule/encoding[@attr="color"]')
    assert colors and all({m.findtext('bucket'):m.get('to') for m in c.findall('map')} == {'0':'#cac4be','1':'#5557eb','%null%':'#cac4be'} for c in colors)
    assert table.xpath('./table/style/style-rule[@element="axis"]/format[@attr="render-fold-reversed" and @value="true"]')
    assert table.xpath('.//shelf-sort-v2[@direction="DESC"]')
    for c in table.xpath('./table/view/datasource-dependencies/column-instance[table-calc]'):
        assert c.get('derivation')=='User',c.attrib
        assert all(tc.get('ordering-type') == 'Field' for tc in c.findall('table-calc'))
        for tc in c.findall('table-calc'):
            if tc.get('ordering-type') != 'Field': continue
            assert [o.get('field').split('.')[-1].strip('[]') for o in tc.findall('order')] == ['Order ID', 'Order Date']
    for c in root.xpath('//worksheet[@name="BAN"]/table/view/datasource-dependencies/column-instance[table-calc]'):
        assert c.get('derivation')=='User',c.attrib
    for tc in root.xpath('//table-calc[@level-address]'):
        assert tc.get('level-address').startswith('[') and tc.get('level-address').endswith(']'),tc.attrib
    customers = defaultdict(set)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint, str(data)) as connection:
        rows = connection.execute_list_query('SELECT "Customer Name", "Order ID", "Order Date" FROM "Extract"."Extract"')
    for customer, orderid, dt in rows:
        customers[customer].add((date(dt.year, dt.month, dt.day), orderid))
    profiles, orders = {}, []
    for customer, events in sorted(customers.items()):
        events = sorted(events)
        count = 0
        for i, (dt, orderid) in enumerate(events):
            previous = events[i-1][0] if i else None
            days = (dt-previous).days if previous else None
            within = int(days <= 90) if days is not None else None
            duration = -days if days is not None else None
            assert duration is None if previous is None else dt + timedelta(days=duration) == previous
            count += within or 0
            orders.append({'Customer Name': customer, 'Order ID': orderid, 'Order Date': dt.isoformat(), 'Previous Order Date': previous.isoformat() if previous else None, 'Days Since Previous Order': days, 'Reorder Within 90 Days': within, 'Connection Duration': duration})
        profiles[customer] = {'total_orders': len(events), 'reorders': len(events)-1, 'within90': count, 'rate': count/(len(events)-1) if len(events)>1 else 0}
    assert profiles['Noel Staavos']['total_orders'] > len({dt for dt, _ in customers['Noel Staavos']}), 'Same-day multiple-order edge case must be covered'
    total_reorders = sum(p['reorders'] for p in profiles.values())
    within90 = sum(p['within90'] for p in profiles.values())
    kpis = {'Overall Reorder Rate': within90/total_reorders, 'Avg Reorders per Customer': total_reorders/len(profiles)}
    report = {'status': 'pass', 'artifact_sha256': digest, 'source_rows': len(rows), 'distinct_orders': len(orders), 'customers': len(profiles), 'total_reorders': total_reorders, 'within90': within90, 'kpis': kpis, 'customer_profiles': profiles, 'order_events': orders, 'browser_interaction_executed': False}
    cloudpath = HERE / 'evidence/cloud-verification.json'
    if cloudpath.exists():
        cloud = json.loads(cloudpath.read_text()); provenance = json.loads((HERE / 'evidence/export-provenance.json').read_text())
        assert cloud['source_hashes']['replica'] == digest
        assert cloud['source_hashes']['author'] == provenance['comparison_sha256']
        assert provenance['original_sha256'] == lock['locked_original_sha256']
        assert {s['name'] for s in cloud['states']}=={'default','noel'}
        checks = []
        for state in cloud['states']:
            for image in state['views'].values():assert sha256((HERE/image['path']).read_bytes()).hexdigest()==image['sha256']
            selected = 'Noel Staavos' if state['name'] == 'noel' else None
            wanted = {(r['Customer Name'],r['Order ID']):r for r in orders if selected is None or r['Customer Name']==selected}
            cohort = {k:v for k,v in profiles.items() if selected is None or k==selected}
            reorders = sum(p['reorders'] for p in cohort.values())
            cohortkpis = {'Overall Reorder Rate':sum(p['within90'] for p in cohort.values())/reorders,'Avg Reorders per Customer':reorders/len(cohort)}
            for capture in state['data']:
                path = HERE / capture['path']; assert sha256(path.read_bytes()).hexdigest()==capture['sha256']
                with path.open(encoding='utf-8-sig',newline='') as f: exported=list(csv.DictReader(f))
                assert exported, (path,'Empty CSV')
                if capture['view']=='BAN':
                    for field,value in cohortkpis.items():
                        values=[r[field] for r in exported if r.get(field)]
                        assert values and all(abs(number(v)-value)<=tolerance(v) for v in values),(path,field,values,value)
                else:
                    found=set()
                    for row in exported:
                        if not row.get('Order ID'): continue
                        key=(row['Customer Name'],row['Order ID']);assert key in wanted,(path,key)
                        expected=wanted[key];found.add(key)
                        exported_date=row.get('Order Date') or row.get('Timeline Date')
                        assert exported_date and parse_date(exported_date)==expected['Order Date'],(path,key,exported_date,expected)
                        if 'Previous Order Date' in row:
                            assert parse_date(row['Previous Order Date'])==expected['Previous Order Date'],(path,key,row['Previous Order Date'],expected)
                        if 'Days Since Previous Order' in row:
                            gap = row['Days Since Previous Order']
                            parsed_gap = None if not gap or gap == 'Null' else int(number(gap))
                            assert parsed_gap==expected['Days Since Previous Order'],(path,key,gap,expected)
                        if capture['role']=='replica':
                            assert 'Connection Duration' in row, (path, 'Gantt interval export missing')
                            duration = row['Connection Duration']
                            parsed_duration = None if not duration or duration == 'Null' else int(number(duration))
                            assert parsed_duration == expected['Connection Duration'], (path,key,duration,expected)
                            if parsed_duration is not None:
                                assert date.fromisoformat(expected['Order Date']) + timedelta(days=parsed_duration) == date.fromisoformat(expected['Previous Order Date']), (path,key,'Gantt endpoint')
                        p=profiles[key[0]]
                        assert abs(number(row['90-Day Reorder Rate'])-p['rate'])<=0.0051,(path,key,row['90-Day Reorder Rate'],p['rate'])
                        assert int(number(row.get('Total Orders') or row['Display Total Orders']))==p['total_orders']
                        if 'Reorder Within 90 Days' in row:
                            flag = row['Reorder Within 90 Days']
                            parsed_flag = None if not flag or flag == 'Null' else int(flag)
                            assert parsed_flag==expected['Reorder Within 90 Days'],(path,key,flag,expected)
                    assert found==set(wanted),(path,len(found),len(wanted))
                checks.append({'path':capture['path'],'status':'pass','rows':len(exported),'scope':capture['scope']})
        assert len(checks)==8
        report['cloud_checks']=checks
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2),encoding='utf-8')
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',len(orders),'orders;',len(profiles),'customers;',total_reorders,'reorders;',kpis)


if __name__=='__main__':
    verify()
