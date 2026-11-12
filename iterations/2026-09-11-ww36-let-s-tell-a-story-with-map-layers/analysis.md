# 2026-09-11-ww36-let-s-tell-a-story-with-map-layers

## Problem

Recreate John Snow's 1854 cholera map as a four-step story whose parameter switches visible marks between homes/buildings, deaths, sewerage vents, and pumps.

## Why the obvious approach fails

Four independent maps lose the narrative and require users to manage multiple views. The author keeps one map and controls mark layers with a pScroll integer parameter and `MAKEPOINT` calculations.

## Tableau solution chain

```text
Deaths by Building (independent latitude/longitude extract)
→ pScroll values 1..4
→ conditional spatial calculations for each story layer
→ layered map with parameter control
```

The author also uses separate Sewergrate Locations and Pump Locations extracts. The released SDK cannot model the three-source map-layer arrangement in one builder call, so this replica uses the locked Deaths extract for the shared spatial contract and records the source limitation.

## Required behavior

- pScroll aliases 1–4 are visible and select a story step.
- Only the matching conditional spatial layer is non-null for each step.
- The map remains a single layered worksheet with ID/deaths tooltips.

## Allowed visual differences

Background map, custom icon shapes, story text zones, and the exact point palette may differ.

## cwtwb baseline

Conditional spatial calculations, parameter domain, and layered map are supported. Separate-source marks and dynamic zone visibility are not represented; this is a documented partial workaround. Cloud/browser execution was not performed.
