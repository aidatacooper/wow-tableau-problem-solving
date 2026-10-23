import sys, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import tableauserverclient as TSC
from scripts.cloud_credentials import require_credentials
p=Path(__file__).resolve().parent
request=json.loads((p/'evidence/cloud-request.json').read_text(encoding='utf-8'))
report=json.loads((p/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert digest(p/'outputs/replicated-workbook.twbx')==report['source_hashes']['replica']
c=require_credentials()
server=TSC.Server(c['TABLEAU_SERVER_URL'],use_server_version=True)
auth=TSC.PersonalAccessTokenAuth(c['TABLEAU_TOKEN_NAME'],c['TABLEAU_TOKEN_SECRET'],site_id=c['TABLEAU_SITE_ID'])
exports=[]
role='author' if '--author' in sys.argv else 'replica'
with server.auth.sign_in(auth):
    for state in [{'name':'default'},*request.get('states',[])]:
        for v in report['workbooks'][role]['views']:
            if v['name']==request[role+'_view']: continue
            item=server.views.get_by_id(v['id'])
            opts=TSC.CSVRequestOptions(maxage=1)
            for k,val in state.get('parameters',{}).items(): opts.parameter(k,str(val))
            for k,val in state.get('filters',{}).items(): opts.vf(k,str(val))
            server.views.populate_csv(item,opts)
            slug=''.join(ch.lower() if ch.isalnum() else '-' for ch in v['name'])
            target=p/'outputs'/f"cloud-{role}-{slug}-{state['name']}.csv"
            target.write_bytes(b''.join(item.csv))
            exports.append({'state':state['name'],'view':v['name'],'path':target.relative_to(p).as_posix(),'sha256':digest(target),'parameters':state.get('parameters',{}),'filters':state.get('filters',{})})
            print(v['name'],state['name'],target.stat().st_size,flush=True)
            if '--images' in sys.argv:
                server.views.populate_image(item,TSC.ImageRequestOptions(maxage=1))
                target.with_suffix('.png').write_bytes(item.image)
(p/f'evidence/{role}-data-exports.json').write_text(json.dumps({'artifact_sha256':report['source_hashes'][role],'exports':exports},indent=2),encoding='utf-8')
