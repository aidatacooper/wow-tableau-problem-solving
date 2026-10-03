"""Independent monthly fact-level ranks and advanced-chart contracts."""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import calendar
import csv
import json
import math
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
# Acceptance: blank-sdk-build, locked-extract, independent-metric-oracle,
# artifact-contract, cloud-rest-states.


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(next((HERE / 'inputs').glob('*.hyper')))) as c:
        table = next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        rows = c.execute_list_query('SELECT "Order Date", "Region", "Sales" FROM '+str(table))
    facts = defaultdict(list)
    for d, region, sales in rows:
        facts[d.month, region].append(float(sales))
    sales = {k: math.fsum(v) for k, v in facts.items()}
    values = []
    for month in range(1, 13):
        regions = sorted([r for m, r in sales if m == month], key=lambda r: -sales[month, r])
        assert len(regions) == 4
        for region in regions:
            rank = 1+sum(sales[month, other] > sales[month, region] for other in regions)
            label = ['1st', '2nd', '3rd', '4th'][rank-1] if month == 1 else region if month == 12 else ''
            values.append({'month': month, 'region': region, 'sales': sales[month, region], 'rank': rank, 'rank_line': rank+0.4, 'label': label})
    assert len(rows) == 9994 and len(values) == 48
    return {'row_count': len(rows), 'aggregation': 'Month-of-year over the complete extract; no year filter.', 'values': values}


def verify_cloud(data):
    expected = {(v['month'], v['region']): v for v in data['values']}
    checks = []
    author_primary=HERE/'outputs/cloud-author-chart.csv'
    author_fallback=author_primary.exists() and author_primary.stat().st_size==0
    selections=[('author','basic-data',False,False),('author','data-labels',False,True),('replica','chart',True,True)] if author_fallback else [('author','chart',True,True),('replica','chart',True,True)]
    selections += [('replica',kind,True,True) for kind in ['basic-data','data-labels'] if (HERE/f'outputs/cloud-replica-{kind}.csv').exists()]
    for role,kind,require_line,require_labels in selections:
        path = HERE / f'outputs/cloud-{role}-{kind}.csv'
        if not path.exists():
            continue
        rows = list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))
        seen = set(); rank_seen = set(); line_seen = set(); label_seen = {}
        for row in rows:
            region = next((v.strip() for k,v in row.items() if ('Region' in k) and v.strip() in {'Central','East','South','West'}), None)
            assert region is not None, (path, row)
            month_text = next(v for k,v in row.items() if 'Order Date' in k and v.strip())
            months = {calendar.month_name[i].lower():i for i in range(1,13)} | {calendar.month_abbr[i].lower():i for i in range(1,13)}
            month = months.get(month_text.strip().lower())
            if month is None:
                month = int(month_text)
            key = month, region; seen.add(key); value = expected[key]
            for field, raw in row.items():
                if not raw.strip():
                    continue
                if 'rank' in field.lower() and 'label' not in field.lower():
                    actual = float(raw.replace(',', ''))
                    line = 'offset' in field.lower() or 'line' in field.lower() or field == 'Rank Line'
                    assert abs(actual-value['rank_line' if line else 'rank']) < 1e-8, (path,key,field,actual,value)
                    (line_seen if line else rank_seen).add(key)
                if 'LABEL To Display' in field or 'Label To Display' in field:
                    assert raw == value['label'], (path,key,raw,value)
                    label_seen[key] = raw
                elif 'LABEL:Rank' in field:
                    assert raw==['1st','2nd','3rd','4th'][value['rank']-1],(path,key,raw)
        assert seen == set(expected) and rank_seen == set(expected), (path,len(seen),len(rank_seen))
        if require_line:assert line_seen==set(expected),(path,len(line_seen))
        if require_labels:assert len(label_seen)==8,(path,label_seen)
        checks.append({'role':role,'source_view_kind':kind,'file':path.relative_to(HERE).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'region_months_verified':48,'rank_axes_verified':2 if require_line else 1,'endpoint_labels_verified':8 if require_labels else 0})
    if (HERE / 'evidence/cloud-verification.json').exists():
        assert len(checks) == (3 if author_fallback else 2) + sum((HERE/f'outputs/cloud-replica-{kind}.csv').exists() for kind in ['basic-data','data-labels'])
        report=json.loads((HERE / 'evidence/cloud-verification.json').read_text())
        assert report['source_hashes']['replica'] == sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    if checks:
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','scope':'Replica advanced chart: all48region-months, bothrankaxes and8endpointlabels. Author fallback, ifused: complete BasicData ranks and DataLabels ranks/labels; emptyadvanced-chart CSVexcluded and doesnotproveauthoraxispositions.','author_advanced_csv_empty':author_fallback,'checks':checks},indent=2)+'\n')


