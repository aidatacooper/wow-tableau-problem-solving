from pathlib import Path
from cwtwb import TWBEditor
OUT=Path(__file__).resolve().parent/'outputs'/'replicated-workbook.twbx'
# acceptance: author-source-blocker-recorded
# acceptance: desktop-placeholder-loads
def verify():
 assert OUT.exists(); e=TWBEditor.open_existing(OUT); assert any(d.get('name')=='2026_09_02_WW35_Cyclone_Path_Map_Web_Edit' for d in e.list_dashboards())
if __name__=='__main__': verify(); print('PASS')
