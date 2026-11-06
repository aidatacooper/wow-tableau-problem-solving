"""Independent raw Hyper SQL oracle and restricted emitted-formula evaluation."""
from pathlib import Path
from datetime import date,timedelta
from collections import defaultdict
import copy,hashlib,json,re,zipfile
from lxml import etree as E
from tableauhyperapi import HyperProcess,Telemetry,Connection
HERE=Path(__file__).resolve().parent
IDS=['customer-metrics','fixed-date-boundaries','sort-contract','product-tooltip-contract','dashboard-contract','negative-controls','product-rank','help-toggle','aligned-headings','metric-shelf']
def contract(root):
    cols=root.xpath('./datasources/datasource/column')
    names={c.get('name'):'['+c.get('caption')+']' for c in cols if c.get('caption')}
    formulas={}
    for c in cols:
        calc=c.find('calculation')
        if calc is not None:
            f=calc.get('formula')
            for internal,caption in names.items(): f=f.replace(internal,caption)
            formulas[c.get('caption')]=f
    customer=root.xpath('./worksheets/worksheet[@name="Customers"]')[0]
    assert 'Customer ID' in customer.findtext('table/rows')
    panes=customer.xpath('./table/panes/pane')
    assert [x.find('mark').get('class') for x in panes]==['Text','Bar','Bar','Bar','Circle']
    internal={c.get('caption'):c.get('name').strip('[]') for c in cols if c.get('caption')}
    for pane,field in zip(panes,['Recency Axis','Orders','Sales','Average Order Value','Quantity Axis']):
        assert internal.get(field,field) in pane.get('x-axis-name')
    assert internal['Active'] in panes[0].find('encodings/color').get('column')
    assert 'sum:Quantity' in panes[4].find('encodings/text').get('column')
    assert internal['Unique Products'] in panes[4].find('encodings/tooltip').get('column')
    # Pane definitions alone do not put metric axes on Tableau's visible shelf.
    shelf=customer.findtext('table/cols') or ''
    axis_refs=[pane.get('x-axis-name') for pane in panes]
    shelf_refs=re.findall(r'\[[^\]]+\]\.\[[^\]]+\]',shelf)
    assert shelf_refs==axis_refs, ('missing/reordered metric shelf',shelf,axis_refs)
    assert shelf.count('+')==4 and 'fold' not in shelf
    instances={x.get('name'):x for x in customer.xpath('./table/view/datasource-dependencies/column-instance')}
    for ref in shelf_refs:
        instance=instances[ref.split('].',1)[1]]
        assert instance.get('type')=='quantitative'
        column=instance.get('column')
        assert customer.xpath('./table/view/datasource-dependencies/column[@name="'+column+'"]')
    sort=customer.find('table/view/computed-sort')
    assert sort is not None and sort.get('direction')=='DESC' and 'Customer ID' in sort.get('column')
    sortid=next(c.get('name').strip('[]') for c in cols if c.get('caption')=='Sort Key')
    assert sortid in sort.get('using')
    products=root.xpath('./worksheets/worksheet[@name="Top Products"]')[0]
    assert products.xpath('.//filter[@context="true"][contains(@column,"Tooltip (Customer ID)")]')
    rankid=internal['Product Rank']
    rank_filter=products.xpath('.//filter[@class="quantitative"]')[0]
    assert rankid in rank_filter.get('column')
    assert rank_filter.findtext('min')=='1' and rank_filter.findtext('max')=='10'
    rank_instance=products.xpath('.//column-instance[@column="['+rankid+']"]')[0]
    assert rank_instance.find('table-calc').get('ordering-type')=='Field'
    address=rank_instance.find('table-calc').get('ordering-field')
    assert address and address.endswith('.[Product Name]')
    assert rank_instance.get('name') in rank_filter.get('column')
    assert internal['Recency Label'] in panes[0].find('encodings/text').get('column')
    assert ' days' in formulas['Recency Label'] and ' years' in formulas['Recency Label']
    sortparam=next(c for c in cols if c.get('caption')=='Sort Metric')
    assert sortparam.get('datatype')=='string' and 'Recency ascending' in sortparam.get('value')
    assert len(sortparam.findall('members/member'))==5
    assert '\\n' not in formulas['Help Text'] and formulas['Help Text'].isascii()
    assert 'Product Name' in products.findtext('table/rows')
    # Product Name is the sole addressing dimension; customer is a context filter.
    assert products.findtext('table/rows').count(':nk]')==1
    assert products.xpath('.//pane//text[contains(@column,"Multiple Values")]')
    assert any(rankid in x.get('member','') for x in products.xpath('.//groupfilter[@function="member"]'))
    assert rankid in products.findtext('.//manual-sort/dictionary/bucket')
    toggle=root.xpath('./dashboards/dashboard//zone[button/toggle-action]')
    assert len(toggle)==1
    button=toggle[0].find('button')
    assert button.get('active-visual-state-index')=='1'
    assert button.xpath('./button-visual-state/caption/text()')==['X','?']
    helpzone=root.xpath('./dashboards/dashboard//zone[@name="Help"]')[0]
    container=helpzone.getparent()
    assert container.get('type-v2')=='layout-flow' and container.get('hidden-by-user')=='true'
    assert 'zone-ids=['+container.get('id')+']' in button.findtext('toggle-action')
    assert root.xpath('./worksheets/worksheet[@name="Help"]//text')
    headings=['Customer','Recency','Orders','Revenue','Average order value','Quantity']
    textzones=root.xpath('./dashboards/dashboard//zone[@type-v2="text"]')
    for i,title in enumerate(headings):
        z=[z for z in textzones if ''.join(z.xpath('./formatted-text//text()'))==title]
        assert len(z)==1
        assert {k:z[0].get(k) for k in ['x','y','w','h']}==dict(x=str(1250+16250*i),y='15556',w='16250',h='4444')
    assert 'Top Products' in E.tostring(panes[4],encoding='unicode')
    size=root.find('./dashboards/dashboard/size')
    assert size.get('maxwidth')=='1600' and size.get('maxheight')=='900'
    assert len(root.xpath('.//zone[@type-v2="paramctrl"]'))==2
    assert formulas['Reference Date']=='#2022-01-01#' and formulas['Active Threshold']=='90'
    return formulas

