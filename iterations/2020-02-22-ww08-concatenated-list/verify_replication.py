"""Independent complete patient/list oracle and native table-calculation contracts."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
import ast
import csv
import json
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent


def verify():
    # blank-sdk-build; locked-patient-data; native-concatenated-list;
    # tablecalc-last-row-filter; patient-controls; independent-patient-oracle;
    # cloud-rest-patient-lists; cloud-visual-review
    source = (HERE / 'build_replication.py').read_text(encoding='utf-8')
    assert 'TWBEditor("")' in source
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(ast.parse(source)))
    lock = json.loads((HERE / 'inputs/source-lock.json').read_text())
    entry = lock['extracted_data'][0]
    data = HERE / entry['file']
    assert sha256(data.read_bytes()).hexdigest() == entry['sha256']
    artifact = HERE / 'outputs/replicated-workbook.twbx'
    digest = sha256(artifact.read_bytes()).hexdigest()
    with ZipFile(artifact) as z:
        root = etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        assert sha256(z.read(next(n for n in z.namelist() if n.endswith('.hyper')))).hexdigest() == entry['sha256']
    columns = {c.get('caption'): c for c in root.xpath('/workbook/datasources/datasource/column[@caption]')}
    assert columns['Index'].find('calculation').get('formula') == 'INDEX()'
    assert columns['Size'].find('calculation').get('formula') == 'SIZE()'
    assert 'PREVIOUS_VALUE' in columns['Health Check Name List'].find('calculation').get('formula')
    sheet = root.xpath('//worksheets/worksheet[@name="Report"]')[0]
    instances = sheet.xpath('./table/view/datasource-dependencies/column-instance')
    for name in ['Health Check Name List', 'Size', 'Index=Size?', 'FILTER:Health Check Names']:
        instance = next(c for c in instances if c.get('column') == columns[name].get('name'))
        assert instance.get('derivation')=='User', (name, instance.attrib)
        calculations = instance.findall('table-calc')
        assert calculations and all(c.get('ordering-type') == 'Field' and 'Health Check Name' in c.get('ordering-field', '') for c in calculations)
    assert len(sheet.xpath('./table/view/filter')) == 5
    assert sheet.xpath('./table/panes/pane/encodings/lod[contains(@column,"Health Check Name")]')
    assert len(root.xpath('//dashboards/dashboard//zone[@type-v2="filter"]')) == 3
    assert root.xpath('//dashboards/dashboard//zone[@type-v2="paramctrl"]')
    assert sheet.xpath('./table/style/style-rule[@element="header"]/format[@attr="width" and @value="420"]')
    assert sheet.xpath('./table/style/style-rule[@element="cell"]/format[@attr="height" and @value="53"]')
    assert root.xpath('//dashboards/dashboard//zone[@type-v2="filter" and @mode="dropdown"]')
    patients = defaultdict(set)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint, str(data)) as connection:
        records = connection.execute_list_query('SELECT "Member ID", "Member Name", "Gender", "Age Category", "Phone Number", "Physician", "Health Check Name" FROM "Extract"."Extract"')
    for row in records:
        patients[tuple(row[:6])].add(row[6])
    oracle = [{**dict(zip(['Member ID', 'Member Name', 'Gender', 'Age Category', 'Phone Number', 'Physician'], key)), 'Health Check Name List': ', '.join(sorted(values)), 'Size': len(values)} for key, values in sorted(patients.items())]
    assert max(r['Size'] for r in oracle)==9
    states = {'default': ('Adult BMI Assessment', None, None), 'all': ('All', None, None), 'flu': ('Annual Flu Vaccine', None, None), 'physician-age': ('All', 'Phil Flood', '65-69')}
    expected = {name: [r for r in oracle if (check == 'All' or check in r['Health Check Name List']) and (physician is None or r['Physician'] == physician) and (age is None or r['Age Category'] == age)] for name, (check, physician, age) in states.items()}
    report = {'status': 'pass', 'artifact_sha256': digest, 'input_rows': len(records), 'unique_patient_rows': len(oracle), 'states': {name: {'patient_rows':len(rows),'oracle_sha256':sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()} for name,rows in expected.items()}, 'browser_interaction_executed': False, 'scope': 'Independent complete patient profiles and concatenated distinct alphabetic checks; native INDEX/SIZE/PREVIOUS_VALUE and filter contracts. Full oracle recomputed from the locked Hyper input; evidence stores count/hash rather than duplicating 59,272 patient profiles.'}
    cloudpath = HERE / 'evidence/cloud-verification.json'
    if cloudpath.exists():
        cloud = json.loads(cloudpath.read_text())
        assert cloud['source_hashes']['replica'] == digest
        provenance = json.loads((HERE / 'evidence/export-provenance.json').read_text())
        assert cloud['source_hashes']['author'] == provenance['comparison_sha256']
        assert provenance['original_sha256'] == lock['locked_original_sha256']
        assert {s['name'] for s in cloud['states']}==set(states)
        checks = []
        for state in cloud['states']:
            for image in state['views'].values():
                assert sha256((HERE/image['path']).read_bytes()).hexdigest()==image['sha256']
            wanted = {str(r['Member ID']): r for r in expected[state['name']]}
            for capture in state['data']:
                path = HERE / capture['path']
                assert sha256(path.read_bytes()).hexdigest() == capture['sha256']
                with path.open(encoding='utf-8-sig', newline='') as f:
                    rows = list(csv.DictReader(f))
                assert rows, (path, 'Empty CSV')
                found = {}
                for row in rows:
                    key = row['Member ID'].replace(',', '')
                    assert key in wanted, (path, key)
                    for field in ['Member Name', 'Gender', 'Age Category', 'Phone Number', 'Physician', 'Health Check Name List']:
                        assert row[field] == wanted[key][field], (path, key, field, row[field], wanted[key][field])
                    assert key not in found, (path, 'Patient must appear exactly once', key)
                    found[key] = row
                assert set(found) == set(wanted), (path, len(found), len(wanted))
                checks.append({'file': capture['path'], 'patient_rows': len(found), 'status': 'pass'})
        assert len(checks)==8
        (HERE / 'evidence/cloud-data-comparison.json').write_text(json.dumps({'status': 'pass', 'checks': checks, 'scope': 'Complete patient report rows in each exported state, including entire comma-separated list.'}, indent=2), encoding='utf-8')
        report['cloud_checks'] = checks
    (HERE / 'evidence/functional-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS', len(records), 'input rows;', len(oracle), 'patient profiles;', {k: len(v) for k,v in expected.items()})


if __name__ == '__main__':
    verify()
