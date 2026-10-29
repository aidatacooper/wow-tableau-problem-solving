"""Rebuild the advent calendar using extracted data and public cwtwb APIs."""
from pathlib import Path
import json, hashlib, importlib.metadata, tempfile
import cwtwb
from cwtwb import TWBEditor, convert_workbook, read_workbook

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / 'outputs'
DASHBOARD = 'Advent Calendar'

def repair_shape_bindings(payload):
    """Bind external custom shapes in our own native document at datasource scope.

    Released set_shape_palette emits a style field reference but omits its
    datasource column-instance. Build that binding from our worksheet dependency
    and use explicit embedded-shape maps without an unregistered palette name.
    """
    def descend(n):
        yield n
        for child in n.get('children', []):
            yield from descend(child)
    document = payload['document']['root']
    datasources = next(n for n in document['children'] if n.get('tag') == 'datasources')
    for datasource in datasources['children']:
        children = datasource.get('children', [])
        encodings = [n for n in descend(datasource) if n.get('tag') == 'encoding'
                     and n.get('attributes', {}).get('attr') == 'shape']
        for encoding in encodings:
            reference = encoding['attributes']['field']
            existing = [n for n in children if n.get('tag') == 'column-instance'
                        and n.get('attributes', {}).get('name') == reference]
            if not existing:
                candidates = [n for dep in descend(document)
                              if dep.get('tag') == 'datasource-dependencies'
                              and dep.get('attributes', {}).get('datasource') == datasource['attributes']['name']
                              for n in dep.get('children', [])
                              if n.get('tag') == 'column-instance'
                              and n.get('attributes', {}).get('name') == reference]
                if not candidates or any(n['attributes'] != candidates[0]['attributes'] for n in candidates):
                    raise ValueError('Custom shape needs an unambiguous own-workbook field binding')
                index = max(i for i,n in enumerate(children)
                            if n.get('tag') in {'column','column-instance'}) + 1
                children.insert(index, {'tag':'column-instance',
                                        'attributes':dict(candidates[0]['attributes'])})
            encoding['attributes'].pop('palette', None)


def add_mapped_background(output):
    """Structural public-API workaround on OUR freshly blank-built document.

    These native nodes are authored from analysis bounds, not read or copied
    from any reference workbook. Conversion is structural, not a semantic DSL.
    """
    image_bytes = (HERE/'inputs/assets/christmas-tree.png').read_bytes()
    with tempfile.TemporaryDirectory(prefix='advent-native-') as temporary:
        folder = Path(temporary)
        native = folder/'own-build.json'
        convert_workbook(output, native)
        payload = json.loads(native.read_text(encoding='utf-8'))
        repair_shape_bindings(payload)
        document = payload['document']['root']
        datasources = next(n for n in document['children'] if n.get('tag') == 'datasources')
        datasource = datasources['children'][0]
        def node(tag, attributes=None, children=None):
            return {'tag': tag, 'attributes': attributes or {}, 'children': children or []}
        image = node('mapped-image', {
            'name': '[Advent Tree Background]', 'caption': 'Christmas tree',
            'expression': 'file:Images/christmas-tree.png',
        }, [node('mapping', {'x': '[Y]', 'y': '[X]', 'left': '0',
                            'right': '4', 'bottom': '0', 'top': '6'}),
            node('image-options', {'lock-aspect-ratio': 'false',
                                   'show-entire-image': 'false'})])
        children = datasource['children']
        index = max(i for i, n in enumerate(children)
                    if n.get('tag') in {'column', 'column-instance', 'group'}) + 1
        children.insert(index, node('mapped-images', children=[image]))
        (folder/'tree.png').write_bytes(image_bytes)
        payload['resources'].append({
            'archive_path': 'Images/christmas-tree.png', 'file': 'tree.png',
            'sha256': hashlib.sha256(image_bytes).hexdigest(),
        })
        native.write_text(json.dumps(payload), encoding='utf-8')
        convert_workbook(native, output, force=True)
    if read_workbook(output).resources.get('Images/christmas-tree.png') != image_bytes:
        raise AssertionError('Background resource did not survive public conversion')


