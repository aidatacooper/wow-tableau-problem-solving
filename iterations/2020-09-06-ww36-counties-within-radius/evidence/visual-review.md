# WW36 Cloud review

Result: **acceptable_delta** within Cloud REST image/data states and native artifact contracts. This is not a pixel match.

Replica TWBX SHA256: `6e987088f510a666965e6619044bef3c134ab5ec8cba48e39056a833d76cf381`.

All six PNGs were inspected in original/replica pairs: default 100 miles, 50 miles, and 250 miles. The title updates to the requested mileage, Selected County displays All, and the bed-percentile legend is present. Cases by County and Estimated Utilisation remain on the left; continental, Alaska and Hawaii filled county maps remain on the right. County labels, bars and hospital/ICU/ventilator labels are readable. Correct yellow-to-green variation is now present in all three maps, including Hawaii and Alaska; the earlier erroneous uniform green/rank100% output is not accepted evidence.

All **36 full worksheet CSVs** passed the independent locked-Hyper oracle: original and replica, six worksheets, three states. Input consists of 3,142 county records at the fixed August 26, 2020 snapshot. The checks cover every county, not only the top bars visible before scrolling:

| Worksheet | Complete verification scope per workbook/state |
| --- | --- |
| Cases Bar | 3,142 unique counties: exact case counts, All-set In membership, and global ascending bed percentile |
| Data | 3,142 counties x 2 diagnostic measures: source explicit rank and quick-calculation rank independently checked; replica explicit rank and raw hospital-bed count checked |
| Map - Main | All 3,108 continental county rows, raw case/resource counts, local map-partition percentile, and complete state-outline rows |
| Map - AL | All 29 Alaska county rows, raw counts, local percentile and state outline |
| Map - HI | All 5 Hawaii county rows, raw counts, local percentile and state outline |
| Utilisation Bar | All 3 resource sums: hospital beds 893,691; ICU beds 98,704; estimated ventilators 64,360 |

Total cases are 6,645,958 in each All-set state. The replica diagnostic Data sheet intentionally exports raw bed capacity alongside the explicit rank, whereas the original exports two independently checked percentile measures. It is not represented as a byte-identical diagnostic table. The caption Hospital Beds in the replica diagnostic CSV is the existing native Measure Names alias for the locked num_staffed_beds field; exact integer capacities are checked.

Native verification resolves the five actual rank calculation instances from the artifact, checks workbook-wide distinct SDK-generated contexts, exact Field addressing, column lineage, colour encodings/styles, dashboard legend identity and Measure Names membership. The source percentile uses maximum tied rank divided by non-null count minus one, matching Tableau RANK_PERCENTILE. For example Hawaii ranks are Kauai 0%, Maui 33.33%, Hawaii 66.67%, Honolulu 100%, and Kalawao null. Alaska Dillingham is 20% and Bethel 66.67%; all county values are checked independently.

**Interaction scope:** every captured state keeps native set membership All. The source explicitly ignores the radius when more than one county is selected, so unchanged county data across 50/100/250 miles is the correct source behavior. REST set-member mutation was not validated. The setMembership dropdown/card, initial full membership, FIXED selected coordinates, MAKEPOINT/DISTANCE, conditional radius filter and state-outline contracts are verified in the artifact. Independently derived single-Autauga-county great-circle scenarios at 0/50/100/250/500 miles produce 1/9/42/328/1,036 counties. These are raw-data/artifact checks, not claims of executed selections or exact ellipsoid agreement. No browser click, selection, scroll or hover was executed.

Visible differences:

- Replica map panels have thin frames and Mapbox/OSM attribution. Map and inset spacing/extent differs slightly; the source places its maps on an unframed white area.
- Header/control background coverage, heading weight, row/axis typography and footer/URL alignment differ. The replica legend caption is Percentile Beds rather than the longer source caption.
- Case axis displays full comma-separated values instead of K abbreviations. Both workbooks show a scrollable top section in the PNG; full county coverage is established by the worksheet CSVs, not by a claimed scroll interaction.
- Source credits and data/challenge links are preserved semantically, with explicit CWTWB replica attribution and different positioning.

Original comparison provenance binds the untouched author archive to its windows-only worksheet export copy. PNG and CSV hashes and the exact replica identity are validated in `cloud-verification.json`; numeric scope is recorded in `cloud-data-comparison.json` and `functional-verification.json`. Failed earlier captures and root-authorized SDK-generated diagnostic XML variants are analysis-only scratch evidence. The formal builder starts TWBEditor("") and calls public SDK APIs, including generic table_calc_context=True; it contains no experimental XML edits or author-workbook reads.
