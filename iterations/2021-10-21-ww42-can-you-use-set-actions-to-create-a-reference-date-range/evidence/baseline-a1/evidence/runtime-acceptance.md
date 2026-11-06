# Runtime acceptance — PENDING, parent-owned

No Tableau Desktop or Cloud process was opened by the implementation agent.
These are instructions and expected results, not evidence of execution.
Bind screenshots, exported data, Desktop verdict and all manual decisions to
the frozen SHA256 in handoff.json. Rebuilding invalidates that binding.

## Initial state

Open `outputs/replicated-workbook.twbx` and select `Reference Date Range`.
Desktop must print LOADED. UNKNOWN or FAIL is not acceptance.
Check all six dashboard views and the US filled map render.
Expected default October 2020–June 2021: 9 months, $493,007.986 selected sales,
$54,778.66511111111 average per selected month, −11.235169464% endpoint change.
Overall summary remains $2,297,200.8603 total / $47,858.35125625 per month.
Selected peak is December 2020. Top states are California ($99,025.3305,
20.085948567%), New York ($44,986.034, 9.124808376%), Washington ($38,240.64,
7.756596462%). Percentage denominator includes ALL selected states.

## Required event sequence

1. Drag/select the January, February and March 2019 marks on Trend. Confirm
   selection assigns these three months, replacing the prior nine. All selected
   views update; the gray full-history line and global summary remain intact.
   Expected selected total $68,851.7386, average $22,950.579533333334, change
   +113.085126596%, top states California/Washington/Georgia.
2. Click blank space to clear the mark selection. The set MUST retain Q1 2019;
   neither reset to the default nor empty the selected views. Repeat after
   another selection. This event is distinct from assigning an empty set.
3. Select June 2021 alone. Count = 1, selected total and monthly average both
   $52,981.7257, change = 0%; first and last month coincide. A zero-width band
   is legitimate; the single selected mark must remain discoverable.
4. Ctrl-select October 2020 and June 2021. Count = 2, total $112,669.4707,
   average $56,334.73535, change −11.235169464%, top states
   Indiana/California/New York. The band spans the endpoints but intervening
   months MUST NOT contribute to the selected summary, state table, donut or
   map. Confirm the purple line does not falsely imply those intervening
   points are selected. Clear selection and confirm this state persists.
5. Select all 48 monthly marks. Selected and global totals/averages agree;
   top states California/New York/Texas. Repeat a smaller selection to verify
   assignment replaces the prior state rather than adding to it.

## Rendering checks

- Full trend and selected trend share synchronized sales axes; label only the
  maximum selected monthly sales (all ties if present). Reference band follows
  min/max selected dates, never fixed constants.
- Donut angles use sales, colors distinguish rank 1/2/3 versus others, white
  circle forms the hole, center shows total selected sales. Wedges need not
  match the author's order. Table rank filter is after percent-of-total.
- Map colors and tooltips match per-state selected sales. Validate US state
  geocoding, including states that disappear for sparse selections.
- Summary dates are readable, no duplicate title/labels overflow, and no
  formula errors appear. Compare state/month exports to local-verification.json.

## Remaining gates

- Desktop artifact load: PENDING.
- Native UI interactions and Tableau/VizQL numeric output: PENDING.
- Visual/Cloud comparison and independent review: PENDING.
- Full Desktop corpus regression: PENDING.
- Shared catalogue integration and final PR: PENDING.
