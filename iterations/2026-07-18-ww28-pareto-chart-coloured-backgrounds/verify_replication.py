# acceptance: pareto-running-percentages
# acceptance: pareto-guides
# acceptance: pareto-workbook-structure
from pathlib import Path
import zipfile
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
def verify():
 if not OUT.exists(): raise AssertionError('missing output')
 e=TWBEditor.open_existing(OUT); sheets=set(e.list_worksheets())
 for s in ('Data','Viz'):
  if s not in sheets: raise AssertionError(f'missing worksheet {s}')
 text=zipfile.ZipFile(OUT).read('replicated-workbook.twb').decode('utf-8')
 for f in ('RUNNING_SUM(COUNTD([Customer ID])) / TOTAL(COUNTD([Customer ID]))','RUNNING_SUM(SUM([Sales]) / TOTAL(SUM([Sales])))'):
  if f not in text: raise AssertionError('missing formula '+f)
 print('acceptance: pareto-table-calcs PASS')
if __name__=='__main__': verify()

