"""Verify locked order-time data, native small multiples and independent marks."""
from collections import defaultdict
from datetime import date
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import csv
import calendar
import ast
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent


def verify_cloud(data):
    checks = []
    for mode, sheet, suffix in [('Weeks', 'by-weekday', ''), ('Days', 'by-day', '-days')]:
        expected = data['states'][mode]
        circle_oracle = {(m['month'], m['x'], m['hour']): m['orders'] for m in expected['circle_marks']}
        span_oracle = {(m['month'], m['x']): (m['max_hour'], m['negative_range']) for m in expected['gantt_spans']}
        for role in ['author', 'replica']:
            path = HERE / f'outputs/cloud-{role}-{sheet}{suffix}.csv'
            with path.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            assert rows, (path, 'Empty active-state CSV cannot establish acceptance')
            circles, spans = {}, {}
            for row in rows:
                month = list(calendar.month_name).index(row['Month of Order Date'])
                x = int(row['Day of Order Date']) if mode == 'Days' else ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index(row['Weekday of Order Date']) + 1
                assert int(row['Month Column']) == (month - 1) % 3 + 1
                assert row['Quarter of Order Date'] == 'Q' + str((month - 1) // 3 + 1)
                if row.get('Hour of Order'):
                    key = (month, x, int(row['Hour of Order']))
                    value = int(row['Distinct count of Order ID'])
                    assert key not in circles and circle_oracle[key] == value, (path, key, value)
                    circles[key] = value
                else:
                    max_field = 'Max Hour Per Day of Month' if mode == 'Days' else 'Max Hour PerWeekday of Month'
                    size_field = next(k for k in row if k.startswith('Negative Range') or k.startswith('MIN([Time Range'))
                    value = (int(row[max_field]), int(row[size_field]))
                    key = (month, x)
                    assert key not in spans and span_oracle[key] == value, (path, key, value)
                    spans[key] = value
            assert circles == circle_oracle and spans == span_oracle
            assert len(rows) == len(circles) + len(spans)
            checks.append({'role': role, 'parameter': mode, 'file': path.relative_to(HERE).as_posix(),
                           'sha256': sha256(path.read_bytes()).hexdigest(), 'rows': len(rows),
                           'circle_marks': len(circles), 'gantt_spans': len(spans)})
    # Empty opposite sheets are the expected parameter filter outcome.
    empty_checks = []
    for role in ['author', 'replica']:
        for sheet, suffix in [('by-day', ''), ('by-weekday', '-days')]:
            p = HERE / f'outputs/cloud-{role}-{sheet}{suffix}.csv'
            assert not p.read_text(encoding='utf-8-sig').strip(), (p, 'Inactive sheet should have no marks')
            empty_checks.append(p.relative_to(HERE).as_posix())
    report = {'status': 'pass', 'checks': checks, 'inactive_sheet_exports': empty_checks,
              'scope': 'Every latest-year circle (distinct order count) and every month/day or month/weekday min-max Gantt span in both active selectors; inactive sheets explicitly empty.',
              'browser_interaction_executed': False}
    (HERE / 'evidence/cloud-data-comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(next((HERE / 'inputs').glob('*.hyper')))) as c:
        table = next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s))
        rows = c.execute_list_query('SELECT "Order Date", "Order ID", "Time of Order" FROM ' + str(table))
    latest = max(d.year for d, _, _ in rows)
    selected = [(date(d.year, d.month, d.day), order, int(time.split(':')[0])) for d, order, time in rows if d.year == latest]
    assert len(rows) == 9994 and latest == 2019 and len(selected) == 3312
    assert len({order for _, order, _ in selected}) == 1687
    # Tableau's datasource uses Sunday as weekday 1.
    states = {}
    for mode in ['Days', 'Weeks']:
        circles = defaultdict(set)
        ranges = defaultdict(list)
        for d, order, hour in selected:
            assert 0 <= hour <= 23
            x = d.day if mode == 'Days' else (d.weekday() + 1) % 7 + 1
            circles[(d.month, x, hour)].add(order)
            ranges[(d.month, x)].append(hour)
        marks = [{'month': m, 'quarter': (m - 1) // 3 + 1, 'month_column': (m - 1) % 3 + 1, 'x': x, 'hour': h, 'orders': len(orders)} for (m, x, h), orders in sorted(circles.items())]
        spans = [{'month': m, 'x': x, 'min_hour': min(hours), 'max_hour': max(hours), 'negative_range': min(hours) - max(hours)} for (m, x), hours in sorted(ranges.items())]
        assert {v['month'] for v in marks} == set(range(1, 13))
        assert all(v['orders'] > 0 for v in marks)
        assert sum(v['orders'] for v in marks) == 1687
        assert all(v['negative_range'] <= 0 for v in spans)
        states[mode] = {'circle_marks': marks, 'gantt_spans': spans, 'circle_count': len(marks), 'span_count': len(spans)}
    return {'source_rows': len(rows), 'latest_year': latest, 'latest_year_rows': len(selected), 'latest_year_orders': 1687, 'states': states}


def verify():
    # blank-sdk-build
    builder = ast.parse((HERE / 'build_replication.py').read_text(encoding='utf-8'))
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'TWBEditor' and len(n.args) == 1 and isinstance(n.args[0], ast.Constant) and n.args[0].value == '' for n in ast.walk(builder))
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(builder))
    # locked-joined-order-times
    output = HERE / 'outputs/replicated-workbook.twbx'
    lock = json.loads((HERE / 'inputs/source-lock.json').read_text(encoding='utf-8'))
    with ZipFile(output) as archive:
        root = etree.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.twb'))))
        for item in lock['extracted_data']:
            p = HERE / item['file']
            assert sha256(p.read_bytes()).hexdigest() == item['sha256']
            assert sha256(archive.read(next(n for n in archive.namelist() if Path(n).name == p.name))).hexdigest() == item['sha256']
    assert {s.get('name') for s in root.findall('worksheets/worksheet')} == {'By Day', 'By Weekday'}
    ds = next(d for d in root.findall('datasources/datasource') if d.get('name') != 'Parameters')
    assert ds.find('date-options').get('start-of-week') == 'sunday'
    columns = {c.get('caption'): c for c in ds.findall('column') if c.get('caption')}
    formulas = {name: c.find('calculation').get('formula') for name, c in columns.items() if c.find('calculation') is not None}
    for name, formula in list(formulas.items()):
        for caption, col in columns.items():
            formula = formula.replace(col.get('name'), '[' + caption + ']')
        formulas[name] = formula
    # latest-year-small-multiples / native-hour-range-gantt
    assert formulas['Hour of Order'] == 'INT(TRIM(SPLIT([Time of Order], ":", 1)))'
    assert formulas['Latest Year'] == 'YEAR([Order Date]) = {FIXED: MAX(YEAR([Order Date]))}'
    assert formulas['Max Hour Per Day of Month'] == '{FIXED [Order Date]: MAX([Hour of Order])}'
    assert formulas['Min Hour Per Day of Month'] == '{FIXED [Order Date]: MIN([Hour of Order])}'
    for name in ['Max Hour PerWeekday of Month', 'Min Hour PerWeekday of Month']:
        assert "DATEPART('weekday',[Order Date]), MONTH([Order Date]), YEAR([Order Date])" in formulas[name]
    assert formulas['Time Range Days'] == '[Max Hour Per Day of Month]-[Min Hour Per Day of Month]'
    assert formulas['Time Range Weekdays'] == '[Max Hour PerWeekday of Month]-[Min Hour PerWeekday of Month]'
    for mode in ['Days', 'Weekdays']:
        assert formulas['Negative Range ' + mode] == 'MIN([Time Range ' + mode + '])*-1'
    # days-weekdays-selector
    parameter = root.find('datasources/datasource[@name="Parameters"]/column[@caption="Time Selector"]')
    assert parameter.get('value') == '"Weeks"'
    assert {m.get('value') for m in parameter.findall('members/member')} == {'"Days"', '"Weeks"'}
    for sheet_name, expected_value in [('By Day', 'true'), ('By Weekday', 'false')]:
        sheet = root.find('worksheets/worksheet[@name="' + sheet_name + '"]')
        assert 'qr:Order Date:ok' in sheet.findtext('table/rows')
        assert columns['Month Column'].get('name').strip('[]') in sheet.findtext('table/cols')
        expected_datepart = 'Day' if sheet_name == 'By Day' else 'Weekday'
        assert sheet.find('table/view/datasource-dependencies/column-instance[@column="[Order Date]"][@derivation="' + expected_datepart + '"]') is not None
        switch = columns['Time Selected is Days'].get('name').strip('[]')
        filters = sheet.findall('table/view/filter')
        latest_instance = sheet.find('table/view/datasource-dependencies/column-instance[@column="' + columns['Latest Year'].get('name') + '"]')
        assert latest_instance.get('derivation') == 'None', 'Latest-year LOD comparison is row-level, not an aggregate calculation'
        filter_node = next(f for f in filters if switch in f.get('column'))
        assert filter_node.find('groupfilter').get('member') == expected_value
        assert any(columns['Latest Year'].get('name').strip('[]') in f.get('column') and f.find('groupfilter').get('member') == 'true' for f in filters)
        panes = sheet.findall('table/panes/pane')
        assert len(panes) == 2
        assert [p.find('mark').get('class') for p in panes] == ['Circle', 'GanttBar']
        assert all(p.find('mark-sizing').get('mark-sizing-setting') == 'marks-scaling-off' for p in panes)
        # native-order-count-circles
        assert 'cntd:Order ID:qk' in panes[0].find('encodings/color').get('column')
        assert 'cntd:Order ID:qk' in panes[0].find('encodings/size').get('column')
        assert 'Negative Range' in next(c.get('caption') for c in sheet.findall('table/view/datasource-dependencies/column') if c.get('name').strip('[]') in panes[1].find('encodings/size').get('column'))
        axes = sheet.findall('table/style/style-rule[@element="axis"]/encoding')
        assert any(a.get('reverse') == 'true' and a.get('major-spacing') == '5' for a in axes)
        assert any(a.get('fold') == 'true' and a.get('synchronized') == 'true' for a in axes)
        # dotted-linear-trendline
        assert panes[0].find('trendline').get('fit') == 'linear'
        assert panes[0].find('trendline').get('enabled') == 'true'
        assert panes[0].find('style/style-rule[@element="trendline"]/format[@attr="line-pattern-only"]').get('value') == 'dotted'
    size = root.find('dashboards/dashboard/size')
    assert size.get('maxwidth') == '1200' and size.get('maxheight') == '800'
    # independent-full-hour-oracle
    data = oracle()
    data.update({'status': 'pass', 'artifact_sha256': sha256(output.read_bytes()).hexdigest(), 'browser_interaction_executed': False,
                 'scope': 'Independent latest-year distinct-order circle marks and daily/weekday min-max Gantt spans across every month; serialized selector filters, axes and panes.'})
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/functional-verification.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    if (HERE / 'evidence/cloud-verification.json').exists():
        cloud = json.loads((HERE / 'evidence/cloud-verification.json').read_text(encoding='utf-8'))
        assert cloud['source_hashes']['replica'] == sha256(output.read_bytes()).hexdigest(), 'Cloud evidence must match final artifact'
        provenance = json.loads((HERE / 'evidence/export-provenance.json').read_text(encoding='utf-8'))
        assert provenance['original_sha256'] == lock['locked_original_sha256']
        assert provenance['comparison_sha256'] == cloud['source_hashes']['author']
        assert provenance['comparison_used_by_replica_builder'] is False
        # cloud-rest-day-weekday-matrices
        verify_cloud(data)
    print('PASS: WW03 locked joined data, latest year, day/week circles and full-month min/max range oracle')
    return data


if __name__ == '__main__':
    verify()
