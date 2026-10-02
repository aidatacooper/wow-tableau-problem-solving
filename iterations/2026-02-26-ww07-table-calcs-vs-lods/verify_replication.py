"""WW07 locked source, late filters, regional percentages and LOD contracts."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from collections import defaultdict
import json,math,tempfile
from lxml import etree
from tableauhyperapi import HyperProcess,Telemetry,Connection
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent

def verify():
    output=HERE/'outputs/replicated-workbook.twbx'
    lock=json.loads((HERE/'inputs/source-lock.json').read_text())
    # locked-source-artifact-contract
    with ZipFile(output) as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        for item in lock['extracted_data']:
            p=HERE/item['file'];assert sha256(p.read_bytes()).hexdigest()==item['sha256']
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==p.name))).hexdigest()==item['sha256']
    ds=root.find('./datasources/datasource[@caption]');fields={c.get('caption'):c for c in ds.findall('column') if c.get('caption')}
    # category-late-filter-contract
    tc=root.find('./worksheets/worksheet[@name="Table Calcs"]')
    late=fields['TC - Filter Category'];pct=fields['TC - % of Sales']
    assert late.find('calculation').get('formula')=='LOOKUP(MIN([Category]),0)'
    ci=tc.find('.//column-instance[@column="'+late.get('name')+'"]');assert ci.get('derivation')=='User'
    assert tc.find('.//filter[@column="['+ds.get('name')+'].'+ci.get('name')+'"]') is not None
    pctci=tc.find('.//column-instance[@column="'+pct.get('name')+'"]')
    addressing=pctci.find('table-calc');assert addressing.get('ordering-type')=='Field' and 'Category' in addressing.get('ordering-field')
    assert not any('none:Category:' in f.get('column') for f in tc.findall('.//filter'))
    # lod-denominator-contract
    lod=fields['LOD - Sales per Region & Segment'].find('calculation').get('formula')
    assert lod=='{FIXED [Region], [Segment]:SUM([Sales])}'
    assert fields['LOD - % of Sales'].find('calculation').get('formula')=='SUM([Sales]) / SUM('+fields['LOD - Sales per Region & Segment'].get('name')+')'
    for name,color in [('Table Calcs','#f28e2b'),('LODs','#4e79a7')]:
        ws=root.find('./worksheets/worksheet[@name="'+name+'"]')
        sort=ws.find('table/view/shelf-sorts/shelf-sort-v2')
        assert sort.get('dimension-to-sort').endswith('.[none:Category:nk]')
        assert sort.get('direction')=='DESC' and sort.get('shelf')=='rows'
        style=ws.find('.//pane/style/style-rule[@element="mark"]/format[@attr="mark-color"]')
        assert style.get('value')==color
    assert len(root.findall('.//dashboard/./zones//zone[@type-v2="filter"]'))==6
    # independent-filter-numerical-contract: three states, both denominator strategies.
    hyper=next((HERE/'inputs').glob('*.hyper'))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(hyper)) as c:
        rows=c.execute_list_query('SELECT "Region", "Segment", "Category", "Sales" FROM "Extract"."Extract"')
    assert len(rows)==10194
    states=[]
    for state,segments,regions,categories in [('all',None,None,None),('consumer',{'Consumer'},None,None),('consumer-hide-furniture-east',{'Consumer'},{'East'},{'Office Supplies','Technology'})]:
        sales=defaultdict(float);denom=defaultdict(float);fixed=defaultdict(float)
        for r,s,cat,v in rows:fixed[r,s]+=v
        for r,s,cat,v in rows:
            if segments and s not in segments:continue
            if regions and r not in regions:continue
            sales[r,cat]+=v;denom[r]+=v
        values=[]
        for (r,cat),v in sorted(sales.items()):
            ld=sum(total for (fr,fs),total in fixed.items() if fr==r and (not segments or fs in segments))
            assert math.isclose(ld,denom[r],rel_tol=1e-12)
            ratio=v/denom[r]
            if categories and cat not in categories:continue
            values.append({'Region':r,'Category':cat,'Sales':v,'Denominator':denom[r],'Percent':ratio})
        if not categories:
            for r in {v['Region'] for v in values}:assert math.isclose(sum(v['Percent'] for v in values if v['Region']==r),1,abs_tol=1e-12)
        else:assert sum(v['Percent'] for v in values)<1
        states.append({'state':state,'rows':values})
    anchor=next(v for v in states[0]['rows'] if v['Region']=='Central' and v['Category']=='Furniture')
    assert math.isclose(anchor['Sales'],164537.6518,abs_tol=1e-7)
    assert math.isclose(anchor['Percent'],0.3270016729798559,abs_tol=1e-12)
    baseline={ (v['Region'],v['Category']):v['Percent'] for v in states[1]['rows']}
    for v in states[2]['rows']:assert math.isclose(v['Percent'],baseline[v['Region'],v['Category']],abs_tol=1e-12)
    with tempfile.TemporaryDirectory() as d:
        roundtrip=Path(d)/'roundtrip.twbx';TWBEditor.open_existing(output).save(roundtrip,validate=False);assert roundtrip.exists()
    evidence={'status':'pass','rows':len(rows),'states':states,'artifact_sha256':sha256(output.read_bytes()).hexdigest(),'browser_interaction_executed':False}
    (HERE/'evidence').mkdir(exist_ok=True)
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    # cloud-lod-data-contract: actual REST scope explicitly excludes Table Calcs.
    if (HERE/'outputs/cloud-author-dashboard.csv').exists():
        from verify_cloud_data import verify as verify_cloud
        verify_cloud()
    print('PASS: WW07 locked Hyper, category late-filter, LOD formula, independent filter-state ratios and round trip')
    return evidence
if __name__=='__main__':verify()
