"""Independent raw-data oracle, emitted contracts, and negative mutations.

Default mode verifies only a fresh primary build. --historical separately checks
archived probes, which CI deliberately removes before rebuilding the primary.
No URLs are followed and no Tableau runtime success is claimed.
"""
from pathlib import Path
import argparse, base64, collections, copy, csv, hashlib, json, math, re, tempfile, zipfile
from urllib.parse import urlparse,unquote
from lxml import etree as E
from tableauhyperapi import HyperProcess, Telemetry, Connection

HERE=Path(__file__).resolve().parent

def require(condition,message):
    if not condition: raise AssertionError(message)

def digest(data):return hashlib.sha256(data).hexdigest()

def load(path):
    with zipfile.ZipFile(path) as z:
        return E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb')))),{n:z.read(n) for n in z.namelist() if not n.endswith('.twb')}

def data_oracle():
    lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
    for rec in lock['extracted_data']+lock['derived_data']+lock['extracted_assets']:
        data=(HERE/rec['file']).read_bytes();require(len(data)==rec['bytes'] and digest(data)==rec['sha256'],'source asset hash '+rec['file'])
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        def query(name,sql):
            with Connection(h.endpoint,str(HERE/'inputs'/name)) as c:return c.execute_list_query(sql)
        raw=query('federated_0647kt40xit7hq0zxnps10.hyper','SELECT * FROM "Extract"."Extract"')
        counts=collections.Counter(r[4] for r in raw if r[0] is not None)
        require(counts=={2018:10,2019:3,2020:5,2021:6},'year counts')
        require(sorted(r[0] for r in raw if r[0] is not None)==list(range(1,25)),'24 unique countdown days')
        require([r for r in raw if r[0] is None]==[[None,None,6,2.0,None]],'Christmas star')
        require(all(0<=r[3]<=4 and 0<=r[2]<=7 for r in raw),'fixed coordinate bounds')
        require(all(urlparse(r[1]).scheme in {'http','https'} and urlparse(r[1]).netloc.endswith('workout-wednesday.com') for r in raw if r[0] is not None),'challenge URL domain')
        other=query('federated_04jakgc1k2a0xz1dyckmx0.hyper','SELECT * FROM "Extract"."Sheet1_E0A05D272ADA4BEFB82A742E60A03684"')
        require(collections.Counter(r[0] for r in other if r[0] is not None)==counts,'second author extract corroborates counts')
        ranges=query('federated_04jakgc1k2a0xz1dyckmx0.hyper','SELECT * FROM "Extract"."Range_C46B6249BED4462F851741163615F617"')
        require(sorted(r[0] for r in ranges)==[1,500],'densification endpoints')
        gradient=query('gradient.hyper','SELECT * FROM "Extract"."Extract" ORDER BY "Challenge Year","Segment"')
        check_segments(gradient,counts)
        combined=query('calendar.hyper','SELECT * FROM "Extract"."Extract"')
        require(collections.Counter(tuple(r[1:6]) for r in combined if r[0]=='Tree')==collections.Counter(tuple(r) for r in raw),'unchanged tree records in runtime input')
        require(len(combined)==2025,'combined row count')
        check_segments([r[5:] for r in combined if r[0]=='Bar'],counts)
    csvrows=list(csv.DictReader((HERE/'inputs/gradient.csv').open(encoding='utf-8')))
    check_segments([[int(r['Challenge Year']),int(r['Segment']),float(r['Segment Start']),float(r['Segment Width']),float(r['Gradient']),int(r['Challenge Count'])] for r in csvrows],counts)
    # Independent state transitions: selected years, multiselect, clear, null star.
    selections={str(y):sorted(r[0] for r in raw if r[4]==y) for y in counts}
    require(len(selections['2018'])==10 and len(selections['2019'])==3,'year filter oracle')
    require(len(selections['2018']+selections['2020'])==15,'multiselect oracle')
    return {'counts':dict(counts),'tree_marks':25,'segments':len(gradient),'selected_days':selections,'clear_selection_marks':25},gradient,counts

