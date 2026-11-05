"""Verify frozen WW34 Cloud exports against an independent raw-game counter.

Author Data contains only ARZ/ATL/BLT; its 720 rows are compared without
altering its original filter. Both replica sheets must contain all 7680 games.
"""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json
from tableauhyperapi import Connection, HyperProcess, Telemetry
HERE=Path(__file__).resolve().parent

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def integer(value):
    value=str(value).strip().replace(',','')
    return None if value in ('','Null','null') else int(value)
def boolean(value):
    value=str(value).strip().lower()
    if value in ('','null'):return None
    assert value in ('true','false'),value
    return value=='true'

def oracle():
    lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf8'))
    record=lock['extracted_data'][0]; path=HERE/record['file']; assert digest(path)==record['sha256']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint,path) as c:
        tables=c.catalog.get_table_names('Extract')
        qb=next(t for t in tables if 'qb_starters.csv_' in str(t)); teams=next(t for t in tables if 'NFL_Teams.csv_' in str(t))
        rows=c.execute_list_query(f'SELECT t.team,s.season,s.week,s.player_id FROM {qb} s JOIN {teams} t ON s.offense_franchise_id=t.franchise_id WHERE s.week BETWEEN 1 AND 17 ORDER BY t.team,s.season,s.week,s.player_id')
    grouped=defaultdict(list)
    for team,season,week,player in rows:grouped[team].append((season,week,player))
    result={}
    for team,games in grouped.items():
        previous=None;run=0;team_records=[]
        for index,(season,week,player) in enumerate(games,1):
            run=run+1 if player==previous else 1
            key=(team,season,week,player)
            assert key not in result
            result[key]={'Consecutive Streak':run,'INDEX':index,'Prev Player ID':previous,'Match Prev Player ID':None if previous is None else player==previous}
            team_records.append(result[key]); previous=player
        for rec in team_records:rec['Current Streak']=run
    assert len(result)==7680 and len(grouped)==32 and all(len(g)==240 for g in grouped.values())
    assert sum(result[(t,*g[-1])]['Current Streak'] for t,g in grouped.items())==563
    assert max(v['Consecutive Streak'] for v in result.values())==224
    return result,record['sha256']

def exports(role,artifact_hash):
    manifest=json.loads((HERE/f'evidence/{role}-data-exports.json').read_text(encoding='utf8'))
    assert manifest['artifact_sha256']==artifact_hash,f'{role} exports refer to stale workbook'
    result={}
    for record in manifest['exports']:
        if record['state']!='default':continue
        path=HERE/record['path']; assert digest(path)==record['sha256'],f'stale CSV hash: {path}'
        rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        result[record['view']]=(rows,record)
    return result

def keyed(rows):
    result={}
    for row in rows:
        key=(row.get('Team',row.get('team')),integer(row['Season']),integer(row['Week']),integer(row['Player Id']))
        assert key not in result,f'duplicate Cloud grain: {key}'
        result[key]=row
    return result

def compare(label,rows,expected,fields,full):
    actual=keyed(rows)
    assert set(actual)==set(expected) if full else set(actual)<=set(expected),f'{label}: game domain mismatch'
    checks=0
    for key,row in actual.items():
        for field in fields:
            observed=boolean(row[field]) if field=='Match Prev Player ID' else integer(row[field])
            assert observed==expected[key][field],f'{label} {key} {field}: observed={observed}, expected={expected[key][field]}'
            checks+=1
    return actual,checks

def verify():
    expected,extract_hash=oracle(); replica=HERE/'outputs/replicated-workbook.twbx'; replica_hash=digest(replica)
    cloud=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf8'))
    assert cloud['source_hashes']['replica']==replica_hash,'Cloud image capture refers to stale replica'
    author=exports('author',cloud['source_hashes']['author']); generated=exports('replica',replica_hash)
    fields=['Consecutive Streak','Current Streak','INDEX','Prev Player ID','Match Prev Player ID']
    author_rows,n_author=compare('author Data',author['Data'][0],expected,fields,False)
    assert len(author_rows)==720 and {k[0] for k in author_rows}=={'ARZ','ATL','BLT'},'Unexpected original author Data scope'
    data,n_data=compare('replica Data',generated['Data'][0],expected,fields,True)
    viz,n_viz=compare('replica Viz',generated['Viz'][0],expected,fields[:3],True)
    for key,row in author_rows.items():
        for field in fields:
            norm=boolean if field=='Match Prev Player ID' else integer
            assert norm(row[field])==norm(data[key][field]),f'author/replica difference at {key} {field}'
    report={'status':'PASS','result':'PASS','artifact_sha256':replica_hash,'source_hashes':cloud['source_hashes'],'extract_sha256':extract_hash,'replica_games_per_sheet':7680,'author_data_games':720,'author_data_teams':['ARZ','ATL','BLT'],'numeric_and_boolean_checks':n_author+n_data+n_viz,'checks_by_view':{'author Data':n_author,'replica Data':n_data,'replica Viz':n_viz},'sum_current_streak':563,'max_streak':224,'independent_oracle':'Chronologically sort raw joined regular-season games; maintain previous player and running counter per team. No builder formulas imported.','scope':'Full replica Data/Viz vs raw Hyper oracle; original author Data three-team subset vs both oracle and replica. Original author workbook untouched.','csv_sources':[item[1] for views in [author,generated] for name,item in views.items() if name in ('Data','Viz')]}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(f"PASS: {report['numeric_and_boolean_checks']} Cloud field checks; replica 7680 games x 2 sheets, original author 720 games")
    return report
if __name__=='__main__':verify()
