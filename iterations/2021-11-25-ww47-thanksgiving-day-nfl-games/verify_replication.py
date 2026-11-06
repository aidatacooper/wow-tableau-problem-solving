"""Independent raw-data oracle versus packaged data + emitted calculation semantics.
The raw oracle does not import builder logic. SQLite evaluates the emitted row-level IF/subtraction subset.
This is an offline evaluator, not a claim that Tableau rendered or executed it.
"""
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
import json,re,sqlite3,tempfile,zipfile,hashlib
from lxml import etree
from tableauhyperapi import HyperProcess,Connection,Telemetry
HERE=Path(__file__).resolve().parent

def read_rows(path):
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint,str(path)) as c:
            return [[str(v) if hasattr(v,'year') else v for v in row] for row in c.execute_list_query('SELECT * FROM "Extract"."Extract"')]

def oracle(raw):
    groups=defaultdict(list)
    for d,v,a,h,s in raw: groups[h].append((str(d),v,int(a),int(s)))
    expected={}
    for home,games in groups.items():
        wins=len([g for g in games if g[3]>g[2]]); losses=len([g for g in games if g[3]<g[2]])
        byyear={int(g[0][:4]):g for g in games}; assert len(byyear)==len(games)
        for year in range(min(byyear),max(byyear)+1):
            cumulative=sum((s>a)-(s<a) for d,v,a,s in games if int(d[:4])<=year)
            g=byyear.get(year)
            expected[home,year]={'game':g,'cumulative':cumulative,'total':str(len(games)),'record':f'{wins}-{losses}-{len(games)-wins-losses}','rate':f'{wins/len(games):.0%}'}
    return expected

def formulas(root):
    return {c.get('caption'):c.find('calculation').get('formula') for c in root.findall('./datasources/datasource/column') if c.find('calculation') is not None}

def evaluate(formula,h,a):
    sql=re.sub(r'ISNULL\((\[[^]]+\])\)',r'(\1 IS NULL)',formula)
    sql=re.sub(r'\bELSEIF\b','WHEN',sql); sql=re.sub(r'\bIF\b','CASE WHEN',sql)
    db=sqlite3.connect(':memory:')
    try: return db.execute('SELECT '+sql+' FROM (SELECT ? AS [Home Score], ? AS [Visiting Score])',(h,a)).fetchone()[0]
    finally: db.close()

