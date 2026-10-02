"""Contract checks and complete independent state aggregation for WW48."""
from pathlib import Path
import hashlib, json, math, zipfile
from lxml import etree
from tableauhyperapi import HyperProcess, Telemetry, Connection
HERE=Path(__file__).resolve().parent

# case-functional-contract: threshold-domain, grouping-and-order, dual-axis-labels,
# count-summary, threshold-reference, dashboard-control, independent-numerics.
def load_root():
    with zipfile.ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        return etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))

def check_contract(root):
    columns={c.get("caption", c.get("name", "").strip("[]")): c for c in root.findall("./datasources/datasource/column")}
    p=columns["Threshold Percent"]
    assert p.get("param-domain-type")=="any" and float(p.get("value"))==.03, "threshold-domain"
    assert columns["% Sales Per State"].find("calculation").get("formula") == "[Sales] / " + columns["Total Sales"].get("name"), "row share has correct total denominator"
    assert "All Other States" in columns["State Grouping"].find("calculation").get("formula"), "grouping-and-order"
    assert ">=" in columns["State Grouping"].find("calculation").get("formula"), "threshold equality stays listed"
    viz=root.find("./worksheets/worksheet[@name='Viz']")
    sort=viz.find("table/view/shelf-sorts/shelf-sort-v2")
    assert sort is not None and sort.get("direction")=="DESC" and columns["State Grouping"].get("name").strip("[]") in sort.get("dimension-to-sort"), "grouping-and-order descending retained states"
    panes=viz.findall("table/panes/pane")
    assert [p.find("mark").get("class") for p in panes]==["Bar", "GanttBar"], "dual-axis-labels"
    color_maps = root.xpath(".//encoding[@attr='color']/map/@to")
    assert "#28a1a7" in color_maps and "#bab0ac" in color_maps, "teal individual states and grey Other"
    buckets=root.xpath(".//encoding[@attr='color']/map/bucket/text()")
    assert "0" in buckets and "1" in buckets and '"0"' not in buckets, "numeric palette members must stay numeric"
    assert len(panes[1].findall("encodings/text"))==2
    assert panes[1].find("customized-label") is not None
    assert root.xpath(".//encoding[@synchronized='true']"), "synchronized axes"
    title="".join(viz.find("layout-options/title/formatted-text").itertext())
    for name in ["Count States Listed", "Count States Grouped"]:
        assert columns[name].get("name").strip("[]") in title, "count-summary"
        instances=viz.findall("table/view/datasource-dependencies/column-instance")
        tc=next(i.find("table-calc") for i in instances if i.get("column")==columns[name].get("name") and i.find("table-calc") is not None)
        assert tc.get("ordering-type")=="Field" and len(tc.findall("order"))==2, "counts address both nested row dimensions"
    line=panes[0].find("reference-line")
    assert line.get("scope")=="per-table" and columns["Threshold Line"].get("name").strip("[]") in line.get("value-column"), "threshold-reference"
    dashboard=root.find("./dashboards/dashboard")
    control=dashboard.find(".//zone[@type-v2='paramctrl']")
    assert control is not None and control.get("mode")=="type_in" and control.get("param")=="[Parameters].[Parameter 1]", "dashboard-control"
    assert dashboard.find("size").get("maxwidth")=="1100"

def independent_numerics():
    hyper=next((HERE/"inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint,str(hyper)) as c:
            table=c.catalog.get_table_names("Extract")[0]
            state_rows=c.execute_list_query(f'SELECT "State", SUM("Sales") FROM {table} GROUP BY "State"')
            total=float(c.execute_scalar_query(f'SELECT SUM("Sales") FROM {table}'))
            count=int(c.execute_scalar_query(f'SELECT COUNT(*) FROM {table}'))
    assert count==9994 and len(state_rows)==49
    assert math.isclose(total,2297200.8603,abs_tol=1e-6)
    result={"rows":count,"states":len(state_rows),"total_sales":total,"thresholds":{}}
    for threshold in [.01,.03,.05]:
        listed=sorted([(state,float(sales)/total) for state,sales in state_rows if float(sales)/total>=threshold],key=lambda x:(-x[1],x[0]))
        grouped=[(state,float(sales)/total) for state,sales in state_rows if float(sales)/total<threshold]
        rows=[{"state_grouping":state,"state_order":0,"share":share} for state,share in listed]
        if grouped:
            rows.append({"state_grouping":"All Other States","state_order":1,"share":sum(x[1] for x in grouped)})
        assert math.isclose(sum(r["share"] for r in rows),1,abs_tol=1e-12)
        assert rows[0]["state_grouping"]=="California" and rows[-1]["state_grouping"]=="All Other States"
        result["thresholds"][str(threshold)]={"listed":len(listed),"grouped":len(grouped),"rows":rows}
    assert [(result["thresholds"][str(t)]["listed"],result["thresholds"][str(t)]["grouped"]) for t in [.01,.03,.05]]==[(23,26),(10,39),(5,44)]
    return result

def main():
    check_contract(load_root())
    result=independent_numerics()
    result["workbook_sha256"]=hashlib.sha256((HERE/"outputs/replicated-workbook.twbx").read_bytes()).hexdigest()
    (HERE/"evidence").mkdir(exist_ok=True)
    (HERE/"evidence/local-verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("WW48 contract and full-state numeric validation passed")
if __name__=="__main__":main()
