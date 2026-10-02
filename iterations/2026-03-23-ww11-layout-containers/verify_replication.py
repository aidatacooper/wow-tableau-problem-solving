"""Locked input, container, computation and monthly independent oracle."""
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
            p=HERE/item["file"];assert sha256(p.read_bytes()).hexdigest()==item["sha256"]
            assert sha256(z.read(next(n for n in z.namelist() if Path(n).name==p.name))).hexdigest()==item["sha256"]
    # nested-layout-contract
    db=root.find("dashboards/dashboard")
    assert db.get("name")=="#WOW2026 Week 11" and db.find("size").get("maxwidth")=="1200"
    assert len(db.findall("zones//zone[@type-v2='layout-flow']"))>=10
    corners=db.findall("zones//_.fcp.DashboardRoundedCorners.true...format")
    assert len([c for c in corners if c.get("value")=="5"])==5
    assert len([c for c in corners if c.get("value")=="20"])==3
    assert root.find("document-format-change-manifest/_.fcp.DashboardRoundedCorners.true...DashboardRoundedCorners") is not None
    assert len(root.findall("worksheets/worksheet"))==10
    assert len(db.findall("zones//zone[@name]"))==10
    # current-prior-year-trends-and-quadrants-contract
    ds=root.find("datasources/datasource[@caption]")
    fields={c.get("caption"):c for c in ds.findall("column")}
    assert fields["CY"].find("calculation").get("formula")=="{MAX(YEAR([Order Date]))}"
    for metric in ["Sales","Profit","Profit Ratio"]:
        ws=root.find("worksheets/worksheet[@name='"+metric+" Over Time']")
        assert len(ws.findall("table/panes/pane/mark[@class='Line']"))==2
        assert ws.find("table/cols") is not None
    scatter=root.find("worksheets/worksheet[@name='Scatter']")
    assert len(scatter.findall(".//reference-line"))==2
    ci=scatter.find(".//column-instance[@column='"+fields["Above Below CY Sales & Profit"].get("name")+"']")
    assert ci.find("table-calc").get("ordering-type")=="Field"
    assert 'Sub-Category' in ci.find("table-calc").get("ordering-field")
    # independent-monthly-kpi-scatter-oracle
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,Connection(h.endpoint,str(next((HERE/"inputs").glob("*.hyper")))) as c:
        table=next(t for s in c.catalog.get_schema_names() for t in c.catalog.get_table_names(s) if 'Orders_' in str(t))
        rows=c.execute_list_query('SELECT "Order Date","Sub-Category","Order ID","Sales","Profit" FROM '+str(table))
    assert len(rows)==10194
    current=max(r[0].year for r in rows);prior=current-1
    months=defaultdict(lambda:[0.,0.]);cats=defaultdict(lambda:[0.,0.,set()])
    for date,cat,order,sales,profit in rows:
        months[date.year,date.month][0]+=float(sales);months[date.year,date.month][1]+=float(profit)
        if date.year==current:cats[cat][0]+=float(sales);cats[cat][1]+=float(profit);cats[cat][2].add(order)
    assert len(cats)==17 and all((current,m) in months and (prior,m) in months for m in range(1,13))
    means=[sum(v[i] for v in cats.values())/17 for i in [0,1]]
    result={"row_count":len(rows),"current_year":current,"prior_year":prior,"csv_scope":"Dashboard exports only one worksheet; independent Hyper oracle covers monthly sales/profit/ratio, KPI and all 17 scatter subcategories.","monthly":[{"year":y,"month":m,"sales":v[0],"profit":v[1],"profit_ratio":v[1]/v[0]} for (y,m),v in sorted(months.items()) if y in (current,prior)],"scatter":[]}
    for cat,(sales,profit,orders) in sorted(cats.items()):
        label='Below Both' if sales<=means[0] and profit<=means[1] else 'Above Sales Below Profit' if sales>=means[0] and profit<=means[1] else 'Above Sales Above Profit' if sales>=means[0] and profit>=means[1] else 'Below Sales Above Profit'
        result['scatter'].append({'subcategory':cat,'sales':sales,'profit':profit,'order_count':len(orders),'quadrant':label})
    result['kpis']={}
    for index,metric in enumerate(['sales','profit']):
        cy=sum(v[index] for (y,m),v in months.items() if y==current);py=sum(v[index] for (y,m),v in months.items() if y==prior)
        result['kpis'][metric]={'current':cy,'prior':py,'increase':(cy-py)/py}
    cy_ratio=sum(v[1]/v[0] for (y,m),v in months.items() if y==current);py_ratio=sum(v[1]/v[0] for (y,m),v in months.items() if y==prior)
    result['kpis']['profit_ratio']={'current':cy_ratio,'prior':py_ratio,'increase':cy_ratio-py_ratio,'aggregation':'SUM of INCLUDE year/month ratios, matching author, not overall profit / sales.'}
    out=HERE/'evidence';out.mkdir(exist_ok=True);(out/'data-contract.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if (HERE/'evidence/cloud-verification.json').exists():
        from verify_cloud_data import verify as verify_cloud
        verify_cloud()
    print('WW11 source, 10 worksheets, nested containers and monthly/scatter oracle verified')
if __name__=='__main__':verify()