def check(root,rows,raw):
    # acceptance: game-identity, score-direction, team-summary, cumulative-gaps
    f=formulas(root); expected=oracle(raw); assert len(rows)==len(expected)
    seen=set()
    for year,home,day,away,h,a,identity,total,record,rate,cumulative,tip in rows:
        key=(home,year); assert key not in seen; seen.add(key); want=expected[key]
        assert (total,record,rate,cumulative)==(want['total'],want['record'],want['rate'],want['cumulative'])
        outcome=evaluate(f['Result'],h,a); difference=evaluate(f['Score Difference'],h,a)
        if want['game']:
            d,v,vs,hs=want['game']; assert (str(day),away,h,a,identity)==(d,v,hs,vs,f'{d}|{home}|{v}')
            assert outcome==((hs>vs)-(hs<vs)) and difference==hs-vs
            verb='won' if hs>vs else 'lost' if hs<vs else 'tied'
            assert tip==f'{d}: {home} {verb} vs {v}, {max(hs,vs)}–{min(hs,vs)}'
        else: assert h is None and a is None and identity=='' and outcome is None and difference is None
    # Synthetic tie, missing game, loss and win execute actual emitted expressions.
    for h,a,w in [(7,7,0),(None,None,None),(3,24,-1),(31,0,1)]: assert evaluate(f['Result'],h,a)==w
    # acceptance: chart-contract
    sheets=root.findall('./worksheets/worksheet')
    assert len(sheets)==1
    game=sheets[0]; assert game.get('name')=='Game Results'
    deps=game.find('table/view/datasource-dependencies')
    ds=deps.get('datasource')
    source=root.find(f'./datasources/datasource[@name="{ds}"]')
    columns={c.get('name'):c for c in source.findall('column')}
    local={c.get('name'):c for c in deps.findall('column')}
    instances={c.get('name'):c for c in deps.findall('column-instance')}
    ids={c.get('caption'):c.get('name').strip('[]') for c in columns.values() if c.get('caption')}
    def ref(name): return f'[{ds}].[{name}]'
    result=ref('sum:'+ids['Result']+':qk')
    cumulative=ref('sum:Cumulative Differential:qk')
    date_ref=ref('tyr:Game Date:qk')
    refs=lambda text:re.findall(r'\[[^]]+\]\.\[[^]]+\]',text or '')
    rowrefs=refs(game.findtext('table/rows'))
    assert rowrefs==[ref('none:'+n+':nk') for n in ('Home Team','Total Games','W-L-T','Win %')]+[result,result,cumulative]
    assert refs(game.findtext('table/cols'))==[date_ref]
    assert not game.findall('.//sort[@direction="DESC"]')
    # Every qualified reference in shelves, encodings, styles and tooltip text
    # resolves to an instance, a dependency column and a datasource column.
    for full in refs(etree.tostring(game).decode()):
        prefix,instance=full.split('].',1); assert prefix+']'==f'[{ds}]'
        assert instance in instances, ('missing instance',full)
        column=instances[instance].get('column')
        assert column in local and column in columns, ('missing column',column)
    for name,c in local.items():
        assert name in columns
        original=columns[name]
        assert c.get('datatype')==original.get('datatype'), ('dependency type',name)
        calc=c.find('calculation')
        if calc is not None:
            assert calc.get('formula')==original.find('calculation').get('formula')
            for field in re.findall(r'\[[^]]+\]',calc.get('formula')):
                assert field in local and field in columns
    panes=game.findall('table/panes/pane')
    assert [p.find('mark').get('class') for p in panes]==['Bar','Circle','Area']
    bar,circle,area=panes
    assert [p.get('y-axis-name') for p in panes]==[result,result,cumulative]
    assert bar.get('y-index') is None and circle.get('y-index')=='1' and area.get('y-index') is None
    for p in (bar,circle):
        assert p.find('encodings/lod').get('column')==ref('none:Game Identity:nk')
        assert p.find('encodings/tooltip') is not None
        assert p.find('encodings/tooltip').get('column')==ref('attr:Game Tooltip:nk')
    assert circle.find('encodings/color').get('column')==ref('sum:'+ids['Score Difference']+':qk')
    assert not area.findall('encodings/lod')
    # Every custom-tooltip token is queried in that pane or is already on a shelf.
    for p in panes:
        queried=set(rowrefs+[date_ref]+[x.get('column') for x in p.findall('encodings/*')])
        tokens=refs(etree.tostring(p.find('customized-tooltip')).decode())
        assert tokens and set(tokens)<=queried, ('unqueried tooltip token',tokens,queried)
    folds=game.findall('table/style/style-rule[@element="axis"]/encoding[@fold="true"]')
    assert len(folds)==1
    fold=folds[0]
    assert (fold.get('field'),fold.get('class'),fold.get('scope'),fold.get('synchronized'))==(result,'1','rows','true')
    # acceptance: readable-lollipop. Native screen-size marks must not scale to
    # continuous-date bin width. These authored units are not literal pixels.
    for pane in (bar,circle):
        sizing=pane.find('mark-sizing')
        assert sizing is not None and sizing.get('mark-sizing-setting')=='marks-scaling-off'
        assert not pane.findall('encodings/size')
    stem=float(bar.find('style/style-rule[@element="mark"]/format[@attr="size"]').get('value'))
    dot=float(circle.find('style/style-rule[@element="mark"]/format[@attr="size"]').get('value'))
    assert 0.005<=stem<=0.02 and 1.2<=dot<=1.8 and dot/stem>=60
    assert columns['['+ids['Result']+']'].get('default-format')=='*"Win";"Loss";"Tie"'
    hidden=game.findall('table/style/style-rule[@element="axis"]/format[@attr="display"]')
    assert any(x.get('field')==result and x.get('class')=='1' and x.get('scope')=='rows' and x.get('value')=='false' for x in hidden)
    colorref=ref('sum:'+ids['Score Difference']+':qk')
    palette=game.find('table/style/style-rule[@element="mark"]/encoding[@attr="color"]')
    assert palette is not None and palette.get('field')==colorref
    assert palette.get('palette')=='orange-blue-diverging' and float(palette.get('center'))==0
    legends=root.findall('./dashboards/dashboard/zones//zone[@type-v2="color"]')
    assert len(legends)==1
    legend=legends[0]
    assert legend.get('name')=='Game Results' and legend.get('param')==colorref
    assert legend.get('pane-specification-id')==circle.get('id')
    assert legend.get('show-title')!='false' and float(legend.get('h'))>=5000
    # Legend query resolves to the same Circle encoding/dependency, not a free label.
    assert legend.get('param')==circle.find('encodings/color').get('column')


