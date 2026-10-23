# Can you make stacked bar charts easier to compare?

The business question is how to compare one selected product category across two stacked bars without doing mental subtraction from different baselines. Group states A–M and N–Z by first letter, then move the clicked category to the bottom of both stacks. Total height and category sales must not change.

The source article was published 2021-10-08; the official W40 challenge by Candra McRae was published 2021-10-06 (WP post 6031). Original Donna Coles workbook was inspected only during analysis. Its extract contains 9994 rows and only State, Category and Sales; the builder reads the locked Hyper, never the author workbook.

## Author method and reconstruction

ASCII(UPPER(LEFT(State,1))) <= 77 produces A-M; all other states produce N-Z. The native parameter caption is misspelled `pSelectedCategpry` in the published workbook (the article spells it correctly). We retain the published caption for identical Cloud state queries; its default is Office Supplies.

`Sort = IF [pSelectedCategpry]=[Category] THEN 0 ELSE 1 END` drives a **descending computed sort by SUM(Sort)** on the Category colour encoding. The selected category has zero and is drawn at the bottom. Nonselected categories are ordered by their row counts, not by sales or alphabetically. Counts are Furniture 2121, Office Supplies 6026, Technology 1847. Top-to-bottom order is Furniture/Technology/Office Supplies by default, Office Supplies/Technology/Furniture for Furniture selection, and Office Supplies/Furniture/Technology for Technology selection.

Two native stacked bars use State Group on Columns and SUM(Sales) on Rows. Furniture is #1170aa, Office Supplies #fc7d0b, Technology #a3acb9. White labels show sales in rounded $K. A FIXED State Group LoD provides native per-cell total reference labels above the bars. Tooltip shows group, category, category sales and group total. The chart uses the original 400x800 dashboard size, title banner and challenge credits; the replica footer credits cwtwb.

The dashboard parameter action sets ATTR(Category) on select, retaining the last value when cleared. A second auto-clear filter action maps the True field to False on the same sheet, with show-all on clearing. These are public SDK native actions, not scripted image substitutions. Serialized action validation and REST parameter states are the intended verification scope; they do not prove a browser click was exercised.

## Independent oracle

The verifier reads raw Hyper rows into Python, chooses groups by alphabet membership rather than ASCII, accumulates six category sums, and independently derives totals and the three category orders. Expected cells:

| Group | Furniture | Office Supplies | Technology |
|---|---:|---:|---:|
| A-M | 352580.9045 | 381184.1580 | 394487.3420 |
| N-Z | 389418.8908 | 337862.8740 | 441666.6910 |

`outputs/expected-sales.csv` provides precise comparison values. The verifier also checks native computed-sort, reference-line, two action contracts, layout, colours, and exact packaged extract hash. No author-derived values or XML are read by the builder.

## SDK baseline and remaining gates

Public cwtwb 0.29.0a1 @23b1df0 expresses the entire required chain. No SDK workaround or capability gap is claimed. The public SDK omits `clear-option` for keep-current (Tableau default), rather than serializing the author's explicit do-nothing value.

The final artifact passes Desktop LOADED and actual Cloud rendering/CSV comparison. Metadata is replicated/verified/acceptable_delta. The selected category is at the bottom, totals remain above each stack, and sales are invariant across all three states. Running validate_iteration rebuilds with random GUIDs; use isolated rebuild validation after final capture to preserve the evidence hash binding.


## Cloud acceptance and title correction

The first full three-state Cloud capture confirmed all six category cells, totals, exact dynamic Sort values and selected-category baseline, but visual inspection found the worksheet title hidden. That omitted the category colour key and the selection instruction, so it was treated as a usability defect rather than an acceptable styling difference. The builder now displays the native rich worksheet title: Sales by Category, Select a category to re-order the stack, and the three category names in their matching colours. Static verification asserts the title and its visible dashboard zone. The revised workbook was recaptured in all three states and rebound to passing Desktop and Cloud evidence; all 90 data checks pass.

The original author exposes only the dashboard on Cloud, so the author workbook remains unmodified and its original three screenshots are the visual reference. `capture_replica_data.py` exports the replica Chart in the same three parameter states. `verify_cloud_data.py` compares all 18 exported group/category cells with independent raw-extract arithmetic, with $500 tolerance only for whole-$K display rounding. Sort values and True/False fields compare exactly; stack sequence is checked in each group. It verifies all six image hashes and CSV/state/artifact bindings. No browser click execution is claimed.
