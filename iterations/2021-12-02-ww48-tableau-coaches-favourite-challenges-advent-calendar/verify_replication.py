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

def contracts(root,assets,require_background=True):
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
    highlight=root.find('actions/action[@caption="Keep all ornaments highlighted"]');require(highlight.find('command').get('command')=='tsc:brush' and highlight.find('command/param[@name="field-captions"]').get('value')=='Keep All' and fieldref(tp,'lod',col('Keep All')[1:-1]),'constant self-highlight static contract; runtime untested')
    dash=root.find('dashboards/dashboard');size=dash.find('size');require(size.get('maxwidth')=='1000' and size.get('maxheight')=='800','dashboard size')
    require({z.get('name') for z in dash.findall('.//zone[@name]')}=={'Tree','Bar'},'two worksheet zones')
    text=' '.join(dash.itertext());require('Click an ornament' in text and 'clear the selection' in text and 'CANDRA' in text,'help and attribution')
    for connection in root.findall('.//connection[@class="hyper"]'):
        filename=connection.get('dbname');require(filename in assets and assets[filename]==(HERE/'inputs'/filename).read_bytes(),'portable packaged data')
    strict_contracts(root,assets,require_background)
    return {'native_background_present':bool(root.findall('.//mapped-image'))}

def strict_contracts(root, assets, require_background=True):
    """Exact emitted contracts; these are not proof of Tableau event execution."""
    sources = root.findall('datasources/datasource')
    require(len(sources) == 1, 'exactly one runtime datasource')
    ds = sources[0]
    prefix = '[' + ds.get('name') + '].'
    columns = {n.get('name'): n for n in ds.findall('column')}
    captions = {n.get('caption', n.get('name').strip('[]')): n.get('name') for n in columns.values()}
    raw_types = {n.findtext('local-name'): n.findtext('local-type') for n in ds.findall('.//metadata-record') if n.find('local-name') is not None}
    expected_types = {'[Kind]':'string', '[Day]':'integer', '[Link to the Challenge]':'string', '[X]':'integer', '[Y]':'real', '[Challenge Year]':'integer', '[Segment]':'integer', '[Segment Start]':'real', '[Segment Width]':'real', '[Gradient]':'real', '[Challenge Count]':'integer'}
    require(raw_types == expected_types, 'physical field schema matches independently known input schema')
    groups = {n.get('name'): n for n in ds.findall('group')}
    worksheets = {w.get('name'): w for w in root.findall('worksheets/worksheet')}
    require(set(worksheets) == {'Tree', 'Bar'}, 'worksheet identities')
    bindings = {}
    token_pattern = r'(?:\[[^\]]+\]\.)?\[[^\]]+\]'
    for name, ws in worksheets.items():
        dependencies = ws.findall('table/view/datasource-dependencies')
        require(len(dependencies) == 1 and dependencies[0].get('datasource') == ds.get('name'), 'worksheet datasource identity')
        dep = dependencies[0]
        local = {c.get('name'): c for c in dep.findall('column')}
        instances = {n.get('name'): n for n in dep.findall('column-instance')}
        require(len(local) == len(dep.findall('column')) and len(instances) == len(dep.findall('column-instance')), 'no ambiguous definitions')
        for field, definition in local.items():
            if field in columns:
                original = columns[field]
                for attr in ('datatype','role','type','caption'):
                    require(definition.get(attr) == original.get(attr), 'local/global definition consistency '+field+' '+attr)
                a, b = definition.find('calculation'), original.find('calculation')
                require((a is None) == (b is None), 'local/global calculation presence')
                if a is not None:
                    require(dict(a.attrib) == dict(b.attrib), 'local/global formula consistency '+field)
            else:
                require(field in raw_types and definition.get('datatype') == raw_types[field], 'local physical definition '+field)
                require(definition.find('calculation') is None, 'physical field cannot acquire a local formula')
                expected_role = ('dimension','nominal') if raw_types[field] == 'string' else ('measure','quantitative')
                require((definition.get('role'),definition.get('type')) == expected_role, 'physical field semantic role '+field)
        def check_reference(value):
            if '.' in value and re.match(r'^\[[^\]]+\]\.', value):
                require(value.startswith(prefix), 'foreign datasource reference '+value)
                value = value[len(prefix):]
            require(value in local or value in instances or value in groups, 'unresolved reference '+value)
        for element in ws.iter():
            for attr in ('column','field','level','x-axis-name','y-axis-name','using','dimension-to-sort'):
                value = element.get(attr)
                if value:
                    require(re.fullmatch(token_pattern, value) is not None, 'malformed reference '+value)
                    check_reference(value)
            if element.tag in ('rows','cols','run'):
                for value in re.findall(token_pattern, element.text or ''):
                    check_reference(value)
        bindings[name] = (local, instances)
    def field(name):
        return captions.get(name, '['+name+']')
    def ref(sheet, name, derivation='None', kind='nominal'):
        matches = [n for n in bindings[sheet][1].values() if n.get('column') == field(name) and n.get('derivation') == derivation and n.get('type') == kind]
        require(len(matches) == 1, 'unique typed binding '+sheet+'/'+name+'/'+derivation)
        return prefix + matches[0].get('name')
    tree, bar = worksheets['Tree'], worksheets['Bar']
    require(tree.findtext('table/cols') == ref('Tree','Y','Avg','quantitative'), 'exact horizontal shelf')
    require(tree.findtext('table/rows') == ref('Tree','X','Avg','quantitative'), 'exact vertical shelf')
    require(bar.findtext('table/rows') == ref('Bar','Year'), 'exact year shelf')
    require(bar.findtext('table/cols') == '('+ref('Bar','Segment Start','Sum','quantitative')+' + '+ref('Bar','Challenge Count','Avg','quantitative')+')', 'exact bar shelves')
    def encodings(pane):
        return collections.Counter((n.tag,n.get('column')) for n in pane.findall('encodings/*'))
    tp = tree.find('table/panes/pane')
    require(encodings(tp) == collections.Counter([
        ('shape',ref('Tree','Day is Null')), ('size',ref('Tree','Day is Null')),
        ('text',ref('Tree','Day Label')), ('lod',ref('Tree','Link to the Challenge')),
        ('lod',ref('Tree','Day Label')), ('lod',ref('Tree','Keep All')), ('lod',ref('Tree','Year')),
        ('tooltip',ref('Tree','Tooltip','Attribute'))]), 'exact Tree mark and tooltip bindings')
    bp = bar.findall('table/panes/pane')
    require(encodings(bp[0]) == collections.Counter([('color',ref('Bar','Gradient','Avg','quantitative')),('size',ref('Bar','Segment Width','Sum','quantitative')),('lod',ref('Bar','Segment ID'))]), 'exact gradient mark bindings')
    require(encodings(bp[1]) == collections.Counter([('text',ref('Bar','Challenge Count','Avg','quantitative'))]), 'exact count mark bindings')
    def tooltip_runs(pane):
        return [(n.text or '',dict(n.attrib)) for n in pane.findall('customized-tooltip/formatted-text/run')]
    require(tooltip_runs(tp) == [('<'+ref('Tree','Tooltip','Attribute')+'>',{'bold':'true'})], 'exact countdown tooltip token')
    for pane in bp:
        require(tooltip_runs(pane) == [('<'+ref('Bar','Year')+'>',{'bold':'true'}),(' | ',{}),('<'+ref('Bar','Challenge Count','Avg','quantitative')+'>',{}),(' favourite challenges',{})], 'exact year/count tooltip tokens')
    size = tree.find('.//encoding[@type="catsize"]')
    require(size.get('field') == ref('Tree','Day is Null') and size.get('field-type') == 'nominal', 'categorical size binding')
    require(size.get('reverse','false') == 'false' and float(size.get('min-size')) == 0.500889 and float(size.get('max-size')) == 1, 'categorical size direction and bounds')
    require(columns[field('Day is Null')].get('datatype') == 'boolean', 'false then true boolean size domain')
    require(not tree.findall('.//manual-sort') and not tree.findall('.//computed-sort') and not tree.findall('.//shelf-sort'), 'no reversal of natural boolean category order')
    for name, ws in worksheets.items():
        filters = ws.findall('table/view/filter')
        require(len(filters) == (2 if name == 'Tree' else 1), 'exclusive known worksheet filters')
        kind_filters = [n for n in filters if n.get('column') == ref(name,'Kind')]
        require(len(kind_filters) == 1 and kind_filters[0].get('class') == 'categorical', 'Kind filter identity')
        members = kind_filters[0].findall('groupfilter')
        require(len(members) == 1 and len(members[0]) == 0, 'Kind filter has exactly one member')
        m = members[0]
        require(m.get('function') == 'member' and m.get('level') == '[none:Kind:nk]' and m.get('member') == json.dumps(name), 'Kind filter identity and exclusive value')
        require(m.get('{http://www.tableausoftware.com/xml/user}ui-enumeration') == 'inclusive', 'Kind filter is inclusive')
    actions = {a.get('caption'):a for a in root.findall('actions/action')}
    require(len(root.findall('actions/action')) == 3 and len({a.get('name') for a in actions.values()}) == 3, 'unique action identities')
    require(set(actions) == {'Filter tree by challenge year','Open selected challenge','Keep all ornaments highlighted'}, 'exact action set')
    def action_contract(caption, source):
        a = actions[caption]
        require(dict(a.find('activation').attrib) == {'type':'on-select','auto-clear':'true'}, 'exact action activation '+caption)
        require(dict(a.find('source').attrib) == {'dashboard':'Advent Calendar','type':'sheet','worksheet':source}, 'exact action source '+caption)
        return a
    def command(a, kind, expected):
        c = a.find('command')
        require(c is not None and c.get('command') == kind, 'action command type')
        params = c.findall('param')
        require(len(params) == len(expected) and {n.get('name'):n.get('value') for n in params} == expected, 'exact action target/parameters')
    a = action_contract('Filter tree by challenge year','Bar')
    command(a,'tsc:tsl-filter',{'exclude':'Bar','target':'Advent Calendar','on-empty':'all'})
    link = a.find('link')
    require(unquote(link.get('expression')) == 'tsl:Advent Calendar?'+prefix+field('Year')+'~s0=<'+field('Year')+'~na>', 'exact action expression and source/target Year references')
    for attr,value in {'delimiter':',','escape':'\\','include-null':'true','multi-select':'true','url-escape':'true'}.items():require(link.get(attr) == value, 'filter link option '+attr)
    action_filter = next(n for n in tree.findall('table/view/filter') if n.get('column') == prefix+'[Action (Year)]')
    union = action_filter.find('groupfilter')
    require(union.get('function') == 'union' and len(union) == 5, 'year action union')
    for m in union:
        require(m.tag == 'groupfilter' and m.get('function') == 'member' and m.get('level') == field('Year') and len(m) == 0, 'Year action member level')
    g = groups.get('[Action (Year)]')
    require(g is not None and g.get('{http://www.tableausoftware.com/xml/user}auto-column') == 'sheet_link', 'native action group')
    require(g.find('groupfilter').get('function') == 'crossjoin' and len(g.find('groupfilter')) == 1 and g.find('groupfilter/groupfilter').get('function') == 'level-members' and g.find('groupfilter/groupfilter').get('level') == field('Year'), 'action group Year closure')
    a = action_contract('Open selected challenge','Tree')
    require(a.find('command') is None and len(a.findall('link')) == 1 and a.find('link').get('expression') == '<[Link to the Challenge]>', 'exact URL action expression')
    a = action_contract('Keep all ornaments highlighted','Tree')
    command(a,'tsc:brush',{'exclude':'Bar','field-captions':'Keep All','target':'Advent Calendar'})
    require(a.find('link') is None, 'highlight has no URL side effect')
    if require_background:
        images = root.findall('.//mapped-image')
        require(len(images) == 1 and images[0].getparent().getparent() is ds, 'single datasource-owned background')
        image = images[0]
        require(image.get('expression') == '"Images/christmas-tree.png"', 'portable background expression')
        require(len(image.findall('mapping')) == 1, 'one background mapping')
        mapping = image.find('mapping')
        require(dict(mapping.attrib) == {'x':'[Y]','y':'[X]','left':'0','right':'4','bottom':'0','top':'6'}, 'background field identity and finite rectangle bounds')
        require(raw_types[mapping.get('x')] in {'integer','real'} and raw_types[mapping.get('y')] in {'integer','real'}, 'numeric image axes')
        require(dict(image.find('image-options').attrib) == {'lock-aspect-ratio':'false','show-entire-image':'false'}, 'background stretching contract')
        require(assets.get('Images/christmas-tree.png') == (HERE/'inputs/assets/christmas-tree.png').read_bytes(), 'background packaged bytes')
        require(not root.findall('.//dashboard//zone[@type-v2="bitmap"]'), 'background is not a dashboard image')


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
    def set_attr(xpath, attr, value):
        return lambda r: r.find(xpath).set(attr,value)
    def foreign_ref(r):
        n=r.find('.//worksheet[@name="Tree"]/table/panes/pane/encodings/text')
        n.set('column','[ForeignDatasource].'+n.get('column').split('].',1)[1])
    def wrong_tooltip(r):
        n=r.find('.//worksheet[@name="Tree"]//customized-tooltip/formatted-text/run')
        n.text='<'+r.find('.//worksheet[@name="Tree"]/table/rows').text+'>'
    def foreign_tooltip(r):
        n=r.find('.//worksheet[@name="Tree"]//customized-tooltip/formatted-text/run')
        n.text='<[ForeignDatasource].'+n.text.split('].',1)[1]
    def inconsistent_local_formula(r):
        dep=r.find('.//worksheet[@name="Tree"]//datasource-dependencies')
        dep.find('column[@caption="Tooltip"]/calculation').set('formula','STR([Day])')
    def wrong_expression(r):
        ds=r.find('datasources/datasource')
        a=r.find('.//action[@caption="Filter tree by challenge year"]/link')
        year=ds.find('column[@caption="Year"]').get('name')
        other=ds.find('column[@caption="Keep All"]').get('name')
        a.set('expression',unquote(a.get('expression')).replace('<'+year+'~na>','<'+other+'~na>'))
    def extra_kind_member(r):
        f=r.find('.//worksheet[@name="Bar"]//filter')
        E.SubElement(f,'groupfilter',function='member',level='[none:Kind:nk]',member='"Tree"')
    def wrong_action_level(r):
        n=r.find('.//worksheet[@name="Tree"]//filter/groupfilter/groupfilter')
        n.set('level',r.find('datasources/datasource/column[@caption="Keep All"]').get('name'))
    mutations.update({
        'foreign-mark-datasource':foreign_ref,
        'foreign-tooltip-datasource':foreign_tooltip,
        'wrong-valid-tooltip-binding':wrong_tooltip,
        'local-global-formula-inconsistency':inconsistent_local_formula,
        'local-raw-role-inconsistency':set_attr('.//worksheet[@name="Tree"]//datasource-dependencies/column[@name="[X]"]','role','dimension'),
        'local-raw-type-inconsistency':set_attr('.//worksheet[@name="Tree"]//datasource-dependencies/column[@name="[X]"]','datatype','string'),
        'categorical-size-reversed':set_attr('.//worksheet[@name="Tree"]//encoding[@type="catsize"]','reverse','true'),
        'boolean-category-type':set_attr('datasources/datasource/column[@caption="Day is Null"]','datatype','string'),
        'kind-filter-wrong-level':set_attr('.//worksheet[@name="Bar"]//filter/groupfilter','level','[Challenge Year]'),
        'kind-filter-wrong-identity':set_attr('.//worksheet[@name="Bar"]//filter','column','[none:Segment:nk]'),
        'kind-filter-exclusion':set_attr('.//worksheet[@name="Bar"]//filter/groupfilter','function','except'),
        'kind-filter-extra-member':extra_kind_member,
        'action-filter-wrong-valid-level':wrong_action_level,
        'filter-command-type':set_attr('.//action[@caption="Filter tree by challenge year"]/command','command','tsc:brush'),
        'filter-command-target':set_attr('.//action[@caption="Filter tree by challenge year"]/command/param[@name="target"]','value','Bar'),
        'filter-multiselect':set_attr('.//action[@caption="Filter tree by challenge year"]/link','multi-select','false'),
        'filter-source-expression':wrong_expression,
        'url-activation':set_attr('.//action[@caption="Open selected challenge"]/activation','type','on-hover'),
        'url-source':set_attr('.//action[@caption="Open selected challenge"]/source','worksheet','Bar'),
        'highlight-source':set_attr('.//action[@caption="Keep all ornaments highlighted"]/source','worksheet','Bar'),
        'highlight-activation':set_attr('.//action[@caption="Keep all ornaments highlighted"]/activation','type','on-hover'),
        'highlight-target':set_attr('.//action[@caption="Keep all ornaments highlighted"]/command/param[@name="target"]','value','Bar'),
        'highlight-exclusion':set_attr('.//action[@caption="Keep all ornaments highlighted"]/command/param[@name="exclude"]','value','Tree'),
        'background-swapped-field':set_attr('.//mapped-image/mapping','x','[X]'),
        'background-foreign-field':set_attr('.//mapped-image/mapping','x','[Foreign].[Y]'),
        'background-nonnumeric-field':set_attr('.//mapped-image/mapping','x','[Kind]'),
        'background-wrong-bound':set_attr('.//mapped-image/mapping','top','7'),
        'background-nonfinite-bound':set_attr('.//mapped-image/mapping','right','NaN'),
        'background-resource-reference':set_attr('.//mapped-image','expression','"Images/missing.png"'),
        'background-aspect-lock':set_attr('.//mapped-image/image-options','lock-aspect-ratio','true'),
    })

    for name,mutate in mutations.items():
        bad=copy.deepcopy(root);mutate(bad)
        try:contracts(bad,assets)
        except (AssertionError,KeyError):pass
        else:raise AssertionError('mutation survived: '+name)
    bad=copy.deepcopy(segments);bad[0][3]*=2
    try:check_segments(bad,counts)
    except AssertionError:pass
    else:raise AssertionError('data mutation survived')
    for name, altered in [('missing-background-resource', {n:b for n,b in assets.items() if n != 'Images/christmas-tree.png'}), ('corrupt-background-resource', dict(assets, **{'Images/christmas-tree.png': b'broken'}))]:
        try: contracts(root,altered)
        except AssertionError: pass
        else: raise AssertionError('resource mutation survived: '+name)
    # Roundtrip our OWN output through the public structural conversion API.
    from cwtwb import convert_workbook, read_workbook, validate_against_schema
    schema = validate_against_schema(root)
    require(schema.schema_available and not schema.errors, 'original mapped workbook XSD')
    with tempfile.TemporaryDirectory(prefix='advent-roundtrip-') as temporary:
        folder=Path(temporary)
        convert_workbook(path,folder/'editable.json')
        convert_workbook(folder/'editable.json',folder/'roundtrip.twbx')
        roundroot,roundassets=load(folder/'roundtrip.twbx')
        contracts(roundroot,roundassets)
        require(read_workbook(folder/'roundtrip.twbx').resources == read_workbook(path).resources, 'public API resource roundtrip')
        require(not validate_against_schema(roundroot).errors, 'roundtrip mapped workbook XSD')
    archive=[]
    if historical:
        for name in ['background-image-probe.twbx','baseline-background-probe.twbx','baseline-0.29.0a2.twbx','retest-cac8820.twbx','frozen-546ed6e.twbx']:
            r,a=load(HERE/'outputs'/name)
            require(not r.findall('.//mapped-image'),'historical snapshot should retain its original unmapped state')
            if 'probe' in name:
                require(not any(n.endswith('.png') for n in a),'probe unexpectedly packages a raster')
                require(r.find('external/shapes/shape') is not None,'valid synthetic image accepted by shape control')
            else:
                contracts(r,a,require_background=False)
                evidence=HERE/'outputs/local-verification.json' if name.startswith('frozen') else HERE/'evidence'/('baseline-verification.json' if name.startswith('baseline') else 'retest-verification.json')
                require(json.loads(evidence.read_text(encoding='utf-8'))['workbook_sha256']==digest((HERE/'outputs'/name).read_bytes()),'archived run hash')
            archive.append({'file':name,'sha256':digest((HERE/'outputs'/name).read_bytes())})
    if historical:
        preserved=json.loads((HERE/'evidence/prior-evidence-preservation.json').read_text(encoding='utf-8'))
        for relative, expected in preserved.items():
            actual=HERE/relative if relative != 'outputs/replicated-workbook.twbx' else HERE/'outputs/frozen-546ed6e.twbx'
            require(digest(actual.read_bytes()) == expected, 'prior evidence changed: '+relative)
    report={'result':'PASS local background, data and structural contracts; runtime pending','workbook_sha256':digest(path.read_bytes()),'oracle':oracle,'contracts':state,'negative_mutations_rejected':len(mutations)+3,'mutation_names':list(mutations)+['gradient-width-data','missing-background-resource','corrupt-background-resource'],'public_conversion_roundtrip':'PASS mapping/contracts/resources/XSD','historical_checked':archive,'acceptance':['raw-data-oracle','tree-marks','gradient-bars','url-and-filter-actions','portable-assets','dependency-closure','negative-mutations','native-tree-background'],'runtime':'NOT RUN; Desktop, rendered alignment and live interactions remain parent gates'}
    (HERE/'outputs/background-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--historical',action='store_true');verify(parser.parse_args().historical)
