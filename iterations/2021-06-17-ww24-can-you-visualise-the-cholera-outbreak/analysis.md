# Analysis: 2021 Week 24 — Can you visualise the Cholera Outbreak?

- Article: <https://donnacoles.home.blog/2021/06/17/can-you-visualise-the-cholera-outbreak/>
- Challenge: <https://www.workout-wednesday.com/2021w24tab/> (Lorna Brown, 2021-06-15)
- Author workbook: `dashboards/2021_06_16_WW24_Cholera_Outbreak_Map/2021_06_16_WW24_Cholera_Outbreak_Map.twbx`
- Extract: `inputs/water_pumps.hyper` with three tables:
  - `water_pumps.csv` — 8 pumps (`PumpID`, `Location`, `PumpLon`, `PumpLat`)
  - `deaths_individual.csv` — 489 deaths (`DeathID`, `DeathLon`, `DeathLat`)
  - `deaths_aggregate.csv` — 250 death locations (`LocID`, `Deaths`, `DeathLon`, `DeathLat`)

## Business question

Recreate John Snow's 1854 cholera map: show where the deaths clustered, let the
user click a pump, and reveal that pump's average distance to every death plus
how many deaths fall inside that radius.

## The model

The author relates the three tables with 1=1 relationship calculations so every
pump sees every death. The calculations are:

```
Pump Location              = MAKEPOINT([PumpLat],[PumpLon])
Individual Death Location  = MAKEPOINT([DeathLat],[DeathLon])
Distance Pump to Death     = DISTANCE([Pump Location], [Individual Death Location],'m')
Avg Distance               = {FIXED [PumpID]: AVG([Distance Pump to Death])}
Number Deaths within Avg Distance = SUM(INT([Distance Pump to Death] <= [Avg Distance]))
```

`INT(bool)` is the article's shorthand for `IF ... THEN 1 ELSE 0 END`; summing it
at the PumpID level gives the count of deaths inside the average radius.

The selected pump drives four more fields:

```
Is Selected Pump?        = [PumpID]=[pSelectedPump]
Selected Pump Lat        = {FIXED: MIN(IIF([Is Selected Pump?],[PumpLat],NULL))}
Selected Pump Long       = {FIXED: MIN(IIF([Is Selected Pump?],[PumpLon],NULL))}
Selected Pump Location   = MAKEPOINT([Selected Pump Lat],[Selected Pump Long])
Selected Pump Avg Distance = {FIXED :SUM( IF [Is Selected Pump?] THEN [Avg Distance] END)}
Pump Buffer              = BUFFER([Selected Pump Location],[Selected Pump Avg Distance],'m')
```

## The map

Four native map layers, bottom to top:

1. **Deaths Density** — a Heatmap of `Individual Death Location` / `DeathID`,
   blue-teal, ~60% opacity.
2. **Pump Buffer** — the selected pump's average-distance circle, filled with
   the sheet background at very low opacity.
3. **Pumps** — red circles labelled with `PumpID` and a dark grey border.
4. **Deaths Agg** — black circles sized by the aggregated death count with a
   white border.

Background map: normal style, washout 0, streets/highways/routes on and every
other layer off, worksheet background `#f5f1f0`.

## The two bar charts

`Avg Distance to Pump` and `Total Deaths within Avg Distance` both put `PumpID`
on Rows and the measure on Columns, colour by `Is Selected Pump?` (black when
true, the background colour when false), show value labels and hide the measure
axis. Both rank the pumps 1-8 in data-source order.

## Interactivity

- One **change-parameter** action sets `pSelectedPump` from the clicked
  `PumpID`; it runs on select of the map and both bars.
- Three **filter** actions map `True` → `False`, one per sheet, so the click
  never leaves Tableau's selection highlight behind. Both `True` and `False` are
  bound on Detail so the mapping has something to act on.

## Numbers (independently recomputed with the WGS84 Vincenty formula)

| Pump | Location | Avg distance | Deaths within |
| --- | --- | --- | --- |
| 1 | Broad Street | 119 m | 259 |
| 2 | Carnaby Street | 248 m | 242 |
| 3 | Marlborough Mews | 297 m | 252 |
| 4 | Dean Street | 335 m | 258 |
| 5 | Rupert Street | 260 m | 228 |
| 6 | Bridle Street | 231 m | 251 |
| 7 | Fishborne Street | 421 m | 256 |
| 8 | Warwick Street | 278 m | 279 |

Every label matches the article's published screenshot exactly. The spherical
law of cosines is a metre low on pumps 2-6; Tableau's `DISTANCE(...,'m')` uses
the WGS84 Vincenty inverse, which is what the verifier implements.

## cwtwb notes

- The three-table Hyper relationship the author uses returns Cloud error 403132,
  so the builder materialises one flat `(pump x individual death)` Extract with
  the aggregated location columns joined on. `DISTANCE` is defined per pair
  anyway, so the flat grain is also the natural one.
- `configure_chart(mark_type="Map", map_layer_mode="native", map_layers=[...])`
  emits the `customization-axis='layer'` pane structure.
- `DISTANCE`, `BUFFER` and `MAKEPOINT` all pass the released SDK's formula
  validation.
- One parameter action per source sheet is the SDK's equivalent of the author's
  single all-sheets action (the SDK's `source_sheets` list is filter/highlight
  only).
