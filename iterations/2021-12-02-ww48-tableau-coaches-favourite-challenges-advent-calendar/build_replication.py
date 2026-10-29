"""Rebuild the advent calendar using extracted data and public cwtwb APIs."""
from pathlib import Path
import json, hashlib, importlib.metadata
import cwtwb
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / 'outputs'
DASHBOARD = 'Advent Calendar'

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
        dict(axis='SUM(Segment Start)',mark_type='GanttBar',size='SUM(Segment Width)',color='AVG(Gradient)',detail='Segment ID',tooltip=['Year','AVG(Challenge Count)'],mark_style={'size':'0.95552486181259155','has-stroke':'false'}),
        dict(axis='AVG(Challenge Count)',mark_type='Bar',label='AVG(Challenge Count)',tooltip=['Year','AVG(Challenge Count)'],mark_style={'size':'0.95552486181259155','mark-transparency':'0','mark-labels-show':'true','mark-labels-cull':'false','has-stroke':'false'})])
    e.configure_worksheet_style('Bar',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,hide_row_field_labels=True,color_style={'field':'AVG(Gradient)','palette':'red_green_diverging_10_0'},axis_style={'encodings':[{'field':'SUM(Segment Start)','scope':'cols','type':'space','attr':'space','class':'0','field-type':'quantitative','range-type':'fixed','min':0,'max':11}]})
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
    provenance={'sdk_version':importlib.metadata.version('cwtwb'),'sdk_module':str(Path(cwtwb.__file__).resolve()),'workbook_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (OUTPUTS/'build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    return output

if __name__=='__main__': print(build())
