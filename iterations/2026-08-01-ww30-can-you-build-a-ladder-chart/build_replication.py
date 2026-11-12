from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=next((HERE/'inputs').glob('*.hyper')); OUT=HERE/'outputs'/'replicated-workbook.twbx'
def build(path=OUT):
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER)); e.set_date_options(start_of_week='sunday')
 e.add_parameter('pGrandSlamsOnly','boolean','true')
 fs=[('Round Position',"CASE [Round] WHEN 'F' THEN 1 WHEN 'SF' THEN 2 WHEN 'QF' THEN 3 WHEN 'R16' THEN 4 WHEN 'R32' THEN 5 WHEN 'R64' THEN 6 WHEN 'R128' THEN 7 WHEN 'Q3' THEN 8 WHEN 'Q2' THEN 9 WHEN 'Q1' THEN 10 WHEN 'RR' THEN 11 END",'integer'),('Best Round per Date','{FIXED [Date]: MIN([Round Position])}','integer'),('Is Grand Slam',"[Tournament] IN ('Australian Open','Roland Garros','Wimbledon','US Open')",'boolean'),('Filter - Matches','([pGrandSlamsOnly] AND [Is Grand Slam]) OR NOT([pGrandSlamsOnly])','boolean'),('Keep Best Round Only','[Round Position] = [Best Round per Date]','boolean'),('Is Winner',"CONTAINS([Match],'Sinner')",'boolean')]
 for n,f,dt in fs: e.add_calculated_field(n,f,datatype=dt,role='dimension' if dt!='integer' else 'measure',field_type='quantitative' if dt=='integer' else 'nominal')
 e.add_worksheet('Ladder'); e.configure_chart('Ladder',mark_type='Line',columns=['Date'],rows=['MIN(Round Position)'],detail='Tournament',color='Is Winner',label='Tournament',tooltip=['Tournament','Round','Round Position','Is Winner'],filters=[{'column':'Filter - Matches','values':[True]},{'column':'Keep Best Round Only','values':[True]}])
 e.add_worksheet('Match Details'); e.configure_chart('Match Details',mark_type='Text',rows=['Tournament','Round'],measure_values=['MIN(Rank)'],tooltip=['Match','Score','Is Winner'],filters=[{'column':'Filter - Matches','values':[True]}])
 for s in ('Ladder','Match Details'): e.configure_worksheet_style(s,hide_gridlines=True,hide_borders=True,hide_zeroline=True)
 layout={'type':'container','direction':'vertical','children':[{'type':'text','text':'#WOW2026 | WEEK 30 | Can you build a ladder chart?','font_size':20,'bold':True,'fixed_size':50},{'type':'worksheet','name':'Ladder','show_title':True,'fit':'entire'},{'type':'worksheet','name':'Match Details','show_title':True,'fit':'entire'}]}
 e.add_dashboard('2026_07_29_WW30_Tennis_Career_Ladder_Chart',width=1300,height=900,layout=layout,worksheet_names=['Ladder','Match Details']); path.parent.mkdir(exist_ok=True); e.save(path,validate=False); return path
if __name__=='__main__': print(build())

