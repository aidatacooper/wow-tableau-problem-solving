# WW48 Cloud visual review

Artifact SHA256: `90fcf9ff916639a44c0663f781ab194a91855e6b937ae7cb77e7630a70540b01`

Visual status: `acceptable_delta`.

All six captured PNGs (source and replica, default / Live / Recording) were independently inspected. Functional review strictly passes all twelve CSV exports: source and replica Viz each 34 / 16 / 14 rows and Data each 51 / 24 / 21 rows. All 17 / 8 / 7 session groups are checked against the 94333 raw attendance facts; both pane heights, one duration width per group, attendee CountD, complete Data three-measure values and original session titles/descriptions/end times are independently verified. Two null-location break sessions remain in the default data and beige marks.

The refined layout restores the actual automatic time domain and 15-minute axis encoding, the native render-fold-reversed colored foreground, hidden synchronized attendee axes, the blank time-axis title, left-aligned 20-point heading with 10-point subtitle, and the source 1000x600 absolute zones. Every session starts at its actual time and extends according to actual duration; this is native width sizing, not a visual-only facsimile.

Recorded differences: the replica has a faint enclosing plot border, approximately 8-pixel zone/plot offsets, and slight text/tick spacing differences. The 9:30/10:00 labels in the default capture are tight. Footer credits truthfully identify SDK recreation. The source Recording-state REST image itself omits its heading/footer, whereas the replica retains them; this is an actual captured image difference, not evidence that browser/device behavior was exercised. The source has a `Break` display alias for null Location; the replica CSV preserves raw null values and documents that normalization. Replica Data uses an explicit Session Key instead of the source's five separate row dimensions, without changing any business groups or measures.

Tooltip formatting also differs at the artifact level: the generated runs use the raw timestamp fields without a source-style field default time format, and the SDK tooltip does not explicitly suppress command buttons as the source does. Hover rendering was not exercised.

No browser clicks or hover events were executed. Tooltips and native width/axis contracts were inspected in the generated artifact, while calculations were established through raw facts and complete Cloud CSV scopes.
