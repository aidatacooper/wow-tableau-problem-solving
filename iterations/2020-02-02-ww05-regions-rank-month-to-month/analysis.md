# Analysis

Article date: 2020-02-02; official challenge 2020 WW05 was published 2020-01-28
(WordPress post 3444). The chosen scope is the advanced variant: exactly one
worksheet, 700 x 350 dashboard, Gantt blocks and line marks; no Square or
Shape marks. Original files remain in ignored analysis scratch. The builder
starts from TWBEditor("") and reads only the extracted Hyper.

Sales are aggregated by month-of-year and region over all 9,994 extract rows;
the author has no year filter. Each month ranks four regions descending by
SUM(Sales), using competition ranks. The independent verifier computes the
48 ranks from facts, rather than trusting the source worksheet. The two
colored Region aliases separate line and block palettes. Table calculations
address regions and partition by month. Rank Line is Rank + Offset (0.4),
and Gantt length is MIN(0.9). Both axes are reversed and synchronized.

Exactly one field is put on the label shelf. Its nested calculation displays
ordinal rank on January, region on December, and blank otherwise. Complete
worksheet CSV must establish both numeric axes for all 48 region-months and
eight endpoint labels. Visual line order and gaps are reviewed from images;
CSV row order alone cannot establish them. Only the advanced author dashboard
is compared; its exploratory text and standard variants are outside scope.

Baseline SDK 0.27.1 / 12aae31 builds this contract without enhancement.
Cloud REST visual/data review passed with documented acceptable visual differences. No browser events are claimed.

Actual Cloud CSV exposed a partitioning error in the initial case builder:
Gantt Rank addressed the line alias while the block alias also partitioned
marks, yielding rank1 for every region. The corrected Gantt uses only the
block alias and addresses that alias; line and nested labels address the line
alias. Palette identities are explicitly Westgreen, Centralpurple,
Southlightblue and Eastpink. This is a case authoring correction, not an SDK
capability gap. Failed images/data are kept only in ignored scratch.

If the author advanced worksheet REST CSV is empty, it is excluded from data
proof. The analysis comparison additionally exports the author's original
Basic Data and Data Labels worksheets, which retain the complete48monthly
region ranks and endpoint labels. Replica advanced CSV must still verify
both numeric axes for all48region-months. Such a fallback is explicitly
reported and cannot certify author advanced axis positions from CSV alone;
paired advanced dashboard images establish the visual path/block contract.

Final style refinement uses the author's native Gantt size1.824088454246521 with mark scaling disabled. White bold labels are applied to the actual Line pane, with centered cell alignment, rather than the generic first pane. This uses existing public style APIs and preserves rank calculations.

The Cloud comparison additionally exposed mark stacking: a first Gantt pane hides later line segments when blocks are widened. The final pane order follows the author: Line first, Gantt second. The verifier checks this order and applies centered white labels to Line id1. Earlier occluded captures are archived in ignored scratch.

Pane ordering alone did not change native folded-axis paint order. The final source-consistent axis style additionally sets render-fold-reversed=true; final Cloud confirms complete lines drawn above blocks.
