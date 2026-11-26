# Current a4 publication provenance

The accepted primary workbook SHA256 is `dad8b357161b428c980f465d1368e95d5c40c4fde58d12c84171067c619ba33c`. It was built with clean SDK `175471b0fa4ad0ae91b4d9b6d629a621583d945e`, version `0.29.0a4`. `desktop-a4-tooltip-fix-20261114.json` binds its builder, strengthened verifier, SDK source-file hashes, zero strict XSD errors and Desktop 2026.2 LOADED verdict. The parent fixed the generic missing circle Sales tooltip through SDK PR26.

The repository dependency now pins PR26's merged commit `81362658fa1856ce98e86033b05e9f77c6bdad47`. The actual artifact-build commit remains recorded separately and is not relabeled as a merge-commit build. Exact-pin validation rebuilds only in a disposable copy, preserving the accepted primary workbook and Desktop evidence.

## Current case acceptance

`desktop-a4-live-acceptance-20261114.json` records actual Desktop interactions and Copy > Crosstab output. All 68 runtime rows, covering 34 unique annual values, agree with the source oracle within `1e-6`. Seven observed tooltips, including corrected circle Sales values, agree with whole-number display formatting. Selecting Phones and clicking that selected circle again restores all 17 rows, amounts and original colors. Blank dashboard clicks did not clear selection and are not accepted as a clearing method.

Envelopes 2021's thin endpoint is occluded by the overlapping year-level circles of the analyzed standard LOD design. It was not directly hovered. Its `4745.41` value is verified by the actual Desktop crosstab. This hit-target limitation is retained explicitly; no assertion of every endpoint being directly hoverable is made.

The official baseline requires one sheet in an 800 x 700 dashboard, 2021 narrow and 2022 wide comet ends, 2022 labels, white circles, direction colors and matching formatting. Static contracts and the parent's final visual inspection support this baseline: all 17 rows and labels, directional shapes and red Machines/Envelopes agree. Typography and title wrapping differ, so visual status is `acceptable_delta`. The optional ADVANCED table-calculation-only tier is not claimed. Case status is `replicated` / `verified`.

## Superseded evidence retained

`stable-run.json`, `final-run.json`, `sdk-source-manifest.json`, `case-static-gates.json`, `desktop-publication-20261114.json`, `desktop-final-fit-20261114.json`, `publication-final.md`, old screenshots and `baseline-compatibility.md` retain their historical bytes and scope. The old files called `final-run.json` and `publication-final.md` are not current publication evidence. The pre-fix `desktop-circle-tooltip-missing-sales.png` and `desktop-tooltip-phones-2021.png` document the superseded failure investigation. `pre-tooltip-fix-rejection.log` records the strengthened circle Sales assertion rejecting the prior artifact.

`static-verification.json` covers the current artifact's automated contracts and source numerics. Its generic pending runtime fields are superseded by the actual a4 live acceptance report.

## Integration gate passed

`desktop-corpus.json` and `desktop-corpus-evidence.json` describe the superseded pre-fix corpus on SDK `2b72232245959934281c49308f5c3b2fca8fc519`.

The parent's final evidence is copied byte-for-byte from `tmp/cwtwb-a4-regression-20261114` into `corpus-a4/`: `desktop-summary.json`, `artifact-hashes.csv`, `summary.json` and `sdk-source-hashes.json`. All 50 distinct Desktop results are LOADED, with 0 FAIL and 0 UNKNOWN. Their artifact hashes match the 50 successful isolated builds in the CSV. Every result uses SDK source `175471b0fa4ad0ae91b4d9b6d629a621583d945e`, matching the accepted primary's build source. The source manifest matches the primary build's recorded SDK files. `summary.json` is the earlier build-phase report (`desktop_run: false`); the later `desktop-summary.json` supplies the actual completed Desktop gate. This corpus checks loading, while case interactions and rendering are covered by the separate a4 live acceptance evidence.

Exact merged-pin validation on committed case `3ecbda3` passed `validate_changed_cases.py --base-ref origin/main` with rebuilding only in a disposable copy; all 83 repository unittests passed. Logs are `a4-exact-pin-changed-cases.log.txt` and `a4-exact-pin-unittests.log.txt`. The environment imports installed `cwtwb` 0.29.0a4 from this clone's `.venv`, with direct URL commit `81362658fa1856ce98e86033b05e9f77c6bdad47`, and no `CWTWB_SRC` or `PYTHONPATH`. GitHub's source-to-merge comparison contains no changed files. The primary artifact hash remains unchanged. Finalization did not launch Desktop or rebuild the primary workbook. All required gates now pass.
