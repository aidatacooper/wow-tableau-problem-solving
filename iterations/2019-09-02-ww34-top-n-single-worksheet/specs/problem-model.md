# WW34 Problem Model

The user needs one worksheet that compares each region's independently ranked
Top N manufacturers, optionally includes an Other bucket, and reveals rank on
hover. A global Top N produces the wrong regional membership; separate sheets
break the single-worksheet constraint; a rank-only table calculation does not
provide the required reusable membership or hover interaction.

Required semantics are regional set membership, parameters, filtering, ranking,
and Set Action behavior. Exact spacing, fonts, and footer treatment are
presentation-only.