def check_segments(rows,counts):
    require(len(rows)==2000,'500 segments per year')
    seen=set()
    for year,segment,start,width,color,total in rows:
        require(year in counts and 1<=segment<=500 and (year,segment) not in seen,'unique segment key')
        seen.add((year,segment));n=counts[year]
        require(total==n,'total must count challenges, not scaffold rows')
        require(math.isclose(start,(segment-1)*n/500,abs_tol=1e-12),'gradient start')
        require(math.isclose(width,n/500,abs_tol=1e-12),'gradient width')
        require(math.isclose(color,(500-segment)*n/500,abs_tol=1e-12),'gradient color')
    for year,n in counts.items():require(math.isclose(sum(r[3] for r in rows if r[0]==year),n,abs_tol=1e-10),'segments sum to raw count')

def contracts(root,assets):
    ds=root.find('datasources/datasource');require(ds is not None,'datasource')
    columns={c.get('name'):c for c in ds.findall('column')}
    caption={c.get('caption',c.get('name').strip('[]')):c for c in columns.values()}
    def col(name):return caption[name].get('name')
    formulas={n:c.find('calculation').get('formula') for n,c in columns.items() if c.find('calculation') is not None}
    def formula(name):
        value=formulas[col(name)]
        for display,c in caption.items():value=value.replace(c.get('name'),'['+display+']')
        return value
    require(formula('Day is Null')=='ISNULL([Day])','star formula')
    require(formula('Day Label')=='STR([Day])','day label formula')
    require(formula('Year')=='IFNULL(STR([Challenge Year]), "Christmas")','year formula')
    require(formula('Keep All')=='"All ornaments"','constant highlight formula')
    require(formula('Segment ID')=='STR([Segment])','segment detail formula')
    require(formula('Tooltip')=='IF [Day is Null] THEN "It\'s Christmas Day!" ELSEIF [Day] = 1 THEN STR([Day]) + " day until Christmas" ELSE STR([Day]) + " days until Christmas" END','countdown singular/plural/null branches')
    # Every formula operand and every emitted worksheet instance resolves.
    global_fields=set(columns) | {n.text for n in ds.findall(".//metadata-record/local-name")}
    for name,f in formulas.items():
        require(all(ref in global_fields for ref in re.findall(r'\[[^\]]+\]',f)),'global formula dependency '+name)
    for ws in root.findall('worksheets/worksheet'):
        dep=ws.find('table/view/datasource-dependencies');require(dep is not None,'worksheet dependencies')
        locals_={c.get('name') for c in dep.findall('column')};instances={i.get('name'):i for i in dep.findall('column-instance')}
        for i in instances.values():require(i.get('column') in locals_,'instance operand closure')
        for c in dep.findall('column'):
            f=c.find('calculation')
            if f is not None: require(all(ref in locals_ for ref in re.findall(r'\[[^\]]+\]',f.get('formula',''))),'worksheet formula closure')
        refs=[]
        for node in ws.iter():
            for key,value in node.attrib.items():
                if key in {'column','field','x-axis-name','y-axis-name'} and value.startswith('['+ds.get('name')+'].'):
                    local=value[len(ds.get('name'))+3:]
                    if not local.startswith('[Action ('):refs.append(local)
        for tag in ('rows','cols'):
            refs.extend(re.findall(re.escape('['+ds.get('name')+'].')+r'(\[[^\]]+\])',ws.findtext('table/'+tag,'')))
        require(all(ref in instances or ref in locals_ for ref in refs),'emitted field reference closure '+ws.get('name'))
    tree=root.find('worksheets/worksheet[@name="Tree"]');bar=root.find('worksheets/worksheet[@name="Bar"]')
    require(tree is not None and bar is not None and len(root.findall('worksheets/worksheet'))==2,'two sheets')
    require('avg:Y:qk' in tree.findtext('table/cols','') and 'avg:X:qk' in tree.findtext('table/rows',''),'coordinate shelves')
    tp=tree.find('table/panes/pane');require(tp.find('mark').get('class')=='Shape','tree shape marks')
    def fieldref(element,tag,fragment):return any(fragment in n.get('column','') for n in element.findall('.//encodings/'+tag))
    require(fieldref(tp,'lod','Link to the Challenge') and fieldref(tp,'text',col('Day Label')[1:-1]),'tree mark grain and day labels')
    require(fieldref(tp,'shape',col('Day is Null')[1:-1]) and fieldref(tp,'size',col('Day is Null')[1:-1]),'star shape and size channels')
    for field,scope,upper in [('avg:Y:qk','cols','4'),('avg:X:qk','rows','7')]:
        require(any(field in x.get('field','') and x.get('scope')==scope and x.get('min')=='0' and x.get('max')==upper and x.get('range-type')=='fixed' for x in tree.findall('.//encoding')),'fixed tree range '+scope)
    size=tree.find('.//encoding[@type="catsize"]');require(size is not None and float(size.get('max-size'))>float(size.get('min-size'))>0,'star larger than ornaments')
    shapes={n.get('name'):base64.b64decode(n.text) for n in root.findall('external/shapes/shape')}
    for name in ['christmas-ornament.png','star.png']:require(shapes.get('Advent/'+name)==(HERE/'inputs/assets'/name).read_bytes(),'embedded portable shape '+name)
    mappings=ds.findall('.//encoding[@attr="shape"]/map');require({m.findtext('bucket'):m.get('to') for m in mappings}=={'false':'Advent/christmas-ornament.png','true':'Advent/star.png'},'shape assignments')
    for ws,kind in [(tree,'Tree'),(bar,'Bar')]:require(any(n.get('member')=='"'+kind+'"' for n in ws.findall('.//filter//groupfilter')),'sheet kind filter '+kind)
    require('sum:Segment Start:qk' in bar.findtext('table/cols','') and 'avg:Challenge Count:qk' in bar.findtext('table/cols',''),'explicit bar shelves')
    panes=bar.findall('table/panes/pane');require([p.find('mark').get('class') for p in panes]==['GanttBar','Bar'],'gradient and count layers')
    require(fieldref(panes[0],'size','sum:Segment Width:qk') and fieldref(panes[0],'lod',col('Segment ID')[1:-1]) and fieldref(panes[0],'color','avg:Gradient:qk'),'gradient segment encodings')
    require(fieldref(panes[1],'text','avg:Challenge Count:qk'),'count label not scaffold count')
    require(panes[1].find('.//format[@attr="mark-transparency"]').get('value')=='0','transparent count overlay')
    require(bar.find('.//encoding[@fold="true"]').get('synchronized')=='true','synchronized bar axes')
    require(bar.find('.//encoding[@attr="color"]').get('palette')=='red_green_diverging_10_0','gradient palette')
    require(caption['Challenge Count'].get('default-format')=='*0','Tableau integer format')
    for ws in [tree,bar]:require(ws.find('.//customized-tooltip') is not None,'custom tooltips')
    action=root.find('actions/action[@caption="Filter tree by challenge year"]')
    require(action.find('source').get('worksheet')=='Bar' and action.find('activation').get('type')=='on-select','bar selection trigger')
    require(action.find('command/param[@name="on-empty"]').get('value')=='all','clear restores tree')
    require(action.find('command/param[@name="exclude"]').get('value')=='Bar','filter targets tree only')
    require(col('Year') in unquote(action.find('link').get('expression')),'action year field')
    af=tree.find('.//filter[@column="['+ds.get('name')+'].[Action (Year)]"]');require(af is not None,'tree action filter initialized')
    require(set(n.get('member') for n in af.findall('.//groupfilter[@member]'))=={'"2018"','"2019"','"2020"','"2021"','"Christmas"'},'initial full tree including star')
    require(af.find('groupfilter').get('{http://www.tableausoftware.com/xml/user}ui-action-filter')==action.get('name'),'action ownership')
    url=root.find('actions/action[@caption="Open selected challenge"]');require(url.find('source').get('worksheet')=='Tree' and url.find('link').get('expression')=='<[Link to the Challenge]>','per-mark URL action')
    highlight=root.find('actions/action[@caption="Keep all ornaments highlighted"]');require(highlight.find('command').get('command')=='tsc:brush' and highlight.find('command/param[@name="field-captions"]').get('value')=='Keep All' and fieldref(tp,'lod',col('Keep All')[1:-1]),'constant self-highlight prevents greying')
    dash=root.find('dashboards/dashboard');size=dash.find('size');require(size.get('maxwidth')=='1000' and size.get('maxheight')=='800','dashboard size')
    require({z.get('name') for z in dash.findall('.//zone[@name]')}=={'Tree','Bar'},'two worksheet zones')
    text=' '.join(dash.itertext());require('Click an ornament' in text and 'clear the selection' in text and 'CANDRA' in text,'help and attribution')
    for connection in root.findall('.//connection[@class="hyper"]'):
        filename=connection.get('dbname');require(filename in assets and assets[filename]==(HERE/'inputs'/filename).read_bytes(),'portable packaged data')
    # Background absence is a known blocker, never a successful visual assertion.
    return {'native_background_present':bool(root.findall('.//mapped-image'))}

