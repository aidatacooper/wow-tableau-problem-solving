from pathlib import Path
from cwtwb import TWBEditor
OUT=Path(__file__).resolve().parent/'outputs'/'replicated-workbook.twbx'
# acceptance: case-functional-contract
# acceptance: desktop-load
def verify():
 assert OUT.exists(); e=TWBEditor.open_existing(OUT); assert 'Viz' in e.list_worksheets(); assert any(d.get('name')=='2026_09_16_WW37_Number_Format' for d in e.list_dashboards())
if __name__=='__main__': verify(); print('PASS')
