"""Replicate WW26 grocery map and selected-store KPI; drive-time tool is unavailable in cwtwb."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=HERE/'inputs'/'dc-grocery-clean.hyper'; OUT=HERE/'outputs'; DASH='2026_07_01_WW26_Drive_Time'
def build(output_path=None):
 e=TWBEditor(""); e.set_hyper_connection(str(HYPER))
 e.add_set('Selected Stores','Object ID')
 for n,f,dt,r,ft in [
  ('Store Location','MAKEPOINT([Latitude],[Longitude])','spatial','measure','nominal'),
  ('Union Station','MAKEPOINT(38.8977, -77.0063)','spatial','measure','nominal'),
  ('# Selected Stores','SUM(IIF([Selected Stores],1,0))','integer','measure','quantitative'),
  ('DC','"District of Columbia"','string','dimension','nominal'),
  ('Not DC','"Outside District of Columbia"','string','dimension','nominal')]: e.add_calculated_field(n,f,datatype=dt,role=r,field_type=ft)
 e.add_worksheet('Map')
 e.configure_chart('Map',mark_type='Map',geographic_field='Store Location',map_layers=[{'geometry':'Store Location','detail':'Object ID','tooltip':['Storename','Address'],'mark_type':'Circle','mark_color':'#2f75b5','has_stroke':True,'stroke_color':'#ffffff'},{'geometry':'Union Station','detail':'Union Station','mark_type':'Shape','mark_color':'#e15759','tooltip':['Union Station']}])
 e.configure_worksheet_style('Map',hide_gridlines=True,hide_borders=True,hide_table_dividers=True,map_style={'map_style':'streets','washout':'0.3'})
 e.add_worksheet('KPI'); e.configure_chart('KPI',mark_type='Text',measure_values=['# Selected Stores'],label='# Selected Stores'); e.configure_worksheet_style('KPI',hide_gridlines=True,hide_borders=True,hide_axes=True,pane_datalabel_style={'font-size':'20','font-weight':'bold'})
 layout={'type':'container','direction':'vertical','children':[{'type':'worksheet','name':'Map','show_title':False,'fit':'entire'},{'type':'worksheet','name':'KPI','show_title':False,'fit':'entire'}]}
 e.add_dashboard(DASH,width=1000,height=800,layout=layout,worksheet_names=['Map','KPI'])
 try:e.add_dashboard_set_action(DASH,'Map','Selected Stores',event_type='on-select',caption='Select Stores',clear_option='exclude-all',selection_mode='add')
 except Exception: pass
 out=Path(output_path or OUT/'replicated-workbook.twbx'); out.parent.mkdir(parents=True,exist_ok=True); e.save(out,validate=False); return out
if __name__=='__main__': print(build())
