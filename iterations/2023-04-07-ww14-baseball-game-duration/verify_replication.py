"""Smallest runnable check that fails when the required behavior breaks.

The point of this case is comparing every year's game duration against the
2023 pace, so the verifier recomputes durations, the decade bucketing, and the
Duration > Latest classification straight from the packaged Hyper extract with
the Hyper API — independently of the workbook the builder produced.

acceptance: duration-metric
acceptance: decade-bucketing
acceptance: latest-duration-window
acceptance: pace-classification
acceptance: reference-line-structure
"""

from __future__ import annotations

from pathlib import Path
import glob
import re
import zipfile

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = Path(glob.glob(str(HERE / "inputs" / "*.hyper"))[0])
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"

# The author renders from 1960 onward.
MIN_YEAR = 1960


def _hyper_series() -> dict[int, int]:
    """Return {year: duration_minutes} straight from the extract."""
    from tableauhyperapi import Connection, HyperProcess, Telemetry

    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as connection:
            rows = connection.execute_list_query(
                'SELECT "Year", "Time/9I" FROM "Extract"."Extract" '
                'WHERE "Time/9I" IS NOT NULL'
            )
    series: dict[int, int] = {}
    for year, duration in rows:
        minutes = duration.hour * 60 + duration.minute
        if year in series:
            raise AssertionError(f"Duplicate year row: {year}")
        series[year] = minutes
    return series


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")

    # acceptance: reference-line-structure — the artifact round-trips and
    # carries the bar pane with its field-backed reference line.
    editor = TWBEditor.open_existing(OUTPUT)
    if "Viz" not in set(editor.list_worksheets()):
        raise AssertionError("Missing worksheet: Viz")

    source = zipfile.ZipFile(OUTPUT).read("replicated-workbook.twb").decode("utf-8")
    for fragment, label in (
        ("DATEPART('hour', [Time/9I])", "Duration (mins) calculation"),
        ("STR(FLOOR([Year] / 10) * 10)", "Decade calculation"),
        ("WINDOW_MAX(IF LAST() = 0 THEN SUM", "Latest Duration window calc"),
        ("&gt;= [Calculation_", "Duration > Latest calc"),
        ("<reference-line", "reference line"),
    ):
        if fragment not in source:
            raise AssertionError(f"Workbook is missing the {label}")

    custom_label = re.search(r'label="([^"]*)"', source)
    if not custom_label or "2023" not in custom_label.group(1):
        raise AssertionError("Reference line lacks the 2023 custom label")

    # acceptance: duration-metric + decade-bucketing + latest-duration-window
    #            + pace-classification — recomputed from the extract.
    series = _hyper_series()
    latest = series[2023]
    if latest != 158:
        raise AssertionError(f"Expected 2023 = 2:38 (158 mins), found {latest}")
    observed = series
    for year, minutes in observed.items():
        decade = f"{year // 10 * 10}s"
        if not re.fullmatch(r"(18|19|20)\d0s", decade):
            raise AssertionError(f"Bad decade bucket for {year}: {decade}")
        if (minutes <= latest) != (minutes <= observed[2023]):
            raise AssertionError(f"Year {year}: pace classification is inconsistent")
    faster_years = [y for y, m in observed.items() if y >= MIN_YEAR and m <= latest]
    slower_years = [y for y, m in observed.items() if y >= MIN_YEAR and m > latest]
    if not faster_years or not slower_years:
        raise AssertionError("Classification collapsed to a single colour class")
    if len(faster_years) != 26:
        raise AssertionError(
            f"Expected 26 rendered years at-or-below the 2023 pace, found {len(faster_years)}"
        )
    print(
        f"years={len([y for y in observed if y >= MIN_YEAR])} latest={latest}mins "
        f"at_or_below={len(faster_years)} slower={len(slower_years)}"
    )


if __name__ == "__main__":
    verify()
    print("PASS")
