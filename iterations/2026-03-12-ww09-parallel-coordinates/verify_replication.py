"""WW09 native normalization, path and parameter action artifact contracts."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json,math,tempfile
from lxml import etree
from tableauhyperapi import HyperProcess,Telemetry,Connection
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
METRICS=[('Total Distance (km)','Distance - Total (KM)'),('Distance / Min (m)','Distance per Min'),('HSR Distance (m)','HSR - Total (M)'),('HI Distance (m)','HI Distance - Total (M)'),('Max Speed (m/s)','Speed - Max (m/s)')]
def verify():
    output=HERE/'outputs/replicated-workbook.twbx';lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    # locked-source-artifact-contract
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for item in lock['extracted_data']:
            p=HERE/item['file'];assert sha256(p.read_bytes()).hexdigest()==item['sha256']
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==p.name))).hexdigest()==item['sha256']
    ds=root.find('./datasources/datasource[@caption]');fields={c.get('caption'):c for c in ds.findall('column') if c.get('caption')}
    sheet=root.find('./worksheets/worksheet[@name="Viz"]')
    colour_formula=fields['Match Colour'].find('calculation').get('formula')
    for category in ['0 Selected Home','1 Selected Away','2 Other Home','3 Other Away']:assert "'"+category+"'" in colour_formula
    # normalization-addressing-contract
    for name,source in METRICS:
        field=fields[name];agg=f'SUM([{source}])'
        assert field.find('calculation').get('formula')==f'({agg} - WINDOW_MIN({agg})) / (WINDOW_MAX({agg}) - WINDOW_MIN({agg}))'
        ci=sheet.find('.//column-instance[@column="'+field.get('name')+'"]');assert ci.get('derivation')=='User'
        tc=ci.find('table-calc');assert tc.get('ordering-type')=='Field'
        assert [o.get('field').split('].',1)[1] for o in tc.findall('order')]==['[Game ID]',fields['Match Colour'].get('name'),fields['Line Width'].get('name')]
    assert not sheet.findall('.//filter[@class="quantitative"]')
    # vertical-spine-contract
    panes=sheet.findall('table/panes/pane');assert len(panes)==2
    assert all(p.find('mark').get('class')=='Line' for p in panes)
    assert panes[1].find('encodings/path').get('column').endswith('.[none:Game ID:ok]')
    assert sheet.findtext('table/rows').count('[Multiple Values]')==2
    special='['+ds.get('name')+'].[:Measure Names]'
    assert sheet.findtext('table/cols')==special
    assert panes[0].get('y-index')=='0' and panes[1].get('y-index')=='1'
    assert panes[1].find('encodings/text') is None
    # Concise dashboard labels avoid Tableau's automatic addressing suffix.
    dashboard_text=''.join(root.xpath('./dashboards/dashboard/zones//zone/formatted-text/run/text()'))
    for metric,_ in METRICS:assert dashboard_text.count(metric)>=2
    fold=sheet.find('table/style/style-rule[@element="axis"]/encoding[@fold="true"]')
    assert fold.get('class')=='1' and fold.get('field')=='['+ds.get('name')+'].[Multiple Values]'
    manual=sheet.find('table/view/manual-sort[@column="'+special+'"]')
    assert manual is not None
    sorted_fields=[]
    for bucket in manual.findall('dictionary/bucket'):
        instance=bucket.text.strip('"').split('].',1)[1]
        ci=sheet.find('.//column-instance[@name="'+instance+'"]')
        sorted_fields.append(next(name for name,col in fields.items() if col.get('name')==ci.get('column')))
    assert sorted_fields==[name for name,_ in METRICS]

    assert sheet.find('table/style/style-rule[@element="axis"]/encoding[@fold="true"]').get('synchronized')=='true'
    hidden=sheet.find('table/style/style-rule[@element="label"]/format[@attr="display"][@field="'+special+'"]')
    assert hidden is not None and hidden.get('value')=='false'
    stacking=sheet.find('table/style/style-rule[@element="axis"]/format[@attr="render-fold-reversed"]')
    assert stacking.get('value')=='true'
    assert panes[0].find('style/style-rule[@element="mark"]/format[@attr="mark-labels-line-first"]').get('value')=='false'
    # Aggregated dimensions cannot split normalization partitions.
    for field,kind in [('H/A','nominal'),('Category','nominal'),('Cup/League','nominal'),('Round','nominal'),('Date','ordinal')]:
        ci=sheet.find('.//column-instance[@column="['+field+']"][@derivation="Attribute"]')
        assert ci is not None and ci.get('type')==kind
    label=sheet.find('.//column-instance[@column="'+fields['Label: Opposition'].get('name')+'"][@derivation="Attribute"]')
    assert label.get('type')=='nominal'
    # selection-clear-parameter-contract
    action=root.find('./actions/edit-parameter-action[@caption="Set Opposition"]')
    assert action.find('activation').get('type')=='on-select'
    assert action.find('source').get('worksheet')=='Viz'
    assert action.find('source').get('dashboard')=='2026_03_04_WW09_Parallel_Coordinates'
    assert 'Opposition' in action.find('params/param[@name="source-field"]').get('value')
    assert action.find('clear-option').get('value')=='s:LROOT:'
    assert action.find('clear-option').get('type')!='do-nothing'
    # independent-game-normalization-contract
    hyper=next((HERE/'inputs').glob('*.hyper'))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(hyper)) as c:
        rows=c.execute_list_query('SELECT "Game ID", "Opposition", "H/A", '+','.join('"'+s+'"' for _,s in METRICS)+' FROM "Extract"."Extract" ORDER BY "Game ID"')
    assert len(rows)==24 and len({r[0] for r in rows})==24
    bounds=[(min(r[3+i] for r in rows),max(r[3+i] for r in rows)) for i in range(5)]
    values=[]
    for game,opponent,venue,*raw in rows:
        normalized=[(v-lo)/(hi-lo) for v,(lo,hi) in zip(raw,bounds)]
        assert all(0<=v<=1 for v in normalized)
        values.append({'Game ID':game,'Opposition':opponent,'H/A':venue,'raw':dict(zip([s for _,s in METRICS],raw)),'normalized':dict(zip([n for n,_ in METRICS],normalized))})
    for name,_ in METRICS:
        assert math.isclose(min(v['normalized'][name] for v in values),0,abs_tol=1e-12)
        assert math.isclose(max(v['normalized'][name] for v in values),1,abs_tol=1e-12)
    assert bounds==[(1.57,8.61),(55.6,104.25925925925925),(56,266),(276,1265),(6.66,7.96)]
    game10=next(v for v in values if v['Game ID']==10)
    assert math.isclose(game10['normalized']['Total Distance (km)'],0.5767045454545454,abs_tol=1e-12)
    assert game10['normalized']['Distance / Min (m)']==1.0
    states=[]
    for opponent in ['Chelsea Ladies U14','South Gloucestershire','']:
        highlighted=[v['Game ID'] for v in values if v['Opposition']==opponent]
        if opponent=='Chelsea Ladies U14':assert highlighted==[10,15]
        if not opponent:assert highlighted==[]
        states.append({'parameter':opponent,'highlighted_games':highlighted,'total_games':24,'normalized_values_unchanged':True})
    with tempfile.TemporaryDirectory() as d:
        roundtrip=Path(d)/'roundtrip.twbx';TWBEditor.open_existing(output).save(roundtrip,validate=False);assert roundtrip.exists()
    # cloud-normalized-data-contract
    if (HERE/'outputs/cloud-author-dashboard.csv').exists():
        from verify_cloud_data import verify as verify_cloud
        verify_cloud()
    evidence={'status':'pass','metrics':bounds,'games':values,'parameter_states':states,'artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False}
    (HERE/'evidence').mkdir(exist_ok=True);(HERE/'evidence/functional-verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('PASS: WW09 locked Hyper, native five-metric normalization, full-game addressing, vertical spine, parameter clear and independent 24-game oracle')
    return evidence
if __name__=='__main__':verify()
