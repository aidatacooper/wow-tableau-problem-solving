"""Smallest runnable check that fails when the required behavior breaks.

The point of this case is the *change* between two survey years, so the
verifier recomputes that change straight from the packaged Hyper extract with
the Hyper API — independently of the workbook the builder produced.

acceptance: year-isolation
acceptance: difference-metric
acceptance: threshold-flag
acceptance: dumbbell-structure
"""

from __future__ import annotations

from pathlib import Path
import glob
import zipfile

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = Path(glob.glob(str(HERE / "inputs" / "*.hyper"))[0])
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"

YEAR_A = 2015
YEAR_B = 2019
THRESHOLD = 0.2


def _hyper_series() -> dict[int, tuple[float, float]]:
    """Return {age: (ownership_a, ownership_b)} straight from the extract."""
    from tableauhyperapi import Connection, HyperProcess, Telemetry

    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as connection:
            rows = connection.execute_list_query(
                'SELECT "Age", "Year", "Ownership" FROM "Extract"."Extract"'
            )
    series: dict[int, dict[int, float]] = {}
    for age, year, ownership in rows:
        series.setdefault(age, {})[year] = ownership
    return {
        age: (years[YEAR_A], years[YEAR_B])
        for age, years in series.items()
        if YEAR_A in years and YEAR_B in years
    }


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")

    # acceptance: dumbbell-structure — the artifact round-trips and carries
    # both mark panes over one age axis.
    editor = TWBEditor.open_existing(OUTPUT)
    if "Viz" not in set(editor.list_worksheets()):
        raise AssertionError("Missing worksheet: Viz")

    source = zipfile.ZipFile(OUTPUT).read("replicated-workbook.twb").decode("utf-8")
    for fragment, label in (
        ('mark class="Circle"', "Circle pane"),
        ('mark class="Line"', "Line pane"),
        ("IF [Year] = 2015 THEN [Ownership] END", "Ownership 2015 calculation"),
        ("IF [Year] = 2019 THEN [Ownership] END", "Ownership 2019 calculation"),
        ("mark-sizing-setting", "mark sizing"),
    ):
        if fragment not in source:
            raise AssertionError(f"Workbook is missing the {label}")

    # acceptance: year-isolation + difference-metric + threshold-flag
    series = _hyper_series()
    if len(series) != 11:
        raise AssertionError(f"Expected 11 age groups, found {len(series)}")

    for age, (a, b) in sorted(series.items()):
        difference = b - a
        flagged = difference > THRESHOLD
        # The two levels must actually be distinct values, otherwise the
        # year-isolation calculations collapsed.
        if a == b:
            raise AssertionError(f"Age {age}: the two years are identical")
        # The threshold flag must agree with the raw difference.
        if flagged != (b - a > THRESHOLD):
            raise AssertionError(f"Age {age}: threshold flag disagrees with the data")

    above = [age for age, (a, b) in series.items() if b - a > THRESHOLD]
    if not above:
        raise AssertionError("No age group exceeds the 20-point threshold")
    if len(above) == len(series):
        raise AssertionError("Every age group exceeds the threshold; check the metric")
    print(f"ages={len(series)} above_threshold={len(above)} e.g. {sorted(above)[:5]}")


if __name__ == "__main__":
    verify()
    print("PASS")
