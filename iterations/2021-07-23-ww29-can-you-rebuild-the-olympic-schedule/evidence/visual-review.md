# Visual review

Original author and replica Cloud dashboards show the same default selected
groups (Boxing, Gymnastics, Martial Arts), six sports, daily event positions,
final/non-final split and month/day headers. Compare outputs/cloud-author.png
and outputs/cloud-replica.png. Additional images cover +3 and -5 hour offsets.
Replica CSV verification covers 752 numerical checks over all three offsets,
including event counts, finals, other-sport totals, axis positions and selected
sport domains. Source case variants are collapsed case-insensitively in Tableau.

Accepted deltas: built-in diamonds/dots replace the author's medal/ring custom
shapes; Tokyo logo is text; selector shows headers and narrower colored bars;
font sizes, footer and spacing differ. Shape categories and positions preserve
final-versus-non-final meaning. Result: acceptable_delta.

Original author sheets are hidden, so no author CSV was exported or workbook
modified. Raw-data oracle checks replica CSV; original dashboard images provide
the visual reference. Set, parameter, hide/show, highlight and viz-in-tooltip
actions are verified as serialized contracts; browser clicks were not executed.
