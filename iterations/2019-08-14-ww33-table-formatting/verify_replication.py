"""Deterministic SDK, extract, formula and visual-structure contracts for WW33.
Cloud visual and parameter interaction review are separate evidence gates.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
ROOT = Path(__file__).resolve().parent

# case-functional-contract: explicit assertions plus independent data and SDK round-trip.
def main() -> int:
    root = etree.parse(str(ROOT / "outputs/2019-08-14-ww33-table-formatting-replicated-workbook.twb")).getroot()
    script = (ROOT / "build_replication.py").read_text()
    calls = [n for n in ast.walk(ast.parse(script)) if isinstance(n, ast.Call)]
    empty = any(isinstance(n.func, ast.Name) and n.func.id == "TWBEditor" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "" for n in calls)
    ds = next(d for d in root.findall("./datasources/datasource") if d.get("name") != "Parameters")
    formulas = {c.get("caption"): c.find("calculation").get("formula", "") for c in ds.findall("column[calculation]")}
    params = {c.get("caption"): c.get("value") for c in root.findall("./datasources/datasource[@name='Parameters']/column")}
    wss = {w.get("name"): w for w in root.findall("./worksheets/worksheet")}
    bar = wss["Bar"]
    bar_panes = bar.findall("table/panes/pane[@x-axis-name]")
    maps = ds.findall("style/style-rule/encoding/map")
    palette = {m.findtext("bucket"): m.get("to") for m in maps}
    lock = json.loads((ROOT / "inputs/source-lock.json").read_text())
    with ZipFile(ROOT / "outputs/replicated-workbook.twbx") as archive:
        extracts = {hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.endswith(".hyper")}
    input_hash = hashlib.sha256((ROOT / "inputs/Orders (Sample - Superstore).hyper").read_bytes()).hexdigest()
    checks = {
      "sdk_from_scratch": empty and not any(x in script for x in ("lxml", "SubElement(", "open_existing(")),
      "independent_extract": lock.get("source_workbook_used_by_builder") is False and input_hash in extracts,
      "worksheet_contract": set(wss) == {"Bar", "Table", "Title"} and len(root.findall("./dashboards/dashboard")) == 1,
      "parameter_defaults": params.get("Highlight Threshold") == "30" and params.get("Selected Region") == '\"East\"',
      "highlight_formula": "100" in formulas.get("Highlight", "") and ">" in formulas.get("Highlight", ""),
      "conditional_table_labels": all(x in formulas for x in ["LABEL:Subcat BOLD", "LABEL:Subcat Normal", "LABEL:Sales BOLD", "LABEL:Sales Normal", "LABEL:Profit BOLD", "LABEL:Profit Normal", "LABEL:Profit Ratio BOLD", "LABEL:Profit Ratio Normal", "LABEL:Qty BOLD", "LABEL:Qty Normal"]),
      "selected_region_ratio": "SUM(" in formulas.get("% Sales for Selected Region", "") and "Region" in formulas.get("% Sales for Selected Region", ""),
      "dual_axis_outlined_comparison": len(bar_panes) == 2 and all(p.find("mark").get("class") == "Bar" for p in bar_panes) and all(p.find("encodings/text") is not None for p in bar_panes) and all(p.find("style/style-rule[@element='mark']/format[@attr='has-stroke'][@value='true']") is not None for p in bar_panes),
      "highlight_palette": palette.get("true") == "#d3d3d3" and palette.get("false") == "#ffffff",
      "shared_filters": any("Sub-Category" in f.get("column", "") for f in root.findall(".//filter")) and any("yr:Order Date:ok" in f.get("column", "") and "2018" in str(etree.tostring(f)) for f in root.findall(".//filter")),
    }
    result = {"gate": "local_structure", "passed": all(checks.values()), "checks": checks, "visual_review": "separate Cloud evidence", "interaction_review": "not asserted by XML checks"}
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/validation.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
