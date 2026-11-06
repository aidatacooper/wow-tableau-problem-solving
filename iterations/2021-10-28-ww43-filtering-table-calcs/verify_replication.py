"""Raw CSV Decimal oracle versus packaged Hyper SQL and generated TWB contracts.

SQL models the inspected workbook's semantics; this is NOT a Tableau runtime
execution or a substitute for Desktop/Cloud interaction acceptance.
"""
from collections import defaultdict
import csv
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry
from cwtwb.validator import validate_against_schema

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'outputs/replicated-workbook.twbx'
SENTINEL = date(1900, 1, 1)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_rows():
    with (HERE / 'inputs/WOW2021_Superstore_Orders.csv').open(encoding='utf-16', newline='') as f:
        return [(datetime.strptime(r['Order Date'], '%m/%d/%Y').date().replace(day=1),
                 r['Sub-Category'], Decimal(r['Sales'])) for r in csv.DictReader(f, delimiter='\t')]


def oracle(rows, start, end, categories=None):
    # All data bounds precede an ordinary sub-category filter (FIXED LOD).
    lo = min(r[0] for r in rows) if start == SENTINEL else start
    hi = max(r[0] for r in rows) if end == SENTINEL else end
    totals, bars = defaultdict(Decimal), defaultdict(Decimal)
    for month, category, sales in rows:
        if not categories or category in categories:
            totals[month] += sales
        if lo <= month <= hi:
            bars[category] += sales
    timeline = sorted(totals)
    trend = []
    for i, month in enumerate(timeline):
        window = timeline[max(0, i - 2):i + 1]
        if lo <= month <= hi:
            trend.append((month.isoformat(), totals[month], sum(totals[m] for m in window) / len(window)))
    n = (hi.year - lo.year) * 12 + hi.month - lo.month + 1
    return trend, [(c, s, s / n) for c, s in sorted(bars.items(), key=lambda x: (-x[1], x[0]))], lo, hi


