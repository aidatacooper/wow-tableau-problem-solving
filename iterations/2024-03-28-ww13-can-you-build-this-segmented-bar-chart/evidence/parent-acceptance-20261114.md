# Parent acceptance, 2026-11-14

Historical load-stage report below is preserved. Its pending interaction and visual
conclusions are superseded by the final acceptance addendum at the end.

Final artifact SHA256: `5a6f759ecd2c8e8c09b4b9adae754e1c921eec069f406fb1ac221426c7a55b22`.

The full validator and numerical verifier passed after the parent corrected the
public header-width configuration and selected the dashboard as the startup view.
Desktop process 21288 loaded this artifact; the matching launch and load records,
SDK source identity and file hashes are in `desktop-final-20261114.json`.
`desktop-publication-20261114.json` repeats the observed load evidence after a
trailing blank line was removed from the builder, recording its publication hash.
The primary workbook was unchanged. Case-local Git attributes preserve exact
Python source bytes and literal SDK diff evidence across platforms.

The parent inspected `desktop-final-dashboard.png`, captured directly from the
Tableau window. All 17 category pairs are visible without scrolling or clipping,
from Chairs to Fasteners. Each total bar is taller than its annual segmented bar.
Both bars have the same full length, with space between pairs. The final image
shows full category labels, cream background, tan bars, white segment boundaries,
and no visible axes or gridlines. Earlier captures exposed truncated labels;
the final builder fixes this using field-specific `header_formats` width with no
scope selector.

Runtime tooltip values remain **unverified**. Attempts to deliver hover events
did not produce observable tooltip values, so neither the presence of tooltip XML
nor the numerical oracle is counted as interaction acceptance. The recovery
dialog was dismissed without deleting recovered files. No user workbook was saved.

The supplied author dashboard PNG was a placeholder, not a usable final reference.
Article construction screenshots were inspected, but a final visual comparison
has not been accepted. `visual_status` therefore remains `not_evaluated`.

Separately, an isolated Python 3.11 environment installed the repository's exact
requirements pin, SDK commit `cac8820f26e703c3858253adfa21efd989eb8a78`.
The case rebuilt and verified in a disposable copy with source overrides removed;
83 shared tests passed. See `ci-pin-parent-20261114.json`. Later final formatting
and startup changes are covered again by the post-commit changed-case check.

The parent-supplied shared Desktop load regression is complete: 50 LOADED,
0 FAIL and 0 UNKNOWN. `desktop-corpus-evidence.json` records the 50 artifact
hashes and the SDK Python source hashes matching the prior isolated corpus
rebuild; `desktop-corpus.json` contains the corresponding load verdicts.
These records were copied unchanged into this case's evidence. They establish
the shared load gate, not live interaction acceptance, and do not represent
another Desktop run during submission.

This case remains partial with hover acceptance and final visual comparison
pending. Loading and rendered geometry are demonstrated; full completion is
not claimed.

## Final actual acceptance addendum

The parent subsequently verified all ten required hovers in actual Tableau Desktop
presentation mode: Chairs and Fasteners totals plus each category's 2021–2024
annual amounts and shares. `desktop-live-acceptance-20261114.json` records the
observations and ten screenshot hashes. All values match the frozen numerical
oracle at the displayed precision; later annual tooltips show annual amounts.

The downloaded actual article GIF (`article-reference.gif`, with
`article-reference-frame0.png`) was compared directly with
`desktop-presentation-20261114.png`. All 17 ordered pairs, full labels,
cream/tan colors, white separators and absence of axes/gridlines are accepted.
Title/footer wording and font sizes differ, yielding `acceptable_delta`.

The primary artifact hash above is unchanged. Prior Desktop LOADED and the
50 LOADED / 0 FAIL / 0 UNKNOWN corpus retain their original scope and SDK baseline.
Final status is `replicated`, `verified`, and `acceptable_delta`, with no remaining
acceptance work. The run history appends the frozen live acceptance record without
changing previous runs. No primary rebuild, new Desktop run or SDK change was
performed during metadata finalization.
