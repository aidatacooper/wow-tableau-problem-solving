# 2021 WW03 ? Control chart

Builds a weekly complaints control chart, native show/hide parameter panel, and complaint detail navigation from locked original Hyper data using public cwtwb APIs.

```powershell
python iterations/2021-01-22-ww03-control-chart/build_replication.py
python iterations/2021-01-22-ww03-control-chart/verify_replication.py
```

The verifier independently checks all 75,513 original complaints, all 30 parameter combinations, native calculations/layout/actions, and actual captured REST CSV states. See [analysis.md](analysis.md) and [visual review](evidence/visual-review.md) for the coverage boundary and visual deltas.

After Cloud acceptance, run the verifier directly; rebuilding changes workbook identity and requires fresh publication and hash-bound evidence.
