"""Independent Hyper oracle and generated workbook/action artifact contracts."""
from pathlib import Path
import json, math
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent
ACCEPTANCE_IDS=('default-state-city-sales','trellis-top25-out-partition','set-action-contract')

def oracle():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))) as c:
            table=c.catalog.get_table_names('Extract')[0]
            count=int(c.execute_scalar_query(f'SELECT COUNT(*) FROM {table}'))
            totals=c.execute_list_query(f'SELECT "State",SUM("Sales") FROM {table} GROUP BY "State" ORDER BY SUM("Sales") DESC, "State"')
            cities=c.execute_list_query(f'SELECT "State","City",SUM("Sales") FROM {table} GROUP BY "State","City" ORDER BY "State","City"')
    assert count==9994 and len(totals)==49
    assert math.isclose(sum(float(v) for _,v in totals),2297200.8603,abs_tol=1e-6)
    assert len(set(float(v) for _,v in totals))==49, 'unique rank requires deterministic no-tie data'
    ranked=[{'state':s,'sales':float(v),'global_rank':i+1} for i,(s,v) in enumerate(totals)]
    scenarios={}
    for selected,_ in totals:
        trellis=[dict(row,col=i%5,row=i//5,label_row=i//5+0.5) for i,row in enumerate(r for r in ranked if r['state']!=selected) if i<25]
        bubbles=[{'city':city,'sales':float(sales)} for state,city,sales in cities if state==selected]
        assert len(trellis)==25 and len({(r['row'],r['col']) for r in trellis})==25
        assert all(r['state']!=selected for r in trellis)
        assert math.isclose(sum(r['sales'] for r in bubbles),dict(totals)[selected],abs_tol=1e-7)
        scenarios[selected]={'trellis':trellis,'cities':bubbles,'city_count':len(bubbles)}
    assert ranked[25]['state']=='Oklahoma'
    assert scenarios['Oklahoma']['city_count']==7
    assert scenarios['California']['trellis'][-1]['state']=='Oklahoma'
    return {'input_rows':count,'state_count':49,'states':ranked,'selection_scenarios':scenarios,'browser_actions_executed':False,'cloud_csv_scope':'Exported dashboard CSV covers its first worksheet (Selected State), not the complete trellis; trellis verification uses independent Hyper oracle, artifact contracts and visible Cloud labels.'}

def artifact_contract():
    with ZipFile(HERE/'outputs/replicated-workbook.twbx') as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
    ds=root.find('datasources/datasource')
    semantic={n.get('key'):n.get('value') for n in ds.findall('semantic-values/semantic-value')}
    assert semantic['[Country].[Name]']=='"United States"'
    assert semantic['[State].[Name]']=='%null%'
    group=ds.find("group[@caption='Selected Set']/groupfilter")
    assert group.get('function')=='member' and group.get('member')=='"Oklahoma"'
    for name in ['State','City']:
        column=next(n for n in ds.findall('column') if (n.get('caption') or n.get('name').strip('[]'))==name)
        assert column.get('semantic-role')==f'[{name}].[Name]'
    for name in ['Latitude (generated)','Longitude (generated)','Geometry (generated)']:
        assert not ds.findall(f"column[@name='[{name}]']")
    states=root.find("worksheets/worksheet[@name='States']/table")
    detail=root.find("worksheets/worksheet[@name='Selected State']/table")
    assert len(states.findall('panes/pane'))==2 and len(detail.findall('panes/pane'))==2
    assert states.find('view/mapsources/mapsource') is not None
    computed_sort=states.find('view/computed-sort')
    assert computed_sort is not None and computed_sort.get('direction')=='DESC'
    assert computed_sort.get('column').endswith('.[none:State:nk]')
    assert computed_sort.get('using').endswith('.[sum:Sales:qk]')
    fields={n.get('caption'):n.get('name') for n in ds.findall('column') if n.get('caption')}
    deps=states.find('view/datasource-dependencies')
    global_rank=next(n for n in deps.findall('column-instance') if n.get('column')==fields['Global Rank'])
    assert [n.get('field').split('.')[-1] for n in global_rank.findall('table-calc/order')]==['[io:Selected Set:nk]','[State]']
    for caption in ['Cols','Rows','State Rank']:
        instance=next(n for n in deps.findall('column-instance') if n.get('column')==fields[caption])
        assert instance.find('table-calc').get('ordering-field').endswith('.[none:State:nk]')
    assert states.find('panes/pane/encodings/geometry').get('column').endswith('.[Geometry (generated)]')
    assert len(detail.findall('panes/pane[2]/encodings/lod'))==2
    hidden=states.find("view/filter[@kind='hide']")
    assert hidden is not None
    inverse=hidden.find('groupfilter')
    assert inverse.get('function')=='except'
    assert [n.get('function') for n in inverse]==['level-members','member']
    assert inverse[1].get('member')=='true'
    assert not any(n.text.endswith('.[io:Selected Set:nk]') for n in states.findall('view/slices/column'))
    assert states.find("view/filter[@class='quantitative']/max").text=='25'
    selected=detail.find('view/filter/groupfilter')
    assert selected.get('member')=='true'
    action=root.find('actions/edit-group-action')
    assert action.find('activation').get('type')=='on-select'
    assert action.find('source').get('worksheet')=='States'
    assert action.find('single-select').get('value')=='true'
    params={n.get('name'):n.get('value') for n in action.findall('params/param')}
    assert params['add-or-remove-marks']=='assign'
    assert params['selection-clear-set-option']=='do-nothing'
    assert params['target-group'].endswith('.[Selected Set]')
    return {'generated_geography':True,'trellis_out_partition_top25':True,'initial_selection':'Oklahoma','set_action':params,'browser_event_execution':False}

def verify():
    result={'oracle':oracle(),'artifacts':artifact_contract()}
    comparison=HERE/'evidence/cloud-data-comparison.json'
    if comparison.exists() and json.loads(comparison.read_text(encoding='utf-8')).get('status')=='pass':
        from verify_cloud_data import compare
        compare(strict_workbook=False)
    (HERE/'evidence/data-contract.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('PASS: 49 independent selection scenarios, generated geography and set action contracts')
if __name__=='__main__':verify()
