# Analysis: 2021 Week 25 — Can You Make Spine Charts?

- Article: <https://donnacoles.home.blog/2021/06/25/can-you-make-spine-charts/>
- Challenge: <https://www.workout-wednesday.com/2021w25tab/> (Sean Miller,
  resurrecting Emma Whyte's 2017 challenge; 2021-06-23)
- Author workbook: `dashboards/2021_06_23_WW25_Spine_Chart/2021_06_23_WW25_Spine_Chart.twbx`
- Extract: `inputs/TEMP_11t94k216ehodl0zrdp701x51e14.hyper`
  (`Question Number`, `Question Text`, `University`, `Sample Size`, `% Agree`;
  10,095 rows = 27 questions x 374 universities)

> Note: the article links to two published workbooks. The 2021 WW25 rebuild
> ("associated to this challenge") is `2021_06_23_WW25_Spine_Chart`; the
> `14062017-WW24-SpineCharts` workbook is the 2017 original the article
> references separately. This case replicates the 2021 rebuild.

## Business question

For a chosen university, show each question's average agreement alongside the
overall average for that question, with the spread of universities behind the
overall average (min/max and the inter-quartile range) drawn as reference bands.
The challenge forbids table calcs and LoDs, so the selection must be driven by a
parameter rather than a filter (a filter would remove the data needed for the
overall average).

## The model

```
pUniversity            = list parameter, default "The University of Liverpool"
University Avg         = AVG(IF [University] = [pUniversity] THEN [% Agree] END)
Sample Size            = AVG(IF [University] = [pUniversity] THEN [Sample Size] END)
Overall Avg            = AVG([% Agree])
Delta                  = [University Avg] - [Overall Avg]
Colour                 = [Delta] >= 0
Lower Quartile         = PERCENTILE([% Agree], 0.25)
Upper Quartile         = PERCENTILE([% Agree], 0.75)
Legend Avg             = AVG(IF [University] = 'Middlesex University' THEN [% Agree] END)
Legend Colour          = [Legend Avg] - [Overall Avg] >= 0
```

## The Viz sheet

Question Number, Question Text, Sample Size, University Avg, Overall Avg and
Delta are **discrete** row pills (the author keeps two instances of each
measure: an ordinal copy for Rows and a quantitative copy for Columns). The
University Avg axis is on Columns with a Circle mark coloured by `Colour`
(`#f2c14e` when the delta is positive, `#5b9bd6` when negative). `% Agree`
AVG/MIN/MAX and the two quartiles sit on Detail and back three reference
elements:

1. an average line (`AVG(% Agree)`, black, 2 px),
2. a per-cell min→max band filled `#f5f5f5`,
3. a per-pane lower→upper quartile band filled `#d9d9d9`.

## The Legend sheet

A fixed Middlesex University marker with labelled bands ("Overall Min",
"Lower Quartile", "Overall Avg", "Upper Quartile", "Overall Max") that does not
change with the parameter.

## Numbers (independently recomputed from the locked extract)

| Question | University Avg | Overall Avg | Delta |
| --- | --- | --- | --- |
| Q01 | 89.8% | 89.1% | +0.70% ▲ |
| Q02 | 82.4% | 84.7% | 2.30% ▼ |

Both match the author's published screenshot. Q01 min/max = 60%/100%,
Q1/Q3 = 86.1%/92.5%. The legend's Middlesex average is 74.76%.

## cwtwb notes

- `configure_layered_chart(axis_shelf="columns", fold_axes=False)` with six
  ordinal row pills plus a quantitative axis pill reproduces the discrete
  measure rows and continuous column axis.
- Two copies of each measure are needed: `field_type="ordinal"` for the Rows
  shelf and `field_type="quantitative"` for the Columns axis / reference lines.
- `PERCENTILE(...)` is not in the SDK's aggregation map, so a bare
  `PERCENTILE(...)` field is registered as an unknown dimension and renders the
  pane empty; passing `table_calc="Rows"` (or `{"ordering_type": "Table"}`)
  makes the field resolve as a proper measure.
- `add_reference_band` writes a `refband` style rule with `fill-color`, paired
  min/max reference lines.
- `add_reference_line(..., formula="average", label_type="none")` reproduces
  the black average line.
