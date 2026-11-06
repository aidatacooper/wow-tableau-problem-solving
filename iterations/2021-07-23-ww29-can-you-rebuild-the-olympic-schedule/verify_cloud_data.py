"""Verify published schedule marks against locked event rows for three offsets."""
import csv, datetime as dt, hashlib, json
from collections import Counter
from pathlib import Path
from tableauhyperapi import Connection,HyperProcess,Telemetry
from verify_replication import is_victory,is_final,x_axis,INITIAL_SET
HERE=Path(__file__).resolve().parent
def main():
    lock=json.loads((HERE/'inputs/source-lock.json').read_text())['extracted_data'][0]
    source=HERE/lock['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==lock['sha256']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint,str(source)) as c:
        rows=c.execute_list_query('SELECT "Sport Group","Events Split","UK Date Time","Sport" FROM "Extract"."Extract"')
    report=json.loads((HERE/'evidence/replica-data-exports.json').read_text())
    count=0
    for state,offset in [('default',0),('plus3',3),('minus5',-5)]:
        adjusted=[]
        for g,e,date,sport in rows:
            if is_victory(e): continue
            shifted=date+dt.timedelta(hours=offset)
            adjusted.append((g,e,dt.date(shifted.year,shifted.month,shifted.day),sport))
        totals=Counter(day for g,e,day,s in adjusted)
        events=Counter((day,s) for g,e,day,s in adjusted)
        finals=Counter((day,s) for g,e,day,s in adjusted if is_final(e))
        expected={(day,s,g,is_final(e)) for g,e,day,s in adjusted if g in INITIAL_SET}
        records=list(csv.DictReader((HERE/'outputs'/f'cloud-replica-date-chart-{state}.csv').open(encoding='utf-8-sig')))
        actual=set()
        for r in records:
            day=dt.datetime.strptime(r['Day of Adjusted Date'],'%m/%d/%Y').date()
            sport=r['Sport']; final=r['Is Final?']=='True'; key=(day,sport)
            actual.add((day,sport,r['Sport Group'],final))
            assert int(r['#Events by Sport Per Day'])==events[key],(state,r,events[key])
            assert int(r['#Event Finals by Sport Per Day'])==finals[key]
            assert int(r['#Events Per Day of Other Sports'])==totals[day]-events[key]
            assert int(r['X-Axis'])==x_axis(events[key],finals[key],final)
            count+=4
        assert actual==expected,(state,len(actual),len(expected),actual^expected)
        selectors=list(csv.DictReader((HERE/'outputs'/f'cloud-replica-sport-selector-{state}.csv').open(encoding='utf-8-sig')))
        assert {r['Sport Group'].casefold() for r in selectors}=={g.casefold() for g,e,d,s in rows}
        assert {r['Sport Group'] for r in selectors if r['In / Out of Sport Group Set']=='In'}==set(INITIAL_SET)
    sha=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    assert sha==report['artifact_sha256']
    result={'result':'PASS','states':3,'numeric_checks':count,'artifact_sha256':sha,'scope':'Default selected sports and selector domain; offsets 0,+3,-5 hours. Native action/VIT contracts checked separately. Original author dashboard images only; hidden sheets unmodified.'}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS Olympic Cloud',count,'numeric checks')
if __name__=='__main__':main()
