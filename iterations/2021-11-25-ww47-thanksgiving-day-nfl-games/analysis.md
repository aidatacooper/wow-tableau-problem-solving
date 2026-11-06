# NFL Thanksgiving analysis

Identity is wow-2021-ww47-thanksgiving-day-nfl-games. case_intake incorrectly selects the first historical 2019 rugby example. Override confirmed against the article's final published-viz link, 2021_11_24_WW47_NFL_Games, and official challenge record dated 2021-11-24 at https://www.workout-wednesday.com/2021w47tab/ . Article publication is 2021-11-25.

Business question: compare Thanksgiving home-team outcomes over time, preserving the date, home team and visiting team as game identity. Scores determine home win +1, loss -1, tie 0; dot colour represents home minus visiting score. Official requirements also include lollipop stems, a cumulative area chart and total games, W-L-T and wins / games, all in one sheet. Dallas missing years 1975 and 1977 must keep cumulative totals flat, without counting absent games as ties. The official requirement includes ties even though the article's record formula omits ties.

Analysis inspected only the correct packaged archive: Data and Viz worksheets, five raw fields, no dashboard actions. No required custom selection action is stated; native game selection and tooltip behaviour need live verification. Data extracted once by prepare_case; source-lock preserves archive/data hashes. Builder starts blank and uses public SDK calls and extracted Hyper only.

## Current implementation

One worksheet contains the grey Bar stems, score-difference Circle marks and cumulative Area pane. All three axes are explicit row-shelf entries. The duplicate Result Circle has y-index 1. configure_layered_chart(fold_axes=False) followed by public configure_worksheet_style(axis_style.encodings) folds only duplicate Result class 1, synchronized, while Cumulative Differential stays separate. No private SDK access or XML mutation is used.

The prior claim that published a2 could not compose this worksheet was incorrect. The probes tested global fold_axes and an incomplete extra-axis shelf, not the full public API. Independent review identified selective axis_style encodings; the corrected synthetic probe now proves this supported path. Prior two-sheet evidence is archived under evidence/prior-two-sheet-* solely as history, not current acceptance. No reusable SDK blocker remains.

Each actual game retains date/home/opponent identity, home score minus away score, Win/Loss/Tie result, and tooltip prose with highest score first. Both game panes explicitly query Game Tooltip; custom tooltip tokens use ATTR(Game Tooltip), matching their query encoding. Area tooltip fields likewise bind to queried instances or existing shelves.

Team total, W-L-T including ties, and wins/games headers are materialized from extracted raw Hyper. Cumulative wins minus losses is materialized in chronological order for each home team. Dallas's absent 1975 and 1977 years have NULL scores and no game identity, carry previous cumulative values, and do not increase games or ties. Generated chart-data Hyper is packaged in the workbook. Native mark selection does not recalculate all-time summary values; the article and challenge require no custom selection action.

The independent oracle compares every packaged game/year and summary against raw data. The verifier evaluates emitted IF/subtraction expressions using SQLite, tests shuffled synthetic multi-team games with ties and missing years through the production transform, and verifies the complete emitted shelf/encoding/reference/dependency closure. Twenty-six mutation controls cover numerical errors, missing queries/declarations, incorrect axis folding, mark types and order. This is an offline subset evaluator, not Tableau runtime execution.

Functional status stays partial and visual status not_evaluated pending parent Desktop, corpus, live tooltips/selection and rendered review. Parent's earlier Desktop LOADED belongs exclusively to old workbook SHA 5d1254219800580ea6c82feb0124e7fd3ab37e87c29b2efa76af8791996e9d78, with no visual approval. It does not apply to this rebuilt artifact.

## Runtime-driven sizing correction

Parent evidence for e949cce9c114576160e020165575d70170cc09127788afce946e6041334d283e confirms Desktop LOADED and successful default Cloud capture, but the image fails functional readability: date-bin-width Bar blocks obscure virtually pixel-sized Circle marks. These observations supersede the earlier static-only optimism. That workbook is preserved directly under outputs/e949-runtime-workbook.twbx; original Cloud files and a hash manifest are copied into evidence/runtime-e949 before rebuilding. Desktop LOADED is parent-reported, not independently rerun here.

Analysis-only targeted inspection of the author pane configuration shows native marks-scaling-off for both lollipop layers, stem size approximately 0.01 and Circle size approximately 1.42. These are native mark-size units, not direct pixel widths. Builder uses public pane mark_sizing_off=True and mark_style size 0.01/1.42. The original automatic scaling on continuous dates defeated the tiny Bar size setting; Circle size 0.12 was also much too small. No author XML is read or copied by the builder.

Result default-format now includes Tableau's required leading asterisk: *"Win";"Loss";"Tie". The duplicate right-hand Result axis is hidden. A plain-language dashboard key provides the numerical semantics as well. Circle color uses a zero-centered orange-blue diverging palette, and a native Score Difference legend is bound to Circle pane 2 and the exact SUM(Score Difference) query reference. One worksheet still contains all three panes.

The strengthened offline contract requires scaling-off on both marks, bounded native size values and sufficient dot/stem contrast, no accidental size field encoding, native custom number format, hidden secondary axis, a zero-centered palette, and a visible correctly bound legend. Seven additional mutations target the runtime failure causes (26 total). These checks prevent regression of the authored configuration; actual visual readability must still be demonstrated by the parent's repeat Desktop/Cloud capture for the new SHA. No visual approval is claimed.