def contracts(root):
    ds = next(d for d in root.findall('datasources/datasource') if d.get('name') != 'Parameters')
    fields = {c.get('caption', c.get('name').strip('[]')): c for c in ds.findall('column')}
    parameters = {c.get('caption'): c for c in root.findall("datasources/datasource[@name='Parameters']/column")}
    refs = {c.get('name'): f'[{n}]' for n, c in fields.items()}
    refs.update({f"[Parameters].{c.get('name')}": f'[{n}]' for n, c in parameters.items()})

    def formula(name):
        result = fields[name].find('calculation').get('formula')
        for old, new in sorted(refs.items(), key=lambda x: -len(x[0])):
            result = result.replace(old, new)
        return re.sub(r'\s+', '', result)

    # acceptance: generated-formulas
    expected = {
        'Order Date Month': "DATE(DATETRUNC('month',[Order Date]))",
        'Min Date Selected': 'IF [pMinDate]=#1900-01-01# THEN {FIXED : MIN([Order Date Month])} ELSE [pMinDate] END',
        'Max Date Selected': 'IF [pMaxDate]=#1900-01-01# THEN {FIXED : MAX([Order Date Month])} ELSE [pMaxDate] END',
        'Is Month Selected?': '[Order Date Month]>=[Min Date Selected] AND [Order Date Month]<=[Max Date Selected]',
        'Visible Month': 'LOOKUP(MIN([Is Month Selected?]),0)',
        'Rolling Average': 'WINDOW_AVG(SUM([Sales]),-2,0)',
        'No. Months': "DATEDIFF('month',[Min Date Selected],[Max Date Selected])+1",
        'Avg Monthly Sales': 'SUM([Sales])/MIN([No. Months])',
    }
    for name, value in expected.items():
        assert formula(name) == re.sub(r'\s+', '', value), (name, formula(name))
    trend = root.find("worksheets/worksheet[@name='Trend']")
    bars = root.find("worksheets/worksheet[@name='Bars']")

    def instances(ws, field):
        return ws.findall(f".//datasource-dependencies/column-instance[@column='{fields[field].get('name')}']")

    # acceptance: chronological-partition
    month = instances(trend, 'Order Date Month')
    shelf = trend.findtext('table/cols')
    on_shelf = [c for c in month if shelf.endswith('.' + c.get('name'))]
    assert len(on_shelf) == 1
    assert on_shelf[0].get('derivation') == 'None' and on_shelf[0].get('type') == 'quantitative', 'Must preserve 48 continuous exact months, not month-of-year'
    month_ref = f"[{ds.get('name')}].{on_shelf[0].get('name')}"
    for name in ('Rolling Average', 'Visible Month'):
        ci = instances(trend, name)
        assert len(ci) == 1 and ci[0].get('derivation') == 'User'
        tc = ci[0].find('table-calc')
        assert tc is not None and tc.get('ordering-type') == 'Field'
        assert [x.get('field') for x in tc.findall('order')] in ([month_ref], [f"[{ds.get('name')}].{fields['Order Date Month'].get('name')}"])
        assert tc.get('level-break') is None and tc.get('restart-every') is None
    assert not trend.findall('.//encodings/lod'), 'No extra view dimensions may partition the monthly series'
    assert not trend.findall('.//computed-sort') and not trend.findall('.//sort'), 'Use natural chronological order'
    assert [p.find('mark').get('class') for p in trend.findall('table/panes/pane[@id]')] == ['Area', 'Line']
    assert len(trend.findall(".//encoding[@synchronized='true'][@fold='true']")) == 2

    # acceptance: filter-order
    tf = trend.findall('table/view/filter')
    assert len(tf) == 1 and tf[0].get('column').endswith('.' + instances(trend, 'Visible Month')[0].get('name'))
    assert tf[0].find('groupfilter').get('member') == 'true'
    bf = bars.findall('table/view/filter')
    assert len(bf) == 1 and bf[0].get('column').endswith('.' + instances(bars, 'Is Month Selected?')[0].get('name'))
    assert bf[0].find('groupfilter').get('member') == 'true'
    assert not instances(bars, 'Is Month Selected?')[0].findall('table-calc')
    assert instances(bars, 'Is Month Selected?')[0].get('derivation') == 'None'
    assert not bars.findall('.//table-calc')

    # acceptance: bar-panels
    assert '[none:Sub-Category:nk]' in bars.findtext('table/rows')
    bar_shelf = bars.findtext('table/cols')
    assert ' + ' in bar_shelf and '[sum:Sales:qk]' in bar_shelf
    assert instances(bars, 'Avg Monthly Sales')[0].get('name') in bar_shelf
    assert not bars.findall(".//encoding[@fold='true']")
    assert [p.find('mark').get('class') for p in bars.findall('table/panes/pane')] == ['Bar', 'Bar']
    sorts = bars.findall('.//shelf-sort-v2')
    assert len(sorts) == 1 and sorts[0].get('direction') == 'DESC'
    assert 'Sales' in sorts[0].get('measure-to-sort-by', '')

    # acceptance: selection-and-reset
    actions = root.findall('actions/edit-parameter-action')
    assert len(actions) == 2
    for prefix, agg in (('Min', 'min'), ('Max', 'max')):
        parameter = parameters[f'p{prefix}Date']
        assert parameter.get('value') == '#1900-01-01#' and parameter.get('datatype') == 'date'
        action = next(a for a in actions if a.find('agg-type').get('type') == agg)
        assert action.find('source').get('worksheet') == 'Trend'
        assert action.find('activation').get('type') == 'on-select'
        assert action.find('clear-option').attrib == {'type': 'assign-fixed-value', 'value': 'd:1900-01-01'}
        params = {p.get('name'): p.get('value') for p in action.findall('params/param')}
        assert params['source-field'] == month_ref
        assert params['target-parameter'] == '[Parameters].' + parameter.get('name')
    # acceptance: subcategory-action
    filters = root.findall('actions/action')
    assert len(filters) == 1
    a = filters[0]
    assert a.find('source').get('worksheet') == 'Bars'
    assert a.find('activation').attrib == {'auto-clear': 'true', 'type': 'on-select'}
    assert '[Sub-Category]' in unquote(a.find('link').get('expression'))
    assert a.find('link').get('multi-select') == 'true'
    assert {p.get('name'): p.get('value') for p in a.findall('command/param')} == {'exclude': 'Bars', 'target': 'Filtering Table Calcs'}
    dashboard = root.find('dashboards/dashboard')
    assert {z.get('name') for z in dashboard.findall('.//zone') if z.get('name')} == {'Trend', 'Bars'}
    assert dashboard.find('size').get('maxwidth') == '800' and dashboard.find('size').get('maxheight') == '1000'
    return {'formulas': expected, 'window_preceding': 2, 'partition': 'one ascending exact-date monthly series',
            'date_filter': 'post-window LOOKUP boolean', 'subcategory_filter': 'pre-window ordinary action filter'}


