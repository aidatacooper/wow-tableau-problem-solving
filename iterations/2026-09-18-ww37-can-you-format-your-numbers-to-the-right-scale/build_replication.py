"""Replicate WW37 dynamic hierarchy and custom scale number format."""
from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=HERE/'inputs'/'Orders (Sample - Superstore).hyper'; OUT=HERE/'outputs'; DASH='2026_09_16_WW37_Number_Format'
def build(output_path:Path)->Path:
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER))
 e.add_parameter('pSegment','string','',domain_type='any',alias='Segment')
 e.add_calculated_field('Segment Display','IIF([pSegment]=[Segment], \'- \' + [Segment], \'+ \' + [Segment])',datatype='string',role='dimension',field_type='nominal',validate_formula=False)
 e.add_calculated_field('Display','IF [Segment] = [pSegment] THEN [Sub-Category] ELSE \'\' END',datatype='string',role='dimension',field_type='nominal',validate_formula=False)
 e.add_calculated_field('False','FALSE',datatype='boolean',role='dimension',field_type='nominal')
 e.add_calculated_field('Segment for Param','IIF([pSegment]=[Segment],\'\',[Segment])',datatype='string',role='dimension',field_type='nominal',validate_formula=False)
 e.set_field_format('Sales','$0.0[scale]')
 e.add_worksheet('Viz')
 e.configure_chart('Viz',mark_type='Bar',rows=['Segment Display','Display'],columns=['SUM(Sales)'],color='Segment',label='SUM(Sales)',detail='False',tooltip=['Segment Display','Display','SUM(Sales)'],sort_descending='SUM(Sales)',color_map={'Consumer':'#4e79a7','Corporate':'#f28e2b','Home Office':'#59a14f'})
 e.configure_worksheet_style('Viz',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_col_field_labels=True,disable_tooltip=False,label_formats=[{'field':'SUM(Sales)','text-format':'$0.0[scale]'}])
 layout={'type':'container','direction':'floating','style':{'background-color':'#ffffff'},'children':[{'type':'text','text':'#WOW2026 Week 37 | Can you format your numbers to the right scale?','font_size':'18','absolute':{'x':1000,'y':1000,'w':98000,'h':7000}},{'type':'worksheet','name':'Viz','show_title':False,'fit':'entire','absolute':{'x':1000,'y':10000,'w':98000,'h':76000}},{'type':'text','text':'Select a Segment to expand/collapse its Sub-Categories. Sales uses the custom $0.0[scale] format.','font_size':'11','absolute':{'x':1000,'y':90000,'w':98000,'h':5000}}]}
 e.add_dashboard(DASH,width=1300,height=850,layout=layout,worksheet_names=['Viz'])
 e.add_dashboard_action(DASH,action_type='parameter',source_sheet='Viz',target_sheet='Viz',source_field='Segment for Param',target_parameter='pSegment',caption='Set Segment')
 e.add_dashboard_action(DASH,action_type='highlight',source_sheet='Viz',target_sheet='Viz',fields=['False'],caption='Keep selection neutral')
 OUT.mkdir(exist_ok=True); e.save(output_path,validate=False); return output_path
if __name__=='__main__': print(build(OUT/'replicated-workbook.twbx'))
