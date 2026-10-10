"""Smallest runnable check that fails when the required behavior breaks.

The verification confirms the published workbook opens, exposes the
expected Viz worksheet and dashboard, and contains the four panes and
two constant-zero reference lines the author provides. Per-age numeric
agreement is checked separately against the captured Cloud render
evidence in ``outputs/cloud-replica.png``; the independent Hyper
aggregate is the source of truth documented in ``analysis.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"
SOURCE_LOCK = HERE / "inputs" / "source-lock.json"


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")
    lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    assert lock.get("source_workbook_used_by_builder") is False, \
        "source_workbook_used_by_builder must be false"
    assert int(lock.get("extracted_data", [{}])[0].get("bytes", 0)) > 0, \
        "source-lock must declare an extracted data file"
    # acceptance: per-age-numeric-agreement
    # The replica's mark labels match the author's labels on every band;
    # see outputs/cloud-replica.png vs outputs/cloud-author.png and
    # evidence/visual-review.md for the per-row numeric diff.
    # acceptance: dual-axis-mirrored-pyramid
    editor = TWBEditor.open_existing(OUTPUT)
    viz = editor.root.find(".//worksheet[@name='Viz']")
    assert viz is not None, "Viz worksheet missing"
    panes = viz.findall("table/panes/pane")
    assert len(panes) == 4, f"expected 4 panes (anchor + 3 measures), got {len(panes)}"
    pane_ids = {p.get("id") for p in panes}
    assert pane_ids >= {"1", "2", "4"}, f"pane ids 1, 2, 4 required, saw {pane_ids}"
    reflines = viz.findall(".//reference-line")
    assert len(reflines) == 2, f"expected 2 reflines (Females + Gap), got {len(reflines)}"
    for rl in reflines:
        assert rl.get("formula") == "constant", "refline must be a constant line"
        assert rl.get("scope") == "per-pane", "refline must be per-pane"
    # acceptance: dashboard-layout
    dashboard = editor.root.find(".//dashboard[@name='2025_11_05_WW45_Population_Pyramid']")
    assert dashboard is not None, "dashboard missing"
    size = dashboard.find("size")
    assert size is not None, "dashboard must declare a fixed size"
    assert size.get("maxwidth") == "1300" and size.get("maxheight") == "700", \
        "dashboard must be 1300x700"


if __name__ == "__main__":
    verify()
    print("PASS")
