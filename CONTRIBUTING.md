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
  --iteration-id YYYY-MM-DD-short-slug \
  --case-id stable-case-id \
  --post posts/YYYY-MM-DD-article.html
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

## 5. Verify

```bash
python scripts/validate_iteration.py iterations/<iteration-id>
```

Also open the TWBX manually when interactions cannot be proven statically.
Describe the tested parameter/filter/action scenario and attach one useful
screenshot. Exact fonts, padding, borders, and decoration are optional unless
they change the answer.

## 6. Submit one-directory PR

Your PR should normally change only:

```text
iterations/<iteration-id>/
```

Do not edit `usage/consumed-cases.json`; maintainers update shared indexes
after merge. Link any related cwtwb issue/PR from `case.yaml` and the PR body.

Before submission:

```bash
python -m unittest discover -s tests -v
git diff --check
```
