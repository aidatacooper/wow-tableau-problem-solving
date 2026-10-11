# Visual review — WW16 Quick LoDs

## Scope

`outputs/cloud-author.png` and `outputs/cloud-replica.png` are the author's
published dashboard and the replica Viz sheet in the same default state.

## Result: acceptable_delta

The business answer is identical. The replica reproduces:

- the same three Category bands (Furniture, Office Supplies, Technology) with
  the same Sub-Categories in the same order (sorted by Sales descending within
  each Category);
- the same signed percent differences: Chairs ▲77%, Tables ▲12%, Bookcases
  ▼38%, Furnishings ▼51%, Storage ▲180%, Binders ▲155%, Appliances ▲35%,
  Paper ▼2%, Supplies ▼42%, Art ▼66%, Envelopes ▼79%, Labels ▼84%,
  Fasteners ▼96%, Phones ▲58%, Machines ▼9%, Accessories ▼20%, Copiers ▼28%;
- teal bars for the six above-average Sub-Categories (Chairs, Tables, Storage,
  Binders, Appliances, Phones) and grey bars for the rest;
- the flat grey full-height backdrop at each Category's average sales, with a
  vertical line at the benchmark.

The Cloud CSV exports agree row for row: for example Bookcases
`$185,500` / `$114,880` / ▼38%, Chairs `$185,500` / `$328,449` / ▲77%, and
Phones `$209,039` / `$330,007` / ▲58%.

## Allowed differences

- The author's export formats Sales as whole-dollar currency; the replica exports
  the raw values (`114,879.9963`).
- The replica's Category and Sub-Category header bands are plain text rather
  than the author's styled band; fonts and padding differ.
- The title and footer text are approximated.
