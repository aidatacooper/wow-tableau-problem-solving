# Parent handoff — background implementation complete locally

Worktree: `C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-518c0bcc`
Branch: `t3/ww48-advent-calendar`
Prior implementation commit: `64f1020bd9e30bfe38818c80391f86bdc77ee536`
Current commit: returned in task response; `git rev-parse HEAD` after commit.
Frozen primary SHA256: `264257cd5b710753e4c13ac5f4737d0740af3517e1d659c5a7bd03c8d3aae0b7`
Builder source SHA256: `977879b5445a1cbb9bd37b4a35b6c3b487154b968a7e5fe6f03bbc201a4c6b91`
Verifier source SHA256: `fcbb49d67bdc88f271b10f15aa46977c0c0105ed6a449a7002a0d5ee4590eea3`
All source/evidence hashes: `evidence/frozen-background-manifest.json`.

## Current result

The native mapped tree background is implemented on released **0.29.0a2** through exported `convert_workbook` / `read_workbook`. This is a **structural public-API workaround**, not a semantic API pass. The builder converts only its own newly blank-built workbook, independently authors mapping Y=horizontal 0..4 and X=vertical 0..6, packages the extracted PNG, and converts back. No author TWB/TWBX/XML/JSON is read or copied. No SDK edit is needed.

Tree + Bar, portable bauble/star shapes, larger-star category sizing, fixed viewport, countdown labels/tooltips, gradients/count labels, URL/filter/self-highlight actions, help and layout are all locally implemented. Static contracts do not prove rendered alignment or no-grey/live behavior. Metadata remains functional `partial`, visual `not_evaluated`, SDK `workaround`, awaiting parent runtime gates.

## Evidence and correction

The previous absolute incapability conclusion was incorrect. The old probe tested only Cartesian `configure_chart(map_layers=...)`; public structural conversion works. `evidence/background-workaround.md` corrects that interpretation while preserving prior evidence bytewise. Old `evidence/background-blocker.md` is historical, not the current conclusion.

Original frozen SHA256 546ed6e1246c09c9a284a32b1ed9b4288121f270bbdfd507049307d8bf613dbc is `outputs/frozen-546ed6e.twbx`. All old run entries and reports remain unchanged, including outputs/local-verification.json and outputs/build-provenance.json. The new run is appended and reports to outputs/background-verification.json and outputs/background-build-provenance.json. The prior manifest remains historical at commit 64f1020; its old primary is now the archive. `evidence/prior-evidence-preservation.json` binds old outputs/evidence, and `--historical` checks them separately.

## Local results

- Metadata/source-lock/public-API phase boundary and strict XSD: PASS.
- Raw Hyper oracle: 24 challenges + star; counts 10/3/5/6; all 2000 segments and 2025 runtime rows reconcile.
- Mapping types/bounds/resource closure and public JSON/TWBX roundtrip: PASS; exact PNG/Hyper bytes retained.
- Strong reference/definition/tooltip/Kind/action/category-direction contracts: PASS; **43 negative mutations rejected**.
- **83 repository tests pass**; catalogue consistent; disposable-copy fresh rebuild passes with all historical workbooks removed first.
- Historical bytes, append-only run history and staged source hashes verified.

## Reproduction commands (PowerShell, repository root)

```powershell
$env:PYTHONPATH='C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving/scratch/sdk-release-0.29.0a2'
$env:CWTWB_SRC=$env:PYTHONPATH
$case='iterations/2021-12-02-ww48-tableau-coaches-favourite-challenges-advent-calendar'
python scripts/validate_iteration.py $case
python "$case/verify_replication.py" --historical
python -m unittest discover -s tests -v
python scripts/case_catalogue.py
python -c "from pathlib import Path; from scripts.validate_iteration import run_case_scripts_isolated; run_case_scripts_isolated(Path('$case').resolve())"
```

The first command rebuilds and changes UUID/hash. After freeze, use disposable-copy validation to preserve accepted bytes. Default verifier checks only fresh output; `--historical` adds archive checks. Historical reports are never rewritten. `probe_background.py` is now explicitly a narrow chart-map-layers probe and uses new output names if rerun; it is not a capability blocker test.

## Remaining parent gates

Independent review of the structural workaround and strengthened verifier; serialized Desktop LOADED and corpus checks with explicit SDK source; rendered tree mapping/viewport, category mark sizes, gradient continuity and text/layout inspection; year select/multiselect/clear, tooltip and no-grey interaction testing. Inspect challenge URL payloads without opening external pages unless authorized to execute that runtime test. No browser/Desktop/Cloud/live events, SDK edits, push or PR were performed here. Parent owns publish/review workflow and final status promotion.
