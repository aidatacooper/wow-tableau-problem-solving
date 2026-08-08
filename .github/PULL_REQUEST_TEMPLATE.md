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
- [ ] Visual differences that do not affect the answer are documented.
- [ ] This PR changes one iteration and does not edit the shared usage registry.

## cwtwb follow-up

Related cwtwb issue/PR, if a reusable capability gap was found:
