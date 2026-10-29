$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'C:/Users/imgwho/Desktop/project/cwtwb-three-20261029/src'
$env:CWTWB_SRC = $env:PYTHONPATH
$env:PYTHONUTF8 = '1'
$casePath = $PSScriptRoot
$repoPath = Split-Path (Split-Path $casePath -Parent) -Parent
Push-Location $repoPath
try {
    python -c "import cwtwb, pathlib, tomllib; print(tomllib.loads((pathlib.Path(cwtwb.__file__).resolve().parents[2] / 'pyproject.toml').read_text())['project']['version']); print(cwtwb.__file__)"
    if ($LASTEXITCODE -ne 0) { throw 'SDK identity failed' }
    python scripts/case_catalogue.py --write
    if ($LASTEXITCODE -ne 0) { throw 'Catalogue failed' }
    python "$casePath/verify_replication.py" --candidate-probe
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic probe failed' }
    python scripts/validate_iteration.py $casePath *> "$casePath/validation.txt"
    if ($LASTEXITCODE -ne 0) { Get-Content "$casePath/validation.txt" -Tail 25; throw 'Case validation failed' }
    Get-Content "$casePath/validation.txt" -Tail 4
    python -m unittest discover -s tests -v *> "$casePath/tests.txt"
    if ($LASTEXITCODE -ne 0) { Get-Content "$casePath/tests.txt" -Tail 25; throw 'Repository tests failed' }
    Get-Content "$casePath/tests.txt" -Tail 4
} finally { Pop-Location }
