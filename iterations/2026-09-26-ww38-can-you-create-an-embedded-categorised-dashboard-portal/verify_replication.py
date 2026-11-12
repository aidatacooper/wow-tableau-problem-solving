from pathlib import Path
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
# acceptance: case-functional-contract
# acceptance: desktop-load
def verify():
 assert OUT.exists(), OUT
 e=TWBEditor.open_existing(OUT); assert 'Selector' in e.list_worksheets(); assert any(d.get('name')=='2026_09_23_WW38_Embed_WebPage' for d in e.list_dashboards())
if __name__=='__main__': verify(); print('PASS')
