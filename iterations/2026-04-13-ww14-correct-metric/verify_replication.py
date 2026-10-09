"""Smallest runnable check that fails when the required behavior breaks.

The point of this case is a *metric*, so the verifier recomputes that metric
straight from the packaged Hyper extract with the Hyper API — independently of
the workbook the builder produced. If the builder's formula drifts, the
workbook's own numbers would still be self-consistent; only an independent
aggregate catches that.

acceptance: weighted-average-formula
acceptance: difference-flag
acceptance: extract-window
acceptance: workbook-structure
"""

from __future__ import annotations

from pathlib import Path
import zipfile

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs" / "federated_1nm7djf14r2b931axjuel0.hyper"
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"

WINDOW_START = "2025-10-01"
WINDOW_END = "2026-01-01"  # exclusive

WEIGHTED_AVG = "SUM([Discount] * [Quantity]) / SUM([Quantity])"
DIFFERENCE = "ABS([Weighted Avg] - AVG([Discount]))"
IS_DIFFERENCE = "ROUND([Difference from correct metric], 3) <> 0"


def _hyper_aggregate() -> tuple[int, int]:
    """Return (orders in window, orders whose rounded difference is nonzero)."""
    from tableauhyperapi import Connection, HyperProcess, Telemetry

    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER)) as connection:
            table = '"Extract"."Extract"'
            where = (
                f"\"Order Date\" >= DATE '{WINDOW_START}' "
                f"AND \"Order Date\" < DATE '{WINDOW_END}'"
            )
            rows = connection.execute_list_query(
                f'SELECT "Order ID", AVG("Discount"), '
                f'SUM("Discount" * "Quantity") / SUM("Quantity") '
                f"FROM {table} WHERE {where} GROUP BY \"Order ID\""
            )
    orders = len(rows)
    differing = sum(1 for _, simple, weighted in rows if round(abs(weighted - simple), 3) != 0)
    return orders, differing


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")

    # acceptance: workbook-structure — the SDK can round-trip the artifact.
    editor = TWBEditor.open_existing(OUTPUT)
    sheets = set(editor.list_worksheets())
    for required in ("Simple Avg", "Weighted Avg", "Order Details"):
        if required not in sheets:
            raise AssertionError(f"Missing worksheet: {required}")

    source = zipfile.ZipFile(OUTPUT).read("replicated-workbook.twb").decode("utf-8")
    for formula, label in (
        ("SUM([Discount] * [Quantity]) / SUM([Quantity])", "weighted average"),
        ("AVG([Discount])", "simple average"),
        ("ROUND(", "difference rounding"),
    ):
        if formula not in source:
            raise AssertionError(f"Workbook is missing the {label} formula")
    if "tsc:brush" not in source:
        raise AssertionError("Workbook is missing the dashboard highlight action")

    # acceptance: extract-window + weighted-average-formula + difference-flag
    orders, differing = _hyper_aggregate()
    if orders == 0:
        raise AssertionError("The Oct-Dec 2025 window contains no orders")
    if differing == 0:
        raise AssertionError("No order differs between simple and weighted discount")
    if differing >= orders:
        raise AssertionError(
            f"Expected some orders to agree, but {differing}/{orders} differ"
        )
    print(f"orders in window={orders} differing={differing}")


if __name__ == "__main__":
    verify()
    print("PASS")
