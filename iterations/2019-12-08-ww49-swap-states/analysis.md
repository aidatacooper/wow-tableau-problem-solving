# 2019 WW49: swap states

The dashboard displays the 25 highest-sales states outside the selected set as a 5 x 5 silhouette trellis, and the selected state above with city bubbles sized by sales. Selection replaces the set with one state; clearing preserves the previous state.

The initial selection is Oklahoma (nationwide rank 26, sales $19,683.39, seven cities). Selecting California promotes Oklahoma into the OUT-partition top 25. Trellis positions address State within the Selected Set partition, while labels display nationwide ranks across both dimensions. A hidden set-membership filter preserves the calculations' partition rather than removing input rows early.

The independent builder starts with `TWBEditor("")`, reads only extracted Hyper input, uses generated geographic fields and public APIs, and never opens the author workbook. Author map-layer identifiers were enumerated during analysis and recorded as constants, not read at build time.

The released SDK baseline at 0958b51 was blocked by explicit set members, generated geometry, layered filters and map-layer controls. Generic SDK primitives and synthetic regression tests supply these capabilities. The independently queried Hyper oracle checks all 49 possible selections, sums city sales back to state totals, and verifies complete 25-cell positions and nationwide ranks.

Cloud REST evidence covers exported images and the actual dashboard CSV scope. Set replacement and clear behavior are verified as serialized artifact contracts; no browser click has been executed or claimed.

The first Cloud rendering exposed an additional reusable gap: the empty SDK template retained a China geocoding context, so US State/City lookups returned blank generated coordinates and all maps vanished although their sales CSV was correct. `set_geocoding_context(country="United States", state=None)` fixes the lookup domain. The failed capture is retained as `evidence/cloud-initial-blank-geography.json`; generated-map regressions now test country replacement, null-state lookup and idempotence. Cloud CSV checks also require populated Oklahoma coordinates, rather than accepting correct Sales on blank maps.
