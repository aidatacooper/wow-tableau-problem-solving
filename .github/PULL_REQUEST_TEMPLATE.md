## Case

- Issue: Closes #
- Post:
- Iteration:
- Tested cwtwb version:

## Result

- Functional status: `partial | replicated | blocked`
- Visual status: `not_evaluated | acceptable_delta | matched`
- cwtwb result: `pass | workaround | blocked`

## Functional checks

- [ ] AI analysis explains the problem and why the obvious approach fails.
- [ ] The builder reads extracted data, not the author TWB/TWBX.
- [ ] `python scripts/validate_iteration.py iterations/<id>` passes.
- [ ] The generated TWBX opens in Tableau, or the blocker is documented.
- [ ] Parameters, filters, and actions were manually exercised when present.
- [ ] Automated acceptance IDs are named in the verifier; manual IDs link evidence.
- [ ] Partial/blocked results state remaining work and blocked results reproduce the gap.
- [ ] The latest cwtwb run matches the summary version and result.
- [ ] Visual differences that do not affect the answer are documented.
- [ ] This PR changes one iteration and does not edit the shared usage registry.
- [ ] The case ID and post are not already owned by another v1 iteration.
- [ ] Included third-party assets may be redistributed, or only URLs and hashes are committed.

## cwtwb follow-up

Related cwtwb issue/PR, if a reusable capability gap was found:

- [ ] The gap is reusable and reproduced against a released cwtwb version.
- [ ] Any upstream reproducer is synthetic and contains no author-owned assets.
