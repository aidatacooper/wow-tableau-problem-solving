"""Build WW13 from locked Hyper using the public SDK."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
DASHBOARD='2020_03_25_WW13_Sales_Performance'

def build(output_path=None):
 e=TWBEditor("")
 e.set_hyper_connection(str(HERE/'inputs/Orders (Sample - Superstore).hyper'))
 calculations=[('Current Year','{FIXED:MAX(YEAR([Order Date]))}','integer','dimension','ordinal'),('Previous Year','[Current Year]-1','integer','dimension','ordinal'),('Yesterday','MAKEDATE([Current Year],MONTH(TODAY()),DAY(TODAY()))-1','date','dimension','ordinal'),('Dates To Include','YEAR([Order Date])>=[Previous Year] AND [Order Date]<=[Yesterday]','boolean','dimension','nominal'),('Current Month',"DATETRUNC('month',[Yesterday])",'datetime','dimension','ordinal'),('Yesterday Previous Month',"DATEADD('month',-1,[Yesterday])",'datetime','dimension','ordinal'),('Previous Month',"DATETRUNC('month',[Yesterday Previous Month])",'datetime','dimension','ordinal'),('Days in Current MTD','DAY([Yesterday])','integer','measure','quantitative'),('Days in Current Full Month',"DATEDIFF('day',DATETRUNC('month',[Yesterday]),DATEADD('month',1,DATETRUNC('month',[Yesterday])))",'integer','measure','quantitative')]
 for name,f,d,r,t in calculations:e.add_calculated_field(name,f,datatype=d,role=r,field_type=t)
 metrics=[]
 for metric in ['Sales','Profit']:
  for prefix,formula in [('Current MTD',f"IF DATETRUNC('month',[Order Date])=[Current Month] AND [Order Date]<=[Yesterday] THEN [{metric}] END"),('Current YTD',f'IF YEAR([Order Date])=[Current Year] AND [Order Date]<=[Yesterday] THEN [{metric}] END'),('Previous MTD',f"IF DATETRUNC('month',[Order Date])=[Previous Month] AND [Order Date]<=[Yesterday Previous Month] THEN [{metric}] END"),('MoM',f'SUM([Current MTD {metric}])-SUM([Previous MTD {metric}])'),('Run Rate',f'(SUM([Current MTD {metric}])/SUM([Days in Current MTD]))*SUM([Days in Current Full Month])')]:
   name=f'{prefix} {metric}';e.add_calculated_field(name,formula,datatype='real');e.set_field_format(name,'c"$"#,##0;-"$"#,##0');metrics.append(name)
  e.set_field_format(metric,'c"$"#,##0;-"$"#,##0')
 e.add_calculated_field('Order Year','YEAR([Order Date])',datatype='integer',role='dimension',field_type='ordinal')
 e.add_calculated_field('Year Series',"IF YEAR([Order Date])=[Current Year] THEN 'Current' ELSE 'Previous' END",datatype='string',role='dimension',field_type='nominal')
 e.add_calculated_field('Year Size','IF YEAR([Order Date])=[Current Year] THEN 0 ELSE 1 END',datatype='integer',role='dimension',field_type='ordinal')
 for sheet in ['Date','KPI','Sales','Profit','CHK Data']:e.add_worksheet(sheet)
 e.configure_layered_chart('Date',panes=[{'mark_type':'Text','labels':['EXACTDATE(Yesterday)'],'label_runs':[{'text':'Data as of ','fontcolor':'#285179','fontsize':8},{'field':'EXACTDATE(Yesterday)','fontcolor':'#285179','fontsize':8}],'mark_style':{'mark-labels-show':'true'}}])
 filters=[{'column':'Dates To Include','values':[True]}];panes=[]
 for metric in ['Sales','Profit']:
  e.add_calculated_field(f'{metric} Position','MIN(0)',datatype='integer')
  names=[f'{p} {metric}' for p in ['Current MTD','Previous MTD','MoM','Run Rate','Current YTD']]
  refs=[f'SUM({name})' if name.startswith(('Current','Previous')) else name for name in names]
  panes.append({'axis':f'{metric} Position','mark_type':'Text','labels':refs,'label_runs':[{'text':metric+'\n','bold':True,'fontsize':12,'fontcolor':'#285179'},{'field':refs[0],'bold':True,'fontsize':15,'fontcolor':'#285179'},{'text':' MTD\n','fontsize':8,'fontcolor':'#285179'},{'field':refs[1],'fontsize':8,'fontcolor':'#a8b9c9'},{'text':' PMTD\n\n','fontsize':8,'fontcolor':'#a8b9c9'},{'field':refs[2],'bold':True,'fontsize':8,'fontcolor':'#285179'},{'text':' MoM\n','fontsize':8,'fontcolor':'#285179'},{'field':refs[3],'bold':True,'fontsize':8,'fontcolor':'#285179'},{'text':' Run Rate\n\n','fontsize':8,'fontcolor':'#285179'},{'field':refs[4],'bold':True,'fontsize':15,'fontcolor':'#285179'},{'text':' YTD','fontsize':8,'fontcolor':'#285179'}],'mark_style':{'mark-labels-show':'true','mark-labels-cull':'false'}})
 e.configure_layered_chart('KPI',rows=['Sales Position','Profit Position'],panes=panes,axis_shelf='rows',fold_axes=False,hide_axes=True,filters=filters)
 for metric in ['Sales','Profit']:
  e.configure_layered_chart(metric,columns=['MONTH(Order Date)'],rows=[f'SUM({metric})'],panes=[{'axis':f'SUM({metric})','mark_type':'Bar','color':'Year Series','size':'Year Size','detail_extra':['Order Year'],'color_map':{'Current':'#285179','Previous':'#a8b9c9'},'breakdown':'off','mark_sizing_off':True,'mark_style':{'size':'1.2523757'}}],filters=filters)
  e.set_worksheet_title(metric,'YoY '+metric)
  e.configure_worksheet_style(metric,label_formats=[{'field':'MONTH(Order Date)','text-format':'iLLLLL','font-size':'8'}],axis_style={'per_field':[{'field':f'SUM({metric})','scope':'rows','attr':'title','value':''}]})
 e.configure_layered_chart('CHK Data',rows=['Measure Names'],panes=[{'mark_type':'Text','label':'Multiple Values','measure_values':[f'SUM({m})' if m.startswith(('Current','Previous')) else m for m in metrics],'mark_style':{'mark-labels-show':'true'}}],filters=filters)
 for sheet in ['Date','KPI','Sales','Profit','CHK Data']:
  e.configure_worksheet_style(sheet,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_table_dividers=True,hide_col_field_labels=True,hide_row_field_labels=True,hide_sort_controls=True)
 e.configure_worksheet_style('Date',hide_axes=True,disable_tooltip=True)
 e.configure_worksheet_style('KPI',hide_axes=True,disable_tooltip=True,pane_cell_style={'text-align':'left','vertical-align':'center'})
 def pos(x,y,w,h):return {'x':round(x/800*100000),'y':round(y/600*100000),'w':round(w/800*100000),'h':round(h/600*100000)}
 zones=[{'type':'text','runs':[{'text':'Sales Performance','font_color':'#285179','font_size':20}],'absolute':pos(8,8,650,43)},{'type':'worksheet','name':'Date','show_title':False,'fit':'entire','absolute':pos(8,51,392,40)},{'type':'worksheet','name':'KPI','show_title':False,'fit':'entire','absolute':pos(18,93,254,457)},{'type':'worksheet','name':'Sales','show_title':True,'fit':'entire','absolute':pos(273,93,509,228)},{'type':'worksheet','name':'Profit','show_title':True,'fit':'entire','absolute':pos(273,322,509,228)},{'type':'text','runs':[{'text':'#WOW2020 | WEEK 13 | DESIGNED BY MEERA UMASANKAR | RECREATED WITH CWTWB','font_color':'#285179','font_size':8}],'absolute':pos(8,553,784,24)},{'type':'text','text':'http://www.workout-wednesday.com/2020w13/','absolute':pos(200,578,400,20)}]
 e.add_dashboard(DASHBOARD,width=800,height=600,worksheet_names=['Date','KPI','Sales','Profit'],layout={'type':'container','direction':'floating','children':zones});e.set_active_dashboard(DASHBOARD)
 output=Path(output_path or HERE/'outputs/replicated-workbook.twbx');output.parent.mkdir(exist_ok=True);e.save(output,validate=False);return output
if __name__=='__main__':print(build())
