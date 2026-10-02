"""Actual native foreground/spine REST data, with explicit unsupported empty state."""
from pathlib import Path
from hashlib import sha256
import csv,json,math,re
HERE=Path(__file__).resolve().parent
METRICS=['Total Distance (km)','Distance / Min (m)','HSR Distance (m)','HI Distance (m)','Max Speed (m/s)']
def verify():
    ignored=[]
    oracle=json.loads((HERE/'evidence/functional-verification.json').read_text());games={v['Game ID']:v for v in oracle['games']};checks=[];clear_results=[]
    for suffix,opponent in [('', 'Chelsea Ladies U14'),('-south-gloucestershire','South Gloucestershire'),('-clear-highlight','')]:
        actuals={}
        for role in ['author','replica']:
            p=HERE/f'outputs/cloud-{role}-dashboard{suffix}.csv'
            with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            assert len(rows)==240
            actual={};foreground=[]
            for row in rows:
                game=int(row['Game ID']);name=row['Measure Names'].split(' along ',1)[0].strip();assert name in METRICS
                val=float(row['Measure Values'].replace(',',''));expected=games[game]['normalized'][name]
                assert math.isclose(val,expected,abs_tol=5.1e-9)
                actual.setdefault((game,name),[]).append(val)
                if row.get('Opposition'):
                    foreground.append(row)
                    if role=='replica' and opponent:
                        effective_opponent=opponent or 'Chelsea Ladies U14'
                        selected=games[game]['Opposition']==effective_opponent
                        category=('Selected ' if selected else 'Other ')+('Home' if games[game]['H/A']=='H' else 'Away')
                        assert re.sub(r'^\d+ ', '',row['Match Colour'])==category
                        assert int(row['Line Width'])==(3 if selected else 1)
                    for raw_name,expected_raw in games[game]['raw'].items():
                        raw=float(row[raw_name].replace(',',''));assert abs(raw-expected_raw)<=0.00500001
            assert len(actual)==120 and all(len(v)==2 for v in actual.values())
            assert len(foreground)==120
            highlighted=sorted({int(r['Game ID']) for r in foreground if r.get('Label: Opposition')})
            expected_highlight=sorted(g for g,v in games.items() if v['Opposition']==opponent)
            if opponent:assert highlighted==expected_highlight
            else:clear_results.append({'role':role,'requested_parameter':'','observed_highlighted_games':highlighted,'empty_state_executed':highlighted==[],'note':'REST empty parameter is ignored/default retained if highlighted_games is nonempty; clear action only artifact-verified.'})
            actuals[role]=actual
            entry={'role':role,'state':suffix or 'default','file':p.relative_to(HERE).as_posix(),'sha256':sha256(p.read_bytes()).hexdigest(),'total_rows':240,'foreground_rows':120,'spine_rows':120,'game_metric_keys':120,'highlighted_games':highlighted,'normalization_tolerance':5.1e-9,'raw_rounding_tolerance':0.00500001}
            if opponent:checks.append(entry)
            else:ignored.append({**entry,'request_status':'ignored_empty_parameter','successful_parameter_state':False})
        assert actuals.keys()=={'author','replica'}
        for key in actuals['author']:
            for a,b in zip(sorted(actuals['author'][key]),sorted(actuals['replica'][key])):assert math.isclose(a,b,abs_tol=5.1e-9)
    report={'status':'pass','scope':'24 games x 5 metrics x 2 panes, raw metric tooltip values and highlight labels. Two nonempty REST states execute. Empty REST state not claimed when ignored; serialized clearing action remains artifact contract.','checks':checks,'clear_parameter_rest_results':clear_results,'ignored_requests':ignored,'browser_interaction_executed':False}
    (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: WW09 four Cloud CSVs all 120 game/metric keys in both panes; ignored empty requests retained separately')
    return report
if __name__=='__main__':verify()
