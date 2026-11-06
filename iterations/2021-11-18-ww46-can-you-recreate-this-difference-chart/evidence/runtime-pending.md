# Candidate runtime gates remain pending

Parent-provided evidence for the old e73539d6 artifact is preserved in baseline-a2-e73539d6/. It records Desktop LOADED (load only) and Cloud REST captures; browser_interaction_executed is false. The preservation manifest maps unchanged JSON/image bytes to archived paths. Parent reports excessive spacer gap in that prior Cloud image.

No Desktop, Cloud, browser, render or live hover event was performed on the new candidate by this child. The new four-item sort and three-item filter pass local structural tests. Baseline coupling established an API/structural limitation; it did not prove the cause of rendered spacing. Only parent recapture/comparison can establish whether the candidate improves that gap.

1. SDK PR23 is merged; parent owns final case PR pin integration using the exact tested reachable commit.
2. Run Desktop against the frozen candidate workbook and corpus gate; UNKNOWN is failure.
3. Recapture candidate Cloud image and compare with both author and archived a2 baseline. Confirm one 800x400 sheet, Category columns and Segment rows, PY/CY bars, Gantt then blank row, actual gap size, title and signed labels.
4. Hover both mark layers and verify year-aware values. Real browser events/MFA remain pending.
5. Independent review and publication/PR remain parent-owned.

Lifecycle update from parent: PR23 https://github.com/aidatacooper/cwtwb/pull/23 passed exact-head CI and merged as 54784b4c09018bc9866337fb352f59ccb6753100. Tested source remains cac8820f26e703c3858253adfa21efd989eb8a78. No source switch or rebuild was performed merely for the merge SHA; parent owns final requirements pin and runtime.
