# WoW Lab Agent Guide

This repository turns one `posts/` article and its author Tableau workbook
into one independently buildable project under `iterations/`.

## Start here

To solve one case, the full operational manual is
[docs/start-a-case.md](docs/start-a-case.md). Read it before touching code.

For long, multi-case, or interruptible runs, read
[docs/long-running-tasks.md](docs/long-running-tasks.md) first: it records the
large files that must never be read whole, the progress document that makes a
crash resumable, and when to split work across agents.
Its profile/model examples are environment-specific, not prerequisites. Use
the ownership and Desktop serialization rules in the cross-repo workflow;
delegate only when authorized and supported by the available tools.

To iterate the SDK and this repo together, the short version is
[docs/iterating-cwtwb-and-wow.md](docs/iterating-cwtwb-and-wow.md).

Resolve a case's identity from the article URL alone:

```bash
python scripts/case_intake.py "<article-url>"
```

It prints the `iteration-id`, canonical `case-id`, challenge year/week, the
Tableau Public workbook URL, and the official challenge record to confirm the
date. It reads only `index.json` / `public_links_map.json` and the Workout
Wednesday public API; it never edits metadata or opens the author workbook.

`main` is protected: never commit to it directly. Open a temporary branch
(`feat/<YYYY-wwNN-slug>`), push, and open a pull request. Prefer `--merge`
under the repository convention. Squash creates a different commit; it does
not necessarily make the original unreachable. Pin a fetchable upstream
commit that survives the merge, and verify installation from that pin.

## Goal

For each claimed case:

1. understand the business question before changing code;
2. inspect the author workbook during analysis only;
3. extract its packaged data files once;
4. default to the latest PyPI stable `cwtwb` baseline, or use an explicitly
   requested source baseline with its full SHA; distinguish these channels;
5. record whether `cwtwb` passed, needed a workaround, or was blocked;
6. track reusable gaps through SDK repair and final full-case acceptance.

Functional and interaction correctness matter more than pixel-perfect styling.

## One case, one PR

Case contributions change their own `iterations/<iteration-id>/` directory
and the generated index views. Do not edit unrelated cases. Refresh the views
from case metadata and submit them with the case change; never hand-edit status.

Historical directories without v1 `functional_status` metadata are legacy and
read-only unless the task explicitly requests their migration.

Start from `iterations/_template/` or run:

```bash
python scripts/prepare_case.py \
  --source path/to/author.twbx \
  --iteration-id YYYY-MM-DD-wwNN-short-slug \
  --challenge-year YYYY \
  --case-id wow-YYYY-wwNN-short-slug \
  --post posts/YYYY-MM-DD-article.html
```

## Phase boundary

Analysis may read the article, author TWB/TWBX, and reference screenshots.
`build_replication.py` may read only:

- `case.yaml` and `analysis.md`;
- extracted Hyper/TDE/Excel/CSV/spatial files under `inputs/`;
- an empty workbook/template;
- public `cwtwb` APIs.

The builder must not open, unzip, copy, or import the author TWB/TWBX.

## Required result

Every case records:

- `functional_status`: `partial`, `replicated`, or `blocked`;
- `visual_status`: `not_evaluated`, `acceptable_delta`, or `matched`;
- `cwtwb_result`: `pass`, `workaround`, or `blocked`;
- the exact tested `cwtwb` source/channel, version, import path and full Git SHA
  (or package version/hash when no checkout exists), including dirty state;
- append-only `cwtwb.runs` history for schema 1.1 cases;
- observable acceptance scenarios in `case.yaml`;
- a runnable builder and verifier.

A `partial` or `blocked` PR is useful when the analysis is sound and the
failure is reproducible. It must state `remaining_work`; blocked SDK results
must also identify the blocker and reusable capability gap.
Merging that PR records progress, not a solved case. Keep the case open/partial
until every required acceptance scenario passes on the final artifact.

## When to change cwtwb

