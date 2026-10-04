# 2021 WW08 — Brush Filter Extension

Rebuilds five borough monthly trends from 158,923 locked raw records and embeds the actual Starschema sandboxed Brush Filter extension.

```powershell
.venv/Scripts/python.exe iterations/2021-02-25-ww08-brush-filter-extension/build_replication.py
.venv/Scripts/python.exe iterations/2021-02-25-ww08-brush-filter-extension/verify_replication.py
```

The builder starts from `TWBEditor("")` and uses only public APIs and extracted input data. The verifier independently checks every visible monthly count and endpoint classification, plus the real extension identity, manifest, settings and worksheet binding. REST exports and artifact contracts are the acceptance scope; browser mouse gestures are not claimed. The real extension's overview aggregation limitation is explained in analysis.md.

Do not rebuild to inspect current evidence. Rebuilt workbook identities require new Cloud publication, images and CSV.
