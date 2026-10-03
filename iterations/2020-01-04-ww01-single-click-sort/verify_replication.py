"""Independent WW01 Hyper oracle and serialized interaction contracts.

REST states validate exported marks; no browser click execution is claimed.
"""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import unquote
import csv
import json
import math
import ast
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
STATES = [('default', ' Sales '), ('sales-per-order', ' Sales / Order '), ('profit-ratio', ' Profit Ratio ')]


def oracle():
    hyper = next((HERE / 'inputs').glob('*.hyper'))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(hyper)) as c:
        table = next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        rows = c.execute_list_query('SELECT "Sub-Category", "Order ID", "Sales", "Profit" FROM ' + str(table))
    grouped = defaultdict(list)
    for category, order, sales, profit in rows:
        grouped[category].append((order, float(sales), float(profit)))
    values = []
    for category, records in sorted(grouped.items()):
        sales = math.fsum(r[1] for r in records)
        profit = math.fsum(r[2] for r in records)
        orders = len({r[0] for r in records})
        values.append({'sub_category': category, 'rows': len(records), 'orders': orders,
                       'sales': sales, 'profit': profit, 'sales_per_order': sales / orders,
                       'profit_ratio': profit / sales})
    assert len(rows) == 9994 and len(values) == 17
    assert [v['sub_category'] for v in values if v['profit_ratio'] < 0] == ['Bookcases', 'Supplies', 'Tables']
    assert math.isclose(sum(v['sales'] for v in values), 2297200.8603, abs_tol=1e-7)
    orders = {state: [v['sub_category'] for v in sorted(values, key=lambda v: (-v[key], v['sub_category']))]
              for (state, _), key in zip(STATES, ['sales', 'sales_per_order', 'profit_ratio'])}
    assert orders['default'][0] == 'Phones'
    assert orders['sales-per-order'][0] == 'Copiers'
    assert orders['profit-ratio'][0] == 'Labels'
    return {'row_count': len(rows), 'subcategories': values, 'descending_order': orders}