def build():
    OUTPUTS.mkdir(exist_ok=True)
    e = TWBEditor('')
    e.set_hyper_connection(str(HERE/'inputs/calendar.hyper'))
    e.add_calculated_field('Year', 'IFNULL(STR([Challenge Year]), "Christmas")', 'string', role='dimension', field_type='nominal')
    e.add_calculated_field('Day is Null', 'ISNULL([Day])', 'boolean', role='dimension', field_type='nominal')
    e.add_calculated_field('Day Label', 'STR([Day])', 'string', role='dimension', field_type='nominal')
    e.add_calculated_field('Keep All', '"All ornaments"', 'string', role='dimension', field_type='nominal')
    e.add_calculated_field('Tooltip', 'IF [Day is Null] THEN "It\'s Christmas Day!" ELSEIF [Day] = 1 THEN STR([Day]) + " day until Christmas" ELSE STR([Day]) + " days until Christmas" END', 'string', role='dimension', field_type='nominal')
    e.set_shape_palette('Day is Null', {'false':str(HERE/'inputs/assets/christmas-ornament.png'),'true':str(HERE/'inputs/assets/star.png')}, palette='Advent')
    e.add_worksheet('Tree')
    e.configure_layered_chart('Tree', columns=['AVG(Y)'], rows=['AVG(X)'], panes=[dict(axis='AVG(X)',mark_type='Shape',shape='Day is Null',size='Day is Null',label='Day Label',detail='Link to the Challenge',detail_extra=['Day Label','Keep All','Year'],tooltip='ATTR(Tooltip)',mark_style={'size':'5.6249833106994629','mark-labels-show':'true','mark-labels-cull':'false'})], hide_axes=True, filters=[{'column':'Kind','values':['Tree']}])
    e.configure_worksheet_style('Tree',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,
        pane_cell_style={'text-align':'center','vertical-align':'center'},pane_datalabel_style={'color-mode':'user','color':'#ffffff','font-weight':'bold','font-size':'11'},
        size_style={'field':'Day is Null','type':'catsize','min_size':0.500889,'max_size':1},
        axis_style={'encodings':[{'field':'AVG(Y)','scope':'cols','type':'space','attr':'space','class':'0','field-type':'quantitative','range-type':'fixed','min':0,'max':4},{'field':'AVG(X)','scope':'rows','type':'space','attr':'space','class':'0','field-type':'quantitative','range-type':'fixed','min':0,'max':7}]})
    e.configure_custom_tooltip('Tree',[{'field':'ATTR(Tooltip)','bold':True}])
    e.add_calculated_field('Segment ID', 'STR([Segment])', 'string', role='dimension', field_type='nominal')
    e.set_field_format('Challenge Count','*0')
    e.add_worksheet('Bar')
    e.configure_layered_chart('Bar',columns=['SUM(Segment Start)','AVG(Challenge Count)'],rows=['Year'],axis_shelf='columns',fold_axes=True,synchronized=True,hide_axes=True,filters=[{'column':'Kind','values':['Bar']}],panes=[
        dict(axis='SUM(Segment Start)',mark_type='GanttBar',size='SUM(Segment Width)',color='AVG(Segment Start)',detail='Segment ID',tooltip=['Year','AVG(Challenge Count)'],mark_style={'size':'0.95552486181259155','has-stroke':'false'}),
        dict(axis='AVG(Challenge Count)',mark_type='Bar',label='AVG(Challenge Count)',tooltip=['Year','AVG(Challenge Count)'],mark_style={'size':'0.95552486181259155','mark-transparency':'0','mark-labels-show':'true','mark-labels-cull':'false','has-stroke':'false'})])
    e.configure_worksheet_style('Bar',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,hide_row_field_labels=True,color_style={'field':'AVG(Segment Start)','palette':'red_green_diverging_10_0','reverse':False,'min':0,'max':10},axis_style={'encodings':[{'field':'SUM(Segment Start)','scope':'cols','type':'space','attr':'space','class':'0','field-type':'quantitative','range-type':'fixed','min':0,'max':11}]})
    for i in (0,1): e.configure_custom_tooltip('Bar',[{'field':'Year','bold':True},{'text':' | '},{'field':'AVG(Challenge Count)'},{'text':' favourite challenges'}],pane_index=i)
    e.set_worksheet_title('Bar','Favourite challenges by year')
    def zone(kind,x,y,w,h,**kw):return dict(type=kind,absolute=dict(x=x,y=y,w=w,h=h),**kw)
    e.add_dashboard(DASHBOARD,1000,800,layout=dict(type='container',direction='floating',children=[
        zone('text',800,1000,98400,8750,text="#WOW2021 Tableau Coaches’ Favourite Challenges Advent Calendar\nClick an ornament to visit its challenge. Click a year bar to filter; clear the selection to restore all.",font_size='16'),
        zone('worksheet',800,9750,64300,83500,name='Tree',show_title=False,fit='entire'),
        zone('worksheet',65100,67157,34100,26093,name='Bar',show_title=True,fit='entire'),
        zone('text',800,93250,30400,5750,text='CHALLENGE BY: CANDRA MCRAE',font_size='8',font_color='#e15759'),
        zone('text',31200,93250,36900,5750,text='#WOW2021 | WEEK 48\nworkout-wednesday.com/tab2021w48/',font_size='8',font_color='#e15759'),
        zone('text',68100,93250,31100,5750,text='Based on Donna Coles’ solution\nRebuilt independently with cwtwb',font_size='8',font_color='#e15759')]))
    e.add_dashboard_action(DASHBOARD,'filter',source_sheet='Bar',target_sheet='Tree',fields=['Year'],caption='Filter tree by challenge year',clear_behavior='show-all')
    e.initialize_dashboard_filter_action(DASHBOARD,'Filter tree by challenge year',{'Year':['2018','2019','2020','2021','Christmas']})
    e.add_dashboard_action(DASHBOARD,'url',source_sheet='Tree',url='<[Link to the Challenge]>',caption='Open selected challenge')
    e.add_dashboard_action(DASHBOARD,'highlight',source_sheet='Tree',target_sheet='Tree',fields=['Keep All'],caption='Keep all ornaments highlighted')
    e.set_active_dashboard(DASHBOARD)
    output=OUTPUTS/'replicated-workbook.twbx'
    e.save(output)
    add_mapped_background(output)
    provenance={'sdk_version':importlib.metadata.version('cwtwb'),'sdk_module':str(Path(cwtwb.__file__).resolve()),'authoring_route':'blank TWBEditor plus public native-JSON structural conversion workaround','workbook_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (OUTPUTS/'render-reference-build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    return output

if __name__=='__main__': print(build())