def verify(historical=False):
    oracle,segments,counts=data_oracle()
    path=HERE/'outputs/replicated-workbook.twbx';root,assets=load(path)
    state=contracts(root,assets)
    mutations={
        'wrong-coordinate':lambda r:r.find('worksheets/worksheet[@name="Tree"]/table/cols').__setattr__('text',''),
        'remove-shapes':lambda r:r.find('external/shapes').clear(),
        'wrong-star-size':lambda r:r.find('.//worksheet[@name="Tree"]//encoding[@type="catsize"]').set('max-size','0.1'),
        'break-formula':lambda r:r.find('.//datasource/column[@caption="Tooltip"]/calculation').set('formula','[Missing]'),
        'wrong-bar-grain':lambda r:r.find('.//worksheet[@name="Bar"]/table/panes/pane/encodings/lod').set('column','[Missing]'),
        'remove-gradient':lambda r:r.find('.//worksheet[@name="Bar"]//encoding[@attr="color"]').set('palette','blue'),
        'wrong-clear':lambda r:r.find('.//action/command/param[@name="on-empty"]').set('value','none'),
        'wrong-url':lambda r:r.find('.//action[@caption="Open selected challenge"]/link').set('expression','https://example.invalid/'),
        'break-highlight':lambda r:r.find('.//action[@caption="Keep all ornaments highlighted"]/command/param[@name="field-captions"]').set('value','Day'),
        'wrong-dashboard-size':lambda r:r.find('.//dashboard/size').set('maxwidth','999'),
    }
    for name,mutate in mutations.items():
        bad=copy.deepcopy(root);mutate(bad)
        try:contracts(bad,assets)
        except (AssertionError,KeyError):pass
        else:raise AssertionError('mutation survived: '+name)
    bad=copy.deepcopy(segments);bad[0][3]*=2
    try:check_segments(bad,counts)
    except AssertionError:pass
    else:raise AssertionError('data mutation survived')
    archive=[]
    if historical:
        for name in ['background-image-probe.twbx','baseline-background-probe.twbx','baseline-0.29.0a2.twbx','retest-cac8820.twbx']:
            r,a=load(HERE/'outputs'/name)
            require(not r.findall('.//mapped-image'),'background gap changed; reassess blocker')
            if 'probe' in name:
                require(not any(n.endswith('.png') for n in a),'probe unexpectedly packages a raster')
                require(r.find('external/shapes/shape') is not None,'valid synthetic image accepted by shape control')
            else:
                contracts(r,a)
                evidence='baseline-verification.json' if name.startswith('baseline') else 'retest-verification.json'
                require(json.loads((HERE/'evidence'/evidence).read_text(encoding='utf-8'))['workbook_sha256']==digest((HERE/'outputs'/name).read_bytes()),'archived run hash')
            archive.append({'file':name,'sha256':digest((HERE/'outputs'/name).read_bytes())})
    report={'result':'PASS local implemented-scope checks; BLOCKED native mapped background','workbook_sha256':digest(path.read_bytes()),'oracle':oracle,'contracts':state,'negative_mutations_rejected':len(mutations)+1,'historical_checked':archive,'acceptance':['raw-data-oracle','tree-marks','gradient-bars','url-and-filter-actions','portable-assets','dependency-closure','negative-mutations'],'runtime':'NOT RUN; Desktop, rendered alignment and live interactions remain parent gates'}
    (HERE/'outputs/local-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--historical',action='store_true');verify(parser.parse_args().historical)
