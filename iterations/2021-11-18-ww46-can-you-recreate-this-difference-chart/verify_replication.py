"""Independent raw-row oracle and constrained evaluator of emitted Tableau formulas.

No builder import. This is not a Tableau runtime: it evaluates only the formula
subset used here and rejects all unknown syntax rather than guessing semantics.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date
from pathlib import Path
import hashlib, json, math, re, tempfile, zipfile
from lxml import etree as ET
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'outputs/replicated-workbook.twbx'
RAW = HERE / 'inputs/federated_1vsdkg41w50rva1bkcpyx0.hyper'

class Parser:
    def __init__(self, text):
        self.tokens = re.findall(r'\[[^\]]+\]|\d+(?:\.\d+)?|[A-Za-z_]+|[{}():,=+\-]', text)
        assert ''.join(self.tokens) == re.sub(r'\s+', '', re.sub(r'\[([^\]]+)\]', lambda m:m[0].replace(' ', '\x01'), text)).replace('\x01',' '), 'Unsupported formula syntax'
        self.i = 0
    def take(self, expected=None):
        t = self.tokens[self.i]; self.i += 1
        assert expected is None or t.upper() == expected, (expected, t)
        return t
    def expr(self, minimum=0):
        t = self.take()
        if t.upper() == 'IF':
            condition = self.expr(); self.take('THEN'); yes = self.expr(); self.take('END')
            left = ('if', condition, yes)
        elif t == '{':
            self.take('FIXED'); self.take(':'); left = ('fixed', self.expr()); self.take('}')
        elif t.startswith('['): left = ('ref', t)
        elif t[0].isdigit(): left = ('literal', float(t))
        elif t.upper() == 'NULL': left = ('literal', None)
        else:
            self.take('('); args = [self.expr()]
            while self.tokens[self.i] == ',': self.take(); args.append(self.expr())
            self.take(')'); left = (t.upper(), *args)
        while self.i < len(self.tokens) and self.tokens[self.i] in ('=', '-', '+'):
            op = self.tokens[self.i]; priority = 1 if op == '=' else 2
            if priority < minimum: break
            self.take(); left = (op, left, self.expr(priority + 1))
        return left
    def parse(self):
        node = self.expr(); assert self.i == len(self.tokens); return node

class Model:
    def __init__(self, root):
        self.root = root
        self.fixed_cache = {}
        self.columns = {c.get('name'): c for c in root.findall('./datasources/datasource/column')}
        self.names = {c.get('caption', n.strip('[]')): n for n,c in self.columns.items()}
        self.formulas = {n: Parser(c.find('calculation').get('formula')).parse()
                         for n,c in self.columns.items() if c.find('calculation') is not None}
        self.ws = root.find("./worksheets/worksheet[@name='Viz']")
        self.instances = {c.get('name'): (c.get('column'), c.get('derivation')) for c in self.ws.findall('.//column-instance')}
        self.ds = root.find('./datasources/datasource').get('name')
    def ref(self, name, derivation='None'):
        local = self.names.get(name, '['+name+']')
        return '['+self.ds+'].'+next(n for n,v in self.instances.items() if v == (local,derivation))
    def evaluate(self, node, group, universe, row=None):
        op, *args = node
        ev = lambda n: self.evaluate(n, group, universe, row)
        if op == 'literal': return args[0]
        if op == 'ref':
            n=args[0]
            if n in self.formulas: return ev(self.formulas[n])
            return (row if row is not None else group[0])[n.strip('[]')]
        if op == 'fixed':
            key=(node,id(universe))
            if key not in self.fixed_cache:self.fixed_cache[key]=self.evaluate(args[0],universe,universe)
            return self.fixed_cache[key]
        if op == 'if': return ev(args[1]) if ev(args[0]) else None
        if op in ('SUM','MIN','MAX') and len(args)==1:
            values=[self.evaluate(args[0],group,universe,r) for r in group]
            values=[v for v in values if v is not None]
            if not values:return None
            return {'SUM':math.fsum,'MIN':min,'MAX':max}[op](values)
        values=[ev(a) for a in args]
        if any(v is None for v in values):return None
        if op=='YEAR':return values[0].year
        if op=='MAX':return max(values)
        if op=='=':return values[0]==values[1]
        if op=='-':return values[0]-values[1]
        if op=='+':return values[0]+values[1]
        raise AssertionError('Unsupported operation '+op)
    def bound(self, reference, group, universe):
        local=reference.split('].',1)[1]
        column, derivation=self.instances[local]
        node=('ref',column)
        if derivation in ('Sum','Min','Max'):node=(derivation.upper(),node)
        return self.evaluate(node,group,universe)

def load_rows(connection, path, spacer=False):
    with Connection(connection, str(path)) as c:
        cols=['Order Date','Segment','Category','Sales']+(['Spacer'] if spacer else [])
        rows=c.execute_list_query('SELECT '+','.join('"'+x+'"' for x in cols)+' FROM "Extract"."Extract"')
    return [dict(zip(cols,[date(r[0].year,r[0].month,r[0].day),*r[1:]])) for r in rows]

def oracle(rows):
    latest=max(r['Order Date'].year for r in rows)
    groups=defaultdict(list)
    for row in rows:groups[(row['Category'],row['Segment'])].append(row)
    out={}
    for key,group in groups.items():
        totals=[]
        for year in (latest-1,latest):
            values=[r['Sales'] for r in group if r['Order Date'].year==year and r['Sales'] is not None]
            totals.append(math.fsum(values) if values else None)
        previous,current=totals
        delta=None if None in totals else current-previous
        out[key]=(previous,current,delta,None if delta is None else delta<=0)
    return latest,out,groups

def assert_same_data(raw, packaged):
    cols=('Order Date','Segment','Category','Sales')
    assert Counter(tuple(r[k] for k in cols) for r in raw)==Counter(tuple(r[k] for k in cols) for r in packaged), 'Packaged sales rows changed'
    assert all(r['Spacer'] is None for r in packaged), 'Spacer must always be NULL'

def candidate_identity():
    import cwtwb, os, subprocess, tomllib
    source=Path(os.environ['CWTWB_SRC']).resolve()
    assert Path(cwtwb.__file__).resolve().is_relative_to(source), 'SDK source mismatch'
    repo=source.parent
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    assert commit=='cac8820f26e703c3858253adfa21efd989eb8a78', 'Candidate SDK changed; record a separate run'
    assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain','--','src','pyproject.toml'],text=True).strip(), 'Candidate source has uncommitted edits'
    version=tomllib.loads((repo/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    return {'sdk_version':version,'sdk_module':cwtwb.__file__,'sdk_commit':commit,'sdk_source':str(source),'candidate_only':True}

def reference_closure(root):
    """Check every qualified reference in XML attributes/text, plus formula DAGs.

    Worksheet references must resolve in that worksheet's dependencies. Physical
    fields must exist in datasource metadata; calculated fields must have matching
    source definitions. This also covers order-only dependencies and style/title/
    tooltip references, not just the numeric mark channels.
    """
    sources={d.get('name'):d for d in root.findall('./datasources/datasource')}
    virtual={'[Multiple Values]','[:Measure Names]'}
    pattern=re.compile(r'(\[[^\]]+\])\.(\[[^\]]+\])')
    definitions={};all_instances={};count=0
    for name,ds in sources.items():
        columns={c.get('name'):c for c in ds.findall('column')}
        physical={x.text for x in ds.findall('.//metadata-record[@class="column"]/local-name')}
        known=set(columns)|physical
        definitions[name]=known
        all_instances[name]={x.get('name') for x in ds.findall('column-instance')}
        for col in columns.values():
            calc=col.find('calculation')
            if calc is not None:
                for ref in re.findall(r'\[[^\]]+\]',calc.get('formula','')):
                    assert ref in known, 'Unresolved formula field '+ref
    for ws in root.findall('./worksheets/worksheet'):
        scoped={}
        for dep in ws.findall('table/view/datasource-dependencies'):
            name=dep.get('datasource');assert name in sources
            declared=dep.findall('column-instance')
            names=[x.get('name') for x in declared]
            assert len(names)==len(set(names)), 'Duplicate instance declaration'
            scoped[name]=set(names)
            for inst in declared:
                assert inst.get('column') in definitions[name], 'Instance refers to missing field'
            for col in dep.findall('column'):
                original=sources[name].find(f"column[@name='{col.get('name')}']")
                if col.find('calculation') is not None:
                    assert original is not None and original.find('calculation') is not None
                    assert col.find('calculation').get('formula')==original.find('calculation').get('formula'), 'Stale dependency formula'
        for node in ws.iter():
            for value in [*node.attrib.values(),node.text or '']:
                for prefix,field in pattern.findall(value):
                    name=prefix[1:-1]
                    assert name in scoped, 'Unresolved worksheet datasource '+name
                    assert field in scoped[name]|virtual, 'Unresolved worksheet instance '+field
                    count+=1
        for name,instances in scoped.items():all_instances[name].update(instances)
    for node in root.iter():
        for value in [*node.attrib.values(),node.text or '']:
            for prefix,field in pattern.findall(value):
                name=prefix[1:-1]
                if name in sources:
                    assert field in all_instances[name]|definitions[name]|virtual, 'Unresolved workbook reference '+field
    return {'qualified_worksheet_references_checked':count,'status':'passed'}

def contract(root):
    m=Model(root);w=m.ws
    assert len(root.findall('./worksheets/worksheet'))==1
    assert len(m.formulas)==7, 'Maximum seven calculations'
    assert w.findtext('table/rows')==f'({m.ref("Segment")} / [{m.ds}].[:Measure Names])', 'Segment partition'
    assert w.findtext('table/cols')==f'({m.ref("Category")} * ([{m.ds}].[Multiple Values] + {m.ref("PY Sales (copy)","Sum")}))', 'Category partition/dual axis'
    panes=w.findall('table/panes/pane'); assert [p.find('mark').get('class') for p in panes]==['Bar','GanttBar']
    bar,gantt=panes
    assert gantt.get('x-axis-name')==m.ref('PY Sales (copy)','Sum'), 'Gantt anchor'
    for channel in ('size','text'):assert gantt.find('encodings/'+channel).get('column')==m.ref('Difference','User'), channel
    assert gantt.find('encodings/color').get('column')==m.ref('Is Loss?','User')
    for pane in panes:
        assert pane.find("style/style-rule[@element='mark']/format[@attr='mark-labels-show']").get('value')=='true'
    assert bar.find('encodings/text').get('column')==f'[{m.ds}].[Multiple Values]'
    assert w.find("table/style/style-rule[@element='axis']/encoding[@fold='true'][@synchronized='true']") is not None
    expected=[m.ref('PY Sales','Sum'),m.ref('CY Sales','Sum'),m.ref('Spacer','Min')]
    filters=w.findall('table/view/filter');assert len(filters)==1
    members=[n.get('member').strip('"') for n in filters[0].findall('.//groupfilter[@function="member"]')]
    assert members==expected, 'Measure Names filter must exclude Gantt anchor'
    order=[n.text.strip('"') for n in w.findall('table/view/manual-sort/dictionary/bucket')]
    desired=[*expected[:2],m.ref('PY Sales (copy)','Sum'),expected[2]]
    assert order==desired, 'Required PY,CY,Gantt,Spacer manual order'
    closure=reference_closure(root)
    title=''.join(w.find('layout-options/title/formatted-text').itertext())
    for name in ('Current Year','Previous Year'):
        assert '<'+m.ref(name)+'>' in title, 'Dynamic title field missing'
        for pane in panes:assert m.ref(name) in [n.get('column') for n in pane.findall('encodings/lod')]
    assert not re.search(r'\b20\d\d\b',title), 'Hardcoded title year'
    assert m.columns[m.names['Difference']].get('default-format')=='*\u25b3#,##0;\u25bd#,##0'
    for pane in panes:
        text=''.join(pane.find('customized-tooltip/formatted-text').itertext())
        for n,d in [('PY Sales','Sum'),('CY Sales','Sum'),('Difference','User'),('Current Year','None'),('Previous Year','None')]:
            assert '<'+m.ref(n,d)+'>' in text, 'Tooltip binding'
    size=root.find('./dashboards/dashboard/size')
    assert all(size.get(k)==v for k,v in {'minwidth':'800','maxwidth':'800','minheight':'400','maxheight':'400'}.items())
    assert not root.findall('.//action')
    return m, {'filter':members,'emitted_order':order,'required_order':desired,'reference_closure':closure,'sort_contract':'passed','rendered_spacing':'pending_parent_recapture'}

def numeric(root,rows):
    m=Model(root);latest,expected,groups=oracle(rows);actual=[]
    g=m.ws.findall('table/panes/pane')[1]
    for key,group in groups.items():
        previous,current,delta,loss=expected[key]
        references=[m.ref('PY Sales','Sum'),m.ref('CY Sales','Sum'),g.find('encodings/size').get('column'),g.find('encodings/color').get('column')]
        values=[m.bound(ref,group,rows) for ref in references]
        for got,want in zip(values,(previous,current,delta,loss)):
            assert got==want or (got is not None and want is not None and math.isclose(got,want,abs_tol=1e-8)), (key,got,want)
        start=m.bound(g.get('x-axis-name'),group,rows)
        assert start==previous, 'Gantt starts at PY'
        if delta is not None:assert math.isclose(start+values[2],current,abs_tol=1e-8), 'Gantt ends at CY'
        assert m.bound(m.ref('Current Year'),group,rows)==latest
        assert m.bound(m.ref('Previous Year'),group,rows)==latest-1
        actual.append({'category':key[0],'segment':key[1],'previous':previous,'current':current,'difference':delta,'is_loss':loss})
    return actual

def expect_rejected(name, function):
    try:function()
    except (AssertionError,KeyError,ValueError,IndexError):return name
    raise AssertionError('Mutation survived: '+name)

def verify():
    preserved=json.loads((HERE/'evidence/baseline-a2-e73539d6/preservation.json').read_text())
    for record in preserved['records']:
        assert hashlib.sha256((HERE/record['archived_path']).read_bytes()).hexdigest()==record['sha256'], 'Archived evidence changed: '+record['archived_path']
    with zipfile.ZipFile(OUTPUT) as z, tempfile.TemporaryDirectory() as tmp:
        root=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        data=Path(tmp)/'data.hyper';data.write_bytes(z.read(next(n for n in z.namelist() if n.endswith('.hyper'))))
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
            raw=load_rows(h.endpoint,RAW);packaged=load_rows(h.endpoint,data,True)
    # acceptance: raw-data-integrity, difference-direction, emitted-contract,
    # dynamic-years, signed-labels, measure-filter, negative-mutations, reference-closure
    assert_same_data(raw,packaged)
    m,details=contract(root);values=numeric(root,packaged)
    synthetic=[{'Order Date':date(y,1,1),'Category':c,'Segment':s,'Sales':v,'Spacer':None}
               for c,s,p,curr in [('A','gain',10,14),('A','loss',20,3),('B','zero',9,9),('B','fraction',0.1,0.3)]
               for y,v in [(2036,p),(2037,curr)]]
    numeric(root,synthetic)
    missing=synthetic+[{'Order Date':date(2037,2,1),'Category':'C','Segment':'no-prior','Sales':4,'Spacer':None}]
    numeric(root,missing)
    rejected=[]
    def mutate_formula(name,formula):
        changed=deepcopy(root);node=changed.find(f"./datasources/datasource/column[@caption='{name}']/calculation");node.set('formula',formula)
        return changed
    delta=m.columns[m.names['Difference']].find('calculation').get('formula')
    rejected.append(expect_rejected('reverse-subtraction',lambda:numeric(mutate_formula('Difference','-'.join(reversed(delta.split('-')))),packaged)))
    rejected.append(expect_rejected('wrong-year-offset',lambda:numeric(mutate_formula('Previous Year',m.names['Current Year']+'-2'),packaged)))
    rejected.append(expect_rejected('hardcoded-latest-year',lambda:numeric(mutate_formula('Current Year','2021'),synthetic)))
    rejected.append(expect_rejected('zero-is-gain',lambda:numeric(mutate_formula('Is Loss?','MAX(1,'+m.names['Difference']+')=0'),synthetic)))
    for name,xpath,attribute,value in [
        ('missing-category','./worksheets/worksheet/table/cols',None,'x'),
        ('wrong-gantt-size','./worksheets/worksheet/table/panes/pane[2]/encodings/size','column',m.ref('PY Sales','Sum')),
        ('wrong-label','./worksheets/worksheet/table/panes/pane[2]/encodings/text','column',m.ref('CY Sales','Sum')),
        ('static-title','./worksheets/worksheet/layout-options/title/formatted-text/run[2]',None,'2021 compared with 2020'),
        ('extra-bar-filter','./worksheets/worksheet/table/view/filter/groupfilter/groupfilter[3]','member','"'+m.ref('PY Sales (copy)','Sum')+'"'),
    ]:
        changed=deepcopy(root);node=changed.find(xpath)
        if attribute:node.set(attribute,value)
        else:node.text=value
        rejected.append(expect_rejected(name,lambda:contract(changed)))
    for name, edit in [
        ('baseline-three-item-order', lambda r: r.find('./worksheets/worksheet/table/view/manual-sort/dictionary').remove(r.find('./worksheets/worksheet/table/view/manual-sort/dictionary/bucket[3]'))),
        ('missing-anchor-instance', lambda r: r.find('./worksheets/worksheet/table/view/datasource-dependencies').remove(r.find(f"./worksheets/worksheet/table/view/datasource-dependencies/column-instance[@name='{m.ref('PY Sales (copy)','Sum').split('].',1)[1]}']"))),
        ('dangling-style-reference', lambda r: r.find("./worksheets/worksheet/table/style/style-rule[@element='axis']/encoding").set('field',f'[{m.ds}].[sum:Missing:qk]')),
        ('dangling-formula-reference', lambda r: r.find("./datasources/datasource/column[@caption='PY Sales (copy)']/calculation").set('formula','[Missing]')),
    ]:
        changed=deepcopy(root);edit(changed)
        checker=contract if name=='baseline-three-item-order' else reference_closure
        rejected.append(expect_rejected(name,lambda:checker(changed)))
    corrupt=deepcopy(packaged);corrupt[0]['Sales']+=1
    rejected.append(expect_rejected('changed-packaged-value',lambda:assert_same_data(raw,corrupt)))
    corrupt=deepcopy(packaged);corrupt[0]['Spacer']=0
    rejected.append(expect_rejected('non-null-spacer',lambda:assert_same_data(raw,corrupt)))
    from cwtwb.validator import validate_against_schema
    schema=validate_against_schema(root)
    assert schema.schema_available and not schema.errors, str(schema.errors)
    import cwtwb, importlib.metadata, os
    assert os.environ.get('CWTWB_SRC'), 'Set explicit CWTWB_SRC'
    assert Path(cwtwb.__file__).resolve().is_relative_to(Path(os.environ['CWTWB_SRC']).resolve()), 'SDK source mismatch'
    report={**candidate_identity(),'artifact_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'preserved_baseline_files_checked':len(preserved['records']),'raw_rows':len(raw),'groups':values,'positive_scenarios':['all nine raw groups','gain/loss/zero/fraction','2037 rollover','missing prior year'],
        'rejected_mutations':rejected,'contract':details,'xsd_errors':schema.errors,
        'compatibility_warnings':schema.compatibility_warnings,'status':'PASS candidate local contract; rendered spacing and runtime pending'}
    (HERE/'evidence/local-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=True),encoding='utf-8')
    print(f'PASS local partial contract: {len(raw)} rows, {len(values)} groups, {len(rejected)} rejected mutations; required sort/filter PASS; runtime pending')
def sdk_probe():
    """Author-free, data-free reproducer for inline NULL and independent order."""
    from cwtwb import TWBEditor
    import cwtwb, importlib.metadata
    report={'version':importlib.metadata.version('cwtwb'),'module':cwtwb.__file__,'probes':[]}
    with tempfile.TemporaryDirectory() as tmp:
        for include_anchor in (False,True):
            e=TWBEditor('')
            for name,value in [('Earlier','10'),('Later','15'),('Anchor','10'),('Spacer','NULL')]:
                e.add_calculated_field(name,value)
            e.add_worksheet('Synthetic')
            measures=['SUM(Earlier)','SUM(Later)']+(['SUM(Anchor)'] if include_anchor else [])+['MIN(Spacer)']
            e.configure_layered_chart('Synthetic', columns=['Multiple Values','SUM(Anchor)'], rows=['Measure Names'],axis_shelf='columns',panes=[
                {'axis':'Multiple Values','mark_type':'Bar','measure_values':measures},
                {'axis':'SUM(Anchor)','mark_type':'GanttBar'}])
            path=Path(tmp)/('included.twb' if include_anchor else 'excluded.twb');e.save(str(path), validate=False)
            root=ET.parse(str(path)).getroot()
            view=root.find('./worksheets/worksheet/table/view')
            members=[n.get('member').strip('"') for n in view.findall('filter/groupfilter/groupfilter')]
            order=[n.text.strip('"') for n in view.findall('manual-sort/dictionary/bucket')]
            assert members==order and len(order)==(4 if include_anchor else 3)
            report['probes'].append({'include_anchor':include_anchor,'filter':members,'order':order,'same_list':True})
        e=TWBEditor('');e.add_worksheet('Synthetic')
        try:
            e.configure_chart('Synthetic',mark_type='Bar',columns=['MIN(NULL)'])
        except KeyError as error:
            assert "Unknown field 'NULL'" in str(error)
            report['inline_null']={'rejected_as_unknown_field':True,'error':str(error)}
        else:
            raise AssertionError('Inline NULL behavior changed; reevaluate workaround')
    report['conclusion']='Cannot independently order Gantt anchor before spacer while excluding it from Measure Values filter. MIN(NULL) also fails strict field resolution; typed nullable input is the case workaround.'
    (HERE/'evidence/sdk-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('REPRODUCED: coupled Measure Names filter/order and inline NULL field registration')

def candidate_probe():
    """Synthetic independent order and physical-field normalization regressions."""
    from cwtwb import TWBEditor
    from tableauhyperapi import CreateMode, TableDefinition, TableName, SqlType, Inserter
    report=candidate_identity()
    with tempfile.TemporaryDirectory() as tmp:
        data=Path(tmp)/'synthetic.hyper'
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
            table=TableDefinition(TableName('Extract','Extract'),[TableDefinition.Column(n,SqlType.double()) for n in ('Earlier','Later','Anchor','Spacer','Sales')])
            with Connection(process.endpoint,str(data),CreateMode.CREATE_AND_REPLACE) as c:
                c.catalog.create_schema('Extract');c.catalog.create_table(table)
                with Inserter(c,table) as insert:insert.add_row([10,15,10,None,25]);insert.execute()
        def make(order):
            e=TWBEditor('');e.set_hyper_connection(str(data));e.add_worksheet('Synthetic')
            e.configure_layered_chart('Synthetic',columns=['Multiple Values','SUM(Anchor)'],rows=['Measure Names'],axis_shelf='columns',measure_names_order=order,panes=[
                {'axis':'Multiple Values','mark_type':'Bar','measure_values':['SUM(Earlier)','SUM(Later)','MIN(Spacer)']},
                {'axis':'SUM(Anchor)','mark_type':'GanttBar'}])
            path=Path(tmp)/'candidate.twb';e.save(str(path),validate=False)
            return ET.parse(str(path)).getroot()
        root=make(['SUM(Earlier)','SUM(Later)','SUM(Anchor)','MIN(Spacer)'])
        view=root.find('./worksheets/worksheet/table/view')
        members=[x.get('member').strip('"') for x in view.findall('filter/groupfilter/groupfilter')]
        order=[x.text.strip('"') for x in view.findall('manual-sort/dictionary/bucket')]
        assert len(members)==3 and len(order)==4 and order[:2]==members[:2] and order[-1]==members[-1]
        assert order[2] not in members and order[2].endswith('[sum:Anchor:qk]')
        report['independent_order']={'filter':members,'order':order,'reference_closure':reference_closure(root)}
        # Sales is order-only: bare expression must resolve to SUM(Sales), with
        # a declared instance despite not appearing on any shelf or mark.
        root=make(['Sales']);reference_closure(root)
        bucket=root.findtext('./worksheets/worksheet/table/view/manual-sort/dictionary/bucket')
        assert bucket.strip('"').endswith('[sum:Sales:qk]')
        changed=deepcopy(root);dep=changed.find('./worksheets/worksheet/table/view/datasource-dependencies')
        dep.remove(dep.find("column-instance[@name='[sum:Sales:qk]']"))
        expect_rejected('missing-order-only-instance',lambda:reference_closure(changed))
        error=None
        try:make(['Sales','SUM(Sales)'])
        except ValueError as exc:error=str(exc)
        assert error and 'duplicate resolved' in error
        report['normalization']={'bare_physical_sales_resolves_to_sum':True,'order_only_reference_declared':True,'deleted_order_only_instance_rejected':True,'duplicate_alias_error':error}
    report['status']='PASS candidate API regressions; does not establish rendered necessity or spacing'
    (HERE/'evidence/candidate-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS candidate independent order, physical normalization, duplicate rejection and reference closure')

if __name__=='__main__':
    import sys
    if '--sdk-probe' in sys.argv: sdk_probe()
    elif '--candidate-probe' in sys.argv: candidate_probe()
    else: verify()

