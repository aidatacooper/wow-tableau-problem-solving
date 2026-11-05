# 2021 Week 29 — Can you rebuild the Olympic Schedule?

- Article: <https://donnacoles.home.blog/2021/07/23/can-you-rebuild-the-olympic-schedule/>
- Challenge: <https://www.workout-wednesday.com/2021w29tab/> (2021-07-20)
- Author workbook: `2021_07_21_WW29_Olympic_Schedule.twbx` (Tableau Public)
- Case ID: `wow-2021-ww29-can-you-rebuild-the-olympic-schedule`

## Business question

The challenge was a joint #WOW / #PreppinData week: rebuild Lorna Brown's
Olympic schedule. Given the Tokyo 2020 event list (sport group, sport, event
name, UK date-time), show **which sports run on which day** in a compact
calendar, mark the days that carry a **final / gold-medal** event, and let the
viewer **add and remove sports** from the calendar. Hovering a mark should show
the individual events for that sport-day plus how many events the *other*
sports contribute that day, and a parameter should shift every time by whole
hours so the schedule can be read in a different timezone.

So there are three separate things to get right:

1. a *calendar* layout — month and day across, sport group and sport down;
2. a *shape* language — finals versus qualifying events;
3. *interactivity* — a set-driven sport selector, a hover parameter and a
   timezone offset.

## Data

`inputs/Event Schedule (2021_07_21_WW29_Olympic Event Schedule).hyper`, one
extract table (`Extract"."Extract`) with 1 894 rows and five columns:

| column | type | notes |
| --- | --- | --- |
| `Sport Group` | text | 36 distinct values |
| `Events Split` | text | the event name (the author renamed it "Event") |
| `UK Date Time` | timestamp | the event start, UK time |
| `Date` | date | calendar date of the event |
| `Sport` | text | 51 distinct values |

Two data quirks matter for the verifier's expectations:

- The extract carries **case-variant duplicates** — `Diving`/`diving`,
  `Football`/`football`, `Rugby`/`rugby`, `Volleyball`/`volleyball`. The raw
  distinct counts are therefore 36 sport groups / 51 sports rather than the
  34 / 48 the article's cleaned labels suggest. The reproduction keeps the data
  as published and asserts the raw counts.
- 87 rows are `Victory Ceremony` events. The author excludes them from the
  schedule (they are not competitions) but still counts them in the
  `Is Victory Ceremony?` dimension that the FIXED LoDs group by.

19 distinct event dates (2021-07-21 → 2021-08-08), 353 rows whose event name
contains `Gold Medal` or ` Final`.

## Calculation chain (author formulas, verified against the workbook)

```
Date Time Adjust            DATEADD('hour', [pTimeAdjust], [UK Date Time])
Day of Adjusted Date        DATE(DATETRUNC('day',[Date Time Adjust]))
Is Victory Ceremony?        CONTAINS([Event],'Victory Ceremony')
Is Final?                   CONTAINS([Event],'Gold Medal') OR CONTAINS([Event],' Final')
# Events Per Day            {FIXED [Day of Adjusted Date], [Is Victory Ceremony?] : COUNT([Event])}
#Events by Sport Per Day    {FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]: COUNT([Event])}
#Event Finals by Sport ...  {FIXED [Day of Adjusted Date], [Is Victory Ceremony?],[Sport]: SUM(IIF([Is Final?],1,0))}
#Events Per Day of Other…   SUM([# Events Per Day]) - SUM([#Events by Sport Per Day])
Excluded Sport              [Sport]=[pSportToExclude]
Dummy                       'Dummy'
Event Medal Symbol          IF [Is Final?] THEN '⫱' ELSE '' END
```

The horizontal offset is the clever part:

```
X-Axis = IF [#Event Finals by Sport Per Day] = 0 THEN 5
         ELSEIF [#Event Finals by Sport Per Day] - [#Events by Sport Per Day] = 0 THEN 5
         ELSEIF [Is Final?] THEN 7
         ELSE 3
         END
```

With the axis fixed at 0–10, a sport-day with only qualifying events puts one
mark in the middle (5); a sport-day with a mix puts the qualifying mark at 3 and
the final at 7, side by side inside the same day cell; a sport-day that is
*only* finals stays centred (5). The reproduction keeps the same chain and the
same 0–10 fixed axis.

Parameters (author order): `pSportToExclude` (string, default empty) and
`pTimeAdjust` (integer, 0, range −12…12, step 1 — the step is what makes
Tableau render the prev/next buttons next to the slider).

## Views

