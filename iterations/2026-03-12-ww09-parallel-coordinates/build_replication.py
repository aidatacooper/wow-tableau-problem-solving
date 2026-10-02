"""WW09 builds normalized parallel coordinates from the locked match Hyper."""
from pathlib import Path
from cwtwb import TWBEditor
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent
DASHBOARD='2026_03_04_WW09_Parallel_Coordinates'
METRICS=[('Total Distance (km)','Distance - Total (KM)'),('Distance / Min (m)','Distance per Min'),('HSR Distance (m)','HSR - Total (M)'),('HI Distance (m)','HI Distance - Total (M)'),('Max Speed (m/s)','Speed - Max (m/s)')]
def build():
    editor = TWBEditor("")
    hyper=next((HERE/'inputs').glob('*.hyper'))
    editor.set_hyper_connection(str(hyper))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(hyper)) as c:
        opponents=[r[0] for r in c.execute_list_query('SELECT DISTINCT "Opposition" FROM "Extract"."Extract" ORDER BY "Opposition"')]
    editor.add_parameter('Opposition Parameter',datatype='string',default_value='Chelsea Ladies U14',domain_type='list',allowed_values=opponents)
    editor.add_calculated_field('Highlight Match','[Opposition] = [Opposition Parameter]',datatype='boolean',role='dimension',field_type='nominal')
    editor.add_calculated_field('Label: Opposition','IF [Highlight Match] THEN [Opposition] END',datatype='string',role='dimension',field_type='nominal')
    editor.add_calculated_field('Match Colour',"IF [Highlight Match] THEN IF [H/A]='H' THEN '0 Selected Home' ELSE '1 Selected Away' END ELSE IF [H/A]='H' THEN '2 Other Home' ELSE '3 Other Away' END END",datatype='string',role='dimension',field_type='nominal')
    editor.add_calculated_field('Line Width','IF [Highlight Match] THEN 3 ELSE 1 END',datatype='integer',role='dimension',field_type='ordinal')
    for name,source in METRICS:
        agg=f'SUM([{source}])'
        editor.add_calculated_field(name,f'({agg} - WINDOW_MIN({agg})) / (WINDOW_MAX({agg}) - WINDOW_MIN({agg}))',table_calc='Rows',default_format='n#,##0.0000;-#,##0.0000')
    editor.add_worksheet('Viz')
    measures=[name for name,_ in METRICS]
    editor.configure_layered_chart('Viz',columns=['Measure Names'],rows=['Multiple Values','Multiple Values'],panes=[
        {'axis':'Multiple Values','mark_type':'Line','detail':'Game ID','color':'Match Colour','size':'Line Width','label':'ATTR(Label: Opposition)',
         'tooltip':['Opposition','ATTR(H/A)','ATTR(Category)','ATTR(Cup/League)','ATTR(Round)','ATTR(Date)']+['SUM('+source+')' for _,source in METRICS],
         'measure_values':measures,'color_map':{'0 Selected Home':'#0d74c9','1 Selected Away':'#28aaa7','2 Other Home':'#b7e0f3','3 Other Away':'#bae5d8'},
         'mark_style':{'mark-labels-show':'true','mark-labels-mode':'line-ends','mark-labels-cull':'false','mark-labels-match-mark-color':'true','mark-labels-line-first':'false','mark-markers-mode':'all'}},
        {'axis':'Multiple Values','mark_type':'Line','path':'Game ID','measure_values':measures,
         'mark_style':{'mark-color':'#555555','size':'0.054','mark-labels-show':'false'}},
    ],synchronized=True,hide_axes=True,table_calc_overrides={name:[{'ordering_type':'Field','order':['Game ID','Match Colour','Line Width']}] for name in measures})
    editor.configure_worksheet_style('Viz',background_color='#faf5f4',hide_axes=True,hide_gridlines=True,hide_zeroline=True,hide_borders=True,hide_col_field_labels=True,
        hide_row_label='Measure Names', axis_style={'render-fold-reversed':'true'}, size_style={'field':'Line Width','min':1,'max':3,'min_size':0.12,'max_size':0.5})
    background='#faf5f4'
    children=[
        {'type':'empty','style':{'background-color':background},'absolute':{'x':0,'y':0,'w':100000,'h':100000}},
        {'type':'text','text':"Comparing Mia's Match Performance Statistics\nReading FC U15s | Season 2024-25\nHome matches | Away matches\nEach line represents a cup or league fixture during the season. Select a line to highlight; hover for details.",
         'runs':[{'text':"Comparing Mia's Match Performance Statistics\n",'font_size':'17','font_alignment':'0','bold':'true'}, {'text':'Reading FC U15s | Season 2024-25\n','font_size':'13','font_alignment':'0'}, {'text':'Home matches','font_size':'11','font_alignment':'0','font_color':'#0d74c9'},{'text':' | ','font_size':'11','font_alignment':'0'},{'text':'Away matches\n','font_size':'11','font_alignment':'0','font_color':'#28aaa7'},{'text':'Each line represents a cup or league fixture during the season. Select a line to highlight; hover for details.','font_size':'10','italic':'true','font_alignment':'0'}],
         'style':{'background-color':background},'absolute':{'x':1600,'y':2200,'w':97000,'h':13000}},
        {'type':'worksheet','name':'Viz','show_title':False,'fit':'entire','style':{'background-color':background,'border-width':0},'absolute':{'x':1700,'y':16400,'w':96600,'h':72300}},
        {'type':'text','text':'CHALLENGE BY: Donna Coles','runs':[{'text':'CHALLENGE BY: Donna Coles','font_size':'9'}],'absolute':{'x':1500,'y':92100,'w':32000,'h':3000}},
        {'type':'text','text':'#WOW2026 | WEEK 9','runs':[{'text':'#WOW2026 | WEEK 9','font_size':'9'}],'absolute':{'x':40000,'y':92100,'w':25000,'h':3000}},
        {'type':'text','text':'DATA: Manually Curated','runs':[{'text':'DATA: Manually Curated','font_size':'9'}],'absolute':{'x':76000,'y':92100,'w':23000,'h':3000}},
        {'type':'text','text':'https://www.workout-wednesday.com/2026w09tab/','runs':[{'text':'https://www.workout-wednesday.com/2026w09tab/','font_size':'9','font_color':'#177fa1'}],'absolute':{'x':33000,'y':97000,'w':45000,'h':2500}},
    ]
    # Fixed explanatory text is an accepted presentation alternative to the author toggle.
    # Metric labels are presentation-only: data remains native Measure Values table calculations.
    for index,(name,_) in enumerate(METRICS):
        for y in [15000,89000]:
            children.append({'type':'text','text':name,'runs':[{'text':name,'font_size':'11','font_alignment':'1'}], 'style':{'background-color':background},'absolute':{'x':2000+index*19600,'y':y,'w':17600,'h':2800}})
    editor.add_dashboard(DASHBOARD,width=1000,height=800,worksheet_names=['Viz'],layout={'type':'container','direction':'floating','children':children})
    editor.add_dashboard_action(DASHBOARD,action_type='parameter',source_sheet='Viz',source_field='Opposition',target_parameter='Opposition Parameter',aggregation='attr',clear_behavior='set-value',clear_value='s:LROOT:',caption='Set Opposition')
    output=HERE/'outputs/replicated-workbook.twbx';output.parent.mkdir(exist_ok=True);editor.save(output,validate=False);return output
if __name__=='__main__':print(build())