def verify_cloud(data):
    """Validate complete table CSVs and active sorting values."""
    expected = {v['sub_category']: v for v in data['subcategories']}
    checks = []
    for state, parameter in STATES:
        suffix = '' if state == 'default' else '-' + state
        for role in ['author', 'replica']:
            path = HERE / f'outputs/cloud-{role}-table{suffix}.csv'
            if not path.exists():
                continue
            with path.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 51, (path, len(rows))
            counts = {k: sum(r['Sub-Category'] == k for r in rows) for k in expected}
            assert set(counts.values()) == {3}
            assert {r['Sub-Category'] for r in rows} == set(expected)
            metric_keys = {'Sales': 'sales', 'Sales / Order': 'sales_per_order', 'Profit Ratio': 'profit_ratio'}
            verified = []
            for row in rows:
                value = expected[row['Sub-Category']]
                for caption, key in metric_keys.items():
                    col = next((k for k in row if k.strip() == caption), None)
                    assert col is not None, (path, caption, list(row))
                    text = row[col].replace(',', '').replace('$', '').strip()
                    actual = float(text.rstrip('%')) / (100 if text.endswith('%') else 1)
                    # Cloud formatting may round currency to whole dollars and ratio to 1 decimal percent.
                    decimals = len(text.rstrip('%').split('.', 1)[1]) if '.' in text else 0
                    tolerance = (0.5 * 10 ** -decimals) / (100 if text.endswith('%') else 1) + 1e-8
                    assert abs(actual - value[key]) <= tolerance, (path, value['sub_category'], key, actual, value[key])
                if role == 'replica':
                    key = {'default': 'sales', 'sales-per-order': 'sales_per_order', 'profit-ratio': 'profit_ratio'}[state]
                    sort_value = float(row['Sort By'].replace(',', ''))
                    assert math.isclose(sort_value, value[key], rel_tol=1e-9, abs_tol=1e-8)
                verified.append(row['Sub-Category'])
            expected_order = data['descending_order'][state]
            order_match = verified == expected_order
            checks.append({'role': role, 'state': state, 'parameter': parameter,
                           'file': path.relative_to(HERE).as_posix(), 'sha256': sha256(path.read_bytes()).hexdigest(),
                           'rows': len(rows), 'subcategories': verified, 'csv_order_matches_visible_sort': order_match,
                           'csv_order_used_as_visual_sort_proof': False, 'marks_per_subcategory': 3})
    if (HERE / 'evidence/cloud-verification.json').exists():
        assert len(checks) == 6, 'Both workbook tables must export every sort state'
    if checks:
        report = {'status': 'pass', 'scope': 'Complete 17 subcategories x 3 pane marks per table export; all three metrics and replica sort values verified. CSV row order is not used as proof of visual sort. Header/button CSVs are not matrix proof.',
                  'checks': checks, 'browser_interaction_executed': False}
        (HERE / 'evidence/cloud-data-comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return checks


def verify():
    # blank-sdk-build
    builder = ast.parse((HERE / 'build_replication.py').read_text(encoding='utf-8'))
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'TWBEditor' and len(n.args) == 1 and isinstance(n.args[0], ast.Constant) and n.args[0].value == '' for n in ast.walk(builder))
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(builder))
    # locked-superstore-source
    output = HERE / 'outputs/replicated-workbook.twbx'
    lock = json.loads((HERE / 'inputs/source-lock.json').read_text(encoding='utf-8'))
    with ZipFile(output) as archive:
        root = etree.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.twb'))))
        for item in lock['extracted_data']:
            p = HERE / item['file']
            assert sha256(p.read_bytes()).hexdigest() == item['sha256']
            assert sha256(archive.read(next(n for n in archive.namelist() if Path(n).name == p.name))).hexdigest() == item['sha256']
    sheets = root.findall('worksheets/worksheet')
    assert len(sheets) == 2
    header = next(s for s in sheets if s.get('name').startswith('Header'))
    table = next(s for s in sheets if s.get('name').startswith('Table'))
    dashboard = root.find('dashboards/dashboard')
    size = dashboard.find('size')
    assert size.get('maxwidth') == '700' and size.get('maxheight') == '900'
    ds = next(d for d in root.findall('datasources/datasource') if d.get('name') != 'Parameters')
    fields = {c.get('caption', c.get('name')): c for c in ds.findall('column')}
    formulas = {name: col.find('calculation').get('formula') for name, col in fields.items() if col.find('calculation') is not None}
    for name, formula in list(formulas.items()):
        for caption, col in fields.items():
            if col.get('caption'):
                formula = formula.replace(col.get('name'), '[' + caption + ']')
        formulas[name] = formula
    # three-metric-table
    compact = lambda s: ''.join(s.split()).upper()
    assert compact(formulas['Sales / Order']) == 'SUM([SALES])/COUNTD([ORDERID])'
    assert compact(formulas['Profit Ratio']) == 'SUM([PROFIT])/SUM([SALES])'
    assert compact(formulas['Negative Profit']) == '[PROFITRATIO]<0'
    for term in ['SUM([Sales])', '[Sales / Order]', '[Profit Ratio]']:
        assert term in formulas['Sort By']
    sort = table.find('table/view/shelf-sorts/shelf-sort-v2')
    assert sort.get('direction') == 'DESC'
    assert 'Sub-Category' in sort.get('dimension-to-sort')
    assert fields['Sort By'].get('name').strip('[]') in sort.get('measure-to-sort-by')
    # header-single-click-sort / artifact-action-clear-contract
    actions = root.findall('actions/edit-parameter-action')
    assert len(actions) == 1
    action = actions[0]
    assert action.find('activation').get('type') == 'on-select'
    assert action.find('source').get('worksheet') == header.get('name')
    assert action.find('source').get('dashboard') == dashboard.get('name')
    params = {p.get('name'): p.get('value') for p in action.findall('params/param')}
    assert params['source-field'] == '[' + ds.get('name') + '].[:Measure Names]'
    parameter = root.find('datasources/datasource[@name="Parameters"]/column[@caption="Sort (copy)"]')
    assert parameter.get('value') == '" Sales "'
    assert params['target-parameter'] == '[Parameters].' + parameter.get('name')
    clear = action.find('clear-option')
    assert clear is None or clear.get('type') == 'do-nothing'
    assert any('▼' in formula for formula in formulas.values())
    for pane, caption in zip(header.findall('table/panes/pane'), [v for _, v in STATES]):
        token = fields[caption].get('name').strip('[]')
        assert token in pane.get('x-axis-name'), 'Header must bind the spaced-caption zero calculation, not the physical sales measure'
    assert any(p.find('mark').get('class') == 'Bar' for p in table.findall('table/panes/pane'))
    filters = root.findall('actions/action')
    assert len(filters) == 1
    reset = filters[0]
    assert reset.find('activation').get('type') == 'on-select'
    assert reset.find('activation').get('auto-clear') == 'true'
    assert reset.find('source').get('worksheet') == header.get('name')
    assert reset.find('command/param[@name="target"]').get('value') == header.get('name')
    link = unquote(reset.find('link').get('expression'))
    assert fields['True'].get('name') in link and fields['False'].get('name') in link
    provenance_path = HERE / 'evidence/export-provenance.json'
    if provenance_path.exists():
        provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
        original_hash = lock.get('source_workbook', {}).get('sha256', lock.get('locked_original_sha256'))
        assert provenance['original_sha256'] == original_hash
        assert provenance['comparison_used_by_replica_builder'] is False
        cloud_path = HERE / 'evidence/cloud-verification.json'
        if cloud_path.exists():
            cloud = json.loads(cloud_path.read_text(encoding='utf-8'))
            assert cloud['source_hashes']['author'] == provenance['comparison_sha256']
            assert cloud['source_hashes']['replica'] == sha256(output.read_bytes()).hexdigest()
    # independent-subcategory-oracle
    data = oracle()
    data.update({'status': 'pass', 'artifact_sha256': sha256(output.read_bytes()).hexdigest(),
                 'browser_interaction_executed': False,
                 'interaction_scope': 'Serialized select event, header source, parameter target and keep-current clear behavior; REST states do not execute clicks.'})
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/functional-verification.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    # cloud-rest-sort-states
    verify_cloud(data)
    print('PASS: WW01 locked Hyper, 17-subcategory independent metrics/sort oracle and serialized select action')
    return data


if __name__ == '__main__':
    verify()
