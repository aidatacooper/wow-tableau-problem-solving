"""Run a selected installed/source SDK and preserve append-only evidence."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
channel=sys.argv[1]
label=sys.argv[2]
if (HERE / "evidence" / f"{label}.json").exists():
    raise SystemExit("Evidence label already exists; choose a new append-only run label")
import cwtwb
origin=Path(cwtwb.__file__).resolve()
package=origin.parent
files={str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
source={'channel':channel,'version':cwtwb.__version__,'import_path':str(origin),'package_tree_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}
if channel=='source':
    repo=package.parents[1]
    source['git_sha']=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    source['git_status']=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True)
    source['dirty']=bool(source['git_status'])
    (HERE/'evidence'/f'{label}-source.diff').write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--binary']))
else:
    source.update(git_sha=None,dirty=False)
    import importlib.metadata as md
    distribution=md.distribution('cwtwb')
    source['distribution_record_sha256']=hashlib.sha256(distribution.read_text('RECORD').encode()).hexdigest()
(HERE/'evidence'/f'{label}-package-manifest.json').write_text(json.dumps(files,indent=2),encoding='utf8')
result={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'commands':[]}
for script in [HERE/'build_replication.py',HERE/'verify_replication.py']:
    command=[sys.executable,str(script)]
    run=subprocess.run(command,cwd=HERE,capture_output=True,text=True,encoding='utf8',errors='replace')
    result['commands'].append({'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    if run.returncode:break
output=HERE/'outputs/replicated-workbook.twbx'
if output.exists():result['workbook_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
result['result']='pass' if all(c['returncode']==0 for c in result['commands']) else 'blocked'
result['scope']='Build and static/numerical verifier only; Desktop and tooltip runtime not run.'
(HERE/'evidence'/f'{label}.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'source':source,'result':result['result'],'commands':result['commands'][-1]},indent=2))