def verify():
    output = HERE/'outputs/replicated-workbook.twbx'; lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for filename, digest in lock['data_files'].items():
            assert sha256((HERE/filename).read_bytes()).hexdigest() == digest
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==Path(filename).name))).hexdigest() == digest
    assert root.xpath('worksheets/worksheet/@name') == ['Viz - Advanced']
    size=root.find('dashboards/dashboard/size'); assert size.get('maxwidth')=='700' and size.get('maxheight')=='350'
    sheet=root.find('worksheets/worksheet/table')
    assert sheet.xpath('panes/pane/mark/@class') == ['Line','GanttBar']
    assert sheet.xpath('style/style-rule[@element="axis"]/format[@attr="render-fold-reversed" and @value="true"]')
    assert not root.xpath('//mark[@class="Square" or @class="Shape"]')
    assert len(sheet.xpath('panes/pane/encodings/text')) == 1
    line, block = sheet.findall('panes/pane')
    assert block.find('mark-sizing').get('mark-sizing-setting') == 'marks-scaling-off'
    block_formats = {f.get('attr'): f.get('value') for f in block.xpath('style/style-rule[@element="mark"]/format')}
    assert float(block_formats['size']) > 1.8
    label_formats = {f.get('attr'): f.get('value') for f in line.xpath('style/style-rule[@element="datalabel"]/format')}
    assert label_formats['color'] == '#ffffff' and label_formats['color-mode'] == 'user'
    cell_formats = {f.get('attr'): f.get('value') for f in line.xpath('style/style-rule[@element="cell"]/format')}
    assert cell_formats['text-align'] == 'center' and cell_formats['vertical-align'] == 'center'
    assert sheet.xpath('style/style-rule[@element="axis"]/encoding[@fold="true" and @synchronized="true"]')
    assert not sheet.xpath('style/style-rule/encoding[@axis-display]')
    assert sheet.xpath('.//table-calc[@ordering-type="Field"]/@ordering-field')
    assert sheet.find('cols').text.count('[mn:') == 1
    ds=next(d for d in root.findall('datasources/datasource') if d.get('name')!='Parameters')
    calcs={c.get('caption'):c.find('calculation').get('formula') for c in ds.findall('column') if c.find('calculation') is not None}
    region_locals={c.get('name').strip('[]') for c in ds.findall('column') if c.get('caption') in ['COLOUR:Region (Line)','COLOUR:Region (Block)']}
    assert all(any(local in value for local in region_locals) for value in sheet.xpath('.//table-calc[@ordering-type="Field"]/@ordering-field'))
    assert calcs['Rank']=='RANK(SUM([Sales]))'
    assert 'WHEN 1' in calcs['LABEL To Display'] and 'WHEN 12' in calcs['LABEL To Display']
    assert 'RANK' not in calcs['size'] and calcs['size']=='0.9'
    data=oracle(); data.update({'status':'pass','artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False})
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(data,indent=2)+'\n')
    verify_cloud(data)
    print('PASS: WW05 advanced marks, addressing, single label and 48 independent region-month ranks')
    return data


if __name__=='__main__':
    verify()
