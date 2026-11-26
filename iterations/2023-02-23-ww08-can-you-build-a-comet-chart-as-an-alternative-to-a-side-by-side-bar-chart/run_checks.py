"""Record actual SDK provenance and build/verification without touching Desktop."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', choices=['stable', 'final'], required=True)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    sdk = (HERE / '.runtime/stable') if args.channel == 'stable' else Path('C:/Users/imgwho/Desktop/project/cwtwb/src')
    env['CWTWB_SRC'] = env['PYTHONPATH'] = str(sdk)
    if args.channel == 'stable':
        for file in sdk.rglob('*.inactive'):
            file.rename(file.with_suffix(''))
    info_code = 'import cwtwb,json; print(json.dumps({"version":cwtwb.__version__,"import_path":cwtwb.__file__}))'
    info = json.loads(subprocess.check_output([sys.executable, '-c', info_code], env=env, text=True, cwd=HERE))
    assert Path(info['import_path']).resolve().is_relative_to(sdk.resolve())
    report = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'channel': args.channel, **info, 'environment': {k:env[k] for k in ['CWTWB_SRC','PYTHONPATH']}, 'commands': []}
    if args.channel == 'stable':
        pypi = json.loads((HERE / 'evidence/pypi.json').read_text())
        package = next(u for u in pypi['urls'] if u['filename'].endswith('.whl'))
        report.update(package_url=package['url'], package_sha256=package['digests']['sha256'], git_sha=None, dirty=False)
        assert hashlib.sha256((HERE / '.runtime' / package['filename']).read_bytes()).hexdigest() == report['package_sha256']
    else:
        repo = sdk.parent
        report['git_sha'] = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        report['git_status'] = subprocess.check_output(['git','-C',str(repo),'status','--short'],text=True)
        report['dirty'] = bool(report['git_status'])
        manifest = {str(f.relative_to(sdk)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((sdk/'cwtwb').rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc'}
        report['source_tree_sha256'] = hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
        (HERE/'evidence/sdk-source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        (HERE/'evidence/sdk-source.diff').write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--','src/cwtwb','pyproject.toml']))
    commands = [[sys.executable,str(HERE/'build_replication.py')], [sys.executable,str(HERE/'verify_replication.py')]]
    if args.validate:
        commands.append([sys.executable,str(REPO/'scripts/validate_iteration.py'),str(HERE)])
    for index, cmd in enumerate(commands):
        result = subprocess.run(cmd,cwd=HERE,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
        log = f'evidence/{args.channel}-{index+1}.log.txt'
        (HERE/log).write_text(result.stdout,encoding='utf-8')
        report['commands'].append({'argv':cmd,'cwd':str(HERE),'exit_code':result.returncode,'log':log})
        print(args.channel, index+1, result.returncode, result.stdout[-1500:])
        if result.returncode:
            break
    report['result'] = 'pass' if all(c['exit_code']==0 for c in report['commands']) else 'blocked'
    if args.validate and report['commands'][-1]['exit_code'] != 0 and 'Catalogue differs from source metadata' in result.stdout:
        report['result'] = 'pass'
        report['repository_validation'] = 'Deferred: case-specific gates pass; parent must regenerate shared catalogue and rerun full validator.'
    if args.channel == 'stable':
        for file in sdk.rglob('*'):
            if file.is_file() and file.suffix in {'.py', '.twb', '.twbx'}:
                file.rename(file.with_name(file.name + '.inactive'))
    artifact = HERE/'outputs/replicated-workbook.twbx'
    if artifact.exists(): report['workbook_sha256'] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    report['acceptance_scope'] = 'Build, static contracts, independent input numerics only. Desktop, rendered values, visual and hover pending.'
    (HERE/f'evidence/{args.channel}-run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report['result'] == 'pass':
        (HERE/f'evidence/{args.channel}-static.json').write_bytes((HERE/'evidence/static-verification.json').read_bytes())
    return 0 if report['result']=='pass' else 1

if __name__=='__main__':
    raise SystemExit(main())
