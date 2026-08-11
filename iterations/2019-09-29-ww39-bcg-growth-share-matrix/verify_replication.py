from pathlib import Path
from zipfile import ZipFile
from lxml import etree

HERE = Path(__file__).resolve().parent


def c(r):
    assert {"Scatter:Sales", "Top 20 Bars", "Legend"} <= {
        x.get("name") for x in r.xpath("./worksheets/worksheet")
    }
    f = {
        x.get("caption"): x.find("calculation").get("formula")
        for x in r.xpath(".//column[calculation]")
    }
    assert "TOTAL" in f["Market Share"] and "Question Mark" in f["BCG Quadrant"]



def main():
    c(
        etree.parse(
            str(
                HERE
                / "outputs/2019-09-29-ww39-bcg-growth-share-matrix-replicated-workbook.twb"
            )
        ).getroot()
    )
    with ZipFile(
        HERE
        / "outputs/2019-09-29-ww39-bcg-growth-share-matrix-replicated-workbook.twbx"
    ) as z:
        assert any(x.endswith(".hyper") for x in z.namelist())
        c(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith(".twb")))))
    print("PASS: WW39 growth-share matrix")


if __name__ == "__main__":
    main()
