# Cloud REST review

Result: acceptable_delta. Reviewed replica SHA-256:
`4386b948fdd5b60aaec1563c9ae0e40639c8b1e5f62af2e2fc12bdcf33616657`.
The author export copy changes only worksheet window visibility; original and
comparison-copy hashes are recorded in export-provenance.json.

All five paired states were inspected: default Hoxton/500m, intermediate map,
250m radius, Marriott selected with Yelp-rating sorting, and ratings-count
sorting. The intermediate map shows the same eight hotel buffers and pub-count
labels (5, 2, 2, 2, 2, 2, 1, 1). The selected-hotel map places the same 32 pubs,
uses darker red for nearer pubs and larger circles for more distant pubs, and
shows the selected hotel's gray buffer. The 250m images reduce the buffer, and
the Marriott images move it to Park Lane and recalculate all pub distances.
Changing only the sort parameter leaves the closed map unchanged, as expected.

Thirty full worksheet CSV exports were independently checked against the two
packaged Hyper extracts: all 17 joined hotel/pub pairs, all 32 distinct pub
name/neighborhood keys and distances, and all 10 hotels' ratings, review counts
and price bands across all states and both roles. Distance comparison uses an
independent WGS84 local-curvature calculation with a 1m tolerance for rounded
labels. A whitespace-only author price band is normalized to empty. These are
complete pub-list, map and hotel-list exports, not a button CSV or evidence of
the rendered polygon's geometric radius.

Remaining differences: the intermediate basemap retains more transit/place
icons; map extents and text placement differ slightly; the replica has a wider
color legend and omits the author's separate size legend. In the Marriott state,
the wider color legend covers the beginning of the hotel label. Footer credit,
legend spacing and radius-control presentation also differ. Both views remain
readable, and the full hotel identity and distances are checked in CSV. Pixel
matching is not claimed.

The embedded tooltip sheet, Hotel Name filter, selected-hotel and sort parameter
actions, their sources and clearing behavior, and native hidden-container toggle
are verified in the workbook artifact. REST establishes parameter states;
browser clicks, tooltip hovers and opening the hidden selector were not executed.
