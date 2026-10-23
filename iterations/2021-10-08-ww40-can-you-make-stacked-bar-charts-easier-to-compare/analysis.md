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

Desktop and Cloud are deliberately pending with the coordinator. Until current artifacts pass LOADED and actual Cloud rendering/CSV comparison, metadata remains partial/pending/not_evaluated. Visual acceptance must inspect selected category at the bottom, total labels above each stack and invariant sales across all three states. Running validate_iteration rebuilds with random GUIDs; capture and bind final hashes after the last rebuild.
