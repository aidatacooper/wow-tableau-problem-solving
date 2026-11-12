# acceptance: store-map
# acceptance: selected-store-kpi
# acceptance: drive-time-blocker
from pathlib import Path
import zipfile
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
def verify():
 if not OUT.exists(): raise AssertionError('missing output')
 e=TWBEditor.open_existing(OUT); s=set(e.list_worksheets())
 for n in ('Map','KPI'):
  if n not in s: raise AssertionError('missing '+n)
 t=zipfile.ZipFile(OUT).read('replicated-workbook.twb').decode('utf-8')
 for f in ('MAKEPOINT([Latitude],[Longitude])','MAKEPOINT(38.8977, -77.0063)','SUM(IIF([Selected Stores],1,0))'):
  if f not in t: raise AssertionError('missing '+f)
 if 'set' not in t.lower(): raise AssertionError('set action missing')
 print('acceptance: map-and-selected-store-kpi PASS')
if __name__=='__main__': verify()

