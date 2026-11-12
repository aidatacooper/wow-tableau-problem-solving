from pathlib import Path
from cwtwb import TWBEditor
OUT=Path(__file__).resolve().parent/'outputs'/'replicated-workbook.twbx'
# acceptance: case-functional-contract
# acceptance: desktop-load
def verify():
 assert OUT.exists(); e=TWBEditor.open_existing(OUT); assert 'Map' in e.list_worksheets(); assert any(d.get('name')=='2026_09_09_WW36_John_Snow_Cholera_Map' for d in e.list_dashboards())
if __name__=='__main__': verify(); print('PASS')