| sheet | role | build |
| --- | --- | --- |
| `Sport Selector` | dashboard | `MIN(1)` bars, one per sport group, coloured by `Sport Group Set` membership, label = sport group, `Dummy` on Detail so the highlight action has a brush level |
| `Date Chart` | dashboard | Columns = `MONTH(Date Time Adjust)` / `DAY(Date Time Adjust)` / `X-Axis`; Rows = `Sport Group` / `Sport` / `MIN(1)`; Shape marks by `Is Final?`, size by `Is Final?`; filters = set is True, `Is Victory Ceremony?` is False |
| `VIT-Event Listing` | viz-in-tooltip | Rows = month/day/sport group/sport/medal symbol/`Date Time Adjust`, label = `Event`; filtered by `Sport` + `Day of Adjusted Date` |
| `VIT-Other Event Bar` | viz-in-tooltip | Rows = `Day of Adjusted Date` / `Sport Group`, Columns = `COUNT(Event)`, colour by `Is Final?`; filtered by `Day of Adjusted Date` and `Excluded Sport` is False |

`MIN(1)` on Rows is not decorative: it gives each row a vertical range so the
shape marks are not squeezed onto the cell border, and it is what makes the
3/7 offsets visible.

## Interactions

| interaction | author | reproduction |
| --- | --- | --- |
| Add sport to schedule | set action, run on menu, `add` | `add_dashboard_set_action(..., event_type="on-menu", selection_mode="add", clear_option="do-nothing")` |
| Remove sport | set action, run on menu, `remove` | same with `selection_mode="remove"` |
| Set sport to exclude | parameter action on hover, attr of `Sport` → `pSportToExclude`, clear to empty string | `add_dashboard_action(action_type="parameter", event_type="on-hover", clear_behavior="set-value", clear_value="s:LROOT:")` |
| Stop the selector highlighting the schedule | highlight action on the selector with `Dummy` as the brush field, `Date Chart` excluded | highlight action with `fields=["Dummy"]` |
| Hide / show the selector | 2021.2 hide/show button on the selector container | `add_dashboard_toggle_button(target_worksheets=["Sport Selector"])` |

The viz-in-tooltip filter hand-off is the one place where the reproduction has
to be explicit: `configure_custom_tooltip` writes the `<Sheet name=… filter=…>`
run text *and* the matching `Tooltip (…, …)` datasource group and worksheet
filter, so the embedded sheets actually receive the hovered sport and day.

## Verification

`verify_replication.py` recomputes everything from the locked extract:

- the five row/domain counts and the victory/final row counts;
- for three timezone offsets (0, +3, −5) the full mark set: per sport-day the
  event count, final count, other-sport count and the `X-Axis` value, so the
  FIXED LoDs and the 3/5/7 rule are checked against an independent
  implementation rather than against the workbook;
- that at least 108 sport-days straddle both offsets (`paired_cells`), which is
  what the shape language exists for;
- that shifting the parameter actually moves the marks (`adjust_0` differs from
  `adjust_3`), which is the observable effect of `Date Time Adjust`;
- the native contracts: formulas, parameter domains, shelf nesting, Shape mark,
  shape palette, the two filters, the fixed 0–10 axis, the set membership and
  the five interactions.

Acceptance IDs: `ww29-schedule-calcs`, `ww29-schedule-view`,
`ww29-selector-set`, `ww29-viz-in-tooltip`, `ww29-dashboard-actions`,
`ww29-time-adjust`.

## cwtwb notes

The released SDK (0.29.0a1 / `23b1df0`) covers every primitive this case needs:
layered charts with a fixed axis range, custom tooltips that embed other
sheets, native set actions, native parameter actions, highlight actions and the
hide/show button. Two behaviours are worth recording for future cases:

- **Bare date field names are auto-wrapped.** `default_view_expression` turns a
  date-like bare name into `MONTH(...)`. Passing `"[Day of Adjusted Date]"` (a
  bracketed reference) keeps the discrete day binding; without it the tooltip
  filters and the day column collapse to one mark per month. This is expected
  SDK behaviour, not a defect, so the case records it as a workaround rather
  than a capability gap.
- **The highlight action excludes the sheets it is *not* given.** The author
  workbook's brush lists `exclude="Date Chart"`, which the SDK produces when the
  action is declared on the selector itself. Declaring the schedule as the
  target instead inverts the meaning.

## Result

Functional status `replicated`: the calendar, the final/non-final shape
language, the other-sports comparison, the timezone offset and all five
interactions are rebuilt with public APIs and checked against an independent
oracle. Visual status is judged from the Cloud captures.
