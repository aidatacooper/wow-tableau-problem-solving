# Desktop acceptance — final fit, partial interaction coverage

Final update (2026-11-14, parent operator report): TWBX SHA256 `6438345df80931b943bae5115d13783b6a714a8f381aabd29f5596abab6ee2cb`, SDK `056050c8e95f5fbe3560886e566c34aee53b40b0`, Desktop 2026.2 **LOADED** in `desktop-final-fit-20261114.json`. That record contains no raw load records; none are added here.

The parent visually compared the full DPI-correct `desktop-final-dashboard.png` against the actual `author-reference.png`: all 17 rows and latest amounts agree; no scrollbar; Machines and Envelopes are red; comet directions and white centers are correct. Visual status is **acceptable_delta** because title wrapping and type sizing differ.

All 34 annual points pass automated numerics; the screenshot confirms the 17 latest labels only. Annual tooltip hover and selection clearing remain **unverified**: foreground targeting failed. No successful live interaction is claimed. Functional status stays **partial**.

The original checklist below is preserved as historical planning. Its pending statements are superseded only by the explicit results above. Steps 5 and 6 remain outstanding. See `publication-final.md` for the separate PRE-FIX corpus and old-pin compatibility scopes.

## Original pre-fit checklist

Do not mark replicated based on static checks. No Desktop process was opened by this worker.

1. Build/check with the explicitly selected final SDK and require LOADED. Record Tableau version, final TWBX SHA256 and Desktop log evidence. UNKNOWN/FAIL does not pass.
2. Open dashboard `2023 Week 08 - Comet Chart` at its native 800 x 700. Confirm one worksheet, 17 visible rows, no scrollbar or truncated title/labels, chart/legend/background/separators consistent with author-reference.png. Record screenshot.
3. Check latest-sales labels in descending order: Phones 105,668; Chairs 98,032; Binders 73,651; Storage 70,274; Copiers 62,917; Tables 60,999; Accessories 59,946; Machines 43,888; Appliances 43,111; Bookcases 30,354; Furnishings 29,927; Paper 28,174; Supplies 16,076; Art 9,023; Fasteners 6,162; Labels 3,987; Envelopes 3,379. Prefer exported underlying/crosstab values against evidence/expected-sales.json for all 34 points.
4. Confirm Machines and Envelopes alone are red, with their narrow 2021 end to the right and wide white-ringed 2022 end to the left. Other comets widen to the right. Tables has nearly equal values and must still be visible. All circles must fit within the comet wide end. Check size legend has 2021 small and 2022 large.
5. Hover Phones, Machines and Envelopes at both annual line endpoints. Record year/sub-category/sales values; compare evidence/expected-sales.json. Hover each white circle and verify visible values are consistent with the corresponding underlying year. The two year-level circles overlap at the latest-sales location by design, as in the author's standard solution; use the thin line endpoints for unambiguous 2021 checks.
6. Move pointer off marks and clear selection: no year/filter/parameter state should persist (there are no dashboard actions). All rows/labels must remain visible.
7. Parent runs full regression corpus and repository tests, appends final acceptance/run evidence, then updates status/index and commits/pushes this case separately. Any rebuild after screenshots/interaction evidence requires recapture.

Current outcome (2026-11-14, supersedes the pending procedure above): PASS for case acceptance on a4 artifact `dad8b357161b428c980f465d1368e95d5c40c4fde58d12c84171067c619ba33c`. See `desktop-a4-tooltip-fix-20261114.json` for Desktop LOADED and `desktop-a4-live-acceptance-20261114.json` for actual runtime observations. All 68 crosstab rows / 34 unique annual values agree within 1e-6; seven observed tooltips agree. Clicking the selected Phones circle again restores all 17 rows and colors; blank dashboard clicks did not clear selection. Envelopes 2021 was not directly hovered because the standard LOD circles occlude its thin endpoint; its 4745.41 value is verified in the actual crosstab. All required rows, labels and comet shapes agree; font size/title wrapping differ (`acceptable_delta`). Parent final a4 full-corpus integration evidence remains pending.
