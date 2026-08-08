"""Build this case from extracted data, never from the author TWB/TWBX."""

from pathlib import Path

from cwtwb import TWBEditor


HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"


def build() -> Path:
    OUTPUTS.mkdir(exist_ok=True)
    editor = TWBEditor("")
    # Add the extracted data connection, calculations, views, and interactions.
    output = OUTPUTS / "replicated-workbook.twbx"
    editor.save(output)
    return output


if __name__ == "__main__":
    print(build())
