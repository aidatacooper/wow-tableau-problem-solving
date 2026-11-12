# 2022-01-06-ww01-let-s-analyse-wildlife-strikes

## Problem

Sean Miller's 2022 Week 1 challenge asks for a one-screen view of the FAA
wildlife-strike database (1990–2021): which animal types are struck most often,
where strikes happen, and how the yearly volume has moved. The view is also an
interaction exercise: choosing a state must filter the animal-type bar and the
yearly trend and show the state in both chart titles; choosing an animal type
must filter the map and the trend and show the type in the trend title.

## Why the obvious approach fails

- A plain bar of `Species Type` has 23 members, which makes the long tail
  unreadable. The author keeps the ten most-struck types and groups the rest as
  `Other`, so the bar needs a top-10 set plus a display calculation.
- A state map cannot be built from `State Name` alone in the author's workbook:
  she relates the strike extract to a packaged spatial table on
  `State Name = NAME` and colours the polygons by incident count. The spatial
  table is part of the packaged extract (56 rows: 50 states, DC and five
  territories), and five territories are excluded from the map.
- 36,959 strike records have no state. They are not on the map, but they still
  belong in the totals and in the bar and trend. A naive inner join or a state
  filter would silently drop them, so the default state must include them and a
  separate "Unknown Location" indicator must report them.
- The titles are calculations, not static text: `in <state>` and
  `<species> Incidents Over Time`. Each title field has to be on the view or
  Tableau cannot resolve it.

## Tableau solution chain

```text
strike extract (251,818 rows: Incident Year, State Name, Species Type)
+ spatial extract (56 NAME/Geometry rows)
→ logical relationship on State Name = NAME
→ pSelectedState / pSelectedSpecies string parameters (default empty)
→ Wildlife Incidents = COUNT([Species Type])
→ Species Type Set = top 10 Species Type by COUNT, DESC
→ Species Type to Display = set member ? Species Type : 'Other'
→ Title: Selected State = "in " + parameter, or empty
→ Title: Selected Species = parameter, or empty
→ State Filter / Species Filter = parameter empty OR matching value
→ Bar (set / display, colour by set), Map (state polygons, red-gold),
  Area (continuous Year), Unknown (null State Name, square)
→ dashboard with two parameter actions (select state / select species)
→ observable result: default totals, filtered bar/trend/map and dynamic titles
```

## Required behavior

- Default: 251,818 incidents. The bar has 11 rows: the ten most-struck species
  in descending order plus `Other` = 4,308. The area covers 1990–2021 and the
  unknown indicator reports 36,959.
- Selecting a state (e.g. Alabama) filters the bar and the area to that state,
  keeps the unknown indicator at 36,959 (the author's state filter does not
  touch the unknown sheet), and both titles gain `in Alabama`.
- Selecting an animal type (e.g. Unknown Bird) filters the map, the area and the
  unknown indicator to that type and the area title gains the type name.
- Selecting both applies both filters (Alabama + Unknown Bird = 955).
- Clearing a selection restores the default totals and removes the title suffix.

## Allowed visual differences

- Fonts, padding, borders and exact legend placement may differ.
- The author's map uses the packaged `us_ak_hi_territories_shift_conformal`
  geometry with shifted Alaska/Hawaii. The replica uses Tableau's native state
  geographic role, so state shapes, Alaska/Hawaii placement and the map's
  colour domain (0–21,981 instead of 0–36,959, because the null-state group has
  no polygon) differ. The per-state numbers, red-gold palette, removed
  background layers and click behaviour are preserved.

## cwtwb baseline

Tested with the released `cwtwb` 0.29.0a2 (pin `cac8820f`).

- Supported and used: logical Hyper relationships (`set_hyper_connection` with
  `tables`/`relationships`), top-N sets, boolean calculated filters, continuous
  calculated dimensions, native maps with geographic roles, custom tooltips and
  rich titles, fixed-size dashboard layouts with floating zones and a colour
  legend, and parameter actions.
- Workaround 1 (map geometry): the SDK inspects the Hyper
  `TABLEAU.TABGEOGRAPHY` column as `string`. A geometry encoding referencing it
  renders no marks (Cloud exported an empty CSV for the map view). The replica
  keeps the author's relationship but renders the map through the native state
  geographic role. Recorded in `evidence/final-validation.json`.
- Workaround 2 (action filters): `initialize_dashboard_filter_action` only
  writes explicit member selections. The author's native action filters start
  in the "all members" state, which includes the 36,959 null-state records;
  initialising a native filter with the 51 named states would drop them from the
  default view. The replica therefore drives both cross-filters from the same
  two parameters that drive the titles, using `State Filter` and
  `Species Filter` calculations. Select/clear behaviour and the title updates
  match the author; the interaction is verifiable through REST parameter states.
