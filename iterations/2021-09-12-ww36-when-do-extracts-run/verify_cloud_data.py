"""Compare Cloud Gantt exports with original Data CSV and locked raw tasks.

Duplicate CSV headers and separate waiting/processing pane rows are merged
without dropping nonempty values. --allow-stale diagnoses an earlier capture;
such a run records STALE, never PASS for the currently built artifact.
"""
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import csv
import hashlib
import json
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
NOW = datetime(2021, 2, 5, 16, 30)
STATES = {'default': 5, 'three-days': 3, 'ten-days': 10}
TOLERANCE_DAYS = 1e-9  # CSV decimal precision; less than 0.0001 seconds.

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def raw_tasks():
    lock = json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
    item = lock['extracted_data'][0]
    path = HERE/item['file']
    assert digest(path) == item['sha256']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, str(path)) as c:
            data = c.execute_list_query('SELECT "id", "Site", "title", "created_at", "started_at", "completed_at", "finish_code", "progress" FROM "Extract"."Extract"')
    result = {}
    for ident, site, title, created, started, completed, finish, progress in data:
        created = created.to_datetime()
        started = started.to_datetime() if started else None
        completed = completed.to_datetime() if completed else None
        status = 'In Progress' if finish == 1 and progress != 100 else ('Success' if finish == 0 and progress != 1 else 'Failed')
        # Tableau DATEDIFF('second') counts crossed second boundaries, ignoring
        # any subsecond fractions. These records currently have whole seconds.
        wait = ((started or NOW).replace(microsecond=0)-created.replace(microsecond=0)).total_seconds()/86400
        run = ((completed or NOW).replace(microsecond=0)-started.replace(microsecond=0)).total_seconds()/86400 if started else None
        result[str(ident)] = dict(site=site, title=title, created=created, started=started, completed=completed, status=status, wait=wait, run=run)
    assert len(result) == 34202
    return result

def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for values in reader:
            merged = {}
            for name, value in zip(headers, values):
                name = name.strip()
                if value:
                    assert name not in merged or merged[name] == value, (path.name, name, merged.get(name), value)
                    merged[name] = value
            yield merged

def close(actual, expected, where):
    assert abs(float(actual)-expected) <= TOLERANCE_DAYS, (where, actual, expected)

def parse_date(text):
    return datetime.strptime(text, '%m/%d/%Y %I:%M:%S %p')

def verify(allow_stale=False):
    tasks = raw_tasks()
    replica = json.loads((HERE/'evidence/replica-data-exports.json').read_text(encoding='utf-8'))
    author = json.loads((HERE/'evidence/author-data-exports.json').read_text(encoding='utf-8'))
    capture = json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
    artifact = digest(HERE/'outputs/replicated-workbook.twbx')
    stale = artifact != replica['artifact_sha256'] or artifact != capture['source_hashes']['replica']
    assert not stale or allow_stale, 'Capture/export hash does not match frozen replica; recapture before accepting'
    assert author['artifact_sha256'] == capture['source_hashes']['author']
    records = []
    checks = 0
    evidence_hashes = {}
    for state, days in STATES.items():
        a = next(e for e in author['exports'] if e['state'] == state and e['view'] == 'Data')
        r = next(e for e in replica['exports'] if e['state'] == state and e['view'] == 'Gantt')
        for entry in (a, r):
            assert digest(HERE/entry['path']) == entry['sha256']
            evidence_hashes[entry['path']] = entry['sha256']
        # The original author's supporting Data sheet has no Site/day filters.
        # Verify all original tasks independently before selecting Gantt scope.
        author_values = {}
        for row in read_rows(HERE/a['path']):
            ident = row['Id'].replace(',', '')
            raw = tasks[ident]
            measure = row['Measure Names'].strip()
            assert measure in ('Waiting Time', 'Processing Time')
            key = 'wait' if measure == 'Waiting Time' else 'run'
            value = float(row['Measure Values'])
            close(value, raw[key], (state, ident, key, 'author'))
            assert parse_date(row['Created At']) == raw['created']
            if raw['started'] is not None:
                assert parse_date(row['Started At']) == raw['started']
            if raw['completed'] is not None:
                assert parse_date(row['Completed At']) == raw['completed']
            assert parse_date(row['Created At Baseline']) == raw['created'].replace(year=2021, month=1, day=1)
            assert key not in author_values.setdefault(ident, {})
            author_values[ident][key] = value
            checks += 1
        assert set(author_values) == set(tasks)
        assert all(set(v) == {'wait', 'run'} for v in author_values.values())
        cutoff = NOW.date()-timedelta(days=days-1)
        expected = {i: v for i, v in tasks.items() if v['site'] == 'Site 9' and v['created'].date() >= cutoff}
        actual = {}
        for row in read_rows(HERE/r['path']):
            ident = row['Id'].replace(',', '')
            merged = actual.setdefault(ident, {})
            for name, value in row.items():
                assert name not in merged or merged[name] == value, (state, ident, name, merged.get(name), value)
                merged[name] = value
        assert set(actual) == set(expected), (state, len(actual), len(expected), set(actual)^set(expected))
        for ident, row in actual.items():
            raw = expected[ident]
            assert row['Site'] == raw['site'] and row['Title'] == raw['title']
            assert row['Extract Status'] == raw['status'], (state, ident, row['Extract Status'], raw['status'])
            assert row['Over Wait Time Threshold'].lower() == str(raw['wait'] > .007).lower()
            assert datetime.strptime(row['Day of Created At'], '%a %d %b %Y').date() == raw['created'].date()
            for measure, key in [('Avg. Waiting Time','wait'), ('Avg. Processing Time','run')]:
                close(row[measure], raw[key], (state, ident, measure, 'raw'))
                close(row[measure], author_values[ident][key], (state, ident, measure, 'author'))
                checks += 2
        records.append({'state':state,'days':days,'tasks':len(actual),'author_tasks':len(author_values),'status':'PASS','statuses':{s:sum(v['status']==s for v in expected.values()) for s in ['Success','Failed','In Progress']}})
    result = {'result':'STALE' if stale else 'PASS','artifact_sha256':artifact,'export_artifact_sha256':replica['artifact_sha256'],'source_hashes':capture['source_hashes'],'numeric_checks':checks,'states':records,'evidence_hashes':evidence_hashes,'tolerance_days':TOLERANCE_DAYS,'acceptance_scope':'Cloud REST states; all task IDs, durations, status, threshold, title/site/day vs locked raw tasks; original Data durations independently reconciled. No browser clicks claimed.'}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['result'], checks, 'numeric checks;', ', '.join(f"{x['state']}={x['tasks']} tasks" for x in records))
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-stale',action='store_true')
    verify(parser.parse_args().allow_stale)
