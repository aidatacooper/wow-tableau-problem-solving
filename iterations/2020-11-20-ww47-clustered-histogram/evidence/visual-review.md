# WW47 Cloud visual and data review

Artifact SHA256: `2ab41510854c76f3f43b520b79e2b997ee443e19502a26b2ac55b30ff048c6e8`

Visual status: `acceptable_delta`.

All six final PNGs were independently inspected in source/replica pairs for default, Consumer and Corporate. The native gray $2000+ band is visibly rendered in every state, and its black bold label is at the top, matching the source. Native Tableau palette assignment reindexes Corporate-only filtering to blue in both source and replica; the initial static-color mismatch was corrected. Continuous sale positions and all bar heights agree.

The complete six Chart CSV exports contain 61 / 21 / 20 groups per role. Every group count and segment/offset position is strictly checked against all 3312 raw facts, grouped into 1687 distinct orders (876 Consumer, 493 Corporate, 318 Home Office). All high-value groups have independently verified counts 25 / 27 / 15. Author CSV conditional tooltip fields between/lower/upper/symbol are also independently checked for all groups, including the $2000+ branch. Replica CSV exports only sale position, segment and CountD; native rich tooltip expressions are inspected as artifact contracts, not claimed as executed hover proof.

Source and replica use the same 1400x800 target geometry, title hierarchy, chart region, horizontal categorical legend, credit blocks and official URL. Remaining differences are small title and plot padding offsets, font metrics, a slightly different legend spacing, and truthful SDK footer credit. Tooltip command buttons are not explicitly suppressed by the SDK custom-tooltip API as in the source. These differences are documented; no pixel-perfect match or browser events are claimed.

The first released-SDK attempt failed because no public reference-band authoring API existed. The generic SDK native band enhancement was validated on synthetic author-free fixtures before this case used it. The final artifact was built on immutable Git e977401d862f0754ba610249e6720d61058ebdea and passed a separate zero-author-workbook reconstruction.
