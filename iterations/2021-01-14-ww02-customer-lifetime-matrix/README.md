# 2021 WW02: Customer lifetime value matrix

From-zero public-SDK replication of Donna Coles' 2021-01-14 article and the official 2021-01-12 challenge.

```powershell
python iterations/2021-01-14-ww02-customer-lifetime-matrix/build_replication.py
python iterations/2021-01-14-ww02-customer-lifetime-matrix/verify_replication.py
```

Install the repository requirements first. The builder reads only the SHA256-locked extracted original Hyper input. The verifier independently computes all 136 triangular matrix cells from 9,994 raw order lines and verifies the native FIXED/LOOKUP/running-sum calculations and layout. Cloud CSV/image coverage and visual differences are recorded in evidence/visual-review.md after review.

An accepted workbook must not be rebuilt without republishing, recapturing and updating hash-bound evidence. Running the verifier alone preserves accepted identities. REST images/data plus native artifact contracts establish acceptance; actual browser actions/hover/mobile behavior are outside scope.
