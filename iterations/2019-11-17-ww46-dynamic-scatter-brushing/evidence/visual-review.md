# Cloud REST review

Acceptance uses Cloud REST images and exported data states plus workbook artifact contracts. Browser clicks, hover and brushing events were not executed. The select action's source, set target and exclude-all clearing behavior are verified structurally.

Compare [author](../outputs/cloud-author.png) and [replica](../outputs/cloud-replica.png), then the Product/Sales/Orders and Manufacturer/Sales/Quantity PNG pairs in outputs/. The three top percentage bars, three parameter controls, upper X scale, lower tick suppression and teal scatter population are required. A blank bar or incorrect Manufacturer population is a failed result, not an acceptable styling difference.

The initial capture exposed absent percentage bars/tiny marks and Manufacturer 183 versus 327. Public case styles/range configuration were corrected. Manufacturer mismatch revealed a general SDK bug: categorical-bin string values require Tableau backslash escaping for quotes/hash/percent instead of SQL doubled quotes. The fixed SDK also omits the categorical fallback when default_value=None. The verifier now compares every decoded serialized bin member to locked source business data and asserts percentage axis 0..1.

The default and two valid parameter state dashboard CSVs export only **LOD Bars**, with one Out row. The expected LOD populations are Customer 793, Product 1850 and Manufacturer 183. Both roles must export 100% share and zero selected members. They do not expose scatter coordinates or X/Y bars; evidence/data-contract.json independently validates every scatter population and all 48 axis/LOD combinations and set partitions. This distinction is enforced by verify_cloud_data.py.

Remaining visual differences can include heading alignment, compact footer/omitted attribution link and minor spacing. They are not pixel-exact matching. Final capture paths/hashes and accepted workbook hash are recorded in evidence/cloud-verification.json; --strict-workbook checks the current primary package against that capture. Historical initial metadata is preserved separately; it is not current acceptance.