def verify():
    raw=read_rows(HERE/'inputs/NFL Thanksgiving Games.hyper')
    artifact=HERE/'outputs/replicated-workbook.twbx'
    with zipfile.ZipFile(artifact) as z, tempfile.TemporaryDirectory() as tmp:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        hp=Path(tmp)/'data.hyper'; hp.write_bytes(z.read(next(n for n in z.namelist() if n.endswith('.hyper')))); rows=read_rows(hp)
    from cwtwb.validator import validate_against_schema
    schema=validate_against_schema(root)
    schema_report={'schema_available':schema.schema_available,'errors':schema.errors,'compatibility_warnings':schema.compatibility_warnings}
    (HERE/'evidence/xsd.json').write_text(json.dumps(schema_report,indent=2))
    assert schema.schema_available and not schema.errors
    check(root,rows,raw)
    # Exercise the production transform with shuffled synthetic games, a tie,
    # multiple teams and an interior missing year; oracle remains independent.
    from build_replication import prepare_rows
    synthetic=[['2003-11-27','Away',10,'B',3],['2000-11-23','Away',7,'A',7],['2002-11-28','Away',0,'A',21],['2000-11-23','Away',3,'B',10]]
    check(root,prepare_rows(synthetic),synthetic)
    # acceptance: mutation-rejection
    mutations=[]
    def reject(name,change):
        r=deepcopy(root); data=deepcopy(rows); change(r,data)
        try: check(r,data,raw)
        except (AssertionError,KeyError,sqlite3.Error): mutations.append(name); return
        raise AssertionError('Mutation survived: '+name)
    def formula(r,caption,text):
        for c in r.findall('./datasources/datasource/column'):
            if c.get('caption')==caption: c.find('calculation').set('formula',text)
    reject('reverse-home-away',lambda r,d:formula(r,'Score Difference','[Visiting Score]-[Home Score]'))
    reject('tie-counts-as-win',lambda r,d:formula(r,'Result',formulas(r)['Result'].replace('ELSE 0.0','ELSE 1.0')))
    reject('loss-sign',lambda r,d:formula(r,'Result',formulas(r)['Result'].replace('THEN -1.0','THEN 1.0')))
    reject('corrupt-cumulative',lambda r,d:d[10].__setitem__(10,d[10][10]+1))
    reject('wrong-denominator',lambda r,d:d[0].__setitem__(9,'100%'))
    reject('wrong-record',lambda r,d:d[0].__setitem__(8,'0-0-0'))
    reject('swap-opponent',lambda r,d:d[0].__setitem__(3,'Wrong team'))
    reject('remove-missing-year',lambda r,d:d.pop(next(i for i,x in enumerate(d) if x[4] is None)))
    reject('remove-stems',lambda r,d:r.find('.//mark[@class="Bar"]').set('class','Circle'))
    reject('remove-area',lambda r,d:r.find('.//mark[@class="Area"]').set('class','Line'))
    reject('sum-becomes-average',lambda r,d:setattr(r.find('.//worksheet/table/rows'),'text',r.findtext('.//worksheet/table/rows').replace('sum:Cumulative','avg:Cumulative')))
    reject('date-order-descending',lambda r,d:etree.SubElement(r.find('.//worksheet/table/view'),'sort',direction='DESC'))
    def remove(r,path):
        element=r.find(path); assert element is not None; element.getparent().remove(element)
    reject('missing-tooltip-query',lambda r,d:remove(r,'.//pane/encodings/tooltip'))
    reject('missing-dependency',lambda r,d:remove(r,'.//datasource-dependencies/column'))
    reject('missing-instance',lambda r,d:remove(r,'.//datasource-dependencies/column-instance'))
    reject('wrong-duplicate-index',lambda r,d:r.find('.//pane[@y-index="1"]').set('y-index','2'))
    reject('wrong-fold-scope',lambda r,d:r.find('.//encoding[@fold="true"]').set('scope','cols'))
    reject('unsynchronized-fold',lambda r,d:r.find('.//encoding[@fold="true"]').set('synchronized','false'))
    reject('area-axis-omitted',lambda r,d:setattr(r.find('.//worksheet/table/rows'),'text',r.findtext('.//worksheet/table/rows').replace('sum:Cumulative Differential:qk','sum:Missing:qk')))
    reject('stem-autoscaling',lambda r,d:r.find('.//pane/mark-sizing').set('mark-sizing-setting','marks-scaling-on'))
    reject('pixel-sized-dots',lambda r,d:r.find('.//pane[@id="2"]/style/style-rule/format[@attr="size"]').set('value','0.12'))
    reject('block-width-stems',lambda r,d:r.find('.//pane[@id="1"]/style/style-rule/format[@attr="size"]').set('value','1.0'))
    reject('missing-color-legend',lambda r,d:remove(r,'.//zone[@type-v2="color"]'))
    reject('legend-wrong-pane',lambda r,d:r.find('.//zone[@type-v2="color"]').set('pane-specification-id','1'))
    reject('color-not-zero-centered',lambda r,d:r.find('.//encoding[@attr="color"][@palette]').set('center','20'))
    def remove_number_format_prefix(r,d):
        for c in r.findall('./datasources/datasource/column'):
            if c.get('caption')=='Result': c.set('default-format','"Win";"Loss";"Tie"')
    reject('invalid-custom-number-format',remove_number_format_prefix)
    report={'raw_games'  :len(raw),'packaged_year_rows':len(rows),'numerical_comparisons':'all packaged game outcomes, score differences, cumulative values and summary values versus independent raw oracle','mutations_rejected':mutations,'synthetic_cases':['tie','null missing game','loss','win'],'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'live_Tableau':'pending'}
    (HERE/'evidence/verification.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
def probe():
    from cwtwb import TWBEditor
    e=TWBEditor('')
    for name in ('X','Outcome','Cumulative'): e.add_calculated_field(name,'1.0',datatype='real')
    e.add_worksheet('Probe')
    e.configure_layered_chart('Probe',columns=['SUM(X)'],rows=['SUM(Outcome)','SUM(Outcome)','SUM(Cumulative)'],panes=[{'axis':'SUM(Outcome)','mark_type':'Bar'},{'axis':'SUM(Outcome)','mark_type':'Circle'},{'axis':'SUM(Cumulative)','mark_type':'Area'}],fold_axes=False)
    e.configure_worksheet_style('Probe',axis_style={'encodings':[{'field':'SUM(Outcome)','class':'1','scope':'rows','fold':True,'synchronized':True}]})
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'probe.twb'; e.save(p); root=etree.parse(str(p))
        folds=root.findall('.//style-rule[@element="axis"]/encoding[@fold="true"]')
        panes=root.findall('.//worksheet/table/panes/pane')
        assert len(folds)==1 and folds[0].get('field')==panes[1].get('y-axis-name')
        assert panes[1].get('y-index')=='1' and folds[0].get('field')!=panes[2].get('y-axis-name')
        assert all(p.get('y-axis-name') in root.findtext('.//worksheet/table/rows') for p in panes)
        print('PASS: published a2 supports selective duplicate-axis folding with explicit row shelves and public axis_style. Previous impossibility claim withdrawn.')

if __name__=='__main__':
    import sys
    probe() if '--sdk-probe' in sys.argv else verify()
