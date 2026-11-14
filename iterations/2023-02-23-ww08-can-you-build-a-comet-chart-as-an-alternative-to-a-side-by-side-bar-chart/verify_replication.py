"""Static contracts and independent numeric checks; never claims Desktop acceptance."""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
import sys
import zipfile
from lxml import etree
from tableauhyperapi import HyperProcess, Telemetry, Connection

HERE = Path(__file__).resolve().parent


def verify(workbook=None):
    workbook = Path(workbook or HERE / 'outputs/replicated-workbook.twbx')
    results = {}
    def passed(key):
        results[key] = 'pass'
    with zipfile.ZipFile(workbook) as archive:
        names = archive.namelist()
        root = etree.fromstring(archive.read(next(n for n in names if n.endswith('.twb'))))
        packed = archive.read(next(n for n in names if n.endswith('.hyper')))
    source = HERE / 'inputs/Sample _ Superstore.hyper'
    assert hashlib.sha256(packed).digest() == hashlib.sha256(source.read_bytes()).digest()
    passed('packaged-data')
    sheets = root.findall('./worksheets/worksheet')
    assert len(sheets) == 1
    sheet = sheets[0]
    dashboard = root.find('./dashboards/dashboard')
    size = dashboard.find('size')
    assert {k: size.get(k) for k in ('minwidth', 'maxwidth', 'minheight', 'maxheight')} == dict(minwidth='800', maxwidth='800', minheight='700', maxheight='700')
    passed('single-sheet-dashboard')
    cols = {c.get('caption', c.get('name').strip('[]')): c for c in root.findall('./datasources/datasource/column')}
    latest = cols['Latest Sales']; previous = cols['Previous Sales']; increased = cols['Sales Increased']
    assert latest.find('calculation').get('formula') == '{FIXED [Sub-Category]: SUM(IF YEAR([Order Date]) = 2022 THEN [Sales] END)}'
    assert previous.find('calculation').get('formula') == '{FIXED [Sub-Category]: SUM(IF YEAR([Order Date]) = 2021 THEN [Sales] END)}'
    formula = increased.find('calculation').get('formula')
    assert latest.get('name') in formula and previous.get('name') in formula and ' > ' in formula
    members = sheet.xpath('.//filter/groupfilter//groupfilter/@member')
    assert set(members) == {'2021', '2022'}, members
    passed('year-scope')
    panes = sheet.findall('./table/panes/pane')
    assert [p.find('mark').get('class') for p in panes] == ['Line', 'Circle']
    line, circle = panes
    assert line.find('./encodings/path').get('column').endswith('[yr:Order Date:ok]')
    assert line.find('./encodings/size').get('column').endswith('[yr:Order Date:ok]')
    axis = sheet.find('./table/style/style-rule[@element="axis"]/encoding')
    assert axis.get('synchronized') == 'true' and axis.get('fold') == 'true'
    style = {n.get('attr'): n.get('value') for n in line.findall('./style/style-rule[@element="mark"]/format')}
    assert style['mark-labels-mode'] == 'line-ends' and style['mark-labels-line-first'] == 'false' and style['mark-labels-line-last'] == 'true'
    cstyle = {n.get('attr'): n.get('value') for n in circle.findall('./style/style-rule[@element="mark"]/format')}
    assert cstyle['mark-color'] == '#ffffff' and cstyle['mark-labels-show'] == 'false'
    assert float(cstyle['size']) < float(style['size'])
    size_style = sheet.find('./table/style/style-rule[@element="mark"]/encoding[@attr="size"]')
    assert size_style.get('type') == 'catsize' and float(size_style.get('min-size')) < float(size_style.get('max-size'))
    legend = dashboard.find('.//zone[@type-v2="size"]')
    assert legend.get('pane-specification-id') == circle.get('id')
    assert legend.get('param').endswith(circle.find('./encodings/size').get('column').split('].', 1)[1])
    passed('comet-geometry')
    sort = sheet.find('.//computed-sort')
    assert sort is not None and sort.get('direction') == 'DESC' and latest.get('name').strip('[]') in sort.get('using')
    passed('latest-labels-and-sort')
    palette = root.xpath('./datasources/datasource/style/style-rule/encoding/map')
    mapping = {m.findtext('bucket'): m.get('to') for m in palette}
    assert mapping['false'] == '#d95657' and mapping['true'] == '#b9b0ab'
    assert increased.get('name').strip('[]') in line.find('./encodings/color').get('column')
    for p in panes:
        texts = ''.join(p.xpath('./customized-tooltip/formatted-text/run/text()'))
        assert '[none:Sub-Category:nk]' in texts and '[yr:Order Date:ok]' in texts and '[sum:Sales:qk]' in texts
    passed('color-and-tooltip-structure')
    dividers = sheet.xpath('./table/style/style-rule[@element="table-div"]/format/@attr')
    assert 'div-level' in dividers and 'attr' not in dividers and 'value' not in dividers
    assert sheet.find('./table/style/style-rule[@element="table"]/format[@attr="background-color"]').get('value') == '#f5f5f5'
    passed('formatting-structure')
    # Independent row-by-row Decimal aggregation, compared with analysis-stage SQL totals.
    expected = json.loads((HERE / 'evidence/expected-sales.json').read_text())
    totals = defaultdict(lambda: defaultdict(Decimal))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={'log_config': ''}) as hyper:
        with Connection(hyper.endpoint, str(source)) as connection:
            table = connection.catalog.get_table_names('Extract')[0]
            rows = connection.execute_list_query(f'SELECT "Sub-Category", "Order Date", "Sales" FROM {table}')
            assert len(rows) == 10194
            for category, date, sales in rows:
                if date.year in (2021, 2022):
                    totals[category][str(date.year)] += Decimal(str(sales))
    assert set(totals) == set(expected) and len(totals) == 17
    for category, years in expected.items():
        for year, value in years.items():
            assert abs(float(totals[category][year]) - value) < 0.00001, (category, year)
    declines = sorted(k for k,v in totals.items() if v['2022'] < v['2021'])
    assert declines == ['Envelopes', 'Machines']
    order = sorted(totals, key=lambda k: totals[k]['2022'], reverse=True)
    assert order[0] == 'Phones' and order[-1] == 'Envelopes'
    passed('sales-numerics')
    report = {
        'workbook_sha256': hashlib.sha256(workbook.read_bytes()).hexdigest(),
        'automated': results, 'records': len(rows), 'annual_points': 34,
        'sales_2021': round(sum(float(v['2021']) for v in totals.values()), 6),
        'sales_2022': round(sum(float(v['2022']) for v in totals.values()), 6),
        'declines': declines, 'descending_2022_order': order,
        'desktop': 'pending - parent owns serialized Desktop gate',
        'rendered_numeric_and_visual_acceptance': 'pending; SQL/Python checks do not execute Tableau rendering',
    }
    (HERE / 'evidence/static-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else None)
