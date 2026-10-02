# Case analysis

## Current SDK rebuild and Cloud validation

The current builder starts from an empty workbook, reads only independently locked data under inputs, and uses public cwtwb 0.27.1 APIs. The original workbook is an analysis reference, never a build template. Current Cloud author/replica images and CSV exports are bound to their artifact hashes in evidence/cloud-verification.json. Historical evidence is preserved under evidence/history/pre-ten-cloud-verification and the baseline Git commit.

Acceptance remains pending until the new visual/state review and any actual browser actions are recorded. See evidence/current-functional-verification.json for deterministic checks and docs/case-driven-enhancements.md in cwtwb for reusable SDK changes.
