# Parent handoff — corrected raster/shape references and gradient

Worktree: `C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-518c0bcc`
Branch: `t3/ww48-advent-calendar`
Prior implementation commit: `916452897859a394a404ef3014e26196636fd5df`
New commit: returned in task response; `git rev-parse HEAD` after commit.
Frozen candidate SHA256: `3980ad6e8e6cbb957d3ba19b0faf870df6482323c5bd4e876d87b5dcfeb1069f`
Builder source SHA256: `5ea4bce3205d9d60e8745a2e9452ffb710a97e99fcf38b9d13a88eba16bf0993`
Verifier source SHA256: `dc07ac18044e2cf23e124d3211ce0e8f743ad80806945c082d51148348b4f88c`
Manifest: `evidence/frozen-render-reference-manifest.json`.

## Result and limits

A runnable corrected candidate is built with released **0.29.0a2**. It has **not been rendered**. Parent capture of 264257cd failed: raster absent, default circle/square shapes, barely visible white labels, reversed gradient. Both actual PNGs were inspected; CSVs confirmed the intended data grain. Roundtrip bytes/XSD are no longer treated as evidence that rendering works.

Corrections on our own blank-built native document:

- Raster expression is `file:Images/christmas-tree.png`, not a quoted path literal; exact extracted PNG remains packaged.
- Custom-shape style's field now has a **datasource-scope column-instance**, declared from our own worksheet dependency. Explicit embedded asset maps remain; the unregistered `palette="Advent"` attribute is removed.
- Gradient color uses ascending `AVG(Segment Start)` on a shared 0..10 red-low/green-high domain, reverse=false. Simply reversing the old palette would give wrong short-bar endpoints. Locked inputs remain byte-identical; descending Gradient is unused.

`probe_shape_binding.py` produces a two-row synthetic before/after fixture showing the released shape API's omitted datasource binding. See `evidence/shape-binding-reproducer.json`. This is a concrete reference-emission defect; public structural authoring can work around it. No SDK edit or broad incapability claim. Palette removal versus instance registration has not been isolated at runtime, so parent must recapture the complete correction. White labels remain intended for the red ornaments.

## Preserved evidence

`outputs/frozen-264257cd.twbx` is byte-identical to the failed render source. All parent JSON/PNG/CSV captures and previous background reports were archived under `evidence/runtime-264257cd`; preservation.json hashes both originals and archive copies. The original root cloud*.json and PNG/CSV are also untouched and still describe **264257cd**, never the new artifact. Do not present them as current visual acceptance. Original cwtwb.runs records and old report files remain unchanged; a fifth run is appended.

The previous handoff is archived at `evidence/handoff-before-render-correction.md`. Existing 546ed6e/baseline/retest artifacts and earlier evidence remain preserved.

## Local gates

Metadata, source locks, public-API phase boundary, strict XSD, catalogue, own-native-document roundtrip and portable asset checks PASS. Raw input oracle reconciles 24 days+star and 10/3/5/6 counts. **83 repository tests pass; 49 mutations are rejected.** The mutations include missing datasource shape binding, unregistered palette, quoted image path, descending gradient and shifted/reversed color domain. Isolated fresh rebuild passes after historical workbooks are removed; historical checks remain a separate mode. Captured CSVs reconcile 25 Tree and 2004 Bar rows for the failed artifact.

## Exact local commands

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

Validation rebuilds and changes UUID/hash; use the isolated command after freeze. New local output reports are `render-reference-verification.json` and `render-reference-build-provenance.json`; older background/local reports are immutable historical evidence. Rerunning the synthetic probe changes its archived fixture hashes, so treat committed fixture/report bytes as a matched set.

## Parent gates

Recapture the new frozen candidate to **new capture filenames or archive existing ones first**. Confirm actual tree image, custom red ornaments/yellow star, legible white day labels, star/bauble scale, red-to-green gradients with correct short-bar endpoints and counts. Then review year select/multiselect/clear, URL payload and no-grey behavior. No live event claim is made. Keep functional partial / visual not_evaluated until appropriate runtime acceptance. The globally running corpus was not touched; no Desktop/Cloud/browser launch, SDK edit, push, PR or subagent was used here.
