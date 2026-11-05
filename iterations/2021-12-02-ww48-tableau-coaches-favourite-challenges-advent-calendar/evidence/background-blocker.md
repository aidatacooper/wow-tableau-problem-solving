# Generic capability blocker: Cartesian mapped raster background

Reproducer: `python probe_background.py` with PYTHONPATH and CWTWB_SRC explicitly selecting the SDK. It creates its own CSV and 1×1 PNG in a temporary directory and saves `outputs/background-image-probe.twbx`. No author workbook/data/images are used.

Expected: native datasource `mapped-images/mapped-image`, mapping Horizontal/Vertical to left=0,right=4,bottom=0,top=6, and packaged PNG whose path is relative to the TWBX. This mapping is independent of the worksheet viewport and must remain fixed when marks are filtered.

Observed on published 0.29.0a2: existing Cartesian `configure_chart(..., map_layers=[...])` accepts the payload but emits zero mapped-image nodes and no PNG. The `map_layers` parameter is routed only to the geographic map builder. The complete relevant public method signatures and capability inventory are preserved in `baseline-probe-api.json`. Source search for mapped-image found only the canonical datasource child ordering entry in twb_editor.py. `configure_layered_chart` supports mark panes, and `set_shape_palette` embeds mark images, but neither exposes the independent rectangle mapping.

Retested merged cac8820f26e703c3858253adfa21efd989eb8a78 (installed metadata still says 0.29.0a2): same result. `retest-probe-api.json` preserves the inventory. `retest-provenance.json` records module origin; installed distribution direct_url.json confirmed the full commit. No global install or SDK source was edited.

## Proposed parent-owned SDK work

Generic public capability: attach a PNG/JPEG raster to a datasource's numeric X/Y fields with finite left/right/bottom/top bounds; optional explicit identity and caption; package asset bytes and rewrite expression to a portable relative path. Validate field/type/bounds/file before mutation. Preserve builder → dispatcher → facade → MCP → capability registry path. Add synthetic XPath and TWBX round-trip tests, invalid-bound rollback tests and a Desktop load test. No API should be named after this case or author.

## Local result boundary

The working case has exactly Tree and Bar sheets, custom shapes, countdown tooltips, gradient counts, static action contracts and dashboard help. Native tree background is absent. Thus local verifier PASS means implemented-scope/data contracts passed, not full case acceptance. The tree PNG is source-locked under inputs/assets. Parent must add the background and run runtime gates; this branch must not be promoted to replicated based on XML checks.

No challenge URL or browser action was executed. Keep external opening unexecuted unless parent receives authorization for that runtime test; inspect the per-mark URL payload meanwhile.
