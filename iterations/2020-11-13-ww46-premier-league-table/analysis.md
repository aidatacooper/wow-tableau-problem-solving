# Premier League standings and the last five games

The article was published on 13 November 2020. Official WordPress challenge
post 4068 is dated 10 November, identifying 2020 WW46. The original dashboard
is an 800 × 735 table with four statistics, a stacked total-points bar and five
chronological result circles. It contains no dashboard actions. Each circle's
tooltip shows date, opponent, team-relative score and result.

Three packaged extracts preserve the author's data model: 156 pivoted team-game
facts, plus two independent copies of the 78 original fixtures. The pivoted
extract contains Date, full-time home/away goals, full-time result and the
pivoted home/away/team fields. Team and Home or Away are explicit public
calculated aliases. Results are W/T/L relative to each team; points are 3/1/0.
Matches, wins, ties, losses and total points use team-level FIXED calculations.
`COUNT(Date)` replaces the author's internal logical-table count expression:
all 156 dates are non-null, so both count exactly one team-game per record.

The source's opponent lookup uses two native blends rather than a physical
join. Home and Away sources expose BLEND Team as their respective team name;
the main source exposes the pivoted team. Both BLEND Team and Date link the
independent sources. ATTR(AwayTeam) from Home supplies home-game opponents,
and ATTR(HomeTeam) from Away supplies away-game opponents. An aggregate string
Opposition selects the available value. Every team-date uniquely identifies
one fixture and every fixture has exactly two mirrored team facts. The oracle
checks all opponents, home/away score orientation and mirrored results directly
against original fixture facts, independently of Tableau blends.

The last-five chart uses INDEX(), SIZE(), a late table-calculation filter
`Index > Size - 5`, and plot index `Index - (Size - 5)`. All non-Team detail
dimensions are addressed within each team, with chronological Date order.
Each of the twenty teams has seven or eight fixtures and five visible result
marks numbered 1–5. Team sorting is computed from points before table
calculations, matching all three dashboard worksheets. Three result palettes
preserve dark-green/pale-red stacked points and green/red/grey circle results.

The released SDK baseline `eb1380d5da9c1b1bf1b306128cb8397150ba1a53`
fails a data-free synthetic native-blend request: importing ATTR(Opponent)
incorrectly serializes ATTRIBUTE(), which formula validation rejects.
The released code was checked using `git archive` in an independent subprocess
after the main case environment became editable. This is a reproducible blocked
baseline, not a passed released-SDK run. Its string aggregate proxy also must
retain nominal field semantics. The coordinator owns the generic SDK fix.

The builder reads extracted Hyper files and public SDK APIs only. Source export
preparation removes hidden attributes from existing worksheet windows; its
canonical XML and every other archive member are hash-verified unchanged.
REST states are the complete standings plus Arsenal, Liverpool and Chelsea
ordinary Team filters. All Table, Bar and Chart CSVs and paired dashboard images
will be reviewed. No tooltip hover, browser click or user interaction execution
is claimed; tooltip data and native blend/calculation contracts are validated
through full exports and artifact inspection. Final Cloud acceptance is acceptable_delta at artifact 939c2210723255e049c9727caeca18af831c108d15a7f0ed4fd336e765f393d9: all24CSV and eight paired dashboard images pass full independent review; see evidence/visual-review.md.

The first complete Cloud capture failed visual and Chart CSV acceptance because
the case omitted the public layered-pane axis bindings. This was a case API-use
error, not another SDK gap. The original d8c images and all CSVs are preserved
in analysis scratch. Explicit Points/Total Points and Index To Plot bindings
now accompany strengthened native assertions. A later complete capture exposed default Month detail; public EXACTDATE(Date) restored all100 chronological results and actual opponents. The final fresh capture passes all full-data contracts. All three worksheets use the same computed Points sort to align
standings, stacked totals and chronological results, including tied teams.
CSV record order is not assumed to be display order.
