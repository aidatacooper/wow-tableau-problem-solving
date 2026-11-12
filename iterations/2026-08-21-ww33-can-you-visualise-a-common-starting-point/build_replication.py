from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=next((HERE/'inputs').glob('*.hyper')); OUT=HERE/'outputs'/'replicated-workbook.twbx'
def build(path=OUT):
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER)); e.set_date_options(start_of_week='sunday')
 for n,f,dt in [('Daily Orders','[daily_orders]','real'),('Launch Week',"DATE(DATETRUNC('week',{FIXED [Product]:MIN([Date])}))",'date'),('Week of Date',"DATE(DATETRUNC('week',[Date]))",'date'),('Weeks Since Launch',"DATEDIFF('week',[Launch Week],[Week of Date])",'integer'),('Filter Weeks','[Weeks Since Launch] <= 52','boolean')]: e.add_calculated_field(n,f,datatype=dt,role='dimension' if dt!='integer' else 'measure',field_type='quantitative' if dt=='integer' else 'nominal')
 e.add_worksheet('Current Time'); e.configure_chart('Current Time',mark_type='Line',columns=['WEEK(Date)'],rows=['SUM(daily_orders)'],color='Product',label='SUM(daily_orders)',tooltip=['Product','WEEK(Date)','SUM(daily_orders)'],filters=[{'column':'Date','type':'relative','period':'weeks','range':52}])
 e.add_worksheet('Common Start'); e.configure_chart('Common Start',mark_type='Line',columns=['Weeks Since Launch'],rows=['SUM(daily_orders)'],color='Product',label='SUM(daily_orders)',tooltip=['Product','Week of Date','SUM(daily_orders)'],filters=[{'column':'Filter Weeks','values':[True]}])
 for s in ('Current Time','Common Start'): e.configure_worksheet_style(s,hide_gridlines=True,hide_borders=True,hide_zeroline=True)
 layout={'type':'container','direction':'vertical','children':[{'type':'text','text':'#WOW2026 | WEEK 33 | Can you visualise a common starting point?','font_size':20,'bold':True,'fixed_size':50},{'type':'worksheet','name':'Current Time','show_title':True,'fit':'entire'},{'type':'worksheet','name':'Common Start','show_title':True,'fit':'entire'}]}
 e.add_dashboard('2026_08_19_WW33_Common_Start_Point',width=1200,height=900,layout=layout,worksheet_names=['Current Time','Common Start']); path.parent.mkdir(exist_ok=True); e.save(path,validate=False); return path
if __name__=='__main__': print(build())

