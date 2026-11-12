# 2026-09-26-ww38-can-you-create-an-embedded-categorised-dashboard-portal

## Problem

Create a categorized portal from a curated table of Tableau Public dashboard titles, tags, and URLs. Selecting a row should identify the dashboard and provide its embeddable URL.

## Why the obvious approach fails

A plain table does not make the category navigation obvious and it cannot drive a URL target. The author uses a Gantt selector with a URL field and a Web Page dashboard object.

## Tableau solution chain

```text
Sheet1 catalogue (Viz Title, Tag, Viz Link)
→ Gantt selector with Tag/Viz Title rows and MIN(1) size
→ Viz Link on detail for a URL action
→ dashboard with selector and web target
```

## Required behavior

- Selector lists every catalogue row grouped by Tag.
- Each mark carries its Viz Link and the URL appends `:embed=yes&:showVizHome=no`.
- Selecting a row is represented by a URL action; the released SDK does not expose a native Web Page zone, so the target is documented in the dashboard text.

## Allowed visual differences

Typography, spacing, exact Gantt mark size, and the live browser frame may differ.

## cwtwb baseline

The released SDK reproduced the data connection, selector chart, URL detail, and URL action. A native Web Page dashboard zone is not exposed; this case uses a documented static target note as a workaround. Cloud/browser execution was not performed.
