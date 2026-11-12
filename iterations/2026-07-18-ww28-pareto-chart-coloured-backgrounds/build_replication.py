"""Replicate WW28 Pareto chart from extracted Superstore Hyper data."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
HYPER=HERE/'inputs'/'Sample - Superstore.hyper'
OUT=HERE/'outputs'
DASH='2026_07_15_WW28_Pareto'

def build(output_path=None):
    e=TWBEditor("")
    e.set_hyper_connection(str(HYPER))
    e.add_calculated_field('Running Sum % of Customers','RUNNING_SUM(COUNTD([Customer ID])) / TOTAL(COUNTD([Customer ID]))',datatype='real',role='measure',field_type='quantitative',table_calc='Rows',default_format='p0%')
    e.add_calculated_field('Running Sum % of Sales','RUNNING_SUM(SUM([Sales]) / TOTAL(SUM([Sales])))',datatype='real',role='measure',field_type='quantitative',table_calc='Rows',default_format='p0%')
    e.add_calculated_field('Customer Count','COUNTD([Customer ID])',datatype='integer',role='measure',field_type='quantitative')
    e.add_worksheet('Data')
    e.configure_chart('Data',mark_type='Text',rows=['Customer ID'],measure_values=['SUM(Sales)','Customer Count'])
    e.add_worksheet('Viz')
    e.configure_chart('Viz',mark_type='Area',columns=['Running Sum % of Customers'],rows=['Running Sum % of Sales'],detail='Customer ID',axis_fixed_range={'x':{'min':'0','max':'1'},'y':{'min':'0','max':'1'}},tooltip=['Running Sum % of Customers','Running Sum % of Sales'])
    for axis in ('Running Sum % of Customers','Running Sum % of Sales'):
        for value in ('0.2','0.8'):
            try:
                rid=e.add_reference_line('Viz',axis_field=axis,value_field=value,formula='constant',label_type='none',label='')
                e.configure_reference_line_style('Viz',rid,{'line-color':'#ffffff','stroke-size':'2'})
            except Exception:
                pass
    e.configure_worksheet_style('Data',hide_gridlines=True,hide_borders=True)
    e.configure_worksheet_style('Viz',hide_gridlines=True,hide_borders=True,hide_zeroline=True,hide_table_dividers=True)
    layout={'type':'container','direction':'vertical','children':[{'type':'text','text':'#WOW2026 W28 | Can you build a Pareto chart with coloured backgrounds?'},{'type':'worksheet','name':'Viz','show_title':False,'fit':'entire'}]}
    e.add_dashboard(DASH,width=1000,height=800,layout=layout,worksheet_names=['Viz'])
    p=Path(output_path or OUT/'replicated-workbook.twbx'); p.parent.mkdir(parents=True,exist_ok=True); e.save(p,validate=False); return p
if __name__=='__main__': print(build())
