# Can you find the variance along a line?

Article 2021-01-08; official challenge 2021-01-05 (2021 WW01, WordPress post 4199).

The author uses 25 annual U.S. household food insecurity rates, 1995 through 2019. Values are percentage points already, not fractional ratios. Selected Year defaults to 2018; comparison mode defaults to Previous Year and also supports First Year or Most Recent Year. A black trend line overlays black comparison and magenta selected circles. The header shows the selected rate, signed direction and absolute percentage-point change.

The builder starts at `TWBEditor("")`, reads the locked two-column Hyper extract, and uses only public SDK APIs. Author TWBX is analyzed in scratch and republished only as a comparison; the builder never opens it. Original WINDOW_MIN/MAX and nested table calculations remain in the business Viz and diagnostic Data sheets. A separate Text worksheet provides an equivalent dynamic header through FIXED calculations because the public plain worksheet title API does not support rich bound values. The verifier checks both native calculation addressing and independent raw-data values across all 75 year/comparison combinations.

Cloud acceptance requests default 2018 Previous Year, 2018 First Year, 2018 Most Recent Year, 1995 Previous Year, 1995 First Year and 2011 First Year. The earliest-year Previous Year comparison is absent; this must remain null rather than invented as zero. The earliest-year First Year comparison has zero difference and original N/C indicator. Complete Viz and Data CSV exports establish actual REST parameter state and exported year/measure coverage. Images establish desktop layout. No browser parameter selection, click or hover is claimed. The original phone layout is outside desktop acceptance.