def evaluate(expr,rows,formulas,params):
    expr=expr.strip()
    def run(s): return evaluate(s,rows,formulas,params)
    if expr in params: return params[expr]
    if re.fullmatch(r'#\d{4}-\d{2}-\d{2}#',expr): return date.fromisoformat(expr.strip('#'))
    if re.fullmatch(r'-?\d+(\.\d+)?',expr): return float(expr)
    if expr.startswith('CASE '):
        parameter=expr[5:expr.index(' WHEN ')]
        return run(dict(re.findall(r"WHEN '(.*?)' THEN (.*?)(?= WHEN | END)",expr))[run(parameter)])
    m=re.fullmatch(r"'(.*)'",expr)
    if m:return m[1]
    m=re.fullmatch(r'IF (.*?) THEN (.*?) ELSE (.*?) END',expr)
    if m:return run(m[2]) if run(m[1]) else run(m[3])
    m=re.fullmatch(r"(.*)\+('.*')",expr)
    if m:return str(run(m[1]))+run(m[2])
    m=re.fullmatch(r'STR\((.*)\)',expr)
    if m:
        value=run(m[1]);return str(int(value)) if float(value).is_integer() else str(value)
    m=re.fullmatch(r'ROUND\((.*),(\d+)\)',expr)
    if m:return round(run(m[1]),int(m[2]))
    m=re.fullmatch(r'IF (.*?) THEN (.*?) END',expr)
    if m: return run(m[2]) if run(m[1]) else None
    for op in ['<=','>=','<']:
        if op in expr:
            a,b=expr.split(op,1);a,b=run(a),run(b)
            return {'<=':lambda:a<=b,'>=':lambda:a>=b,'<':lambda:a<b}[op]()
    if '/' in expr:
        a,b=expr.split('/',1);return run(a)/run(b)
    if expr.startswith('-'): return -run(expr[1:])
    m=re.fullmatch(r"DATEDIFF\('day',(.*?),(.*?)\)",expr)
    if m:return (run(m[2])-run(m[1])).days
    if expr=='{FIXED [Customer ID]: MAX([Order Date])}':return max(r['Order Date'] for r in rows)
    m=re.fullmatch(r'(SUM|MIN|MAX|COUNTD|COUNT)\(\[(.*?)\]\)',expr)
    if m:
        op,field=m.groups();vals=[r[field] for r in rows] if field not in formulas else [run('['+field+']')]*len(rows)
        vals=[v for v in vals if v is not None]
        return {'SUM':lambda:sum(vals),'MIN':lambda:min(vals) if vals else None,'MAX':lambda:max(vals) if vals else None,'COUNTD':lambda:len(set(vals)),'COUNT':lambda:len(vals)}[op]()
    m=re.fullmatch(r'(?:\[Parameters\]\.)?\[(.*?)\]',expr)
    if m and m[1] in formulas:return run(formulas[m[1]])
    raise AssertionError('Unsupported expression '+expr)

