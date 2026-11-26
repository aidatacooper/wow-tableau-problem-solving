# Pending serial Desktop and rendered acceptance

Status: PENDING. This worker did not open or control Desktop.

1. After all final rebuilds, run scripts/desktop/build_and_check.py for this case with --sdk-src C:/Users/imgwho/Desktop/project/cwtwb/src. Require LOADED; FAIL and UNKNOWN fail.
2. Open the Visualizing Ranges dashboard. Confirm a single worksheet on 1300x600, title, 24-hour curve, x-axis 0–26, mg/dL axis, black dashed median drawn above nested areas, white below-minimum region, symmetric light blue tails and darker central 25–75% region. Percentile labels must remain legible.
3. Confirm orange dotted reference lines at exactly 80 and 180 (not 0, not displaced to the secondary axis). The secondary synchronized y-axis must be hidden.
4. Compare a crosstab export / underlying displayed measures for all 24 hours with evidence/verification.json hourly records (tolerance 1e-6 unformatted; 0.05 when one decimal is displayed). Hover 00:00, 12:00, 23:00 and one high-variance hour to ensure tooltips report the corresponding median/percentile data. No custom interactions are required by this challenge.
5. Capture screenshot and record Tableau version, artifact SHA256, exact observations and any defects. Re-capture after any rebuild.
6. Run required shared corpus Desktop check serially. Only then may the parent update functional status to replicated and visual status with captured evidence, append the final SDK run and regenerate indexes.
