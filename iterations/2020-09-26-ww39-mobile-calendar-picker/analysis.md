# Mobile calendar picker

Article date: 2020-09-26. Official challenge 2020 WW39 was posted 2020-09-22 (WordPress REST post 4002). Source is the author mobile-calendar workbook, analyzed only in scratch.

The data contains 9994 order facts and a calendar logical table with duplicate dates; the calendar domain is 1461 distinct dates from 2016-01-01 through 2019-12-31. The public logical-relationship API relates calendar Date to Order Date, preserving independent fact aggregation instead of joining duplicate calendar rows into sums. Date selections and month navigation retain the source parameters and formulas, including the two-click string date-range control. No browser clicks or hover are executed.

The four REST parameter states cover June 2019, July 2019, leap February 2016 and December 2018. The independent oracle computes every displayed calendar date/color, all fact-backed daily Sales/Profit/Quantity and complete BAN sums. Full Calendar, BAN and Line CSV must establish data correctness; navigation CSV alone is insufficient.

The default dashboard is 350x700 with an initially hidden year/month picker and native show/hide button. The generic Phone-copy API preserves default zone identities and hidden/button references, using the default device dimensions; this is an artifact contract, not a claim of mobile-browser rendering. Released cbe200a has no explicit device-copy method; the isolated release probe records the gap. The enhanced SDK provides the native Phone-copy contract. Final Cloud validation passed all four parameter states; the exact released SDK runs and pin are recorded in case.yaml and the coordinated zero-build evidence.

Calculation dependencies are registered in topological order and comments removed before normalization; public SDK APIs alone construct the workbook from TWBEditor(""). Source-export comparison only exposes existing hidden worksheet windows, as recorded in export-provenance.json.

The calendar uses a fixed zero-to-one axis so each highlight fills the date cell. Source custom navigation PNGs were extracted and locked for analysis, but Cloud rendered the attempted custom-shape controls as circles. The final public build uses explicit gray Text chevrons, retaining the original MIN(date) details and parameter-action source values. This glyph substitution is a documented visual difference, confirmed readable in all four final paired renders; selection and date clamping are unchanged.

The two-click date-range action uses ATTR(Date Control), matching the author Attribute instance and the actual Calendar tooltip field. The verifier requires every parameter-action source instance to be declared on its worksheet, verifies the target parameter and keep-current clear contract, and checks the three true-to-false deselection mappings. The earlier bare Date Control source did not exist as a mark instance despite correct REST values; its rejected contract is retained in action-source-baseline.json.
