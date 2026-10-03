"""Verify spatial geometry/action contracts and complete REST worksheet data."""
from pathlib import Path
import csv,hashlib,json,math,zipfile
from collections import Counter
from lxml import etree
from tableauhyperapi import HyperProcess,Connection,Telemetry

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'outputs/replicated-workbook.twbx'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def distance(a,b):
    # Independent WGS84 local-curvature approximation. Across these London
    # points its sub-metre precision exceeds the rounded CSV label precision.
    lat=math.radians((a[0]+b[0])/2)
    eccentricity=6.69437999014e-3
    w=math.sqrt(1-eccentricity*math.sin(lat)**2)
    north=6378137*(1-eccentricity)/w**3*math.radians(a[0]-b[0])
    east=6378137/w*math.cos(lat)*math.radians(a[1]-b[1])
    return math.hypot(north,east)


def read_facts():
    result=[]
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        for fragment in ('London Pubs.csv+', 'Hotels_Pubs Combined'):
            path=next(p for p in (HERE/'inputs').glob('*.hyper') if fragment in p.name)
            with Connection(h.endpoint,str(path)) as c:
                table=c.catalog.get_table_names('Extract')[0]
                columns=[f.name.unescaped for f in c.catalog.get_table_definition(table).columns]
                result.append([dict(zip(columns,row)) for row in c.execute_list_query(f'SELECT * FROM {table}')])
    return result


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))


def number(value):return float(str(value).replace(',','').replace(' m','').strip())


def column(row,*names):
    for name in names:
        if name in row:return row[name]
    raise AssertionError('Missing exported column: '+str(names)+'; available: '+str(list(row)))


