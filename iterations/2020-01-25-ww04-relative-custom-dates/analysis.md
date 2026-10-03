# Relative and custom date ranges

The 25 January article recreates Sean Miller's 2020 WW04 challenge (official
challenge date 21 January). The dashboard provides four date choices, three KPI
values, and an edged daily sales area chart. Relative periods use the maximum
order date in the source, rather than today's date. Last N uses a strict lower
bound; custom dates include both endpoints.

Analysis read the article and Donna Coles' published workbook. Only its packaged
Hyper extract is used by the builder, which starts from `TWBEditor("")` and public
SDK APIs. The source lock binds article, workbook and extract hashes.

Acceptance scenarios:

- `ww04-date-oracle`: independently aggregate source sales/profit/ratio and daily
  sales for Last 14, Last 30, Last N=60 and custom 2019 calendar year.
- `ww04-selector-action`: selector marks set Date Selector from virtual Measure
  Names; mapped True-to-False filter clears selection, preserving current parameter.
- `ww04-context-controls`: N Days appears only for Last N, and start/end controls
  appear only for Custom Dates. Validate serialized visibility graph and REST states.
- `ww04-cloud-states`: compare KPI and trend exports in each state. Dashboard CSV
  alone does not establish all daily sales; trend CSV supplies the full date series.
- `ww04-visual`: compare Cloud dashboard screenshots with documented differences.

The modern native dynamic visibility graph replaces the author's transparent
offscreen sheet parameter popping. Text circles replace custom shape radio
buttons, and footer/font spacing may differ. These are implementation/visual
deltas, not a claim of pixel identity or executed browser events.

Cloud clips the selector's text marks at the original 45-pixel height. The replica
allocates a 100-pixel selector zone, places KPI values below it, and shortens the
trend panel by 52 pixels. This preserves visible and selectable options while
recording the resulting vertical layout difference explicitly.
