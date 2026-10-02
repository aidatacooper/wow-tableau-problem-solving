"""Independent Hyper aggregates for all WW47 displayed subcategories and orders."""
from collections import defaultdict
from pathlib import Path
import json,math
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent

def verify(write=False):
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint,str(HERE/'inputs/Orders (Sample - Superstore).hyper')) as con:
            rows=con.execute_list_query('SELECT "Order ID","Order Date","Sub-Category","Category","Sales" FROM "Extract"."Extract"')
            sql_quarters=con.execute_list_query('SELECT "Sub-Category",EXTRACT(YEAR FROM "Order Date"),EXTRACT(QUARTER FROM "Order Date"),SUM("Sales") FROM "Extract"."Extract" GROUP BY 1,2,3 ORDER BY 1,2,3')
            sql_years=con.execute_list_query('SELECT "Sub-Category",EXTRACT(YEAR FROM "Order Date"),SUM("Sales") FROM "Extract"."Extract" GROUP BY 1,2 ORDER BY 1,2')
            sql_orders=con.execute_list_query('SELECT "Sub-Category","Order ID",SUM("Sales"),AVG("Sales"),COUNT(*) FROM "Extract"."Extract" GROUP BY 1,2 ORDER BY 1,2')
            sql_categories=con.execute_list_query('SELECT "Category",AVG("Sales") FROM "Extract"."Extract" GROUP BY 1 ORDER BY 1')
    assert len(rows)==9994
    latest=max(r[1].year for r in rows);assert latest==2018
    quarters=defaultdict(float);years=defaultdict(float);orders=defaultdict(list);categories=defaultdict(list)
    for order,date,sub,category,sales in rows:
        quarters[(sub,date.year,(date.month-1)//3+1)]+=sales;years[(sub,date.year)]+=sales;orders[(sub,order)].append(sales);categories[category].append(sales)
        jitter=(int(order[-6:])*7919 % 997)/997.0;assert 0<=jitter<1
    for sub,year,quarter,sales in sql_quarters:assert math.isclose(quarters[(sub,int(year),int(quarter))],sales,abs_tol=1e-7)
    for sub,year,sales in sql_years:assert math.isclose(years[(sub,int(year))],sales,abs_tol=1e-7)
    for sub,order,total,average,count in sql_orders:
        rs=orders[(sub,order)];assert len(rs)==count and math.isclose(sum(rs),total,abs_tol=1e-7) and math.isclose(sum(rs)/len(rs),average,abs_tol=1e-7)
    for category,average in sql_categories:assert math.isclose(sum(categories[category])/len(categories[category]),average,abs_tol=1e-7)
    subcategories=sorted({r[2] for r in rows});assert len(subcategories)==17 and len(sql_quarters)==271
    result={'rows':9994,'latest_year':latest,'quarters':[{'subcategory':s,'year':int(y),'quarter':int(q),'sales':round(v,6)} for s,y,q,v in sql_quarters],'year_comparison':{s:{'current':round(years[(s,latest)],6),'previous':round(years[(s,latest-1)],6)} for s in subcategories},'orders':[{'subcategory':s,'order':o,'sum_sales':round(total,6),'average_sales':round(avg,6),'records':n,'jitter':round((int(o[-6:])*7919 % 997)/997.0,12)} for s,o,total,avg,n in sql_orders],'order_reference_averages':{s:round(sum(sum(v) for (sub,o),v in orders.items() if sub==s)/sum(1 for sub,o in orders if sub==s),6) for s in subcategories},'category_averages':{c:round(v,6) for c,v in sql_categories},'csv_coverage':'Complete quarter/year/order/category oracles; dashboard REST CSV may export only Trend, so use individual worksheets for other domains.','jitter_policy':'Deterministic order-ID modulo jitter replaces author unsupported RANDOM(); vertical positions intentionally differ.'}
    assert math.isclose(sum(x['current'] for x in result['year_comparison'].values()),733215.2552,abs_tol=1e-5)
    path=HERE/'evidence/data-contract.json'
    if write:path.write_text(json.dumps(result,indent=2),encoding='utf8')
    else:assert json.loads(path.read_text())==result
    return result

if __name__=='__main__':
    import sys
    verify(write='--write' in sys.argv)
    print('PASS: 9994 records, 271 nonempty quarterly totals, 17 current/prior sales, all order/subcategory marks and category averages')
