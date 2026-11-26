"""Independent full-data oracle and emitted-workbook contract checks.

Raw rows are summed in Python; packaged rows are independently aggregated in
Hyper SQL. Formula and addressing assertions bind those numbers to the native
Tableau encodings. This does not claim to execute Tableau's renderer.
"""
from collections import defaultdict
from pathlib import Path
import csv, hashlib, json, math, tempfile, zipfile
from lxml import etree as ET
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'outputs/replicated-workbook.twbx'
RAW = HERE / 'inputs/federated_1l2jyeb12pijk613twqta1.hyper'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def close(a, b): assert math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-7), (a,b)

def verify():
    # acceptance: source-data — packaged extract is byte-identical to locked input.
    lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf8'))
    assert sha(RAW)==lock['extracted_data'][0]['sha256']
    with zipfile.ZipFile(OUTPUT) as z:
        root=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        data=z.read(next(n for n in z.namelist() if n.endswith('.hyper')))
    assert hashlib.sha256(data).hexdigest()==sha(RAW)
    assert len(root.findall('./worksheets/worksheet'))==1
    ws=root.find('./worksheets/worksheet'); table=ws.find('table'); deps=table.find('view/datasource-dependencies')
    ds=deps.get('datasource')
    cols={c.get('caption', c.get('name').strip('[]')):c for c in deps.findall('column')}
    def ref(name, derivation='User'):
        local=cols[name].get('name')
        ci=next(c for c in deps.findall('column-instance') if c.get('column')==local and c.get('derivation')==derivation)
        return '['+ds+'].'+ci.get('name')
    # acceptance: sales-geometry — reject changed formulas and partitioning.
    formulas={'Year':'YEAR([Order Date])','Total Row':'MIN(1.5)','Segment Row':'MIN(0.5)',
              'Cumulative Sales':'RUNNING_SUM(SUM([Sales]))','Year Share':'SUM([Sales])/WINDOW_SUM(SUM([Sales]))'}
    for name, formula in formulas.items(): assert cols[name].find('calculation').get('formula')==formula
    assert table.findtext('cols')==ref('Cumulative Sales')
    assert table.findtext('rows')=='('+ref('Sub-Category','None')+' * ('+ref('Total Row')+' + '+ref('Segment Row')+'))'
    year_local='['+ds+'].'+cols['Year'].get('name')
    for name in ('Cumulative Sales','Year Share'):
        ci=next(c for c in deps.findall('column-instance') if c.get('column')==cols[name].get('name'))
        tc=ci.find('table-calc'); assert tc.get('ordering-type')=='Field'
        assert [o.get('field') for o in tc.findall('order')]==[year_local]
    panes=table.findall('panes/pane'); assert len(panes)==2
    for pane, row in zip(panes,('Total Row','Segment Row')):
        assert pane.get('y-axis-name')==ref(row)
        assert pane.find('mark').get('class')=='Bar'
        assert pane.find('encodings/size').get('column')==ref('Sales','Sum')
        sizing=pane.find('mark-sizing'); assert sizing is not None, 'Missing native axis-unit sizing'
        assert sizing.get('mark-sizing-setting')=='marks-scaling-on'
        assert sizing.get('mark-alignment')=='mark-alignment-right'
        assert sizing.get('use-custom-mark-size')=='false'
    assert not panes[0].findall('encodings/lod')
    assert panes[1].find('encodings/lod').get('column')==ref('Year','None')
    fixed=table.find('style/style-rule/encoding[@range-type="fixed"]')
    assert fixed is not None and fixed.get('field')==ref('Total Row')
    close(fixed.get('min'),-.3);close(fixed.get('max'),1.5)
    assert table.find('style/style-rule/encoding[@synchronized="true"]').get('field')==ref('Segment Row')
    # acceptance: descending-order
    sort=table.find('view/shelf-sorts/shelf-sort-v2')
    assert sort.get('direction')=='DESC' and sort.get('dimension-to-sort')==ref('Sub-Category','None')
    assert sort.get('measure-to-sort-by')==ref('Sales','Sum')
    # acceptance: tooltip-contract — annual raw sum, not running sum.
    texts=[''.join(p.find('customized-tooltip/formatted-text').itertext()) for p in panes]
    assert ref('Sales','Sum') in texts[0] and 'Total Sales' in texts[0]
    assert all(ref(n,d) in texts[1] for n,d in [('Sales','Sum'),('Year','None'),('Year Share','User')])
    assert ref('Cumulative Sales') not in texts[1]
    # acceptance: layout-contract — Desktop must confirm rendered geometry separately.
    dash=root.find('./dashboards/dashboard'); size=dash.find('size')
    assert size.get('maxwidth')=='1000' and size.get('maxheight')=='800'
    assert len(dash.findall('.//zone[@name="Segmented Sales"]'))==1
    assert table.find('style/style-rule[@element="label"]/format[@attr="vertical-align"]').get('value')=='top'
    assert not root.findall('.//actions/action') and not root.findall('.//filter')
    oracle=defaultdict(list)
    with tempfile.TemporaryDirectory(dir=HERE/'outputs') as temporary:
        packaged=Path(temporary)/'packaged.hyper';packaged.write_bytes(data)
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={'log_dir':str(HERE/'outputs')}) as h:
            with Connection(h.endpoint,str(RAW)) as c:
                rows=c.execute_list_query('SELECT "Order Date", "Sub-Category", "Sales" FROM "Extract"."Extract"')
            for date,category,sales in rows:oracle[(category,date.year)].append(float(sales))
            with Connection(h.endpoint,str(packaged)) as c:
                actual=c.execute_list_query('SELECT "Sub-Category", EXTRACT(YEAR FROM "Order Date"), SUM("Sales") FROM "Extract"."Extract" GROUP BY 1,2')
    expected={key:math.fsum(values) for key,values in oracle.items()}
    assert len(rows)==10194 and len(expected)==68 and len(actual)==68
    for category,year,sales in actual:close(sales,expected[(category,int(year))])
    totals={category:math.fsum(v for (cat,year),v in expected.items() if cat==category) for category,year in expected}
    assert len(totals)==17 and {year for category,year in expected}=={2021,2022,2023,2024}
    records=[]
    for rank,category in enumerate(sorted(totals,key=lambda k:-totals[k]),1):
        endpoint=0;shares=[]
        for year in sorted(y for cat,y in expected if cat==category):
            value=expected[(category,year)]; start=endpoint;endpoint+=value;share=value/totals[category];shares.append(share)
            records.append({'rank':rank,'sub_category':category,'year':year,'sales':value,'total_sales':totals[category],
                            'segment_start':start,'segment_end':endpoint,'year_share':share})
        close(endpoint,totals[category]);close(sum(shares),1)
    with (HERE/'outputs/numerical-acceptance.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    result={'status':'PASS','scope':'static structure and full-data numerical oracle; Desktop/render/hover pending',
            'workbook_sha256':sha(OUTPUT),'input_sha256':sha(RAW),'source_rows':len(rows),'sub_categories':len(totals),
            'year_segments':len(expected),'grand_total':math.fsum(totals.values()),'top_category':max(totals,key=totals.get),
            'acceptance_ids':['source-data','sales-geometry','descending-order','tooltip-contract','layout-contract']}
    (HERE/'outputs/static-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':verify()
