"""Structural checks plus independently computed hourly percentile oracle.
Desktop render/tooltip acceptance is deliberately left to the serial UI owner.
"""
import hashlib, json, math, zipfile
from copy import deepcopy
from pathlib import Path
from collections import defaultdict
from lxml import etree as E
from tableauhyperapi import HyperProcess, Telemetry, Connection
HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"outputs"/"replicated-workbook.twbx"

def verify_pattern_manifest(root):
    assert root.find('./document-format-change-manifest/PatternedLineMarks') is not None, 'PatternedLineMarks manifest is required for mark-line-pattern'

def verify_missing_manifest_rejected(root):
    mutant = deepcopy(root)
    for manifest in mutant.findall('./document-format-change-manifest/PatternedLineMarks'):
        manifest.getparent().remove(manifest)
    try:
        verify_pattern_manifest(mutant)
    except AssertionError as error:
        assert str(error) == 'PatternedLineMarks manifest is required for mark-line-pattern'
    else:
        raise AssertionError('Missing PatternedLineMarks manifest was accepted')

def verify():
    with zipfile.ZipFile(OUTPUT) as z:
        root=E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        packaged=[n for n in z.namelist() if n.endswith('.hyper')]
        assert len(packaged)==1
        assert hashlib.sha256(z.read(packaged[0])).hexdigest()==hashlib.sha256((HERE/'inputs/WoW2024Wk49.hyper').read_bytes()).hexdigest()
    # acceptance: single-sheet-layout
    sheets=root.findall('./worksheets/worksheet'); assert len(sheets)==1
    size=root.find('./dashboards/dashboard/size'); assert size.get('maxwidth')=='1300' and size.get('maxheight')=='600'
    ws=sheets[0]; cols={c.get('caption',c.get('name').strip('[]')):c for c in root.findall('./datasources/datasource/column')}
    # acceptance: hourly-percentiles
    for name,q in [('5th Percentile',0.05),('25th Percentile',0.25),('Median',0.5),('75th Percentile',0.75),('95th Percentile',0.95)]:
        assert cols[name].find('calculation').get('formula')==f'PERCENTILE([Glucose mg/dL],{q})'
    assert cols['Hour'].find('calculation').get('formula')=="DATEPART('hour',[Device Timestamp])"
    assert cols['Minimum'].find('calculation').get('formula')=='MIN([Glucose mg/dL])'
    assert cols['Maximum'].find('calculation').get('formula')=='MAX([Glucose mg/dL])'
    panes=ws.findall('./table/panes/pane'); assert len(panes)==2
    # acceptance: median-and-shading
    assert [x.find('mark').get('class') for x in panes]==['Line','Area']
    assert all(x.find('view/breakdown').get('value')=='off' for x in panes)
    assert panes[0].xpath('.//format[@attr="mark-line-pattern"]/@value')==['dashed']
    verify_pattern_manifest(root)
    verify_missing_manifest_rejected(root)
    assert ws.xpath('.//encoding[@fold="true"][@synchronized="true"]')
    assert ws.xpath('.//format[@attr="render-fold-reversed"]/@value')==['true']
    assert len(ws.xpath('./table/view/filter/groupfilter/groupfilter'))==6
    palette=root.xpath('./datasources/datasource/style/style-rule/encoding[@field="[:Measure Names]"]/map')
    assert len(palette)==6
    assert all(m.findtext("bucket").startswith('"[') for m in palette)
    assert sorted(m.get('to') for m in palette)==sorted(['#ffffff','#d2e1f3','#a9c1df','#7a93b9','#a9c1df','#d2e1f3'])
    # acceptance: normal-range
    refs=ws.findall('.//reference-line'); assert len(refs)==2
    for value,line in zip([80,180],refs):
        assert cols[f'Normal {value}'].find('calculation').get('formula')==str(value)
        assert 'avg:'+cols[f'Normal {value}'].get('name').strip('[]') in line.get('value-column')
        assert line.get('formula')=='average'
        assert ws.xpath(f'.//format[@id="{line.get("id")}"][@attr="line-pattern-only"]/@value')==['dotted']
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,parameters={'log_dir':str(HERE/'outputs')}) as h:
        with Connection(h.endpoint,str(HERE/'inputs/WoW2024Wk49.hyper')) as c:
            data=c.execute_list_query('SELECT EXTRACT(HOUR FROM "Device Timestamp"), "Glucose mg/dL" FROM "Extract"."Extract"')
            sql=c.execute_list_query('SELECT EXTRACT(HOUR FROM "Device Timestamp"), COUNT(*), MIN("Glucose mg/dL"), '+', '.join(f'PERCENTILE_CONT({q}) WITHIN GROUP (ORDER BY "Glucose mg/dL")' for q in [.05,.25,.5,.75,.95])+', MAX("Glucose mg/dL") FROM "Extract"."Extract" GROUP BY 1 ORDER BY 1')
    groups=defaultdict(list)
    for hour,value in data: groups[int(hour)].append(value)
    assert set(groups)==set(range(24))
    oracle=[]
    for row in sql:
        hour=int(row[0]); values=sorted(groups[hour]); n=len(values)
        expected=[values[0]]
        for q in [.05,.25,.5,.75,.95]:
            i=(n-1)*q; lo=math.floor(i); hi=math.ceil(i); expected.append(values[lo]+(values[hi]-values[lo])*(i-lo))
        expected.append(values[-1])
        assert row[1]==n
        assert all(math.isclose(float(a),float(b),abs_tol=1e-9) for a,b in zip(expected,row[2:]))
        assert expected==sorted(expected)
        oracle.append(dict(zip(['hour','readings','minimum','p05','p25','median','p75','p95','maximum'],[hour,n]+expected)))
    result={'artifact_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'structural_checks':'pass','numerical_oracle':'pass','rows':len(data),'hour_groups':len(groups),'independent_value_comparisons':24*7,'hourly':oracle,'desktop':'pending parent serial gate','rendered_values':'pending: compare tooltip/table export with hourly oracle; SQL is not rendered evidence'}
    result['patterned_line_manifest'] = 'present; missing-manifest mutation rejected'
    (HERE/'evidence'/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='hourly'},indent=2))
if __name__=='__main__':verify()
