# Case identity, naming and generated indexes

Formal cases live in `iterations/YYYY-MM-DD-wwNN-short-slug/`. The prefix is the
article publication date, `wwNN` is a two-digit challenge week (01?53), and the
slug uses lowercase letters, digits and hyphens. `iteration_id` exactly matches
the folder. `_template` is a template; `archive/` contains historical pilots and
is excluded from active case counts.

Canonical `case_id` is `wow-CHALLENGEYEAR-wwNN-short-slug`. Challenge year is an
explicit field, **not inferred from article publication year**. For example,
an article published on 2026-01-01 about a 2025 challenge uses a 2026 folder
prefix and a `wow-2025-...` ID. Old IDs map to the canonical ID through each
case's `legacy_case_ids`; aliases do not represent additional cases.

Keep `article_date`, `challenge_year`, `challenge_week` and
`source_workbook_date` separate. Unknown original workbook dates are null.
Original workbook filenames, source-lock hashes and historical evidence remain
unchanged. The WW39 original filename's WW38 token is an explicitly recorded
source discrepancy, not silently corrected during naming migration.

## Create a new case

```bash
python scripts/prepare_case.py \
  --source path/to/author.twbx \
  --iteration-id 2026-01-01-ww01-example \
  --challenge-year 2026 \
  --post-url https://example.com/article
```

`--case-id` is optional. When supplied it must equal the generated canonical ID.
Preparation extracts data and writes initial identity metadata; it does not
copy the author workbook or certify a completed replication. Complete the
analysis, builder, verifier and acceptance evidence before submission.

## Standard artifacts

- Primary generated workbook: `outputs/replicated-workbook.twbx`.
- Identified Cloud author image: `outputs/cloud-author.png`.
- Identified Cloud replica image: `outputs/cloud-replica.png`.

A missing screenshot is null metadata, never fabricated. Additional views,
probes and historic TWB companions retain their existing names and are listed
as historical artifacts. `artifact_aliases` resolves renamed paths in historical
records; mutable builders/verifiers use the current path. Renaming screenshots
is not proof of visual parity.

## One editable status source

Each formal case's `case.yaml` is the editable source of identity and status.
`usage/case-index.json` is the generated complete active catalogue.
`usage/consumed-cases.json` is a generated compatibility view; consumed means
claimed and does not mean verified complete. The pre-migration registry is
preserved verbatim in `usage/history/consumed-cases-before-standardization.json`.
Source article collection IDs in `build_dataset.py` remain date/URL-scoped Donna
IDs; the selector resolves their aliases to canonical iteration identities.

After building or changing metadata, regenerate and validate:

```bash
python scripts/case_catalogue.py --write
python scripts/case_catalogue.py
python scripts/validate_changed_cases.py --all --metadata-only
python -m unittest discover -s tests -v
git diff --check
```

Commit the case metadata and generated views together. CI rejects stale/missing
catalogue entries, invalid dates/weeks, canonical ID and alias collisions,
duplicate original article/workbook identities, unsafe/missing artifact paths,
and stale builder/verifier references. Shared Superstore extracts are not
original-case identities and do not indicate duplicate cases.

Legacy `legacy-summary-1.0` metadata is grandfathered only for the explicitly
listed historical directories. It is an identity/status summary, not a claim
that the current v1 provenance and acceptance checks passed. New cases use the
v1.1 contribution contract; the naming migration does not relax its builder
boundary, extracted data hashes or acceptance checks. `verification_status`
distinguishes pending, historical and verified evidence. In particular, WW33
remains pending and WW36 partial. `acceptable_delta` must not be promoted to
`matched` without actual visual evidence.

The existing CI invokes the validators on pushes to main and relevant pull
requests involving cases or Python code. Both derived views and all active cases receive
metadata/index checks. Grandfathered legacy summaries never invoke builders or
verifiers; ordinary PR validation can still build newly contributed v1 cases.
Canonical consumed counts include each record once, while selection and dataset
verification accept the recorded Donna aliases without changing source IDs or
the dataset source schema. Invalid alias targets or conflicting mappings are
errors, not permission to exclude an unrelated source article.
