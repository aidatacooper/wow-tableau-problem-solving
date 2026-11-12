# acceptance: grand-slam-filter
# acceptance: best-round-per-tournament
# acceptance: winner-flag

from pathlib import Path
import zipfile
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
def verify():
 assert OUT.exists(); e=TWBEditor.open_existing(OUT); ss=set(e.list_worksheets()); assert {'Ladder','Match Details'}<=ss
 src=zipfile.ZipFile(OUT).read('replicated-workbook.twb').decode('utf-8')
 for x in ('Round Position','Best Round per Date','Is Grand Slam','Filter - Matches','Keep Best Round Only','Is Winner','pGrandSlamsOnly'): assert x in src
 from tableauhyperapi import Connection,HyperProcess,Telemetry
 h=HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU); c=Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))); n=c.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"'); assert n>0; print('rows=',n); c.close(); h.close()
if __name__=='__main__': verify(); print('PASS')


