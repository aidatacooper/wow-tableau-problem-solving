"""Rebuild both London hotel/pub buffer views from extracted Hyper data."""
from pathlib import Path
from cwtwb import TWBEditor

CASE = Path(__file__).resolve().parent
INT = '2020_03_04_WW10_London_Pubs_Buffer_Int'
JEDI = '2020_03_04_WW10_London_Pubs_Buffer_Jedi'


def calc(e, name, formula, datatype='real', role='measure', field_type='quantitative', **options):
    e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=field_type, **options)


def zone(kind, x, y, w, h, **options):
    return {'type':kind, 'absolute':{k:round(v/700*100000) for k,v in zip(('x','y','w','h'),(x,y,w,h))}, **options}


def style(e, sheet, map_sheet=False):
    settings = dict(hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,hide_row_field_labels=True,hide_col_field_labels=True)
    if map_sheet:
        settings.update(map_style={'map_style':'streets','washout':0},pane_mark_style={'mark-labels-show':'true'})
    e.configure_worksheet_style(sheet, **settings)


def dashboard(e, name, sheet, title, extra=None):
    e.add_dashboard(name,width=700,height=700,layout={'type':'container','direction':'floating','children':[
        zone('worksheet',12,80 if sheet=='Map_Jedi' else 44,676,544 if sheet=='Map_Jedi' else 580,name=sheet,show_title=False,fit='entire'),
        zone('text',12,6,676,38,text=title,font_size='14',font_color='#333333'),
        *(extra or []),
        zone('text',12,640,676,20,text='DESIGNED BY: SEAN MILLER          #WOW2020 | WEEK 10          RECREATED WITH CWTWB',font_size='8',font_color='#ec7d18',bold=True),
        zone('text',12,674,676,20,text='DATA: YELP                    workout-wednesday.com/2020w09/',font_size='8',font_color='#ec7d18',bold=True),
    ]})