def verify():
    # acceptance: empty-public-sdk-build
    with zipfile.ZipFile(OUTPUT) as archive:
        tree=etree.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.twb'))))
        lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
        for record in lock['extracted_data']:
            path=HERE/record['file']
            assert digest(path)==record['sha256']
            assert hashlib.sha256(archive.read(path.name)).hexdigest()==record['sha256']
    assert len(tree.xpath('./datasources/datasource[not(@hasconnection="false")]'))==2
    assert len(tree.findall('dashboards/dashboard'))==2
    # acceptance: native-spatial-tooltips
    formulas='\n'.join(c.get('formula','') for c in tree.findall('.//column/calculation'))
    assert 'BUFFER(MAKEPOINT([LAT],[LON]),500,"m")' in formulas
    assert 'BUFFER(' in formulas and 'MAKEPOINT' in formulas and 'DISTANCE' in formulas
    parameters={p.get('caption'):p for p in tree.xpath('./datasources/datasource[@name="Parameters"]/column')}
    radius=parameters['Buffer Radius']
    assert radius.get('datatype')=='integer' and radius.get('value')=='500'
    buffer=tree.xpath('./datasources/datasource/column[@caption="Hotel Buffer"]/calculation')[0].get('formula')
    assert 'BUFFER(' in buffer and '[Parameters].'+radius.get('name') in buffer
    tooltip=tree.xpath('//worksheet[@name="Map_int"]//customized-tooltip/formatted-text/run')
    embed=next(t.text for t in tooltip if t.text and '<Sheet name="VIT:Pub List"' in t.text)
    assert 'Hotel Name' in embed and 'maxwidth="300"' in embed
    assert tree.xpath('//worksheet[@name="VIT:Pub List"]/table/view/filter[contains(@column,"Tooltip (Hotel Name)")]')
    assert tree.xpath('//worksheet[@name="Map_int"]//pane[@id="1"]//format[@attr="mark-labels-show" and @value="true"]')
    # acceptance: hotel-sort-selection-contract
    actions=tree.xpath('./actions/edit-parameter-action')
    assert len(actions)==2
    for action in actions:
        assert action.find('activation').get('type')=='on-select'
        assert action.find('params/param[@name="source-field"]') is not None
        assert action.find('params/param[@name="target-parameter"]') is not None
        assert action.find('params/param[@name="clear-value"]') is None  # Native keep-current default.
    hotel_action=next(a for a in actions if a.find('source').get('worksheet')=='Hotel Chart')
    assert hotel_action.find('params/param[@name="source-field"]').get('value').endswith('.[none:Name:nk]')
    assert hotel_action.find('params/param[@name="target-parameter"]').get('value')=='[Parameters].'+parameters['Selected Hotel'].get('name')
    sort_action=next(a for a in actions if a.find('source').get('worksheet')=='Sort Selector')
    assert sort_action.find('params/param[@name="source-field"]').get('value').endswith('.[:Measure Names]')
    assert sort_action.find('params/param[@name="target-parameter"]').get('value')=='[Parameters].'+parameters['Selected Sort Measure'].get('name')
    sort_formula=tree.xpath('./datasources/datasource/column[@caption="Chart Sort"]/calculation')[0].get('formula')
    for clause in ['WHEN " Yelp Rating " THEN SUM([Yelp Rating])','WHEN " Price Rating " THEN -SUM([Price Rating Sort])','WHEN " Number of Ratings " THEN SUM([Yelp # of Ratings])']:
        assert clause in sort_formula
    button=tree.find('.//button/toggle-action')
    assert button is not None and 'zone-ids=[' in button.text
    window=tree.xpath('//window[@name="2020_03_04_WW10_London_Pubs_Buffer_Jedi"]/simple-id')[0].get('uuid')
    assert window in button.text
    assert tree.xpath('//dashboard//zone[@name="Hotel Chart" and @hidden-by-user="true"]')
    assert tree.xpath('//worksheet[@name="Hotel Chart"]//shelf-sort-v2[@direction="DESC"]')
    # acceptance: spatial-data-oracle
    joined,combined=read_facts()
    hotels={r['Name']:r for r in combined if r['Location Type']=='Hotel'}
    pubs={(r['Name'],r['Neighborhood']):r for r in combined if r['Location Type']=='Pub'}
    assert len(joined)==17 and len(hotels)==10 and len(pubs)==32
    pairs={(r['Hotel Name'],r['Pub Name']) for r in joined}
    expected_pairs={(name,pub[0]) for name,h in hotels.items() for pub,p in pubs.items() if distance((h['LAT'],h['LON']),(p['LAT'],p['LON']))<=500}
    assert pairs==expected_pairs
    for row in joined:
        assert distance((row['LAT'],row['LON']),(row['Lat1'],row['Lon1']))<=500
    report={'status':'pass','artifact_sha256':digest(OUTPUT),'source_rows':{'joined':len(joined),'combined':len(combined)},'hotels':len(hotels),'pubs':len(pubs),'joined_hotel_counts':dict(Counter(r['Hotel Name'] for r in joined)),'distance_oracle':'Independent WGS84 local-curvature calculation; 1m rounded-label tolerance','cloud_status':'pending','interaction_scope':'REST parameter states and serialized action/toggle/tooltip contracts; no browser events executed.'}
    # acceptance: cloud-complete-map-data
    manifest=HERE/'evidence/cloud-verification.json'
    if manifest.exists():
        cloud=json.loads(manifest.read_text(encoding='utf-8'))
        assert cloud['source_hashes']['replica']==digest(OUTPUT)
        provenance=json.loads((HERE/'evidence/export-provenance.json').read_text(encoding='utf-8'))
        assert cloud['source_hashes']['author']==provenance['comparison_sha256']
        assert provenance['original_sha256']==lock['source_workbook']['sha256']
        checks=[]
        for state in cloud['states']:
            hotel=state.get('parameters',{}).get('Selected Hotel','The Hoxton - Shoreditch')
            selected=hotels[hotel]
            for image in state['views'].values():assert digest(HERE/image['path'])==image['sha256']
            for export in state['data']:
                path=HERE/export['path']; assert digest(path)==export['sha256']
                rows=csv_rows(path)
                if '-pub-list' in path.name:
                    actual={(column(r,'Hotel Name'),column(r,'Pub Name')):number(column(r,'Distance')) for r in rows}
                    assert len(rows)==len(actual), 'Duplicate joined hotel/pub pair'
                    assert set(actual)==pairs
                    for row in joined:
                        assert abs(actual[(row['Hotel Name'],row['Pub Name'])]-distance((row['LAT'],row['LON']),(row['Lat1'],row['Lon1'])))<=1
                    checks.append({'state':state['name'],'role':export['role'],'worksheet':'pub-list','pairs':len(actual)})
                elif '-map' in path.name:
                    actual={}
                    for row in rows:
                        pub_name=column(row,'Pub Name')
                        if not pub_name:continue
                        key=(pub_name,column(row,'Neighborhood'))
                        value=number(column(row,'Distance Selected Hotel-Pub'))
                        assert key not in actual, 'Duplicate active pub geometry mark'
                        actual[key]=value
                    assert set(actual)==set(pubs)
                    for key,pub in pubs.items():assert abs(actual[key]-distance((selected['LAT'],selected['LON']),(pub['LAT'],pub['LON'])))<=1
                    checks.append({'state':state['name'],'role':export['role'],'worksheet':'map','pubs':len(actual),'selected_hotel':hotel})
                elif '-hotels' in path.name:
                    actual={column(r,'Name'):r for r in rows}
                    assert len(rows)==len(actual), 'Duplicate hotel mark'
                    assert set(actual)==set(hotels)
                    for name,fact in hotels.items():
                        row=actual[name]
                        assert number(column(row,'Yelp # of Ratings'))==fact['Yelp # of Ratings']
                        assert number(column(row,'Yelp Rating','Yelp Rating Header'))==fact['Yelp Rating']
                        assert column(row,'Price Rating').strip()==str(fact['Price Rating'] or '').strip()
                    checks.append({'state':state['name'],'role':export['role'],'worksheet':'hotels','hotels':len(actual)})
        assert {s['name'] for s in cloud['states']}=={'default','intermediate','radius250','marriott-rating','ratings-count'}
        assert len(checks)==30
        report['cloud_status']='pass'
        (HERE/'evidence/cloud-data-comparison.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2)+'\n',encoding='utf-8')
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':verify()
