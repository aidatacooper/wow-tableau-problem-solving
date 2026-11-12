"""Replicate WW25 selected-sales difference with parameter actions."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=HERE/'inputs'/'Orders (Sample - Superstore).hyper'; OUT=HERE/'outputs'; DASH='2026_06_24_WW25_Sales_Difference'
def build(output_path=None):
 e=TWBEditor(""); e.set_hyper_connection(str(HYPER))
 e.add_parameter('pSelectedSubCat','string','Storage',domain_type='any')
 e.add_parameter('pSelectedSales','real','224645',domain_type='any',default_format='c$#,##0')
 calc=[
 ('Difference','IIF([pSelectedSales]>0,SUM([Sales])-[pSelectedSales],SUM([Sales]))','real','measure','quantitative'),
 ('LABEL: Sub Cat','IF MIN([Sub-Category])<>MAX([Sub-Category]) THEN "No Comparison" ELSE ATTR([Sub-Category]) END','string','dimension','nominal'),
 ('Is Selected SubCat','ATTR([Sub-Category])=[pSelectedSubCat] OR ([pSelectedSubCat]="" AND [LABEL: Sub Cat]="No Comparison")','boolean','dimension','nominal'),
 ('Sub Cat for Param','IIF([LABEL: Sub Cat]="No Comparison","",ATTR([Sub-Category]))','string','dimension','nominal'),
 ('Sales for Param','IIF([LABEL: Sub Cat]="No Comparison",0,SUM([Sales]))','real','measure','quantitative'),
 ('Dummy HL','"HL"','string','dimension','nominal'),
  ('Selector Axis','-1.0','real','measure','quantitative'),
 ]
 for n,f,dt,r,ft in calc:e.add_calculated_field(n,f,datatype=dt,role=r,field_type=ft)
 e.set_field_format('Difference','c$#,##0;-$#,##0;')
 e.add_worksheet('Bar'); e.configure_chart('Bar',mark_type='Bar',rows=['Sub-Category'],columns=['Difference'],color='Is Selected SubCat',label='Difference',tooltip=['SUM(Sales)','Difference','Sub-Category'],color_map={'true':'#4472C4','false':'#D9D9D9'})
 e.add_worksheet('Selector'); e.configure_chart('Selector',mark_type='Bar',rows=['Sub-Category'],columns=['Selector Axis'],color='Is Selected SubCat',label='LABEL: Sub Cat',detail='Sub Cat for Param',tooltip=['Sales for Param','Sub Cat for Param'],color_map={'true':'#4472C4','false':'#FFFFFF'})
 e.configure_worksheet_style('Bar',hide_gridlines=True,hide_borders=True,hide_zeroline=True,hide_table_dividers=True)
 e.configure_worksheet_style('Selector',hide_gridlines=True,hide_borders=True,hide_zeroline=True,hide_table_dividers=True,hide_axes=True)
 layout={'type':'container','direction':'horizontal','children':[{'type':'worksheet','name':'Selector','show_title':False,'fit':'entire'},{'type':'worksheet','name':'Bar','show_title':False,'fit':'entire'}]}
 e.add_dashboard(DASH,width=1200,height=800,layout=layout,worksheet_names=['Selector','Bar'])
 for source in ('Selector','Bar'):
  e.add_dashboard_action(DASH,'parameter',source_field='Sub Cat for Param',target_parameter='pSelectedSubCat',source_sheet=source,caption='Set Sub Category',clear_behavior='set-value',clear_value='s:LROOT:')
  e.add_dashboard_action(DASH,'parameter',source_field='Sales for Param',target_parameter='pSelectedSales',source_sheet=source,caption='Set Sales Value',aggregation='sum',clear_behavior='set-value',clear_value='0')
 out=Path(output_path or OUT/'replicated-workbook.twbx'); out.parent.mkdir(parents=True,exist_ok=True); e.save(out,validate=False); return out
if __name__=='__main__': print(build())
