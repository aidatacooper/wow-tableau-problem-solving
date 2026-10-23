# Visual review

Reviewed original-author and replica Cloud PNGs in default and Tableau-filtered
states. Both show the participation ring/bars, five sentiment distributions and
seven ranked-choice columns. The replica retains the full business content.
The Tableau filter yields 100% Tableau, participation 10/10/36/40/2/2 percent,
and the leading topic cells agree with the original.

Accepted differences: palette, typography, panel proportions, question and
participation order, ring-label placement, visible axes and rank headers.
Equal-frequency topics may exchange rows under RANK_UNIQUE. CSV verification
requires the same category sets, unique ranks, descending counts and percentages,
so ties are not mistaken for missing categories. Whole-percent display rounding
can differ by one unit at exact half percentages.

Result: acceptable_delta. All 15 replica CSV exports across default, Tableau and
PBI states pass 339 percentage checks against the independent source-data oracle.
Original author sheets remain hidden and unmodified. Cloud REST states and
serialized action contracts were tested; browser clicks were not executed.
