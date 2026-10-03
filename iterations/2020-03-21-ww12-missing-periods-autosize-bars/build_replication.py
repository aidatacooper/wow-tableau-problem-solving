"""Rebuild selectable missing date periods and native adaptive bar widths."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
DASHBOARD='2020_03_18_WW12_Profit_By_Orders'
SUBCATEGORIES=['Accessories','Appliances','Art','Binders','Bookcases','Chairs','Copiers','Envelopes','Fasteners','Furnishings','Labels','Machines','Paper','Phones','Storage','Supplies','Tables']

def build(output_path=None):
 e=TWBEditor("");e.set_hyper_connection(str(HERE/'inputs/TEMP_15dwgu91thw88n194tdxu1u2mxgk.hyper'));e.set_date_options(start_of_week='sunday')
 e.add_parameter('Select Period','string','week',domain_type='list',allowed_values=['day','week','month'],allowed_aliases={'day':'Daily','week':'Weekly','month':'Monthly'},alias='Weekly')
 e.add_parameter('Number of Years','integer','2',domain_type='range',min_value='1',max_value='4',granularity='1')
 e.add_set('Selected Sub-Category','Sub-Category',members=['Tables'])
 for name,f,d,r,t in [('Dates to Include','YEAR([Order Date])>={FIXED:MAX(YEAR([Order Date]))}-([Number of Years]-1)','boolean','dimension','nominal'),('Date to Plot',"DATE(DATETRUNC([Select Period],[Order Date],'Sunday'))",'date','dimension','ordinal'),('Number of Orders','COUNTD([Order ID])','integer','measure','quantitative'),('Size',"CASE [Select Period] WHEN 'day' THEN 1 WHEN 'week' THEN 5 ELSE 10 END",'integer','dimension','quantitative'),('Selected','[Selected Sub-Category]','boolean','dimension','nominal'),('True','TRUE','boolean','dimension','nominal'),('False','FALSE','boolean','dimension','nominal'),('Selector Position','MIN(0)','integer','measure','quantitative'),('Selector Label',"IF [Selected Sub-Category] THEN '● ' ELSE '○ ' END + [Sub-Category]",'string','dimension','nominal')]:e.add_calculated_field(name,f,datatype=d,role=r,field_type=t)
 for sheet in ['Chart','Selector']:e.add_worksheet(sheet)
 e.configure_layered_chart('Chart',columns=['EXACTDATE(Date to Plot)'],rows=['Number of Orders'],panes=[{'axis':'Number of Orders','mark_type':'Bar','color':'SUM(Profit)','size':'Size','tooltip':['Number of Orders','SUM(Profit)'],'mark_style':{'size':'0.7'},'mark_sizing':{'mark-sizing-setting':'marks-scaling-on','mark-alignment':'mark-alignment-center','use-custom-mark-size':False,'custom-mark-size-in-axis-units':1.0}}],filters=[{'column':'Dates to Include','values':[True]},{'column':'Selected','values':[True]}])
 e.set_worksheet_rich_title('Chart',[{'text':'<[Parameters].[Select Period]> Profit by Orders','fontsize':18}])
 e.configure_worksheet_style('Chart',hide_gridlines=True,hide_borders=True,hide_table_dividers=True,color_style={'field':'SUM(Profit)','palette':'red-green-diverging','center':0},axis_style={'per_field':[{'field':'Number of Orders','scope':'rows','attr':'title','value':'Number of Orders'},{'field':'EXACTDATE(Date to Plot)','scope':'cols','attr':'title','value':'Order Date'}]})
 e.configure_layered_chart('Selector',columns=['Selector Position'],rows=['Sub-Category'],axis_shelf='columns',panes=[{'axis':'Selector Position','mark_type':'Text','label':'Selector Label','detail_extra':['True','False'],'mark_style':{'mark-labels-show':'true','mark-labels-cull':'false'},'label_runs':[{'field':'Selector Label','fontsize':9}]}],hide_axes=True)
 e.configure_worksheet_style('Selector',hide_row_label='Sub-Category',hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,hide_row_field_labels=True,hide_col_field_labels=True,hide_sort_controls=True,disable_tooltip=True,pane_cell_style={'text-align':'left'})
 def p(x,y,w,h):return {'x':round(x/1000*100000),'y':round(y/600*100000),'w':round(w/1000*100000),'h':round(h/600*100000)}
 zones=[{'type':'worksheet','name':'Chart','fit':'entire','show_title':True,'absolute':p(8,8,984,512)},{'type':'container','direction':'vertical','absolute':p(853,47,139,540),'style':{'background-color':'#ffffff'},'children':[{'type':'paramctrl','parameter':'Select Period','mode':'compact','caption':'Period','fixed_size':56},{'type':'worksheet','name':'Selector','show_title':False,'fit':'entire'},{'type':'paramctrl','parameter':'Number of Years','mode':'slider','caption':'Number of Years','fixed_size':79}]},{'type':'text','runs':[{'text':'#WOW2020 | WEEK 12 | DESIGNED BY LORNA BROWN | RECREATED WITH CWTWB','font_size':8}],'absolute':p(8,528,984,32)},{'type':'text','text':'http://www.workout-wednesday.com/2020w12/','absolute':p(300,560,500,32)}]
 e.add_dashboard(DASHBOARD,width=1000,height=600,worksheet_names=['Chart','Selector'],layout={'type':'container','direction':'floating','children':zones})
 e.add_dashboard_set_action(DASHBOARD,'Selector','Selected Sub-Category',event_type='on-select',caption='Select Sub-Category',clear_option='do-nothing',single_select=True,selection_mode='assign')
 e.add_dashboard_action(DASHBOARD,'filter',source_sheet='Selector',target_sheet='Selector',field_mappings={'True':'False'},event_type='on-select',clear_behavior='show-all',caption='Deselect Sub-Category')
 e.add_dashboard_toggle_button(DASHBOARD,target_worksheets=['Selector'],caption_shown='Hide',caption_hidden='Show',initially_hidden=True,position={'x':947,'y':3,'w':49,'h':44})
 e.set_active_dashboard(DASHBOARD)
 output=Path(output_path or HERE/'outputs/replicated-workbook.twbx');output.parent.mkdir(exist_ok=True);e.save(output,validate=False);return output
if __name__=='__main__':print(build())
