# WoW Lab Community Case Contribution Protocol v1

Status: active  
Priority: functional correctness, interaction correctness, repeatable build,
then visual similarity.

## Objective

A contributor uses AI to analyze one article from `posts/` and its author
workbook, then creates a resumable, buildable, and verifiable replication under
`iterations/<iteration-id>/`. The result is evidence about the real boundary of
the released cwtwb API.

## Standard flow

```text
Claim one case in a GitHub issue
-> analyze the article and explain why the obvious solution fails
-> inspect the author TWB/TWBX to recover the necessary Tableau solution chain
-> extract Hyper, TDE, Excel, CSV, or spatial data once and record hashes
-> build with the current released cwtwb package
-> run the verifier and manually test interactions when necessary
-> submit a replicated, partial, or blocked iteration PR
-> file a separate cwtwb issue/PR for a confirmed reusable gap
-> retest the case after a new cwtwb release
```

## Provenance boundary

During analysis, AI may read the article, author workbook, and reference images.
During construction, it may read only the extracted data, written case analysis,
blank templates, and cwtwb. It must not read, copy, or patch the author TWB/TWBX.

Run `scripts/prepare_case.py` to extract data. The author workbook must not be
placed inside the iteration directory.

## cwtwb baseline

Each case first tests a released version and records the outcome:

```yaml
cwtwb:
  tested_version: 0.26.0
cwtwb_result: pass  # pass | workaround | blocked
```

Schema 1.1 cases also append `cwtwb.runs` entries containing `version`,
`result`, and a repository-relative `evidence` file. The last run must match
`cwtwb.tested_version` and `cwtwb_result`; older runs are never overwritten.

Preserve evidence from the released version before changing cwtwb:

- Existing API: fix the case implementation or documentation.
- Public API bug: create a separate cwtwb bug PR.
- Reusable capability gap: create a separate cwtwb feature PR.
- One-off visual or XML difference: keep a local case workaround.
- Unresolved behavior: submit a reproducible `partial` or `blocked` result.

A cwtwb PR must use a small synthetic fixture and must not depend on a complete
WoW case or author-owned data.

It is eligible only after a released-version baseline proves a reusable SDK
bug or missing primitive. The contribution must keep the builder, dispatcher,
Python facade, MCP surface, and capability registry aligned where applicable,
and include a focused XPath regression test plus the full cwtwb test run.
Python 3.10+ and `pip install -e ".[dev]"` are sufficient for normal work.
The checked-out fork or branch may live locally, in Codespaces, or in another
development environment; only small documentation changes reasonably use the
GitHub web editor. Tableau credentials are optional unless the changed
behavior requires cloud semantic validation, publishing, or screenshots.
Contributors must have the right to submit the code under cwtwb's
AGPL-3.0-or-later license.

## Pull request boundary

One PR handles one case and normally changes only its iteration directory.
Contributors do not edit `usage/consumed-cases.json`; maintainers update shared
indexes after merge.

Every case contains at least:

```text
case.yaml
analysis.md
build_replication.py
verify_replication.py
inputs/source-lock.json
inputs/<extracted data files>
outputs/replicated-workbook.twbx
```

`partial` and `blocked` are valid outcomes when the analysis, failure evidence,
and continuation point are complete.

## Acceptance

```bash
python scripts/validate_iteration.py iterations/<iteration-id>
python -m unittest discover -s tests -v
```

Static XML cannot prove every parameter, filter, set action, parameter action,
or complex table calculation. When needed, test the interaction in Tableau and
record the scenario in the PR. Visual differences block acceptance only when
they change the business answer, interaction, or readability.

Schema 1.1 gives acceptance scenarios stable IDs and marks each as `automated`
or `manual`. Automated IDs must be named in `verify_replication.py`; manual
IDs must point to a committed evidence file. A `partial` or `blocked` case must
describe `remaining_work`; blocked cwtwb results must also name the blocker and
reusable capability gap.
