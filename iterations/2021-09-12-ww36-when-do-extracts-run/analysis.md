# WW36: When do extracts run during the day?

Article 2021-09-12; official challenge 2021-09-07
(https://www.workout-wednesday.com/2021w36/). Guest challenge by Donna Coles.
The independent workbook starts at `TWBEditor("")` and reads only the extracted
Hyper file under `inputs/`.

## Business question

A Tableau Server administrator wants to see *when* extract refresh tasks ran
during the day, over a rolling window of days, instead of horizontally scrolling
the built-in "Background Tasks for Extracts" admin view. Each row is one
background task (`Id`); the task is created, may queue, then starts, then
completes. Two durations matter:

* **waiting time** — created → started (still waiting means "not started yet");
* **processing time** — started → completed (not completed means "still running").

Because the data is static, "now" is a parameter (`Now`, default
`05 Feb 2021 16:30`), and the rolling window is a parameter
(`pDaysToShow`, integer 1–10, default 5, displayed as "5 days").

## Data

One packaged Hyper extract, `Extract.Extract`, 34,202 rows, `created_at` from
2021-01-11 to 2021-02-05. Four sites: Site 13 (32,330 rows), Site 9 (1,583),
Site 7 (263), Site 11 (26). Columns used: `id`, `title`, `Site`, `created_at`,
`started_at`, `completed_at`, `finish_code`, `progress`, `notes`. The author's
source is an Excel sheet joined to the `_sites` table on a real Tableau Server;
the sample is anonymised but keeps the same shape, and the workbook was shipped
with the extract already built.

`started_at` is never null in this extract; `completed_at` is null for three
tasks, which is what makes the `Now` parameter observable. `progress` only ever
holds 0 or 100, as the article warns.

## Author's calculations (observed during analysis, rebuilt independently)

| Field | Author definition |
| --- | --- |
| Extract Status | `IF [Finish Code] = 1 AND [Progress] <> 100 THEN 'In Progress' ELSEIF [Finish Code] = 0 AND NOT [Progress] = 1 THEN 'Success' ELSE 'Failed' END` |
| Waiting Time | `DATEDIFF('second',[created_at], IF ISNULL([started_at]) THEN [Now] ELSE [started_at] END)/86400` |
| Processing Time | `DATEDIFF('second',[started_at], IF ISNULL([completed_at]) THEN [Now] ELSE [completed_at] END)/86400` |
| Created At Baseline | `DATEADD('day', DATEDIFF('day',[created_at], #2021-01-01#), [created_at])` |
| Started At Baseline | `DATEADD('day', DATEDIFF('day',[started_at], #2021-01-01#), [started_at])` |
| Over Wait Time Threshold | `[Waiting Time] > 0.007` (10 minutes as a fraction of a day) |
| Filter: Days to Show | `DATETRUNC('day',[created_at]) >= DATEADD('day',([pDaysToShow]-1)*-1, DATETRUNC('day',[Now]))` |
| Key Label | `IF [Site] = 'Site 9' THEN 'Waiting' ELSE 'Processing' END` |

Two of the author's copies are dead weight in the shipped file
(`Created At Baseline (copy)` uses `TODAY()`, `Waiting Time (copy)` is a
non-normalised subtraction). They are not reproduced; the live fields above are.

## Views

* **Gantt** — rows `Site / Title / DAY(Created At)`; columns carry *both*
  baselined datetime axes, folded and synchronised. Pane 1 is a thin, 50 %
  transparent `GanttBar` starting at `Created At Baseline` with size
  `AVG(Waiting Time)` coloured by `Over Wait Time Threshold`; pane 2 is the
  thicker `GanttBar` starting at `Started At Baseline` with size
  `AVG(Processing Time)` coloured by `Extract Status`. A filled reference band
  marks core working hours 08:00–17:00. Filters: `Filter: Days to Show = true`
  and `Site = "Site 9"` (the author's published view is a single site).
* **Key** — a two-bar legend built from the data itself: `Key Label` on
  columns, `MIN(1)` on columns, `Site` on both colour and size, filtered to
  Sites 7 and 9, manually sorted `Waiting` before `Processing`, fixed 0–1 axis.
* **Data** — the author's supporting crosstab (`Id / Created At / Created At
  Baseline / Started At / Started At Baseline / Completed At` by
  `Measure Names` of `Waiting Time`/`Processing Time`). Shipped hidden.

Dashboard `When Do Extracts Run During The Day?` is 1000×800: title and subtitle,
a FILTERS row with the `pDaysToShow` slider ("Show data for last...") and a
`Site` check-dropdown, the KEY strip with the Key sheet and both native colour
legends, the Gantt sheet, and the CHALLENGE BY / #WOW2021 WEEK 36 footer.

## Colour assignments

`Extract Status`: In Progress `#4e79a7`, Success `#bab0ac`, Failed `#e15759`.
`Over Wait Time Threshold`: false `#bab0ac`, true `#e15759`.
`Site`: Site 13 `#76b7b2`, Site 7 `#bab0ac`, Site 11 `#e15759`,
Site 9 `#e15759`. Working-hours band `#f3faf9`.

## Build notes and traps

1. `CW` / `cwtwb` 0.29.0a1 (commit `23b1df0`) built this without a workaround.
2. A calculated date used as a *caption* on a shelf (for example
   `EXACTDATE(Created At Baseline)`) resolves to an unresolved table-calculation
   ordering field and renders blank in Tableau Cloud. Every nested dependency
   here is written against the real `created_at` / `started_at` / `completed_at`
   instances, and the built file contains no `table-calc` or `ordering-field`
   metadata at all.
3. The layered pane axis must also appear on the shelf expression, not only in
   the `<style>` axis rule. Both `EXACTDATE(...)` instances are on the columns
   shelf, so the folded dual axis resolves.
4. `cwtwb` auto-registers an unknown *caption* when a field is first used on a
   shelf, guessing a string type for a datetime. The replica therefore declares
   thin pass-through calculated aliases (`Created At`, `Started At`,
   `Completed At`, `Id`, `Title`, `Notes`, `Finish Code`) that simply return the
   physical column, and every shelf, encoding and tooltip uses those aliases.
   They carry no table calculations, so the guard in note 2 still holds.
5. The 08:00-17:00 reference band is declared with two datetime fields
   (`Working Hours Start` / `Working Hours End`) and a min/max band, so the
   endpoints stay real datetime instants. A bare numeric constant on a datetime
   axis is read as an 1899 serial and would draw the band in the wrong place.
6. The template datasource is reused for the locked Hyper file, so the packaged
   workbook contains exactly one data source and only the Hyper file. The
   datasource caption keeps the template default
   (`Sample _ Superstore (Simple)`); `cwtwb` exposes no public caption setter,
   so this is a recorded cosmetic delta, not a functional one.
7. The author's manual sort dictionary on `Key Label` is reproduced with a
   declarative descending sort by `Key Order` (1 for Site 9 / Waiting, 0
   otherwise), which yields the same rendered order without hand-built XML.

## Acceptance

`verify_replication.py` recomputes the status split, both durations, the
same-day normalisation, the >10-minute flag and four `pDaysToShow` windows
straight from the locked Hyper extract, then checks the declared workbook
contract (formulas, shelves, pane encodings, folded axis, reference band,
filters, key legend, dashboard controls, hidden Data sheet, packaged extract
hash). Visual comparison against the author's render is left to the root Cloud
gate.
