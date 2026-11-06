# Parent-render diagnosis and corrected references

## Observed, not inferred

Frozen primary `264257cd5b710753e4c13ac5f4737d0740af3517e1d659c5a7bd03c8d3aae0b7` was captured by the parent. Both PNGs were inspected with view_image. The replica lacks the tree raster; marks are hollow default circles and a square, with white labels barely visible. Its bars go green-to-red, while the author starts each bar red and longer bars reach green. These are actual failed-render observations for the **old** artifact.

The captured Tree CSV has 25 marks, one null-Day Christmas star, and the 24 intended day/URL/year records. Bar CSV has 2004 rows: 500 segments per year and four count labels (10,3,5,6). Numerical grain survives. This narrows the failure to resource/style/reference handling and color encoding; it does not establish the corrected runtime result.

## Bounded analysis and own-document corrections

- The author raster expression is a `file:` resource URI. Our old expression was a quoted pathname string. Corrected: `file:Images/christmas-tree.png`, resolving the exact PNG entry. Numeric Y/X mapping and bounds remain independently authored from analysis (0..4 horizontal, 0..6 vertical).
- The author's datasource declares the column-instance referenced by its custom-shape style. Released `set_shape_palette` emits that reference and PNG bytes, but our output had **zero datasource column-instances**. A worksheet dependency declaration is a different scope. The corrected native document declares the instance using its **own** worksheet binding metadata.
- The author's explicit shape maps do not name a palette. Our API output named `Advent`, which is not an installed standard palette. The correction removes that attribute and retains exact maps to `Advent/christmas-ornament.png` and `Advent/star.png` in external/shapes. The relative contribution of this attribute versus missing instance needs runtime confirmation; no isolated causal proof is claimed.
- Old color was `(500-segment)*count/500`, decreasing toward the right. Corrected color is `AVG(Segment Start)`, increasing from zero, with red/green palette, reverse=false, global domain 0..10. A simple palette reversal would incorrectly change the short bars' start/end colors. Locked inputs remain byte-identical; the historical Gradient column is unused.

All structural edits operate only on our newly blank-built workbook via exported native-JSON conversion. No author XML/JSON is copied. No SDK or global installation is edited. White labels remain intentional over red ornament sprites; they were not changed to disguise missing assets.

## Specific reusable SDK defect

`python probe_shape_binding.py` builds two synthetic CSV rows and a synthetic PNG through released a2. Its output shape style references a datasource instance that does not exist, despite the matching worksheet instance and embedded shape being present. `evidence/shape-binding-reproducer.json` records before/after hashes and scope checks. `outputs/shape-binding-before.twbx` reproduces the missing binding; `outputs/shape-binding-corrected.twbx` declares it using our structural workaround and removes the unregistered palette attribute. This is a precise reference-emission defect, not a broad claim that public APIs cannot package images. The synthetic fixture has not been rendered.

## Preservation and acceptance boundary

The old primary is `outputs/frozen-264257cd.twbx`. All parent capture JSON/PNG/CSV and old build/verification reports are copied byte-for-byte under `evidence/runtime-264257cd`; preservation.json records exact hashes. Original current-directory capture files are also left untouched and still refer to 264257cd. They must not be represented as evidence of the new artifact. Previous runs remain unchanged; the correction is appended.

New local checks reject missing datasource shape instances, unresolved embedded-shape references, unregistered palette names, quoted raster paths, and reversed/shifted gradient bindings, in addition to the previous data/reference/action contracts. XSD and asset roundtrip remain useful integrity checks, **not proof of rendering**. Parent must recapture the new frozen artifact and check actual image resolution, star/bauble scale, legible labels, gradient endpoints and interactions. No Desktop, Cloud, browser or live event action ran locally; the globally running corpus was not touched.