Do not edit `cwtwb` while establishing the baseline. First reproduce the gap
with the latest PyPI stable release by default. An explicitly requested source
baseline must record its full SHA and must not imply a PyPI baseline was run.
Record prerelease and freshly fetched main separately. Never infer "latest"
from an editable install's version.
See the dated source snapshot and selection procedure in
[docs/iterating-cwtwb-and-wow.md](docs/iterating-cwtwb-and-wow.md).

- Existing API, unclear usage: improve the case or documentation.
- Existing API bug: open a `cwtwb` bug with a small synthetic reproducer.
- Reusable missing primitive: open a separate `cwtwb` feature PR and test.
- One-off visual/XML difference: keep a documented case workaround.

Core changes must be generic; never add APIs named for a WoW number, author,
or individual workbook.

Give each reusable gap an identifier, owner, failing acceptance IDs, synthetic
reproducer and next action. Track `identified -> reproduced -> fixing ->
upstream merged -> case retested -> accepted` in analysis/progress evidence.
Add real issue URLs to `related_cwtwb_issues` and real PR URLs to the gap record
only after creation; otherwise say "not created". A merged SDK PR alone does
not close the gap. Append each actual retest to `cwtwb.runs`, preserving earlier
failures; its evidence file records source/version/SHA and observed results.

Before opening a separate cwtwb PR, reduce the gap to a synthetic fixture that
contains no author workbook or data. Preserve the applicable builder ->
dispatcher -> Python facade -> MCP tool -> capability registry path and add an
XPath regression test. Normal cwtwb development needs Python 3.10+,
`pip install -e ".[dev]"`, and `pytest`; Tableau credentials are optional
unless cloud validation, publishing, or screenshots are in scope. Cloud
credentials live outside the repository in `~/.config/wow-cloud/tableau.env`
and are loaded by `scripts/cloud_credentials.py`; see
[docs/tableau-cloud-credentials.md](docs/tableau-cloud-credentials.md). Never
commit a token.

## Verification

The Desktop gate is mandatory, not optional. A workbook that Tableau Desktop
refuses to open fails acceptance even when every XML check passes; `FAIL` and
`UNKNOWN` both count as failures.
`LOADED` proves opening only: verify required clicks, filters, parameter changes,
selections and reset behavior separately. XML assertions are structural evidence,
not interaction acceptance. Serialize all Desktop sessions on a shared machine.

Before opening a PR:

```bash
python scripts/validate_iteration.py iterations/<iteration-id>   # XSD + phase boundary + metadata
python -m unittest discover -s tests -v
python scripts/desktop/build_and_check.py iterations/<iteration-id> --sdk-src <selected-sdk>/src
python scripts/desktop/verify_corpus.py    # all listed cases LOADED; no FAIL/UNKNOWN/NOBUILD
python scripts/case_catalogue.py --write   # refresh the generated index views
```

Select the SDK for the entire command sequence, including standalone validators
and verifiers, using the cross-repo workflow. `--sdk-src` selects it only for
that build invocation. For an SDK regression, rebuild the baseline with that
source before `verify_corpus.py`, which only opens existing artifacts.
Finish all rebuilds before capturing hash-bound Cloud/interaction evidence;
any later rebuild requires recapture. Regenerate indexes from final metadata.

See [docs/cross-repo-desktop-workflow.md](docs/cross-repo-desktop-workflow.md)
for the cross-repository loop and
[docs/desktop-log-verdict.md](docs/desktop-log-verdict.md) for why the verdict
is read from Tableau's own log.

## Maintainer identity migration

Follow [the identity and naming rules](docs/protocols/case-identity-and-naming.md). Formal folders retain the
article publication date; canonical IDs include the explicit challenge year.
Maintain `case.yaml` as the editable status source and regenerate both indexes
with `python scripts/case_catalogue.py --write`. Include generated index changes
with the case change; archived pilots and legacy aliases do not add active cases.
