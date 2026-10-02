"""Independent Hyper aggregation for each displayed sales grain and REST state."""
from pathlib import Path
from collections import defaultdict
from datetime import timedelta, date as Date
import json
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent
def compute():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process,Connection(process.endpoint,str(next((HERE/"inputs").glob("*.hyper")))) as connection:
        table=connection.catalog.get_table_names("Extract")[0]
        records=connection.execute_list_query(f'SELECT "Order Date", "Sub-Category", "State", "Sales" FROM {table}')
    assert len(records)==9994
    result={"weekly_boundary":"Sunday, independently established by original Cloud area-curve comparison against Sunday and Monday Hyper aggregation candidates", "source_records":len(records),"states":{}}
    for name,year,state in [("default",None,None),("year-2019",2019,None),("california",None,"California"),("year-2019-california",2019,"California")]:
        grains={key:defaultdict(float) for key in ["weekly","monthly","subcategory","subcategory_month","state","year"]}
        selected=0
        for date,category,region,sales in records:
            date=Date(date.year,date.month,date.day)
            if year and date.year!=year or state and region!=state:continue
            selected+=1
            month=date.strftime("%Y-%m")
            week=(date-timedelta(days=(date.weekday()+1)%7)).strftime("%Y-%m-%d")
            for key,value in [("weekly",week),("monthly",month),("subcategory",category),("subcategory_month",category+"|"+month),("state",region),("year",str(date.year))]:grains[key][value]+=float(sales)
        values={key:dict(sorted(value.items())) for key,value in grains.items()}
        totals=[sum(value.values()) for value in values.values()]
        assert max(totals)-min(totals)<0.00001
        result["states"][name]={"rows":selected,"sales":totals[0],**values,"subcategory_sales_order":sorted(values["subcategory"],key=values["subcategory"].get,reverse=True)}
    assert abs(result["states"]["default"]["sales"]-2297200.8603)<0.00001
    return result
if __name__=="__main__":
    result=compute()
    (HERE/"evidence").mkdir(exist_ok=True)
    (HERE/"evidence/data-contract.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print({name:{"rows":state["rows"],"sales":state["sales"]} for name,state in result["states"].items()})
