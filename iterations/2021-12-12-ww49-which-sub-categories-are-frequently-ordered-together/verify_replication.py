"""Independent raw-line oracle, emitted-workbook contracts, and negative mutations.
No author workbook is read. The oracle uses indexed SQL EXISTS over raw lines;
it does not reuse the builder's order/category expansion.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile
import zipfile
from lxml import etree as E
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
EXPECTED = {
 'Orders':'COUNTD([Order ID])',
 'Visible Orders':'IF [Orders]>0 THEN [Orders] END',
 'Row Index':'INDEX()', 'Column Index':'INDEX()',
 'Triangle':'[Row Index]>=[Column Index]',
 'Average Row Sales':'SUM([Row Sales])/[Orders]',
 'Average Column Sales':'SUM([Column Sales])/[Orders]',
 'Second Title':'IF [Column Category]="NONE" THEN "" ELSE " & " + [Column Category] END',
 'Category Word':'IF [Column Category]="NONE" THEN "SUB-CATEGORY" ELSE "SUB-CATEGORIES" END',
 'Second Label':'IF [Column Category]="NONE" THEN "" ELSE [Column Category]+":" END',
}

def require(value, message):
    if not value:
        raise AssertionError(message)


def contracts(root):
    # acceptance: emitted-closure, one-sheet-logical-model, triangle-order, tooltip-contract, dashboard-contract
    sheets = root.findall('worksheets/worksheet')
    require(len(sheets)==1, 'exactly one worksheet')
    sheet = sheets[0]
    ds = root.findall('datasources/datasource')
    require(len(ds)==1, 'one datasource')
    ds = ds[0]
    cols = {e.get('name'):e for e in ds.findall('column')}
    captions = {e.get('caption'):e for e in cols.values() if e.get('caption')}
    names = {name:'['+e.get('caption')+']' for name,e in cols.items() if e.get('caption')}
    for name, expected in EXPECTED.items():
        require(name in captions, f'missing calculation {name}')
        actual = captions[name].find('calculation').get('formula')
        actual = re.sub(r'\[[^\]]+\]',lambda m:names.get(m[0],m[0]),actual)
        require(actual == expected, f'formula {name}: {actual}')
    for calc in root.findall('.//calculation'):
        require(not re.search(r'\{\s*(FIXED|INCLUDE|EXCLUDE)|\{',calc.get('formula',''),re.I),'no LODs')
    physical = {x.findtext('local-name'):x.findtext('local-type') for x in ds.findall('connection/metadata-records/metadata-record[@class="column"]')}
    require(physical.get('[Column Sort]')=='integer', 'numeric column sort type')
    graph = ds.find('object-graph')
    require(len(graph.findall('objects/object'))==2, 'two logical tables')
    rels = graph.findall('relationships/relationship')
    require(len(rels)==1,'one logical relationship')
    expression = rels[0].find('expression')
    require(expression.get('op')=='=' and [e.get('op') for e in expression]==['[Pair Key]','[Fact Key]'], 'relationship keys')
    require(not ds.findall('.//relation[@type="join"]'),'no physical join fanout')
    deps = sheet.find('table/view/datasource-dependencies')
    depcols = {e.get('name'):e for e in deps.findall('column')}
    instances = {e.get('name'):e for e in deps.findall('column-instance')}
    declared = set(cols)|set(physical)
    for name,e in depcols.items():
        require(name in declared, f'undeclared dependency {name}')
        if e.find('calculation') is not None:
            require(name in cols and E.tostring(e.find('calculation'))==E.tostring(cols[name].find('calculation')),f'dependency formula mismatch {name}')
            for ref in re.findall(r'\[[^\]]+\]',e.find('calculation').get('formula','')):
                require(ref in declared and ref in depcols,f'unclosed formula dependency {ref}')
    for e in instances.values():
        require(e.get('column') in depcols,f'unbound instance {e.get("name")}')
    # Resolve every qualified field reference in shelves, encodings, filters,
    # sorts, table-calc selectors, styles, tooltip placeholders and dashboards.
    dsname = ds.get('name')
    for region in [sheet,*root.findall('dashboards/dashboard')]:
        for node in region.iter():
            for value in [*node.attrib.values(),node.text or '']:
                for source, ref in re.findall(r'\[([^\]]+)\]\.(\[[^\]]+\])',value):
                    require(source==dsname, f'unknown datasource {source}')
                    require(ref in instances or ref in depcols,f'unresolved reference {ref}')
    def full(instance):
        return '['+dsname+'].'+instance
    def instance_for(caption, derivation=None):
        candidates = [e for e in instances.values() if e.get('column')==captions[caption].get('name') and (not derivation or e.get('derivation')==derivation)]
        require(len(candidates)==1,f'instance for {caption}')
        return candidates[0]
    require(sheet.findtext('table/rows')==full('[none:Row Category:nk]'),'explicit row shelf')
    require(sheet.findtext('table/cols')==full('[none:Column Category:nk]'),'explicit column shelf')
    triangle = instance_for('Triangle')
    require(triangle.get('derivation')=='User' and captions['Triangle'].get('role')=='measure','table-calculated measure role')
    nested = {x.get('field'):x for x in triangle.findall('table-calc') if x.get('field')}
    for index, axis in [('Row Index','Row Category'),('Column Index','Column Category')]:
        spec = nested.get(full(captions[index].get('name')))
        require(spec is not None and spec.get('ordering-type')=='Field' and spec.get('ordering-field')==full('['+axis+']'),f'{index} addresses actual category')
    filters = sheet.findall('table/view/filter')
    require(len(filters)==1 and filters[0].get('column')==full(triangle.get('name')) and filters[0].find('groupfilter').get('member')=='true','triangle filter true only')
    sort = sheet.find('table/view/computed-sort')
    require(sort is not None and sort.get('column')==full('[none:Column Category:nk]') and sort.get('direction')=='DESC' and sort.get('using')==full('[min:Column Sort:qk]'),'NONE-first alphabetical column ordering')
    pane = sheet.find('table/panes/pane')
    require(len(sheet.findall('table/panes/pane'))==1 and pane.find('mark').get('class')=='Square','single square pane')
    require(pane.find('mark-sizing').get('mark-sizing-setting')=='marks-scaling-off','constant mark sizing')
    require(pane.find('style/style-rule[@element="mark"]/format[@attr="size"]').get('value')=='1','square size contract')
    visible = full(instance_for('Visible Orders').get('name'))
    require(pane.find('encodings/color').get('column')==visible and pane.find('encodings/text').get('column')==visible,'count color and label')
    tooltip = ''.join(pane.find('customized-tooltip').itertext())
    for caption, derivation in [('Orders',None),('Average Row Sales',None),('Average Column Sales',None),('Second Title','Attribute'),('Category Word','Attribute'),('Second Label','Attribute')]:
        require(full(instance_for(caption,derivation).get('name')) in tooltip,f'tooltip {caption}')
    require('AVERAGE SALES CONTRIBUTION PER ORDER' in tooltip and 'ORDERS WITH PRODUCTS FROM' in tooltip,'tooltip help text')
    for caption in ['Average Row Sales','Average Column Sales']:
        require(captions[caption].get('default-format')=='*"$"#,##0.00;("$"#,##0.00)','custom currency format prefix')
    colors = sheet.findall('table/style/style-rule/encoding/color-palette/color')
    require([x.text for x in colors]==['#f7fcfd','#e0ecf4','#bfd3e6','#9ebcda','#8c96c6','#8c6bb1','#88419d','#810f7c','#4d004b'],'portable ColorBrewer BuPu palette')
    dashboards = root.findall('dashboards/dashboard')
    require(len(dashboards)==1,'one dashboard')
    dash = dashboards[0]
    require(dash.find('size').get('maxwidth')=='1100' and dash.find('size').get('maxheight')=='900','dashboard size')
    zones = dash.findall('.//zone')
    require(sum(z.get('name')==sheet.get('name') for z in zones)==1,'one dashboard sheet zone')
    require('HOVER TO VIEW AVERAGE SALES CONTRIBUTION BY CATEGORY' in ''.join(dash.itertext()),'hover instruction')
    return captions


def raw_oracle(raw):
    """SQL line-level EXISTS independently calculates eligible order contributions."""
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE lines (oid TEXT, category TEXT, sales REAL)')
    db.executemany('INSERT INTO lines VALUES (?,?,?)',raw)
    db.execute('CREATE INDEX lookup ON lines(oid,category)')
    categories = [r[0] for r in db.execute('SELECT DISTINCT category FROM lines ORDER BY category')]
    expected = {}
    for a in categories:
        for b in [None]+categories:
            if a==b:
                expected[a,b or 'NONE'] = {}
                continue
            if b is None:
                query = 'SELECT a.oid,SUM(a.sales) FROM lines a WHERE a.category=? AND NOT EXISTS (SELECT 1 FROM lines b WHERE b.oid=a.oid AND b.category<>a.category) GROUP BY a.oid'
                expected[a,'NONE'] = {oid:(sales,None) for oid,sales in db.execute(query,(a,))}
            else:
                query = 'SELECT a.oid,SUM(a.sales) FROM lines a WHERE a.category=? AND EXISTS (SELECT 1 FROM lines b WHERE b.oid=a.oid AND b.category=?) GROUP BY a.oid'
                left = dict(db.execute(query,(a,b)))
                right = dict(db.execute(query,(b,a)))
                require(left.keys()==right.keys(),'oracle order symmetry')
                expected[a,b] = {oid:(sales,right[oid]) for oid,sales in left.items()}
    db.close()
    return categories,expected


def compare_model(pairs,facts,categories,expected):
    # acceptance: none-single-category, distinct-order-counts, contribution-sales, missing-pairs
    pairmap = {key:(row,col) for key,row,col,sort in pairs}
    require(len(pairmap)==len(pairs)==len(categories)*(len(categories)+1),'complete unique pair domain')
    require(set(pairmap.values())==set(expected),'exact pair domain')
    for key,row,col,sort in pairs:
        require(sort==(-([None]+categories).index(None if col=='NONE' else col)),'numeric column ordering')
    actual = defaultdict(dict)
    empty = set()
    for key,oid,left,right in facts:
        require(key in pairmap,'foreign key closure')
        cell=pairmap[key]
        if oid is None:
            require(left is None and right is None,'empty scaffolds contain no sales')
            require(cell not in empty,'duplicate scaffold')
            empty.add(cell)
            continue
        require(oid not in actual[cell],'duplicate order/cell contribution multiplies sales')
        actual[cell][oid]=(left,right)
    report=[]
    for cell,wanted in expected.items():
        got=actual[cell]
        require(got.keys()==wanted.keys(),f'eligible distinct orders {cell}')
        require((cell in empty)==(not wanted),f'empty cell scaffold {cell}')
        for oid,amounts in wanted.items():
            for i in [0,1]:
                x,y=got[oid][i],amounts[i]
                require((x is None and y is None) or (x is not None and y is not None and math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-8)),f'sales fanout/loss {cell} {oid}')
        n=len(got)
        sums=[sum(v[i] or 0 for v in got.values()) if any(v[i] is not None for v in got.values()) else None for i in [0,1]]
        # These are the emitted SUM / COUNTD formulas, whose exact syntax and bindings are checked above.
        means=[x/n if x is not None and n else None for x in sums]
        visible=categories.index(cell[0])+1 >= ([None]+categories).index(None if cell[1]=='NONE' else cell[1])+1
        report.append({'row':cell[0],'column':cell[1],'orders':n,'row_average':means[0],'column_average':means[1],'visible':visible,'blank':not n})
    return report


def rejected(label, fn):
    try:
        fn()
    except AssertionError:
        return label
    raise AssertionError('mutation survived: '+label)


def mutations(root,pairs,facts,categories,expected):
    killed=[]
    def xml_change(label, change):
        mutant=deepcopy(root);change(mutant)
        killed.append(rejected(label,lambda:contracts(mutant)))
    def calc(r,caption):
        return r.find(f'datasources/datasource/column[@caption="{caption}"]/calculation')
    xml_change('COUNT-instead-of-COUNTD',lambda r:calc(r,'Orders').set('formula','COUNT([Order ID])'))
    xml_change('reversed-triangle',lambda r:calc(r,'Triangle').set('formula',calc(r,'Triangle').get('formula').replace('>=','<=')))
    xml_change('LOD-insertion',lambda r:calc(r,'Orders').set('formula','{FIXED : COUNTD([Order ID])}'))
    xml_change('wrong-sales-denominator',lambda r:calc(r,'Average Row Sales').set('formula','AVG([Row Sales])'))
    xml_change('NONE-plural-text',lambda r:calc(r,'Category Word').set('formula','"SUB-CATEGORIES"'))
    xml_change('missing-formula-dependency',lambda r:r.find('.//worksheet//datasource-dependencies/column[@caption="Orders"]').getparent().remove(r.find('.//worksheet//datasource-dependencies/column[@caption="Orders"]')))
    xml_change('wrong-tablecalc-addressing',lambda r:r.find('.//worksheet//table-calc[@ordering-field]').set('ordering-type','Rows'))
    xml_change('lost-tablecalc-user-role',lambda r:r.find('.//worksheet//column-instance[table-calc]').set('derivation','None'))
    xml_change('wrong-sort-direction',lambda r:r.find('.//worksheet//computed-sort').set('direction','ASC'))
    xml_change('missing-row-shelf',lambda r:setattr(r.find('.//worksheet/table/rows'),'text',''))
    xml_change('broken-tooltip-reference',lambda r:setattr(r.find('.//customized-tooltip/formatted-text/run'),'text','<[missing].[unknown]>'))
    xml_change('custom-format-prefix',lambda r:r.find('datasources/datasource/column[@caption="Average Row Sales"]').set('default-format','$0.00'))
    xml_change('extra-sheet',lambda r:r.find('worksheets').append(deepcopy(r.find('worksheets/worksheet'))))
    xml_change('relationship-wrong-key',lambda r:r.find('.//object-graph/relationships/relationship/expression/expression').set('op','[Row Category]'))
    xml_change('wrong-mark',lambda r:r.find('.//worksheet//pane/mark').set('class','Circle'))
    bad=deepcopy(facts); i=next(i for i,x in enumerate(bad) if x[1] is not None);bad[i][2]*=2
    killed.append(rejected('joined-line-sales-multiplication',lambda:compare_model(pairs,bad,categories,expected)))
    bad=deepcopy(facts);bad.append(deepcopy(bad[i]))
    killed.append(rejected('duplicate-order-cell',lambda:compare_model(pairs,bad,categories,expected)))
    bad=deepcopy(facts); key=next(x[0] for x in pairs if x[2]=='NONE');bad.append([key,'not-a-single-category-order',12,None])
    killed.append(rejected('NONE-includes-multicategory',lambda:compare_model(pairs,bad,categories,expected)))
    bad=deepcopy(pairs);bad[0][3]=-99
    killed.append(rejected('corrupted-column-sort-data',lambda:compare_model(bad,facts,categories,expected)))
    return killed


def verify():
    workbook=HERE/'outputs/replicated-workbook.twbx'
    with zipfile.ZipFile(workbook) as archive:
        root=E.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.twb'))))
        contracts(root)
        with tempfile.TemporaryDirectory() as temp:
            data=Path(temp)/'model.hyper'
            data.write_bytes(archive.read('matrix.hyper'))
            with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
                with Connection(process.endpoint,str(next((HERE/'inputs').glob('*.hyper')))) as conn:
                    tables=conn.catalog.get_table_names('Extract')
                    raw=conn.execute_list_query(f'SELECT "Order ID","Sub-Category","Sales" FROM {tables[0]}')
                    other=conn.execute_list_query(f'SELECT "Order ID","Sub-Category","Sales" FROM {tables[1]}')
                    require(sorted(raw)==sorted(other),'two packaged source copies agree')
                with Connection(process.endpoint,str(data)) as conn:
                    pairs=conn.execute_list_query('SELECT * FROM "Extract"."Pairs"')
                    facts=conn.execute_list_query('SELECT * FROM "Extract"."Contributions"')
    categories,expected=raw_oracle(raw)
    result=compare_model(pairs,facts,categories,expected)
    killed=mutations(root,pairs,facts,categories,expected)
    # acceptance: adversarial-fixtures. Builder exercised on independent tiny raw-line fixtures.
    from build_replication import prepare_model
    fixture=[('single','C',7),('single','C',3),('pair','A',10),('pair','A',20),('pair','B',5),('pair','B',8),('triple','A',1),('triple','B',2),('triple','C',4),('solo','D',9)]
    fc,fe=raw_oracle(fixture);fp,ff=prepare_model(fixture)
    synthetic=compare_model(fp,ff,fc,fe)
    require(fe['C','NONE']=={'single':(10.0,None)},'duplicate lines still single category')
    require(fe['A','B']['pair']==(30.0,13.0),'asymmetric category contribution')
    require(not fe['D','A'],'missing pair remains blank')
    require(all(not row['visible'] for row in synthetic if row['row']==row['column']),'diagonal excluded')
    # acceptance: provenance. Supports an installed distribution, not a mandatory git checkout.
    provenance=json.loads((HERE/'outputs/build-provenance.json').read_text())
    digest=sha256(workbook.read_bytes()).hexdigest()
    require(provenance['workbook_sha256']==digest,'build provenance binds current workbook')
    require(provenance['version'] and provenance['module_sha256'],'explicit SDK provenance')
    report={'workbook_sha256':digest,'sdk_version':provenance['version'],'raw_lines':len(raw),'categories':len(categories),
            'cells_checked':len(result),'visible_cells':sum(x['visible'] for x in result),
            'mutations_rejected':killed,'synthetic_cells_checked':len(synthetic),'cells':result,
            'runtime_status':'NOT RUN: parent owns Desktop, render and hover checks'}
    (HERE/'outputs/verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(result)} cells; {len(synthetic)} synthetic cells; {len(killed)} mutations rejected; SHA256 {digest}')

def verify_frozen():
    # Historical probes are checked only here; CI deletes copied workbooks before rebuilding.
    manifest=json.loads((HERE/'evidence/frozen-manifest.json').read_text())
    for relative,digest in manifest['sha256'].items():
        require(sha256((HERE/relative).read_bytes()).hexdigest()==digest,f'frozen hash mismatch {relative}')
    print('PASS: frozen source, evidence, primary workbook and historical probe hashes')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--frozen',action='store_true',help='Verify frozen bytes and historical archives without rebuilding')
    if parser.parse_args().frozen:
        verify_frozen()
    else:
        verify()