def metrics(groups,oracle,formulas):
    results={}
    for cid,rows in groups.items():
        ev=lambda x:evaluate(x,rows,formulas,{})
        got=[ev('[Recency]'),ev('[Orders]'),ev('SUM([Sales])'),ev('[Average Order Value]'),ev('SUM([Quantity])'),ev('[Unique Products]')]
        assert all(abs(a-b)<1e-7 for a,b in zip(got,oracle[cid])),(cid,got,oracle[cid])
        assert ev('[Active]')==(got[0]<=90)
        assert ev('[Days Label]')==(got[0] if got[0]<365 else None)
        assert ev('[Years Label]')==(got[0]/365 if got[0]>=365 else None)
        assert ev('[Recency Label]')==(str(int(got[0]))+' days' if got[0]<365 else format(round(got[0]/365,1),'g')+' years')
        for choice,target in zip(['Recency ascending','Orders descending','Revenue descending','Average order value descending','Quantity descending'],[-got[0],got[1],got[2],got[3],got[4]]):
            assert abs(evaluate('[Sort Key]',rows,formulas,{'[Parameters].[Sort Metric]':choice})-target)<1e-7
        results[cid]=got
    return results

def main():
    workbook=HERE/'outputs/replicated-workbook.twbx';raw=next((HERE/'inputs').glob('*.hyper'))
    with zipfile.ZipFile(workbook) as z:
        root=E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        assert z.read(raw.name)==raw.read_bytes()
    formulas=contract(root);groups=defaultdict(list)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint,str(raw)) as c:
            fields=['Order ID','Order Date','Customer ID','Customer Name','Product ID','Product Name','Sales','Quantity']
            for values in c.execute_list_query('SELECT '+','.join('"'+f+'"' for f in fields)+' FROM "Extract"."Extract"'):
                r=dict(zip(fields,values));d=r['Order Date'];r['Order Date']=date(d.year,d.month,d.day);groups[r['Customer ID']].append(r)
            query="""SELECT "Customer ID", CAST(DATE '2022-01-01'-MAX("Order Date") AS INTEGER), COUNT(DISTINCT "Order ID"), SUM("Sales"), SUM("Sales")/COUNT(DISTINCT "Order ID"), SUM("Quantity"), COUNT(DISTINCT "Product ID") FROM "Extract"."Extract" GROUP BY "Customer ID" """
            oracle={r[0]:r[1:] for r in c.execute_list_query(query)}
            product_sql=c.execute_list_query('SELECT "Customer ID","Product Name",SUM("Sales"),SUM("Quantity") FROM "Extract"."Extract" GROUP BY "Customer ID","Product Name"')
            rank_sql=c.execute_list_query('SELECT "Customer ID", "Product Name", ROW_NUMBER() OVER (PARTITION BY "Customer ID" ORDER BY SUM("Sales") DESC, "Product Name" ASC) FROM "Extract"."Extract" GROUP BY "Customer ID", "Product Name"')
    results=metrics(groups,oracle,formulas);products=defaultdict(dict)
    for cid,name,sales,qty in product_sql:products[cid][name]=(sales,qty)
    for cid,rows in groups.items():
        py=defaultdict(lambda:[0.,0])
        for r in rows:py[r['Product Name']][0]+=r['Sales'];py[r['Product Name']][1]+=r['Quantity']
        assert py.keys()==products[cid].keys()
        for name,(s,q) in py.items():assert abs(s-products[cid][name][0])<1e-7 and q==products[cid][name][1]
        # Stable secondary name ordering is an oracle convention, not a claimed Tableau tie ordering.
        assert sorted(py,key=lambda n:(-py[n][0],n))[:10]==sorted(products[cid],key=lambda n:(-products[cid][n][0],n))[:10]
    synthetic={};expected={}
    for days in [0,89,90,91,364,365,366]:
        cid=str(days);synthetic[cid]=[{'Customer ID':cid,'Customer Name':'Same name','Order Date':date(2022,1,1)-timedelta(days=days),'Order ID':'one','Product ID':'p','Product Name':'P','Sales':10.,'Quantity':2} for _ in range(2)]
        expected[cid]=[days,1,20,20,4,1]
    metrics(synthetic,expected,formulas)
    for threshold in [0,90,365]:
        for cid,rows in synthetic.items():
            assert evaluate('[Active]',rows,formulas,{'[Parameters].[Active Threshold]':threshold})==(int(cid)<=threshold)
    negatives=[]
    mutations={'duplicate-orders':('Orders','COUNT([Order ID])'),'active-boundary':('Active','[Recency]<[Parameters].[Active Threshold]'),'weighted-recency-sort':('Sort Key',formulas['Sort Key'].replace('-MIN([Recency])','-SUM([Recency])')),'wrong-date':('Reference Date','#2021-01-01#'),'year-boundary':('Days Label','IF [Recency]<=365 THEN [Recency] END')}
    for name,(key,value) in mutations.items():
        bad=dict(formulas);bad[key]=value
        try:metrics(synthetic,expected,bad)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('Surviving mutation '+name)
    for name,path,attr,value in [('global-tooltip','.//filter[@context="true"]','context','false'),('reverse-sort','.//computed-sort','direction','ASC')]:
        bad=copy.deepcopy(root);bad.find(path).set(attr,value)
        try:contract(bad)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('Surviving mutation '+name)
    # Numerical expectation comes from SQL ROW_NUMBER, not sequential fixture ranks.
    # Tableau execution is reserved for parent REST recapture; addressing is structural.
    assert formulas['Product Rank']=="RANK_UNIQUE(SUM([Sales]), 'desc')"
    sql_ranks={(cid,name):rank for cid,name,rank in rank_sql}
    for cid,items in products.items():
        ordered=sorted(items,key=lambda n:(-items[n][0],n))
        assert all(sql_ranks[cid,name]==i for i,name in enumerate(ordered,1))
    # Independent SQL tied boundary fixture: both first and tenth positions tied.
    import sqlite3
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE sales(product TEXT, revenue REAL)')
        db.executemany('INSERT INTO sales VALUES (?,?)',[(str(i),v) for i,v in enumerate([100,100,90,80,70,60,50,40,30,20,20,10])])
        tie_ranks=db.execute('SELECT product, ROW_NUMBER() OVER (ORDER BY revenue DESC, product) FROM sales').fetchall()
        competition=db.execute('SELECT RANK() OVER (ORDER BY revenue DESC) FROM sales').fetchall()
        assert len({r for _,r in tie_ranks})==12 and sum(r<=10 for _,r in tie_ranks)==10
        assert len({r[0] for r in competition})<12
    negatives.append('competition-rank-ties')
    for name,mutate in [
        ('wrong-rank-address',lambda r:r.xpath('./worksheets/worksheet[@name="Top Products"]//column-instance/table-calc')[0].set('ordering-field','[wrong].[Customer ID]')),
        ('rows-rank-address',lambda r:r.xpath('./worksheets/worksheet[@name="Top Products"]//column-instance/table-calc')[0].set('ordering-type','Rows')),
        ('empty-metric-shelf',lambda r:setattr(r.xpath('./worksheets/worksheet[@name="Customers"]/table/cols')[0],'text','')),
        ('missing-toggle',lambda r:r.xpath('.//zone[button]')[0].remove(r.xpath('.//button')[0])),
        ('missing-rank',lambda r:r.xpath('./datasources/datasource/column[@caption="Product Rank"]')[0].set('caption','Removed Rank')),
        ('misaligned-heading',lambda r:r.xpath('.//zone[@type-v2="text"]')[2].set('x','0')),
        ('rank-eleven',lambda r:setattr(r.xpath('.//worksheet[@name="Top Products"]//filter[@class="quantitative"]/max')[0],'text','11'))]:
        bad=copy.deepcopy(root);mutate(bad)
        try:contract(bad)
        except (AssertionError,KeyError,IndexError):negatives.append(name)
        else:raise AssertionError('Surviving mutation '+name)
    failed=HERE/'outputs/runtime-failed-a89757a4-workbook.twbx'
    if failed.exists():
        with zipfile.ZipFile(failed) as z:
            failed_root=E.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
        try:contract(failed_root)
        except AssertionError:negatives.append('historical-runtime-empty-shelf')
        else:raise AssertionError('Historical runtime failure escaped regression check')
    report={'acceptance_passed'  :IDS,'ranked_customer_products':len(rank_sql),'sql_tie_fixture':tie_ranks,'customers':len(results),'rows':sum(map(len,groups.values())),'active_default':sum(v[0]<=90 for v in results.values()),'year_labels':sum(v[0]>=365 for v in results.values()),'negative_controls_rejected':negatives,'synthetic_recencies':[0,89,90,91,364,365,366],'workbook_sha256':hashlib.sha256(workbook.read_bytes()).hexdigest(),'limitations':'Emitted formula evaluation and XML contracts only; no Tableau render or real event. Top-ten tie ordering unspecified.'}
    (HERE/'evidence/verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
