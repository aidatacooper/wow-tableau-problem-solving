# 2021 WW05 — Predicting the future

Builds a native Gaussian-process predictive chart and three-item measure selector from 26 locked raw enrollment observations.

```powershell
.venv/Scripts/python.exe iterations/2021-02-04-ww05-predicting-the-future/build_replication.py
.venv/Scripts/python.exe iterations/2021-02-04-ww05-predicting-the-future/verify_replication.py
```

The builder uses `TWBEditor("")` and public APIs. Author files are never used as a template. The verifier checks all 31 years under each of three REST parameter states, independently recomputes training actuals and arithmetic, and compares Tableau's GP outputs against the author. It does not claim independent GP fitting or browser action execution.

Rebuilding changes the workbook identity and hash. Existing evidence can be checked by running only the verifier; a rebuilt workbook requires fresh Cloud publication and exports.
