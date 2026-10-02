# Contributing a WoW Case

This lab accepts AI-assisted analysis and replication of one Tableau case per
pull request. A contribution may finish the case or leave a reproducible
`partial`/`blocked` result for someone else to continue.

## 1. Claim a case

Open or claim a GitHub issue for one unconsumed `posts/` article. Link the
article and the primary author workbook. Do not work on several cases in one
PR.

## 2. Create the iteration

Install the released SDK, then prepare the case:

```bash
python -m pip install "cwtwb>=0.26.0"
python scripts/prepare_case.py \
  --source path/to/author.twbx \
  --iteration-id YYYY-MM-DD-wwNN-short-slug \
  --challenge-year YYYY \
  --case-id wow-YYYY-wwNN-short-slug \
  --post posts/YYYY-MM-DD-article.html
```

If you do not already have the TWBX, use its Tableau Public URL and the article
URL. The workbook is downloaded to a temporary directory and removed after its
data is extracted:

```bash
python scripts/prepare_case.py \
  --workbook-url "https://public.tableau.com/views/WORKBOOK/VIEW" \
  --iteration-id YYYY-MM-DD-wwNN-short-slug \
  --challenge-year YYYY \
  --case-id wow-YYYY-wwNN-short-slug \
  --post-url "https://example.com/article"
```

The command copies `iterations/_template`, extracts packaged data files to
`inputs/`, and writes hashes to `inputs/source-lock.json`. It does not copy the
author workbook into the iteration.

## 3. Analyze before building

Complete `analysis.md` before implementing the workbook. Explain:

- the decision or interaction the user needs;
- why the obvious Tableau approach fails;
- the author's necessary calculation/view/action chain;
- observable functional acceptance scenarios;
- presentation details that may differ.

The author workbook is analysis evidence, not a build template.

## 4. Test the released cwtwb first

Set `cwtwb.tested_version` in `case.yaml`. Build with that version before
proposing SDK changes and record one result:

- `pass`: public APIs were sufficient;
- `workaround`: the case works with a documented local workaround;
- `blocked`: a required behavior could not be built.

If a gap is reusable, open a separate issue or PR in
`aidatacooper/cwtwb`. Keep the Lab PR draft until the released SDK version can
be tested again. A core PR should use a small synthetic fixture, not depend on
this full WoW case.

New schema 1.1 cases keep an append-only retest history. Add a run instead of
overwriting the previous result, and keep the latest run aligned with the
summary fields:

```yaml
cwtwb:
  tested_version: 0.27.0
  runs:
    - version: 0.26.0
      result: blocked
      evidence: evidence/cwtwb-0.26.0.json
    - version: 0.27.0
      result: pass
      evidence: verify_replication.py
cwtwb_result: pass
```

## 5. Verify

```bash
python scripts/validate_iteration.py iterations/<iteration-id>
```

Also open the TWBX manually when interactions cannot be proven statically.
Describe the tested parameter/filter/action scenario and attach one useful
screenshot. Exact fonts, padding, borders, and decoration are optional unless
they change the answer.

Schema 1.1 acceptance entries have stable IDs. Name each automated ID beside
the verifier assertion that proves it. Manual entries must link a committed
evidence file:

```yaml
acceptance:
  - id: hover-clears-selection
    description: Leaving the custom axis clears the selected set.
    mode: manual
    evidence: evidence/hover-clears-selection.json
```

## 6. Contribute a confirmed gap to cwtwb

Possessing or cloning this Lab does not by itself make a case suitable for the
SDK. A cwtwb contribution is ready only when all of these are true:

1. The gap was reproduced with a released cwtwb version and recorded in the
   Lab case. An unclear API is a documentation problem, not a new primitive.
2. The behavior is reusable across workbooks. WoW-, author-, or workbook-named
   APIs are not accepted; one-off XML or visual differences stay local.
3. The report includes the smallest synthetic reproducer and expected TWB XML.
   Do not copy the author's TWB/TWBX, extracted data, screenshots, or internal
   Tableau field tokens into cwtwb.
4. The change preserves the complete public path when applicable: builder,
   dispatcher, Python facade, MCP tool, and capability registry.
5. A focused XPath regression test passes, followed by the full cwtwb suite.
   Tableau Desktop/Cloud evidence is required only when local XML/XSD checks
   cannot prove the behavior.
6. The contributor owns the submitted code and can provide it under cwtwb's
   AGPL-3.0-or-later license.

Code contributions need a checked-out working copy, but it does not have to be
on the contributor's own computer. External contributors normally fork cwtwb,
then use a local clone, GitHub Codespaces, or another development environment;
maintainers may use a branch in the upstream repository. Small documentation
changes can use GitHub's web editor.

The normal local setup is:

```bash
git clone https://github.com/<your-account>/cwtwb
cd cwtwb
python -m pip install -e ".[dev]"
pytest
```

Python 3.10 or newer is required. The same install and test commands apply in
Codespaces or another checked-out environment. Tableau Cloud/Server credentials
are not needed for normal SDK changes. They are needed only for cloud semantic
validation, publishing, or screenshot work; install `.[validate]` for those
paths. Open a cwtwb issue first when API shape is uncertain, then submit a
separate cwtwb PR linked from `related_cwtwb_issues` and append the released
version retest to the Lab case.

## 7. Submit one-directory PR

Your PR should normally change only:

```text
iterations/<iteration-id>/
usage/case-index.json
usage/consumed-cases.json
```

Regenerate `usage/case-index.json` and `usage/consumed-cases.json` from case
metadata and include those generated changes; never hand-edit their status. Link any related cwtwb issue/PR from `case.yaml` and the PR body.
Directories marked as legacy predate the v1 contract. Do not use them as
templates; create a new v1 iteration unless a maintainer explicitly assigns a
legacy migration.

Before submission:

```bash
python -m unittest discover -s tests -v
git diff --check
```

Maintainers can validate every v1 case's metadata cheaply on normal changes,
or explicitly rebuild every case after a cwtwb release:

```bash
python scripts/validate_changed_cases.py --all --metadata-only
python scripts/validate_changed_cases.py --all
```

## Case identities and indexes

Follow [the identity and naming rules](docs/protocols/case-identity-and-naming.md). Formal folders retain the
article publication date; canonical IDs include the explicit challenge year.
Maintain `case.yaml` as the editable status source and regenerate both indexes
with `python scripts/case_catalogue.py --write`. Include generated index changes
with the case change; archived pilots and legacy aliases do not add active cases.
