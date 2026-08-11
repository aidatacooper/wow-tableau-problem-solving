# 2019-10-25-ww43-las-vegas-casinos

## Problem

Find casinos within a chosen distance of a selected Las Vegas casino.

## Why the obvious approach fails

A map without a selected origin and radius cannot answer proximity.

## Tableau solution chain

```text
Casino coordinates → selected-casino and miles parameters → distance/range calculations → map and detail table → proximity result.
```

## Required behavior

- Changing the radius changes the in-range classification.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports parameters, calculations, map-like circle encodings, Hyper input, and dashboard layout.
