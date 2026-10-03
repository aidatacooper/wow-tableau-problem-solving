# Cloud REST visual and data review

Reviewed all eight author/replica dashboard PNGs for `default`, `all`, `flu`, and `physician-age`, bound by `cloud-verification.json` to replica SHA-256 `f4e4acd8b4c0fcd9d0812c2a20aa5b460605e73457a02125a5942698a5ac8ba9`.

The replica shows the same visible patients, profiles, health-check lists, and member ordering as the comparison workbook. Long health-check lists wrap onto two lines, including the default examples for Major Mayer, Reuben Andrade, Harvey Owen, and Winnie Harvey. The filtered physician/age state displays Phil Flood and ages 65–69 with matching visible rows. No horizontal scrollbar clips the replica list column.

Independent verification reads the extracted Hyper data and checks every exported patient profile and complete concatenated list, with one row per patient in each role. The four states contain 672, 59,272, 56,683, and 26 patients respectively; all eight full Report CSV comparisons pass. The CSV scope covers the complete table rather than filter controls or dashboard buttons. These checks establish list contents beyond the rows visible in the PNGs.

Accepted visual differences remain: the replica table leaves a white strip on the right, and its slightly narrower list column changes line breaks. Title size, control spacing, and captions differ (`Size` / `Health Check Name Parameter` versus `Min # of Health Checks` / `List Must Contain`). Member IDs use a lighter regular weight, the age heading wraps, and banding edges and footer attribution differ. These differences do not prevent reading the complete lists or evaluating the requested filter states.

Result: `acceptable_delta`, not a pixel-identical reproduction. Acceptance covers Cloud REST images/data states and workbook contracts, including native table-calculation addressing and controls. No browser clicks, hovers, or other action events were executed.
