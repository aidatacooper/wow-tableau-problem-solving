# acceptance: difference-formula
# acceptance: parameter-actions
# acceptance: selector-and-bar
from pathlib import Path
import zipfile
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
def verify():
 if not OUT.exists(): raise AssertionError('missing output')
 e=TWBEditor.open_existing(OUT); s=set(e.list_worksheets())
 for n in ('Bar','Selector'):
  if n not in s: raise AssertionError('missing '+n)
 t=zipfile.ZipFile(OUT).read('replicated-workbook.twb').decode('utf-8')
 for f in ('IIF([Parameters].[Parameter 2]&gt;0,SUM([Sales])-[Parameters].[Parameter 2],SUM([Sales]))','Parameters].[Parameter 1'):
  if f not in t: raise AssertionError('missing '+f)
 if t.count('parameter')<2: raise AssertionError('parameter action missing')
 print('acceptance: selected-sales-difference PASS')
if __name__=='__main__': verify()

