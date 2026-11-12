from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; HYPER=next((HERE/'inputs').glob('*.hyper')); OUT=HERE/'outputs'/'replicated-workbook.twbx'
TOP_STATES=['California','New York','Texas','Washington','Pennsylvania']; BOT_STATES=['North Dakota','Newfoundland and Labrador','Nova Scotia','New Brunswick','Saskatchewan']; TOP_CITIES=['New York City','Los Angeles','Seattle','San Francisco','Philadelphia']
def q(xs): return ','.join("'%s'"%x.replace("'","''") for x in xs)
def build(path=OUT):
 e=TWBEditor(''); e.set_hyper_connection(str(HYPER))
 fields=[('Top 5 States',f'[State/Province] IN ({q(TOP_STATES)})','boolean'),('Top 1 State',"[State/Province] = 'California'",'boolean'),('Bottom 5 States',f'[State/Province] IN ({q(BOT_STATES)})','boolean'),('Bottom 1 State',"[State/Province] = 'Saskatchewan'",'boolean'),('Top 5 Cities',f'[City] IN ({q(TOP_CITIES)})','boolean'),('Bottom 5 Cities',"[City] IN ('Abilene','Elyria','Jupiter','Pensacola','Ormond Beach')",'boolean'),('Colour - State',"IF [Top 1 State] THEN 'dark blue' ELSEIF [Top 5 States] THEN 'blue' ELSEIF [Bottom 1 State] THEN 'dark orange' ELSEIF [Bottom 5 States] THEN 'orange' ELSE 'grey' END",'string'),('Colour - City',"IF [Top 5 Cities] THEN 'dark' ELSEIF [Bottom 5 Cities] THEN 'mid' ELSE 'light' END",'string'),('Size',"IF [Top 5 Cities] THEN 'big' ELSEIF [Bottom 5 Cities] THEN 'mid' ELSE 'small' END",'string'),('Shape',"IF [Top 5 Cities] THEN 'star' ELSEIF [Bottom 5 Cities] THEN 'cross' ELSE 'circle' END",'string')]
 for n,f,dt in fields: e.add_calculated_field(n,f,datatype=dt,role='dimension',field_type='nominal')
 e.add_worksheet('States'); e.configure_chart('States',mark_type='Bar',rows=['State/Province'],columns=['SUM(Sales)'],color='Colour - State',label='SUM(Sales)',tooltip=['State/Province','SUM(Sales)','Colour - State'])
 e.add_worksheet('Cities'); e.configure_chart('Cities',mark_type='Circle',rows=['City'],columns=['SUM(Sales)'],color='Colour - City',label='SUM(Sales)',tooltip=['City','State/Province','SUM(Sales)'])
 e.add_worksheet('State City Detail'); e.configure_chart('State City Detail',mark_type='Text',rows=['State/Province','City'],measure_values=['SUM(Sales)'],filters=[])
 for s in ('States','Cities','State City Detail'): e.configure_worksheet_style(s,hide_gridlines=True,hide_borders=True,hide_zeroline=True)
 layout={'type':'container','direction':'vertical','children':[{'type':'text','text':'#WOW2026 | WEEK 32 | Can you use Sets to highlight top and bottom performing States & Cities?','font_size':18,'bold':True,'fixed_size':50},{'type':'container','direction':'horizontal','children':[{'type':'worksheet','name':'States','show_title':True,'fit':'entire'},{'type':'worksheet','name':'Cities','show_title':True,'fit':'entire'}]},{'type':'worksheet','name':'State City Detail','show_title':True,'fit':'entire'}]}
 e.add_dashboard('2026_08_12_WW32_Sets',width=1300,height=900,layout=layout,worksheet_names=['States','Cities','State City Detail']); path.parent.mkdir(exist_ok=True); e.save(path,validate=False); return path
if __name__=='__main__': print(build())
