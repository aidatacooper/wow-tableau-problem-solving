# Measure Names ordering: candidate local retest

Baseline a2 evidence in sdk-probe.json and baseline-a2-e73539d6/ demonstrates structural coupling: layered chart filter membership and manual ordering used the same list. This establishes an API limitation, not the rendered necessity of a different sort or the cause of the gap. Parent reports an excessive gap in the archived a2 Cloud capture; compare rendered artifacts before making a spacing claim.

Parent candidate commit cac8820f26e703c3858253adfa21efd989eb8a78 at C:/Users/imgwho/Desktop/project/cwtwb-three-20261029/src adds measure_names_order independently of measure_values, including default-view-expression normalization. The case now supplies [SUM(PY Sales), SUM(CY Sales), SUM(PY Sales (copy)), MIN(Spacer)] while keeping its filter list [SUM(PY Sales), SUM(CY Sales), MIN(Spacer)]. Candidate API and emitted case contract both pass.

Reproduce locally with run_local.ps1. verify_replication.py --candidate-probe builds an author-free synthetic Hyper source. It checks the four-member sort/three-member filter, reference closure, order-only physical Sales resolving to SUM(Sales), rejection of Sales plus SUM(Sales) as duplicate resolved references, and failure when the order-only instance declaration is removed. The case verifier checks all qualified worksheet references in attributes/text, including styles, title, tooltip and palettes, plus source/dependency calculation closure. It rejects missing Gantt instance and dangling style/formula references.

The typed nullable Spacer workaround remains because inline MIN(NULL) is not supported by the baseline expression parser. Seven named calculations are retained.

This is an candidate-checkout retest, not a released-SDK success claim. No shared SDK edit, installation, requirements pin, Desktop/Cloud invocation or external publication was made by this child. Parent owns final pin integration and must recapture runtime evidence against the candidate frozen SHA.

Lifecycle update from parent: PR23 https://github.com/aidatacooper/cwtwb/pull/23 passed exact-head CI and merged as 54784b4c09018bc9866337fb352f59ccb6753100. Tested source remains cac8820f26e703c3858253adfa21efd989eb8a78. No source switch or rebuild was performed merely for the merge SHA; parent owns final requirements pin and runtime.
