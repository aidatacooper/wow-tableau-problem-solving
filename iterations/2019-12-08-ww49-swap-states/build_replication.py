"""Independent generated-geography state trellis and selection detail."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
DASHBOARD='2019_12_04_WW49_Select_State_Small_Multiple'
LAYERS=['background','water','waterway-river-canal','barrier_line-land-line','barrier_line-land-polygon','built-up-area','industrial','national_park','parks','pitch','landcover_crop','landcover_grass','landcover_scrub','landcover_wood','aeroway-polygon','aeroway-runway','aeroway-taxiway','9-dash-line','9-dash-line-casing'] + ['admin-0-'+n for n in ['boundaries','boundaries-bg','boundaries-bg-sub','boundaries-dispute','boundaries-dispute-sub','boundaries-sub']] + ['admin-0-label-'+str(n)+s+'-tier' for n,s in [(1,'st'),(2,'nd'),(3,'rd'),(4,'th'),(5,'th')]] + ['admin-1-boundaries-'+n for n in ['lg-parents','lg-parents-bg','md-parents','md-parents-bg','sm-parents','sm-parents-bg','supress','supress-bg']] + ['admin-1-label-'+str(n)+s+'-tier' for n,s in [(1,'st'),(2,'nd'),(3,'rd'),(4,'th'),(5,'th'),(6,'th'),(7,'th'),(8,'th'),(9,'th')]] + ['us-admin-1-label-abbr-'+str(n)+s+'-tier' for n,s in [(1,'st'),(2,'nd'),(3,'rd')]] + ['admin1-water-lines-usa-tableau']

def build():
    editor=TWBEditor('')
    editor.set_hyper_connection(str(next((HERE/'inputs').glob('*.hyper'))), table_name='Extract')
    editor.set_geocoding_context(country='United States',state=None)
    editor.set_field_format('Sales','c"$"#,##0;-"$"#,##0')
    editor.add_set('Selected Set','State',members=['Oklahoma'])
    for name,formula,datatype in [('Cols','FLOAT(INT((INDEX()-1)%5))','real'),('Rows','FLOAT(INT((INDEX()-1)/5))','real'),('Label Rows','[Rows]+0.5','real'),('State Rank','RANK_UNIQUE(SUM([Sales]))','integer'),('Global Rank','RANK_UNIQUE(SUM([Sales]))','integer')]:
        editor.add_calculated_field(name,formula,datatype=datatype,table_calc='Rows')
    editor.add_worksheet('Selected State')
    editor.configure_layered_chart('Selected State',columns=['Longitude (generated)'],rows=['Latitude (generated)','Latitude (generated)'],filters=[{'column':'Selected Set','values':[True]}],hide_axes=True,panes=[
        {'axis':'Latitude (generated)','mark_type':'Multipolygon','detail':'State','geometry':'Geometry (generated)','mark_sizing_off':True,'labels':['State','SUM(Sales)'],'label_runs':[{'field':'State','bold':True,'fontcolor':'#666666','fontsize':20},{'text':'\n'},{'field':'SUM(Sales)','fontsize':15}],'mark_style':{'mark-labels-show':'true','mark-labels-cull':'false','mark-color':'#ffffff','has-stroke':'true','stroke-color':'#e15759','size':'4.91'}},
        {'axis':'Latitude (generated)','mark_type':'Circle','detail':'State','detail_extra':['City'],'size':'SUM(Sales)','tooltip':['State','City','SUM(Sales)'],'mark_style':{'mark-color':'#639ab7','mark-transparency':'60','has-stroke':'false','size':'2.8176796436309814'}}])
    editor.add_worksheet('States')
    overrides={name:[{'ordering_type':'Field','ordering_field':'State'}] for name in ['Rows','Cols','State Rank']}
    overrides['Global Rank']=[{'ordering_type':'Field','order':['Selected Set','State']}]
    overrides['Label Rows']=[{'ordering_type':'Field','ordering_field':'State'},{'field':'Rows','ordering_type':'Field','ordering_field':'State'}]
    editor.configure_layered_chart('States',columns=['Cols'],rows=['Rows','Label Rows'],filters=[{'column':'Selected Set','values':[True],'kind':'hide','exclude':True},{'column':'State Rank','type':'quantitative','max':'25'}],sort_descending='SUM(Sales)',sort_field='State',table_calc_overrides=overrides,hide_axes=True,panes=[
        {'axis':'Rows','mark_type':'Multipolygon','detail':'State','detail_extra':['Selected Set'],'geometry':'Geometry (generated)','mark_sizing_off':True,'tooltip':['State','State Rank','SUM(Sales)'],'mark_style':{'size':'4.28482','mark-color':'#ffffff','has-stroke':'true','stroke-color':'#e15759'}},
        {'axis':'Label Rows','mark_type':'Text','detail':'State','detail_extra':['Selected Set'],'labels':['State','Global Rank','SUM(Sales)'],'label_runs':[{'field':'State','bold':True},{'text':' #'},{'field':'Global Rank'},{'text':'\n'},{'field':'SUM(Sales)'}],'mark_style':{'mark-labels-show':'true','mark-labels-cull':'false','size':'0.691657','mark-color':'#555555'}}])
    for sheet in ['States','Selected State']:
        editor.configure_worksheet_style(sheet,hide_axes=True,hide_gridlines=True,hide_borders=True,hide_zeroline=True,hide_table_dividers=True,map_style={'washout':0.0,'layers':{layer:False for layer in LAYERS}},pane_cell_style={'text-align':'center'})
    editor.configure_worksheet_style('States',axis_style={'encodings':[{'field':'Rows','scope':'rows','class':'0','range_type':'fixed','min':'-0.5','max':'5','reverse':True},{'field':'Cols','scope':'cols','class':'0','range_type':'fixed','min':'-0.5','max':'4.5'}]})
    layout={'type':'container','direction':'vertical','children':[{'type':'text','text':'WEEK 49 : CAN YOU SWAP STATES?','font_size':'15','font_color':'#28a1a7','fixed_size':35},{'type':'worksheet','name':'Selected State','show_title':False,'fit':'entire','fixed_size':285},{'type':'worksheet','name':'States','show_title':False,'fit':'entire','fixed_size':470},{'type':'container','direction':'horizontal','fixed_size':50,'children':[{'type':'text','fixed_size':120,'runs':[{'text':'DESIGNED BY : LUKE\nSTANKE','font_size':'8','font_color':'#28a1a7','font_alignment':'0','bold':True}]},{'type':'text','weight':1,'runs':[{'text':'#WORKOUTWEDNESDAY | 2019 | WEEK 49','font_size':'8','font_color':'#28a1a7','font_alignment':'1','bold':True}]},{'type':'text','fixed_size':126,'runs':[{'text':'REFERENCE :\nDONNA COLES','font_size':'8','font_color':'#28a1a7','font_alignment':'2','bold':True}]}]},{'type':'text','fixed_size':35,'runs':[{'text':'http://www.workout-wednesday.com/2019w49/','font_size':'8','font_color':'#006699','font_alignment':'1','hyperlink':'http://www.workout-wednesday.com/2019w49/'}]}]}
    editor.add_dashboard(DASHBOARD,width=600,height=900,layout=layout,worksheet_names=['Selected State','States'])
    editor.add_dashboard_set_action(DASHBOARD,'States','Selected Set',event_type='on-select',clear_option='do-nothing',selection_mode='assign',single_select=True,caption='Select State')
    editor.set_active_dashboard(DASHBOARD)
    (HERE/'outputs').mkdir(exist_ok=True)
    editor.save(HERE/'outputs/replicated-workbook.twbx',validate=False)
    editor.save(HERE/'outputs/replicated-workbook.twb',validate=False)
if __name__=='__main__':build()
