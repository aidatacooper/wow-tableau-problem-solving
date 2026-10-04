# Cloud comparison: 2020 WW30

Verdict: **acceptable_delta**. Reviewed all six full-size REST PNGs side by side: default, California and Texas, each original and replica. The frozen replica TWBX SHA-256 is `ad342c380c6d6f315cb60f70d6e7a913045e6c66134b9c6cadd48c17af13fa32`. The Cloud manifest binds every PNG and CSV to this artifact and records the source export provenance.

The original 800 x 700 dashboard structure is preserved: heading, centered dynamic chart title and instruction, profit-horizontal/sales-vertical scatter, footer and challenge link. Blue cross marks, red negative-profit marks, labels, zero baselines, numeric axis ticks and the explicit Sales/Profit axis captions render correctly. Both filtered states retain their single correctly positioned state mark; headings, axes and footer are readable without overlapping or truncated content.

The independent verifier passed all six complete Scatter CSVs: 48 state rows per role in default and one row per role in California/Texas. Every exported Sales/Profit pair matches the corresponding aggregation of the locked 8,399 original fact rows within the native displayed precision. The raw oracle separately covers every state/city aggregate. PNG and CSV SHA-256 values were checked against the manifest.

The REST State filters leave the Selected State set empty. These captures therefore demonstrate state filtering, not a city drill-down event. Native action activation/source/target/set clearing, Records to Show, Display Value and both measure branches are independently verified from the generated artifact. No browser selection, click or hover was executed or claimed.

Remaining differences are modest: the replica heading and crosses are larger, chart padding and label placement differ slightly, and the instruction uses upright text rather than the original italic treatment. The footer identifies the SDK reconstruction and its challenge link is plain text instead of the original blue underlined link. Neither values nor chart orientation are altered; this is not a pixel-match claim.

Evidence: [Cloud manifest](cloud-verification.json), [independent verification](functional-verification.json), [author export provenance](export-provenance.json), and the paired `outputs/cloud-{author,replica}[-california|-texas].png` files.
