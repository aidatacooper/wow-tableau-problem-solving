"""Compare actual CSV columns against an independent Hyper oracle."""
from pathlib import Path
import argparse,csv,hashlib,json,math
from verify_replication import oracle
HERE=Path(__file__).resolve().parent

def number(value):
    return float(value.replace('$','').replace(',','').strip())

def compare(strict_workbook=False):
    contract=oracle(); results=[]; coordinate_results={}
    report=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
    if strict_workbook:
        assert hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()==report['source_hashes']['replica']
    for capture in report['states']:
        for record in capture['data']:
            path=HERE/record['path']; assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
            rows=list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))
            assert rows,'empty export'
            headers=list(rows[0]);state_col=next((h for h in headers if h.lower()=='state'),None)
            city_col=next((h for h in headers if h.lower()=='city'),None)
            sales_col=next((h for h in headers if h.lower() in ['sales','sum(sales)','sum of sales']),None)
            if state_col and not sales_col and 'Measure Names' in headers and 'Measure Values' in headers:
                global_ranks={row['state']:row['global_rank'] for row in contract['states']}
                out_ranks={row['state']:i+1 for i,row in enumerate(contract['selection_scenarios']['Oklahoma']['trellis'])}
                for row in rows:
                    measure=row['Measure Names']
                    if 'rank' in measure.lower():
                        expected=global_ranks[row[state_col]] if 'In / Out of Selected Set' in measure else (1 if row.get('In / Out of Selected Set')=='In' else out_ranks[row[state_col]])
                        assert int(number(row['Measure Values']))==expected, 'Author diagnostic rank'
                rows=[dict(row,Sales=row['Measure Values']) for row in rows if 'sales' in row['Measure Names'].lower() and 'rank' not in row['Measure Names'].lower() and row.get('In / Out of Selected Set','Out')=='Out']
                sales_col='Sales'
            assert state_col and sales_col, f'Unsupported exported scope: {headers}'
            state_totals={r['state']:r['sales'] for r in contract['states']}
            city_totals={r['city']:r['sales'] for r in contract['selection_scenarios']['Oklahoma']['cities']}
            verified={}
            for row in rows:
                state=row[state_col];city=row.get(city_col,'') if city_col else ''
                if not row[sales_col].strip():continue
                expected=city_totals[city] if city else state_totals[state]
                actual=number(row[sales_col]);tolerance=0.500001 if '$' in row[sales_col] else 1e-6
                assert math.isclose(actual,expected,abs_tol=tolerance), (record['role'],state,city,actual,expected)
                verified[(state,city)]=actual
            assert verified
            if any(city for _,city in verified):
                latitude_col=next(h for h in headers if h=='Latitude (generated)')
                longitude_col=next(h for h in headers if h=='Longitude (generated)')
                for row in rows:
                    if row.get(city_col,''):
                        assert row[latitude_col].strip() and row[longitude_col].strip(), 'geocoding returned blank generated coordinates'
                        assert 33<float(row[latitude_col])<38 and -104<float(row[longitude_col])<-94, 'Oklahoma generated coordinate bounds'
                        coordinate_results.setdefault(record['role'],{})[row[city_col]]=[float(row[latitude_col]),float(row[longitude_col])]
            scope='Selected State city marks' if any(city for _,city in verified) else 'State-level marks only'
            if scope=='Selected State city marks':
                assert set(city for _,city in verified if city)==set(city_totals)
                assert all(state=='Oklahoma' for state,_ in verified)
            else:
                assert set(state for state,_ in verified)==set(r['state'] for r in contract['selection_scenarios']['Oklahoma']['trellis']), 'Trellis must contain all 25 default OUT states'
                position_lookup={row['state']:row for row in contract['selection_scenarios']['Oklahoma']['trellis']}
                for row in rows:
                    for column,key in [('Cols','col'),('Rows','row'),('Label Rows','label_row')]:
                        if column in row and row[column].strip():
                            assert math.isclose(number(row[column]),position_lookup[row[state_col]][key],abs_tol=1e-9), 'Trellis position'
                global_rank_col=next((h for h in headers if h=='Global Rank'),None)
                if global_rank_col:
                    rank_lookup={r['state']:r['global_rank'] for r in contract['states']}
                    for row in rows:
                        if row[global_rank_col].strip():assert int(number(row[global_rank_col]))==rank_lookup[row[state_col]], 'Global rank label'
            results.append({'role':record['role'],'path':record['path'],'headers':headers,'raw_rows':len(rows),'unique_verified_marks':len(verified),'actual_scope':scope,'sha256':record['sha256'],'rounding_tolerance':tolerance})
    assert set(coordinate_results)=={'author','replica'}
    assert set(coordinate_results['author'])==set(coordinate_results['replica'])
    for city,point in coordinate_results['author'].items():
        assert all(math.isclose(a,b,abs_tol=1e-5) for a,b in zip(point,coordinate_results['replica'][city])), 'Author/replica city coordinate comparison'
    evidence={'status':'pass','city_coordinate_comparison':coordinate_results,'csvs':results,'browser_action_executed':False,'full_selection_matrix':'Independent Hyper oracle covers all 49 selections; this CSV does not prove all action states.'}
    (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print('PASS: actual Cloud CSV scope and every returned sales mark verified')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--strict-workbook',action='store_true');compare(p.parse_args().strict_workbook)
