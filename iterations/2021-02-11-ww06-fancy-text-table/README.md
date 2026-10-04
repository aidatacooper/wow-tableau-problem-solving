# 2021 WW06: Fancy Text Table

The independent builder creates a single eight-measure monthly sales table
from the locked raw Superstore Hyper using the public SDK and an empty workbook.

```powershell
python iterations/2021-02-11-ww06-fancy-text-table/build_replication.py
python iterations/2021-02-11-ww06-fancy-text-table/verify_replication.py
python scripts/validate_iteration.py iterations/2021-02-11-ww06-fancy-text-table
```

The verifier independently computes all 12 months and eight displayed metrics,
including daily extrema, date serial formatting and competition ranks. When
Cloud evidence is present, it also checks every exported table cell and every
capture hash. Source-author workbooks are analysis/publication inputs only and
are absent from the build inputs.

After Cloud acceptance, run the verifier or metadata-only validation against
the frozen output. Rebuilding changes workbook identity and requires fresh
publication and capture evidence.
