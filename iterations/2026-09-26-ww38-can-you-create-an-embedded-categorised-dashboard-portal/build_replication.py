"""Replicate WW38 selector portal using the extracted link catalogue."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent
HYPER=HERE/'inputs'/'Sheet1 (#WOW2026 Week 38).hyper'
OUT=HERE/'outputs'
DASH='2026_09_23_WW38_Embed_WebPage'
def build(output_path:Path)->Path:
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER))
 e.add_calculated_field('True','TRUE',datatype='boolean',role='dimension',field_type='nominal')
 e.add_calculated_field('False','FALSE',datatype='boolean',role='dimension',field_type='nominal')
 e.add_calculated_field('Marker','MIN(1)',datatype='integer',role='measure',field_type='quantitative')
 e.add_worksheet('Selector')
 e.configure_chart('Selector',mark_type='GanttBar',rows=['Tag','Viz Title'],columns=['Marker'],size='Marker',color='Tag',label='Viz Title',detail='Viz Link',tooltip=['Viz Title','Tag','Viz Link'],color_map={'Maps':'#4e79a7','Bars':'#f28e2b','Table':'#59a14f','Other':'#9c9c9c'})
 e.configure_worksheet_style('Selector',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_row_field_labels=True,hide_col_field_labels=True,disable_tooltip=False,pane_mark_style={'size':'1.0','mark-labels-mode':'all'})
 layout={'type':'container','direction':'floating','style':{'background-color':'#f5f5f5'},'children':[{'type':'text','text':'#WOW2026 Week 38 | Embedded Categorised Dashboard Portal','font_size':'18','font_color':'#111111','absolute':{'x':1000,'y':1000,'w':98000,'h':7000}},{'type':'worksheet','name':'Selector','show_title':False,'fit':'entire','absolute':{'x':1000,'y':10000,'w':30000,'h':76000}},{'type':'text','text':'Select a dashboard title to open its Tableau Public view.\nThe released SDK can reproduce the categorised selector and URL contract; the interactive Web Page zone is recorded as a documented workaround.','font_size':'12','font_color':'#333333','absolute':{'x':34000,'y':12000,'w':62000,'h':30000}},{'type':'text','text':'RECREATED BY: Donna Coles','font_size':'9','absolute':{'x':1000,'y':94000,'w':30000,'h':4000}}]}
 e.add_dashboard(DASH,width=1300,height=850,layout=layout,worksheet_names=['Selector'])
 e.add_dashboard_action(DASH,action_type='url',source_sheet='Selector',source_field='Viz Link',url=':embed=yes&:showVizHome=no',caption='Open selected Tableau view')
 OUT.mkdir(exist_ok=True); e.save(output_path,validate=False); return output_path
if __name__=='__main__': print(build(OUT/'replicated-workbook.twbx'))
