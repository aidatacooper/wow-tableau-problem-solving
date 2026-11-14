# Parent acceptance, 2026-11-14

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

This case remains partial until the outstanding hover and shared corpus gates
are completed. Loading and rendered geometry are demonstrated; full completion
is not claimed.
