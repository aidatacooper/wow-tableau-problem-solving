acceptance: state-top-bottom-sets
acceptance: city-top-bottom-sets
acceptance: hyper-data-present

from pathlib import Path
import zipfile
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'/'replicated-workbook.twbx'
def verify():
 assert OUT.exists(); e=TWBEditor.open_existing(OUT); ss=set(e.list_worksheets()); assert {'States','Cities','State City Detail'}<=ss
 src=zipfile.ZipFile(OUT).read('replicated-workbook.twb').decode('utf-8')
 for x in ('Top 5 States','Bottom 5 States','Top 5 Cities','Bottom 5 Cities','Colour - State','Colour - City'): assert x in src
 from tableauhyperapi import Connection,HyperProcess,Telemetry
 h=HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU); c=Connection(h.endpoint,str(next((HERE/'inputs').glob('*.hyper')))); n=c.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"'); assert n>0; print('rows=',n); c.close(); h.close()
if __name__=='__main__': verify(); print('PASS')

