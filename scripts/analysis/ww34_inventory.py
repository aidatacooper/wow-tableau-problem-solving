"""Deterministic inventory for WW34 source workbook (protocol 6.2)."""
import json, sys, zipfile
from pathlib import Path
from lxml import etree

LAB = Path(__file__).resolve().parents[2]
ITER = LAB / "iterations" / "2019-09-02-ww34-top-n-single-worksheet"
SRC = LAB / "dashboards" / "2019_08_21_WW34_TopN_SingleWorksheet" / "2019_08_21_WW34_TopN_SingleWorksheet.twbx"

def load_root(path):
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".twb"))
        return etree.fromstring(z.read(name))

root = load_root(SRC)
inv = {"schema_version": "1.0.0", "iteration_id": "2019-09-02-ww34-top-n-single-worksheet"}

# datasources
dss = []
for ds in root.findall("./datasources/datasource"):
    entry = {"name": ds.get("name"), "caption": ds.get("caption"), "connection": ds.get("connection")}
    conn = ds.find("connection")
    if conn is not None:
        rel = conn.find("relation")
        if rel is not None:
            entry["table"] = rel.get("table")
    cols = []
    for c in ds.findall("column"):
        col = {"name": c.get("name"), "caption": c.get("caption"), "datatype": c.get("datatype")}
        calc = c.find("calculation")
        if calc is not None:
            col["formula"] = calc.get("formula")
            col["class"] = calc.get("class")
            tc = calc.find("table-calc")
            if tc is not None:
                col["table_calc"] = tc.get("ordering-type")
        cols.append(col)
    entry["columns"] = cols
    dss.append(entry)
inv["datasources"] = dss

# parameters
params = []
pds = root.find("./datasources/datasource[@name='Parameters']")
if pds is not None:
    for c in pds.findall("column"):
        params.append({
            "name": c.get("name"), "caption": c.get("caption"),
            "datatype": c.get("datatype"), "value": c.get("value"),
            "param-domain-type": c.get("param-domain-type"),
        })
inv["parameters"] = params

# worksheets
wss = []
for w in root.findall("./worksheets/worksheet"):
    ws = {"name": w.get("name")}
    table = w.find("table")
    if table is not None:
        rows = table.find("rows")
        cols = table.find("cols")
        ws["rows"] = rows.text if rows is not None and rows.text else ""
        ws["cols"] = cols.text if cols is not None and cols.text else ""
        panes = []
        for p in table.findall("panes/pane"):
            pane = {}
            m = p.find("mark")
            pane["mark"] = m.get("class") if m is not None else None
            pane["x_axis"] = p.get("x-axis-name")
            enc = {}
            for e in p.findall("encodings/*"):
                enc[e.tag] = e.get("column")
            pane["encodings"] = enc
            panes.append(pane)
        ws["panes"] = panes
        filters = []
        for f in table.findall("view/filter"):
            members = [g.get("member") for g in f.findall("groupfilter")]
            filters.append({"column": f.get("column"), "class": f.get("class"), "members": members})
        ws["filters"] = filters
    wss.append(ws)
inv["worksheets"] = wss

# dashboards
dbs = []
for d in root.findall("./dashboards/dashboard"):
    db = {"name": d.get("name")}
    sz = d.find("size")
    if sz is not None:
        db["size"] = {k: sz.get(k) for k in ("width", "height", "minwidth", "minheight", "maxwidth", "maxheight", "sizing-mode")}
    zones = []
    for z in d.findall(".//zone"):
        if z.get("name") or z.get("type") or z.get("param"):
            zones.append({
                "name": z.get("name"), "type": z.get("type"),
                "param": z.get("param"), "mode": z.get("mode"),
            })
    db["zones"] = zones
    dbs.append(db)
inv["dashboards"] = dbs

# actions
acts = []
for a in root.findall("./actions/*"):
    act = {"name": a.get("name"), "caption": a.get("caption"), "tag": a.tag}
    actv = a.find("activation")
    act["event"] = actv.get("type") if actv is not None else None
    src = a.find("source")
    if src is not None:
        act["source_dashboard"] = src.get("dashboard")
        act["source_worksheet"] = src.get("worksheet")
    params = []
    for p in a.findall("params/param"):
        params.append({"name": p.get("name"), "value": p.get("value")})
    act["params"] = params
    acts.append(act)
inv["actions"] = acts

# sets
inv["set_definitions"] = [{"name": s.get("name")} for s in root.iter("set")]

# raw set references (formulas / actions that reference sets by caption)
import re
content = etree.tostring(root, encoding="unicode")
inv["set_references_in_formulas"] = sorted(set(
    m for m in re.findall(r"\[([^\]]*Top[^\]]*|Highlighted Manufacturer[^\]]*)\]", content)
))

(ITER / "evidence" / "workbook-inventory.json").write_text(
    json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")
print("inventory written")
