"""Validate WW08 source, actions, visibility and independent numerical states."""
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
from collections import defaultdict
import json
from lxml import etree
from tableauhyperapi import HyperProcess,Connection,Telemetry
HERE=Path(__file__).resolve().parent
def verify():
    lock=json.loads((HERE/"inputs/source-lock.json").read_text(encoding="utf-8"))
    with ZipFile(HERE/"outputs/replicated-workbook.twbx") as z:
        root=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))
        for item in lock["extracted_data"]:
            path=HERE/item["file"]
            assert sha256(path.read_bytes()).hexdigest()==item["sha256"]
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==path.name))).hexdigest()==item["sha256"]
    # action-state-reset-contract
    actions=root.findall("actions/edit-parameter-action")
    assert len(actions)==2
    assert {a.find("source").get("worksheet") for a in actions}=={"Map","Reset Button"}
    assert all(a.find("activation").get("type")=="on-select" for a in actions)
    reset=next(a for a in actions if a.get("caption")=="Reset State")
    assert reset.find("clear-option").get("type")=="assign-fixed-value" and reset.find("clear-option").get("value")=="s:LROOT:"
    filters=root.findall("actions/action")
    assert len(filters)==2 and all(a.find("source").get("worksheet")=="Reset Button" for a in filters)
    shared=[next(f for f in root.find("worksheets/worksheet[@name='"+name+"']").findall("table/view/filter") if "Customer Name" in f.get("column")) for name in ["Customer Orders","KPIs-Customer"]]
    assert shared[0].get("filter-group") and shared[0].get("filter-group")==shared[1].get("filter-group")
    # dynamic-visibility-contract
    db=root.find("dashboards/dashboard")
    graph=root.find("datagraph/graph")
    node=graph.find("nodes/dashboard-zone-visibility-node")
    assert node.get("dashboard-identifier")==db.find("simple-id").get("uuid")
    panel=db.find("zones//zone[@id='"+node.get("zone-id")+"']")
    assert panel is not None and panel.get("hidden-by-user")=="true"
    assert len(graph.findall("edges/edge"))==1
    assert panel.find(".//formatted-text/run[@bold='true']").text=="<[Parameters].[Parameter 1]>"
    control=panel.find(".//zone[@type-v2='filter']")
    assert control.get("values")=="relevant" and control.get("show-all")=="false"
    # independent-state-customer-product-oracle
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(next((HERE/"inputs").glob("*.hyper")))) as c:
        table=next(t for schema in c.catalog.get_schema_names() for t in c.catalog.get_table_names(schema))
        rows=c.execute_list_query('SELECT "State/Province","Customer Name","Product Name","Sales","Profit","Quantity" FROM '+str(table))
    result={"row_count":len(rows),"states":[],"csv_scope":"Cloud dashboard export covers one sheet, identified separately; this locked Hyper oracle covers all KPI/customer/product states.","browser_events_executed":False}
    for state in ["","California","Texas"]:
        selected=[r for r in rows if not state or r[0]==state]
        sales=sum(float(r[3]) for r in selected);profit=sum(float(r[4]) for r in selected);qty=sum(int(r[5]) for r in selected)
        customers=sorted({r[1] for r in selected}); customer=customers[0]
        selected_customer=[r for r in selected if r[1]==customer]
        products=defaultdict(lambda:[0.,0])
        for r in selected_customer:products[r[2]][0]+=float(r[3]);products[r[2]][1]+=int(r[5])
        assert sales>0 and customers and products
        result["states"].append({"parameter":state,"panel_visible":bool(state),"sales":sales,"profit":profit,"profit_ratio":profit/sales,"quantity":qty,"relevant_customer_count":len(customers),"sample_customer":customer,"sample_customer_sales":sum(float(r[3]) for r in selected_customer),"sample_customer_profit":sum(float(r[4]) for r in selected_customer),"sample_customer_quantity":sum(int(r[5]) for r in selected_customer),"sample_customer_profit_ratio":sum(float(r[4]) for r in selected_customer)/sum(float(r[3]) for r in selected_customer),"sample_customer_products":[{"product":k,"sales":v[0],"quantity":v[1]} for k,v in sorted(products.items())]})
    assert len(rows)==9994
    target=HERE/"evidence";target.mkdir(exist_ok=True)
    (target/"data-contract.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    if (HERE/'evidence/cloud-verification.json').exists():
        from verify_cloud_data import verify as verify_cloud
        verify_cloud()
    print("WW08 source/action/DZV and three numerical states verified")
if __name__=="__main__":verify()
