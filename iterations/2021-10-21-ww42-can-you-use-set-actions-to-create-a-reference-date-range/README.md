# WW42: a reference date range with native set actions

Status: **partial / acceptable_delta**. The final workbook opens in Tableau
Desktop, and its default Cloud screenshot and eight worksheet CSV exports were
checked against raw data and independently reviewed. The six local numerical
selection scenarios pass; live selection/clear/Ctrl-select events still await
browser MFA. REST data export does not establish those events.

- Workbook: [outputs/replicated-workbook.twbx](outputs/replicated-workbook.twbx)
- Preview: [outputs/cloud-replica.png](outputs/cloud-replica.png)
- Results and commands: [evidence/handoff.json](evidence/handoff.json)
- Interactive acceptance steps: [evidence/runtime-acceptance.md](evidence/runtime-acceptance.md)
- SDK repair: https://github.com/aidatacooper/cwtwb/pull/22 (merged)

Build with cwtwb source commit `11d72ebe5b7720035e26150bd16af72d67a35bba`
(version 0.29.0a2; fixes are newer than the published a2 tag). Set `PYTHONPATH`
and `CWTWB_SRC` to that checkout's `src` directory, then run:

```powershell
python -X utf8 build_replication.py
python -X utf8 verify_replication.py
python -X utf8 -m unittest test_verifier -v
```

Rebuilding changes the workbook identity and invalidates existing Cloud hashes.
Use an isolated copy for rebuild validation. The baseline a1 output and its
original evidence are retained for regression diagnosis.
