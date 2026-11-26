"""Record actual SDK identity and build/verifier outcomes; does not open Desktop."""
import datetime, hashlib, importlib.metadata, json, os, subprocess, sys
from pathlib import Path
import cwtwb
HERE=Path(__file__).resolve().parent
channel=sys.argv[1]
def git(*args):
    return subprocess.check_output(['git','-C','C:/Users/imgwho/Desktop/project/cwtwb',*args],text=True,encoding='utf-8').strip()
source=Path(cwtwb.__file__).resolve()
r={'date':datetime.datetime.now().isoformat(),'channel':channel,'version':cwtwb.__version__,'import_path':str(source),'CWTWB_SRC':os.getenv('CWTWB_SRC'),'PYTHONPATH':os.getenv('PYTHONPATH'),'git_sha':None,'dirty':None,'commands':[]}
if not channel.startswith('pypi-stable'):
    r.update(git_sha=git('rev-parse','HEAD'),dirty=bool(git('status','--porcelain')),git_status=git('status','--short'),source_tree_sha256=hashlib.sha256(b''.join(str(p.relative_to(source.parent)).encode()+p.read_bytes() for p in sorted(source.parent.rglob('*.py')))).hexdigest())
    (HERE/'evidence'/f'{channel}-source.diff').write_text(git('diff','--','src'),encoding='utf-8')
else:
    r.update(package_sha256='dd8fb1c4a7a1828ba6c102afa5bc13f90dc7c959c58cde608d2de0a830a05225',package_url='https://pypi.org/pypi/cwtwb/0.28.0/json',git_sha='not applicable: wheel install')
for script in ['build_replication.py','verify_replication.py']:
    command=[sys.executable,str(HERE/script)]
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    r['commands'].append({'command':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:break
r['result']='pass' if all(x['returncode']==0 for x in r['commands']) else 'blocked'
if r['result']=='pass':
    r['artifact_sha256']=hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
    (HERE/'evidence'/f'{channel}-verification.json').write_bytes((HERE/'evidence/verification.json').read_bytes())
r['acceptance']={'static_and_numerical':r['result'],'desktop':'pending parent','rendered_business_and_visual':'pending parent'}
(HERE/'evidence'/f'{channel}.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r,indent=2))
