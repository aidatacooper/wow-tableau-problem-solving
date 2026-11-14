# Final publication provenance

The final workbook uses worksheet layout fit entire plus `set_window_state(DASHBOARD, zoom_entire_view=True)`. The parent reports that the full validator passed after this fix.

The authoritative final artifact and SDK source provenance are in `desktop-final-fit-20261114.json`: TWBX SHA256 `6438345df80931b943bae5115d13783b6a714a8f381aabd29f5596abab6ee2cb`, SDK commit `056050c8e95f5fbe3560886e566c34aee53b40b0`. Its per-file source manifest supersedes the earlier aggregate source hash for the current run.

Historical `stable-run.json`, `final-run.json`, `sdk-source-manifest.json`, `case-static-gates.json` and `desktop-publication-20261114.json` retain their original scope and hashes. The historical file named `final-run.json` is a pre-fit run, not the final publication artifact. Its failed catalogue check is preserved.

`static-verification.json` checks the final artifact's automated contracts and source numerics; its generic pending Desktop/render fields are superseded by `desktop-acceptance.md` and the final Desktop run.

## PRE-FIX release corpus

`desktop-corpus.json` and `desktop-corpus-evidence.json` are byte-for-byte copies of the shared release evidence. They record 50 LOADED, 0 FAIL, 0 UNKNOWN on SDK `2b72232245959934281c49308f5c3b2fca8fc519`, before the fit fix. The recorded source match applies to that release and its prior isolated rebuild only. No current-fix corpus run or interaction acceptance is inferred.

## Repository-pin compatibility

The repository still pins SDK `cac8820f26e703c3858253adfa21efd989eb8a78` (`0.29.0a2`). Finalization uses `../case-2024/.venv/Scripts/python.exe` with `CWTWB_SRC` and `PYTHONPATH` absent for full unittests and `validate_changed_cases.py --base-ref origin/main`. The latter validates committed metadata and rebuilds/verifies only in a disposable temporary copy. These checks establish baseline old-pin compatibility, not Desktop/render equivalence to the accepted final SDK artifact. Results are recorded separately in `baseline-compatibility.md`.
