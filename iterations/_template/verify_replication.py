"""Smallest runnable check that fails when the required behavior breaks."""

from pathlib import Path

from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs" / "replicated-workbook.twbx"


def verify() -> None:
    if not OUTPUT.exists():
        raise AssertionError(f"Missing output: {OUTPUT}")
    TWBEditor.open_existing(OUTPUT)
    # Add assertions for every acceptance scenario in case.yaml.


if __name__ == "__main__":
    verify()
    print("PASS")
