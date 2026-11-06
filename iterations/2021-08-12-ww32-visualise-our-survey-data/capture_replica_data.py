"""Read CSV exports from the already published replica; no workbook uploads."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import tableauserverclient as TSC
from scripts.cloud_credentials import require_credentials

HERE = Path(__file__).resolve().parent

def capture():
    report = json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert report['source_hashes']['replica'] == digest(HERE/'outputs/replicated-workbook.twbx')
    c = require_credentials()
    server = TSC.Server(c['TABLEAU_SERVER_URL'], use_server_version=True)
    auth = TSC.PersonalAccessTokenAuth(c['TABLEAU_TOKEN_NAME'],c['TABLEAU_TOKEN_SECRET'],site_id=c['TABLEAU_SITE_ID'])
    exports = []
    with server.auth.sign_in(auth):
        for state in report['states']:
            for view in report['workbooks']['replica']['views']:
                if view['name'] not in ('Donuts','Bar-Participate','Bar-Diverging','Bar-Vertical','Heatmap'):
                    continue
                options = TSC.CSVRequestOptions(maxage=1)
                for key,value in state['filters'].items():
                    options.vf(key,value)
                item = server.views.get_by_id(view['id'])
                server.views.populate_csv(item,options)
                target = HERE/'outputs'/f"cloud-replica-{view['name'].lower()}-{state['name']}.csv"
                target.write_bytes(b''.join(item.csv))
                exports.append({'state':state['name'],'view':view['name'],'path':target.relative_to(HERE).as_posix(),'sha256':digest(target),'filters':state['filters']})
                print(state['name'], view['name'], target.stat().st_size,flush=True)
    (HERE/'evidence/replica-data-exports.json').write_text(json.dumps({'artifact_sha256':report['source_hashes']['replica'],'exports':exports},indent=2),encoding='utf-8')

if __name__ == '__main__':
    capture()
