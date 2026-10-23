"""Independent raw-row oracle and serialized native Tableau contracts."""
from pathlib import Path
from collections import defaultdict, Counter
from zipfile import ZipFile
from lxml import etree as E
from tableauhyperapi import HyperProcess, Telemetry, Connection
import csv, hashlib, json, math
HERE=Path(__file__).resolve().parent
EXPECTED={('A-M','Furniture'):352580.9045,('A-M','Office Supplies'):381184.158,('A-M','Technology'):394487.342,('N-Z','Furniture'):389418.8908,('N-Z','Office Supplies'):337862.874,('N-Z','Technology'):441666.691}
ACCEPTANCE=['ww40-state-groups','ww40-six-sales-cells','ww40-category-sort','ww40-total-reference','ww40-parameter-action','ww40-clear-selection','ww40-layout-palette']

def oracle():
    p=next((HERE/'inputs').glob('*.hyper'))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint,p) as c:
        rows=c.execute_list_query('SELECT "State","Category","Sales" FROM "Extract"."Extract"')
    sums=defaultdict(float); counts=Counter(); states=defaultdict(set)
    for state,cat,sale in rows:
        group='A-M' if state[0].upper() in 'ABCDEFGHIJKLM' else 'N-Z'
        sums[group,cat]+=sale; counts[cat]+=1; states[group].add(state)
    return rows,sums,counts,states

def verify():
    rows,sums,counts,states=oracle()
    assert len(rows)==9994 and len(set(r[0] for r in rows))==49
    assert 'Maryland' in states['A-M'] and 'New York' in states['N-Z']
    assert set(sums)==set(EXPECTED)
    for key,v in EXPECTED.items():assert math.isclose(sums[key],v,abs_tol=1e-6)
    workbook=HERE/'outputs/replicated-workbook.twbx'
    with ZipFile(workbook) as z:
        root=E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        extract=next(n for n in z.namelist() if n.endswith('.hyper'))
        assert hashlib.sha256(z.read(extract)).hexdigest()==hashlib.sha256(next((HERE/'inputs').glob('*.hyper')).read_bytes()).hexdigest()
    ds=next(d for d in root.findall('./datasources/datasource') if d.get('name')!='Parameters')
    cols={c.get('caption',c.get('name').strip('[]')):c for c in ds.findall('column')}
    def formula(n):return cols[n].find('calculation').get('formula')
    assert formula('State Initial ASCII')=='ASCII(UPPER(LEFT([State],1)))'
    assert '<= 77' in formula('State Group') and "'A-M'" in formula('State Group') and "'N-Z'" in formula('State Group')
    ws=root.find('./worksheets/worksheet[@name="Chart"]'); view=ws.find('table/view'); pane=ws.find('table/panes/pane')
    sort=view.find('computed-sort')
    assert sort.get('direction')=='DESC' and 'Category' in sort.get('column') and cols['Sort'].get('name').strip('[]') in sort.get('using')
    assert '[Category]' in formula('Sort') and 'THEN 0 ELSE 1 END' in formula('Sort')
    param=root.find('./datasources/datasource[@name="Parameters"]/column'); assert param.get('caption')=='pSelectedCategpry' and 'Office Supplies' in param.get('value')
    orders={selected:sorted(counts,key=lambda c:(-counts[c] if c!=selected else 0,c)) for selected in counts}
    assert all(order[-1]==selected for selected,order in orders.items())
    total=cols['Total Sales per State Group'].get('name').strip('[]')
    assert 'FIXED' in formula('Total Sales per State Group') and 'SUM([Sales])' in formula('Total Sales per State Group')
    ref=pane.find('reference-line'); assert ref.get('scope')=='per-cell' and ref.get('formula')=='total' and total in ref.get('value-column')
    assert pane.find('mark').get('class')=='Bar' and pane.find('view/breakdown').get('value')=='auto'
    action=root.find('./actions/edit-parameter-action')
    assert action.find('activation').get('type')=='on-select' and action.find('agg-type').get('type')=='attr'
    assert action.find('clear-option') is None or action.find('clear-option').get('type')=='do-nothing'
    params={e.get('name'):e.get('value') for e in action.findall('params/param')}
    assert 'Category' in params['source-field'] and param.get('name') in params['target-parameter']
    clear=root.find('./actions/action'); assert clear.find('activation').get('auto-clear')=='true'
    expr=clear.find('link').get('expression'); assert cols['True'].get('name').strip('[]') in expr and cols['False'].get('name').strip('[]') in expr
    assert formula('True').lower()=='true' and formula('False').lower()=='false'
    assert len(pane.findall('encodings/lod'))>=3
    size=root.find('./dashboards/dashboard/size'); assert size.get('maxwidth')=='400' and size.get('maxheight')=='800'
    xml=E.tostring(root).decode(); assert all(color in xml for color in ['#1170aa','#a3acb9','#fc7d0b'])
    assert 'Select a category to re-order the stack' in xml and 'Sales by Category' in xml
    zone=root.find('.//dashboards/dashboard/zones//zone[@name="Chart"]'); assert zone.get('show-title','true')=='true'
    totals={g:sum(v for (group,cat),v in sums.items() if group==g) for g in states}
    with (HERE/'outputs/expected-sales.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['State Group','Category','Sales','Total Sales per State Group'])
        for (g,c),v in sorted(sums.items()):w.writerow([g,c,round(v,4),round(totals[g],4)])
    result={'status':'PASS','acceptance':ACCEPTANCE,'source_rows':len(rows),'state_counts':{g:len(s) for g,s in states.items()},'category_counts':dict(counts),'totals':totals,'orders_top_to_bottom':orders,'workbook_sha256':hashlib.sha256(workbook.read_bytes()).hexdigest(),'scope':'Independent extract arithmetic and serialized native contracts; runtime gates recorded separately in evidence/.'}
    (HERE/'evidence/functional-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':verify()


