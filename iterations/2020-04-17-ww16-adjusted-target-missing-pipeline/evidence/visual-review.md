# Cloud visual and data review ? 2020 WW16

Accepted within the documented scope as `acceptable_delta`. The reviewed artifact SHA256 is `07c8aafdaa70136299c3d8844313759d16813d6e1aea933b8e83f64115adfefa`. It was checked with released SDK `ac191fde0c2f104697c8dd2d2f0417d9b124dd7e`.

The paired default-state images [author](../outputs/cloud-author.png) and [replica](../outputs/cloud-replica.png) show all twelve monthly bars without overlap or clipping. Closed Won is teal, Pipeline purple, and Missing Pipeline gray. The target markers are now solid black; the adjusted target is a separate dotted black line. The April closed-won and pipeline stack and later monthly shortfalls are readable against both target levels. The axis uses one shared numerical scale.

The [independent verifier](functional-verification.json) and [CSV comparison](cloud-data-comparison.json) pass. Each workbook exports twelve months and all nine monthly/YTD/target/shortfall measures: 108 metric cells per workbook, 216 total, including explicit null checks. Original locked Hyper inputs are the oracle; monthly targets are aggregated from the separate secondary datasource, rather than repeated once per opportunity. Closed-won YTD is 87,922.3918, target YTD is 123,000, and the 35,077.6082 shortfall adds 3,897.5120222222 to each of nine remaining monthly targets. This is full monthly data evidence, not a legend or button CSV.

Remaining visual differences are the compact colored-square text legend in place of the original five filled banners, full month names in place of abbreviations, lighter title typography, and a single-line attribution footer rather than three separate attribution columns. Plot padding and marker lengths also differ slightly. These differences do not hide data or change the target comparison. This is not a pixel-identical result.

Acceptance uses Cloud REST images/data plus the workbook contracts. No browser click or hover was executed or claimed. The author export changes only hidden worksheet window flags, as recorded in [export provenance](export-provenance.json).