def build():
    e = TWBEditor('')
    e.set_hyper_connection(str(CASE/'inputs/2020_03_04_WW09_London Pubs.csv+ (Multiple Connections).hyper'))
    calc(e,'Buffer Hotel','BUFFER(MAKEPOINT([LAT],[LON]),500,"m")','spatial','measure','nominal')
    calc(e,'Pub Location','MAKEPOINT([Lat1],[Lon1])','spatial','measure','nominal')
    calc(e,'Distance','DISTANCE(MAKEPOINT([Lat1],[Lon1]),MAKEPOINT([LAT],[LON]),"m")',default_format='n#,##0;-#,##0')
    calc(e,'Distance Sort','-[Distance]')
    calc(e,'Number of Records','1','integer')
    calc(e,'Distance Caption','"Distance"','string','dimension','nominal')
    e.add_worksheet('Map_int')
    e.configure_chart('Map_int',mark_type='Map',geographic_field='Buffer Hotel',map_layers=[
        {'geometry':'Buffer Hotel','detail':'Hotel Name','label':'SUM(Number of Records)','mark_type':'Multipolygon','mark_color':'#e7aa63'},
        {'geometry':'Pub Location','detail':'Pub Name','mark_type':'Circle','mark_color':'#898989','has_stroke':True,'stroke_color':'#ffffff','mark_size_value':'1.6591712236404419','tooltip':['Pub Name','SUM(Distance)']},
    ])
    style(e,'Map_int',True)
    e.add_worksheet('VIT:Pub List')
    e.configure_chart('VIT:Pub List',mark_type='Text',rows=['Hotel Name','Pub Name'],columns=['Distance Caption'],label='SUM(Distance)',sort_descending='SUM(Distance Sort)',sort_field='Pub Name')
    style(e,'VIT:Pub List')
    e.configure_custom_tooltip('Map_int',[{'text':'There are '},{'field':'SUM(Number of Records)','bold':True},{'text':' pubs within 500m of '},{'field':'Hotel Name','bold':True},{'text':'\n'},{'sheet':{'name':'VIT:Pub List','filter_fields':['Hotel Name'],'maxwidth':300,'maxheight':300}}],pane_index=1)
    e.configure_custom_tooltip('Map_int',[{'field':'Pub Name','bold':True},{'text':'\nDistance: '},{'field':'SUM(Distance)'},{'text':' m'}],pane_index=2)
    e.configure_worksheet_style('Map_int',panes_style={'1':{'datalabel_style':{'font-size':'24','font-weight':'bold'},'mark_style':{'mark-labels-show':'true','mark-transparency':'142','mark-color':'#ffbe7d'}},'2':{'mark_style':{'mark-transparency':'142'}}})
    dashboard(e,INT,'Map_int','Can you isolate the pubs within 500m of a hotel?')

    e.add_hyper_datasource('Hotels and Pubs',str(CASE/'inputs/2020_03_04_WW09_Hotels_Pubs Combined.hyper'))
    e.add_parameter('Selected Hotel',datatype='string',default_value='The Hoxton - Shoreditch',domain_type='any')
    e.add_parameter('Buffer Radius',datatype='integer',default_value='500',min_value='0',max_value='500',granularity='1')
    choices=[' Yelp Rating ',' Price Rating ',' Number of Ratings ']
    e.add_parameter('Selected Sort Measure',datatype='string',default_value=' Price Rating ',domain_type='list',allowed_values=choices)
    calc(e,'Is Selected Hotel?','[Name]=[Selected Hotel]','boolean','dimension','nominal')
    calc(e,'Selected Hotel Lat','{FIXED : MIN(IIF([Is Selected Hotel?],[LAT],NULL))}')
    calc(e,'Selected Hotel Long','{FIXED : MIN(IIF([Is Selected Hotel?],[LON],NULL))}')
    calc(e,'Selected Hotel Location','MAKEPOINT([Selected Hotel Lat],[Selected Hotel Long])','spatial','measure','nominal')
    calc(e,'Hotel Buffer','BUFFER([Selected Hotel Location],[Buffer Radius],"m")','spatial','measure','nominal')
    calc(e,'Hotel Label','[Selected Hotel]','string','dimension','nominal')
    calc(e,'Pub Name','IF [Location Type]="Pub" THEN [Name] END','string','dimension','nominal')
    calc(e,'Pub Key','IF [Location Type]="Pub" THEN [Name]+" | "+[Neighborhood] END','string','dimension','nominal')
    calc(e,'Pub Location','IF [Location Type]="Pub" THEN MAKEPOINT([LAT],[LON]) END','spatial','measure','nominal')
    calc(e,'Distance Selected Hotel-Pub','DISTANCE([Selected Hotel Location],[Pub Location],"m")',default_format='n#,##0;-#,##0')
    calc(e,'Pub Proximity Size','10000-[Distance Selected Hotel-Pub]')
    calc(e,'Chart Sort','CASE [Selected Sort Measure] WHEN " Yelp Rating " THEN SUM([Yelp Rating]) WHEN " Price Rating " THEN -SUM([Price Rating Sort]) WHEN " Number of Ratings " THEN SUM([Yelp # of Ratings]) END')
    calc(e,'Yelp Rating Header','[Yelp Rating]','real','dimension','ordinal')
    for name,value in [('True','TRUE'),('False','FALSE')]:calc(e,name,value,'boolean','dimension','nominal')
    e.add_worksheet('Map_Jedi')
    e.configure_chart('Map_Jedi',mark_type='Map',geographic_field='Pub Location',map_layers=[
        {'geometry':'Pub Location','detail':'Pub Key','color':'SUM(Distance Selected Hotel-Pub)','size':'SUM(Distance Selected Hotel-Pub)','mark_type':'Circle','has_stroke':True,'stroke_color':'#898989','mark_size_value':'1.5052486658096313','tooltip':['Pub Name','Neighborhood','SUM(Distance Selected Hotel-Pub)']},
        {'geometry':'Hotel Buffer','detail':'Hotel Label','label':'Hotel Label','mark_type':'Multipolygon','mark_color':'#b4b4b4'},
    ])
    style(e,'Map_Jedi',True)
    e.configure_worksheet_style('Map_Jedi',panes_style={'1':{'mark_style':{'mark-transparency':'162'}}})
    e.configure_worksheet_style('Map_Jedi',color_style={'field':'SUM(Distance Selected Hotel-Pub)','palette':'red_10_0','reverse':True},size_style={'field':'SUM(Distance Selected Hotel-Pub)','type':'rangesize','max_size':'1','min_size':'0.08','reverse':False})
    e.add_worksheet('Hotel Chart')
    e.configure_chart('Hotel Chart',mark_type='Bar',rows=['Name','Yelp Rating Header','Price Rating'],columns=['SUM(Yelp # of Ratings)'],color='Is Selected Hotel?',color_map={'true':'#499894','false':'#b4b4b4'},label='SUM(Yelp # of Ratings)',sort_descending='Chart Sort',sort_field='Name',filters=[{'column':'Location Type','values':['Hotel']}],tooltip=['Yelp Rating','Price Rating','Yelp # of Ratings'])
    style(e,'Hotel Chart')
    panes=[]
    for index,choice in enumerate(choices):
        axis=choice
        label='Selector Label '+str(index)
        calc(e,axis,'MIN(0.0)')
        calc(e,label,f'IF [Selected Sort Measure]="{choice}" THEN "●{choice}" ELSE "○{choice}" END','string','dimension','nominal')
        panes.append({'axis':'['+axis+']','mark_type':'Text','label':label,'labels':['Measure Names'],'detail_extra':['True','False'],'mark_style':{'mark-labels-show':'true'}})
    e.add_worksheet('Sort Selector')
    e.configure_layered_chart('Sort Selector',panes=panes,axis_shelf='cols',fold_axes=False,hide_axes=True)
    style(e,'Sort Selector')
    dashboard(e,JEDI,'Map_Jedi','Can you find the pubs closest to a chosen hotel?',[
        zone('container',12,104,465,405,direction='vertical',style={'background-color':'#ffffff'},children=[{'type':'worksheet','name':'Sort Selector','fixed_size':100,'show_title':False,'fit':'entire'},{'type':'worksheet','name':'Hotel Chart','show_title':False,'fit':'entire'}]),
        zone('color',16,380,220,58,worksheet='Map_Jedi',field='SUM(Distance Selected Hotel-Pub)',style={'background-color':'#f4f4f4'}),
        zone('paramctrl',16,570,190,45,parameter='Buffer Radius',mode='1'),
    ])
    e.add_dashboard_toggle_button(JEDI,['Sort Selector','Hotel Chart'],caption_shown='Sort & select a hotel | Click here to close',caption_hidden='Click here to select a hotel',initially_hidden=True,position={'x':12,'y':50,'w':330,'h':30})
    e.add_dashboard_action(JEDI,'parameter',source_sheet='Hotel Chart',source_field='Name',target_parameter='Selected Hotel',event_type='on-select',clear_behavior='keep-current')
    # Native virtual Measure Names values map the three selector axes to the
    # same spaced string identities used by the parameter and chart sorting.
    e.add_dashboard_action(JEDI,'parameter',source_sheet='Sort Selector',source_field='Measure Names',target_parameter='Selected Sort Measure',event_type='on-select',clear_behavior='keep-current')
    e.add_dashboard_action(JEDI,'filter',source_sheet='Sort Selector',target_sheet='Sort Selector',field_mappings={'True':'False'},event_type='on-select',clear_behavior='show-all')
    output=CASE/'outputs/replicated-workbook.twbx'
    e.save(str(output))
    return output


if __name__=='__main__':print(build())
