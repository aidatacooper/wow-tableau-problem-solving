# Cloud review: NFL table enhancements

Result: **replicated / acceptable_delta** within the REST-state and workbook-contract scope below. This is not a pixel-identical result.

Accepted TWBX SHA-256: `7d4dd106da75f63e64bfed50975621b5e8e47f4833ce26d408b62ab6c3676a9f`.

The final `cloud-verification.json` binds both published workbooks, all twelve paired dashboard PNGs and sixty worksheet CSV files to their hashes. The comparison copy differs from the downloaded author workbook only in exposing existing worksheet windows, as proven by `export-provenance.json`.

| REST state | Independent data and image checks |
| --- | --- |
| Default, Carries descending, page 1 | Ten player IDs and all four metrics; selected Carries/down-arrow header; page 1 of 56. |
| Page 2 | Exact next ten IDs from the independently sorted full roster; all forty metric values; page 2 and prior/next targets. |
| Expanded top player | Player 10638 has all three seasons, 2017–2019, plus ten collapsed players; thirteen groups and fifty-two metric values. All season labels are fully readable. |
| Yards ascending | Exact ascending roster, including negative yardage; all four metrics and selected Yards/up-arrow header. |
| Avg YPC descending | Exact independently ranked roster and all four metrics; selected Avg YPC/down-arrow header. |
| Touchdowns last page | Exact six remaining IDs and all twenty-four metric values; page 56 of 56 and next target clamped to 56. |

`verify_replication.py` independently reads every locked rushing play: 40,736 facts, 556 players and every player/season group. The twelve Table exports cover 118 paired player/season groups and 472 metric values, not a single CSV containing the entire 556-player roster. The twelve Header exports cover all four measures crossed with all three header positions, including selected direction, reset-to-one source and replica glyphs. Thirty-six page-control CSVs independently verify the current page, total pages and clamped previous/next targets. All sixty exports pass their complete domain and value checks.

All six source/replica image pairs were inspected. Native computed sorting now precedes INDEX and reproduces the requested roster. The four measure headings align with the centered body values. Player identifiers are readable, the expanded years are complete rather than `20..`, and the requested direction and current page are visible. The final source-like Automatic mark and consistent center alignment remove the competing right-aligned pane style from earlier builds.

Remaining visual differences are the larger, heavier title and shorter explanatory copy; lighter unselected header captions and regular rather than bold selected caption; green expanded metrics; a vertically centered expansion arrow; and triangular unboxed pager controls rather than the author's boxed minus/plus controls. Footer credits and the link are condensed, and row separators are less prominent. These differences do not alter the requested page membership, metric values or control targets.

Selection, drilldown, direction changes, page reset and deselection are verified through native action source/target/activation/clear contracts. Every source column-instance must exist on its actual worksheet and resolve to the intended declared field; every target resolves to the correct real parameter. Set Level reads the per-player DD Level encoded on Table marks, matching the author and correctly distinguishing a collapsed different player from the currently expanded player. The earlier global Max Level source was rejected despite passing REST snapshots. REST parameters directly select the six captured states. No browser clicks or hover events were executed, so this evidence does not claim that such events were replayed interactively.
