"""Build WW38 performance indicators from the locked Superstore Hyper."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE.parents[2]/'src'))
from cwtwb.twb_editor import TWBEditor  # noqa: E402
HYPER=HERE/'inputs'/'Orders (Sample - Superstore).hyper'; OUT=HERE/'outputs'
def build(path):
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER),table_name='Extract'); e._datasource.set('caption','Orders (Sample - Superstore)')
 e.add_parameter('SELECT CATEGORY',datatype='string',default_value='All',domain_type='list',allowed_values=['All','Furniture','Office Supplies','Technology'])
 e.add_calculated_field('Category Filter',"[Parameters].[SELECT CATEGORY] = 'All' OR [Category] = [Parameters].[SELECT CATEGORY]",datatype='boolean',role='dimension',field_type='nominal')
 e.add_calculated_field('Today','#2018-09-18#',datatype='date')
 e.add_calculated_field('Today Last Year',"DATEADD('year',-1,[Today])",datatype='date')
 e.add_calculated_field('Date Aligned',"MAKEDATE(YEAR([Today]),MONTH([Order Date]),DAY([Order Date]))",datatype='date',role='dimension',field_type='ordinal')
 e.add_calculated_field('Sales MTD This Year',"IF [Order Date]>=DATETRUNC('month',[Today]) AND [Order Date]<=[Today] THEN [Sales] ELSE 0 END",datatype='real')
 e.add_calculated_field('Sales MTD Last Year',"IF [Order Date]>=DATETRUNC('month',[Today Last Year]) AND [Order Date]<=[Today Last Year] THEN [Sales] ELSE 0 END",datatype='real')
 e.add_calculated_field('Sales Full Month Last Year',"IF DATETRUNC('month',[Order Date])=DATETRUNC('month',[Today Last Year]) THEN [Sales] ELSE 0 END",datatype='real')
 e.add_calculated_field('% Change','(SUM([Sales MTD This Year]) - SUM([Sales MTD Last Year])) / SUM([Sales MTD Last Year])',datatype='real',default_format='*▲ 0%;▼ 0%')
 e.add_calculated_field('Colour BAN',"IF [% Change] >= 0 THEN 'positive' ELSE 'negative' END",datatype='string',role='dimension',field_type='nominal')
 e.add_calculated_field('Running Sum Sales MTD This Year','RUNNING_SUM(SUM([Sales MTD This Year]))',datatype='real',table_calc='Rows')
 e.add_calculated_field('Running Sum Sales MTD Last Year','RUNNING_SUM(SUM([Sales MTD Last Year]))',datatype='real',table_calc='Rows')
 e.add_calculated_field('Running Sum Sales Full Month Last Year','RUNNING_SUM(SUM([Sales Full Month Last Year]))',datatype='real',table_calc='Rows')
 e.add_calculated_field('Segment UPPER','UPPER([Segment])',datatype='string',role='dimension',field_type='nominal')
 e.add_worksheet('Chart')
 e.configure_dual_axis('Chart',mark_type_1='Area',mark_type_2='Line',columns=['EXACTDATE(Date Aligned)'],rows=['Running Sum Sales Full Month Last Year','Running Sum Sales MTD This Year'],color_1='Segment UPPER',color_2='Segment UPPER',filters=[{'column':'Category Filter','values':['true']}],synchronized=True,hide_axes=True,show_labels=False)
 e.add_reference_line('Chart',axis_field='Date Aligned',value_field='Today',formula='min',scope='per-table',label_type='custom',label='TODAY',probability=None,pane_index=1)
 e.configure_reference_line_style('Chart','refline0',{'line-pattern-only':'dotted','stroke-color':'#666666','stroke-size':'1'})
 e.add_worksheet('BAN'); e.configure_chart('BAN',mark_type='Text',label='% Change',color='Colour BAN',color_map={'positive':'#38A169','negative':'#E53E3E'})
 e.add_worksheet('BAN:KPI'); e.configure_chart('BAN:KPI',mark_type='Text',label='MIN(Today)')
 e.add_worksheet('SubTitle'); e.configure_chart('SubTitle',mark_type='Text',columns=['MIN(1)'],rows=['MIN(1)'])
 e.configure_worksheet_style('Chart',hide_gridlines=True,hide_zeroline=True,hide_table_dividers=True)
 e.configure_worksheet_style('BAN',pane_datalabel_style={'font-size':'28','font-family':'Tableau Medium'})
 e.add_dashboard('WW38 Performance Indicators',width=1100,height=700,layout={'type':'container','direction':'vertical','children':[{'type':'container','direction':'horizontal','fixed_size':90,'children':[{'type':'text','text':'MONTHLY SALES PERFORMANCE BY SEGMENT\nMonth-to-date sales compared with the same period last year','font_size':'18','weight':1},{'type':'paramctrl','parameter':'SELECT CATEGORY','mode':'compact','fixed_size':220}]},{'type':'container','direction':'horizontal','children':[{'type':'worksheet','name':'BAN','show_title':False,'fixed_size':250},{'type':'worksheet','name':'Chart','show_title':False,'fit':'entire','weight':1}]},{'type':'text','text':'#WORKOUTWEDNESDAY  |  2019  |  WEEK 38','font_size':'8','bold':True,'fixed_size':32}]},worksheet_names=['BAN','Chart'])
 OUT.mkdir(exist_ok=True); e.save(path,validate=False); return path
if __name__=='__main__':
 for n in ('2019-09-20-ww38-performance-indicators-replicated-workbook.twb','replicated-workbook.twbx'): print(build(OUT/n))

