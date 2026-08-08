# WoW Lab Agent Guide

This repository turns one `posts/` article and its author Tableau workbook
into one independently buildable project under `iterations/`.

## Goal

For each claimed case:

1. understand the business question before changing code;
2. inspect the author workbook during analysis only;
3. extract its packaged data files once;
4. rebuild the required behavior with the currently released `cwtwb`;
5. record whether `cwtwb` passed, needed a workaround, or was blocked;
6. propose a separate `cwtwb` issue/PR only for a reusable capability gap.

Functional and interaction correctness matter more than pixel-perfect styling.

## One case, one PR

Only modify your own `iterations/<iteration-id>/` directory. Do not edit other
cases or `usage/consumed-cases.json`; maintainers update shared indexes after
merge.

Historical directories without v1 `functional_status` metadata are legacy and
read-only unless the task explicitly requests their migration.

Start from `iterations/_template/` or run:

```bash
python scripts/prepare_case.py \
  --source path/to/author.twbx \
  --iteration-id YYYY-MM-DD-short-slug \
  --case-id stable-case-id \
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
- the exact tested `cwtwb` version;
- observable acceptance scenarios in `case.yaml`;
- a runnable builder and verifier.

A `partial` or `blocked` PR is useful when the analysis is sound and the
failure is reproducible.

## When to change cwtwb

Do not edit `cwtwb` while establishing the baseline. First reproduce the gap
with a released version.

- Existing API, unclear usage: improve the case or documentation.
- Existing API bug: open a `cwtwb` bug with a small synthetic reproducer.
- Reusable missing primitive: open a separate `cwtwb` feature PR and test.
- One-off visual/XML difference: keep a documented case workaround.

Core changes must be generic; never add APIs named for a WoW number, author,
or individual workbook.

## Verification

Before opening a PR:

```bash
python scripts/validate_iteration.py iterations/<iteration-id>
python -m unittest discover -s tests -v
```

Open the generated TWBX in Tableau when the case uses actions, parameters,
table calculations, or behavior that static XML checks cannot prove.
