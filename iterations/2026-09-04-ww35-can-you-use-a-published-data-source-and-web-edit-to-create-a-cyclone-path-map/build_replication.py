from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'
def build(output_path:Path)->Path:
 e=TWBEditor('')
 layout={'type':'container','direction':'floating','style':{'background-color':'#202020'},'children':[{'type':'text','text':'#WOW2026 Week 35 | Cyclone Path Map\nBlocked: author workbook uses a published data source with no packaged extract. Provide an independent source to complete the map.','font_size':'16','font_color':'#ffffff','absolute':{'x':3000,'y':3000,'w':94000,'h':18000}}]}
 e.add_dashboard('2026_09_02_WW35_Cyclone_Path_Map_Web_Edit',width=1366,height=768,layout=layout,worksheet_names=[])
 OUT.mkdir(exist_ok=True); e.save(output_path,validate=False); return output_path
if __name__=='__main__': print(build(OUT/'replicated-workbook.twbx'))
