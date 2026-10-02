"""Independent Hyper oracle for all scatter LOD/measure combinations and brushing."""
from collections import defaultdict
from pathlib import Path
import hashlib,json,math
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent

def verify(write=False):
    groups=json.loads((HERE/'inputs/manufacturer-groups.json').read_text())
    mapping={product:maker for maker,products in groups.items() for product in products}
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint,str(HERE/'inputs/TEMP_1rs6x3z03rk5kn19aaa5k0h46p7f.hyper')) as connection:
            rows=connection.execute_list_query('SELECT "Customer Name","Product Name","Order ID","Quantity","Sales","Discount" FROM "Extract"."Extract"')
            sql=connection.execute_list_query('SELECT COUNT(*),COUNT(DISTINCT "Customer Name"),COUNT(DISTINCT "Product Name"),COUNT(DISTINCT "Order ID"),SUM("Quantity"),SUM("Sales"),SUM("Discount") FROM "Extract"."Extract"')[0]
    assert len(rows)==9994 and sql[:4]==[9994,793,1850,5009]
    assert sql[4]==37873 and math.isclose(sql[5],2297200.8603,abs_tol=1e-6)
    assert math.isclose(sql[6],1561.09,abs_tol=1e-6)
    unmatched=sorted({r[1] for r in rows if r[1] not in mapping})
    assert len(unmatched)==10, unmatched
    mapping.update({product:product for product in unmatched})
    result={'row_count':len(rows),'totals':{'Quantity':sql[4],'Sales':round(sql[5],6),'Discount':round(sql[6],6),'Orders':sql[3]},'lod_states':{},'csv_coverage':'Expected full scatter population and each percentage-bar partition are stored; Cloud dashboard CSV may expose only one sheet, so it cannot prove every mark.'}
    for level,index in [('Customer',0),('Product',1),('Manufacturer',1)]:
        buckets=defaultdict(list)
        for row in rows:buckets[mapping[row[index]] if level=='Manufacturer' else row[index]].append(row)
        values={name:{'Quantity':sum(r[3] for r in rs),'Sales':sum(r[4] for r in rs),'Orders':len({r[2] for r in rs}),'Discount':sum(r[5] for r in rs)} for name,rs in sorted(buckets.items())}
        assert sum(v['Quantity'] for v in values.values())==sql[4]
        assert math.isclose(sum(v['Sales'] for v in values.values()),sql[5],abs_tol=1e-6)
        selected=set(list(values)[:5])
        subsets={'empty':set(),'five_members':selected,'all':set(values)}
        selections={}
        for state,members in subsets.items():
            inrows=[r for r in rows if (mapping[r[index]] if level=='Manufacturer' else r[index]) in members]
            outrows=[r for r in rows if (mapping[r[index]] if level=='Manufacturer' else r[index]) not in members]
            partitions={}
            for measure,col in [('Quantity',3),('Sales',4),('Discount',5),('Orders',2)]:
                measure_value=lambda rs:len({r[2] for r in rs}) if measure=='Orders' else sum(r[col] for r in rs)
                v_in=measure_value(inrows);v_out=measure_value(outrows)
                partitions[measure]={'in':round(v_in,6),'out':round(v_out,6),'fraction':round(v_in/(v_in+v_out),12) if v_in+v_out else 0}
                assert 0<=partitions[measure]['fraction']<=1
                if measure!='Orders':assert math.isclose(v_in+v_out,sql[{'Quantity':4,'Sales':5,'Discount':6}[measure]],abs_tol=1e-6)
            partitions['LOD']={'in':len(members),'out':len(values)-len(members),'fraction':len(members)/len(values)}
            selections[state]={'members':sorted(members),'partitions':partitions}
        result['lod_states'][level]={'mark_count':len(values),'marks':values,'selections':selections,'axis_combinations':16}
    path=HERE/'evidence/data-contract.json'
    if write:path.write_text(json.dumps(result,indent=2),encoding='utf8')
    else:assert json.loads(path.read_text())==result,'Independent data oracle changed'
    return result

if __name__=='__main__':
    import sys
    verify(write='--write' in sys.argv)
    print('PASS: full 9994 rows, 48 axis/LOD combinations, empty/five/all set partitions; distinct orders need not be additive across overlapping LOD groups')
