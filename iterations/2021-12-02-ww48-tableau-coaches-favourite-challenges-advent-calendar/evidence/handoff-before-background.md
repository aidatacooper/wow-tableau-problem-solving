# Parent handoff

Branch: `t3/ww48-advent-calendar` in `C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-518c0bcc`.
Base: fetched `origin/main` d52ecab before changes; no unpublished parent history inherited.
Final commit: use `git rev-parse HEAD` after this handoff commit; exact commit is also returned in the task response.
Frozen workbook SHA256: `546ed6e1246c09c9a284a32b1ed9b4288121f270bbdfd507049307d8bf613dbc`.
Builder source SHA256: `8b4721f53b2333a166b887815d9a4fbda8ca8f5be9ba6a3db874c63bcd6bbf17`.
Full source/evidence hashes: `evidence/frozen-manifest.json`. Local attributes preserve binary/data/evidence bytes and LF Python sources.

## Result

Runnable maximal implementation, with a demonstrated generic capability blocker: native coordinate-mapped tree background is unavailable in released 0.29.0a2 and merged cac8820. **The generated Tree has ornaments/star but no tree background.** It must not be called a complete replication. Both sheets, custom shapes, fixed axes, day labels/tooltips, 500-segment gradients, count labels, same-datasource filter/select/clear action, URL action, constant self-highlight, help and 1000×800 layout are implemented and statically verified. No live actions or rendered correctness claimed. All 83 repo tests and local gates pass. Archived baseline/retest artifacts and synthetic probes are declared role=probe.

## Exact local commands (PowerShell, from worktree root)

```powershell
$env:PYTHONPATH='C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving/scratch/sdk-release-0.29.0a2'
$env:CWTWB_SRC=$env:PYTHONPATH
$case='iterations/2021-12-02-ww48-tableau-coaches-favourite-challenges-advent-calendar'
python "$case/build_replication.py"
python "$case/verify_replication.py"
python "$case/probe_background.py"
python "$case/verify_replication.py" --historical
python scripts/case_catalogue.py --write
python scripts/validate_iteration.py $case
python -m unittest discover -s tests -v
python -c "from pathlib import Path; from scripts.validate_iteration import run_case_scripts_isolated; run_case_scripts_isolated(Path('$case').resolve())"
```

Commands that rebuild replace UUIDs/hashes: validate before freezing; after freeze prefer the disposable-copy validation command. The default verifier requires only a fresh primary workbook; `--historical` separately checks archived hashes and synthetic probes. CI deletes historical TWBX files before its fresh verifier, which passes. Distribution provenance does not require a local SDK git checkout. Requirements pins the published prerelease; no global SDK change was made.

Merged retest uses identical commands with both environment variables set to `C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving/scratch/sdk-installed-cac8820`; its installed direct_url commit was `cac8820f26e703c3858253adfa21efd989eb8a78`, despite package metadata retaining 0.29.0a2. Final primary output was rebuilt using released a2 after that retest.

## Remaining parent work

1. Resolve the reusable mapped-image API gap described in `evidence/background-blocker.md`; generic synthetic repro is ready. Parent owns SDK change/PR. Tree mapping: Y horizontal 0–4, X vertical 0–6; viewport horizontal 0–4, vertical 0–7. Same worksheet requirement forbids a dashboard image workaround.
2. Independent different-model review of implementation/oracle and emitted interaction contracts.
3. Serialized Desktop build/load (explicit SDK source) and full corpus gate. FAIL/UNKNOWN are not acceptance. Then render and inspect actual gradient continuity, labels, star sizing, tree coordinate alignment and fixed bounds.
4. Validate year filtering (10/3/5/6 ornaments), multiselect, clear restoring star+24 ornaments, no-grey behavior and tooltips. Challenge links are implemented but **remain unexecuted**; inspect URL payloads without navigation unless authorized to run that test. User MFA remains unavailable; no live events claimed.
5. Rebuild/revalidate/refreeze after any SDK fix, then parent-owned review/push/PR. Do not mark replicated before required runtime gates.

Official challenge publication date verified as **2021-11-30**, not the workbook filename's erroneous January date. Evidence is `evidence/official-challenge.json`.
