"""Deterministic local gates for the WW33 build."""
from __future__ import annotations
import json
from pathlib import Path
from lxml import etree

ROOT = Path(__file__).resolve().parent

def main() -> int:
    twb = ROOT / "outputs" / "2019-08-14-ww33-table-formatting-replicated-workbook.twb"
    result = {"gate": "local_structure", "passed": False, "checks": {}}
    if not twb.exists():
        result["reason"] = "output missing"
    else:
        root = etree.parse(str(twb)).getroot()
        ws = [x.get("name") for x in root.xpath("./worksheets/worksheet")]
        calcs = [x.get("caption") for x in root.xpath(".//datasource/column[calculation]")]
        result["checks"] = {"worksheets": ws, "calculations": calcs, "dashboard_count": len(root.xpath("./dashboards/dashboard"))}
        result["passed"] = all(x in ws for x in ("Bar", "Table", "Title")) and all(x in calcs for x in ("Profit Ratio", "% Sales for Selected Region", "Highlight")) and len(root.xpath("./dashboards/dashboard")) == 1
    (ROOT / "evidence" / "validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