def close(actual, expected):
    assert len(actual) == len(expected), (len(actual), len(expected))
    for a, e in zip(actual, expected):
        assert str(a[0]) == str(e[0]), (a, e)
        for av, ev in zip(a[1:], e[1:]):
            assert abs(float(av) - float(ev)) < 1e-7, (a, e)


def verify():
    rows = raw_rows()
    # acceptance: raw-data-baseline
    assert len(rows) == 9994 and len({r[1] for r in rows}) == 17
    assert sum(r[2] for r in rows) == Decimal('2297200.8603')
    assert len({r[0] for r in rows}) == 48
    report = {'scope': 'Static generated-workbook contracts and independently computed SQL model; Tableau runtime pending',
              'artifact_sha256': sha(OUTPUT), 'row_count': len(rows), 'total_sales': str(sum(r[2] for r in rows)), 'scenarios': []}
    with ZipFile(OUTPUT) as archive, tempfile.TemporaryDirectory(prefix='ww43-verify-') as tmp:
        root = etree.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.twb'))))
        schema = validate_against_schema(root)
        assert schema.schema_available and not schema.errors, schema.errors
        report['schema'] = {'errors': schema.errors, 'schema_available': schema.schema_available, 'compatibility_warnings': schema.compatibility_warnings}
        report['contracts'] = contracts(root)
        # Prove that acceptance rejects the main plausible semantic regressions.
        mutations = {
            'month-of-year': lambda r: r.find(".//worksheet[@name='Trend']//column-instance[@derivation='None']").set('derivation', 'Month'),
            'wrong-window': lambda r: r.find("datasources/datasource/column[@caption='Rolling Average']/calculation").set('formula', 'WINDOW_AVG(SUM([Sales]),-1,0)'),
            'wrong-addressing': lambda r: r.find(".//worksheet[@name='Trend']//column-instance/table-calc").set('ordering-type', 'Columns'),
            'partition-reset': lambda r: r.find(".//worksheet[@name='Trend']//column-instance/table-calc").set('level-break', '[Sub-Category]'),
            'early-date-filter': lambda r: r.find(".//worksheet[@name='Trend']/table/view/filter").set('column', '[Is Month Selected?]'),
            'keep-date-on-clear': lambda r: r.find('actions/edit-parameter-action/clear-option').set('type', 'do-nothing'),
        }
        for name, mutate in mutations.items():
            changed = deepcopy(root)
            mutate(changed)
            try:
                contracts(changed)
            except AssertionError:
                pass
            else:
                raise AssertionError('Verifier missed mutation: ' + name)
        report['rejected_mutations'] = list(mutations)
        report['observed_months_per_subcategory'] = {c: len({m for m,k,_ in rows if k == c}) for c in sorted({r[1] for r in rows})}
        report['sparse_month_policy'] = 'Observed monthly marks, without requested date domain padding; confirm Copiers/Machines in Tableau runtime.'
        hname = next(n for n in archive.namelist() if n.endswith('.hyper'))
        hyper = Path(tmp) / 'packaged.hyper'
        hyper.write_bytes(archive.read(hname))
        assert sha(hyper) == sha(HERE / 'inputs/federated_0dg8n3q1ypgh2719qo5qk1.hyper')
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={'log_config': ''}) as process:
            with Connection(process.endpoint, str(hyper)) as connection:
                assert connection.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"') == 9994
                scenarios = [
                    ('initial', SENTINEL, SENTINEL, None),
                    ('zoom-jun-sep-2018', date(2018,6,1), date(2018,9,1), None),
                    ('single-month', date(2018,6,1), date(2018,6,1), None),
                    ('first-two-months', date(2018,1,1), date(2018,2,1), None),
                    ('year-boundary', date(2019,12,1), date(2020,2,1), None),
                    ('last-month', date(2021,12,1), date(2021,12,1), None),
                    ('noncontiguous-selection-envelope', date(2018,6,1), date(2018,9,1), None),
                    ('multi-category', date(2018,6,1), date(2018,9,1), ['Chairs','Phones']),
                    ('clear-reset', SENTINEL, SENTINEL, None),
                    ('copiers-default-fixed-bounds', SENTINEL, SENTINEL, ['Copiers']),
                ]
                scenarios += [('category-' + c.lower(), date(2018,6,1), date(2018,9,1), [c]) for c in sorted({r[1] for r in rows})]
                # acceptance: numerical-oracle
                # acceptance: rolling-boundary
                for name, start, end, categories in scenarios:
                    trend, bars, lo, hi = oracle(rows, start, end, categories)
                    condition = 'TRUE' if not categories else '"Sub-Category" IN (' + ','.join("'" + c.replace("'", "''") + "'" for c in categories) + ')'
                    preceding = report['contracts']['window_preceding']
                    sql = f'''WITH monthly AS (
                        SELECT CAST(DATE_TRUNC('month',"Order Date") AS DATE) AS m, SUM("Sales") AS sales
                        FROM "Extract"."Extract" WHERE {condition} GROUP BY 1
                    ), rolling AS (
                        SELECT m, sales, AVG(sales) OVER (ORDER BY m ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS avg_sales FROM monthly
                    ) SELECT m,sales,avg_sales FROM rolling
                      WHERE m BETWEEN DATE '{lo}' AND DATE '{hi}' ORDER BY m'''
                    actual = connection.execute_list_query(sql)
                    close(actual, trend)
                    n = (hi.year-lo.year)*12+hi.month-lo.month+1
                    bar_sql = f'''SELECT "Sub-Category", SUM("Sales"), SUM("Sales")/{n}.0
                        FROM "Extract"."Extract" WHERE DATE_TRUNC('month',"Order Date") BETWEEN DATE '{lo}' AND DATE '{hi}'
                        GROUP BY 1 ORDER BY 2 DESC, 1'''
                    close(connection.execute_list_query(bar_sql), bars)
                    report['scenarios'].append({'id': name, 'start': str(lo), 'end': str(hi), 'categories': categories,
                        'trend': [[m, str(s), str(a)] for m,s,a in trend],
                        'bars': [[c, str(s), str(a)] for c,s,a in bars], 'status': 'pass'})
                # Counterexample rejects early date filtering at the first retained month.
                zoom, _, _, _ = oracle(rows, date(2018,6,1), date(2018,9,1))
                assert zoom[0][2] == Decimal('28846.2532')
                assert zoom[0][1] == Decimal('34595.1276')
                assert zoom[0][1] != zoom[0][2]
                report['early_filter_counterexample'] = {'month': '2018-06-01', 'correct_average': str(zoom[0][2]), 'incorrect_early_filter_average': str(zoom[0][1])}
                # A month-of-year partition destroys cross-year and chronological values.
                first, _, _, _ = oracle(rows, SENTINEL, SENTINEL)
                assert first[0][2] == Decimal('14236.895') and first[1][2] == Decimal('9378.3935')
                assert len(first) == 48 and first[12][0] == '2019-01-01'
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/local-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: XSD, generated contracts, {len(report["scenarios"])} SQL/Decimal scenarios; Desktop/Cloud NOT RUN')


if __name__ == '__main__':
    verify()
