"""Build from extracted data and public cwtwb APIs, starting with a blank workbook."""
from collections import defaultdict
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import cwtwb
from cwtwb import TWBEditor
from tableauhyperapi import Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition, TableName, Telemetry
HERE = Path(__file__).resolve().parent
SHEET = 'Frequency Matrix'
DASHBOARD = '2021 Week 49 - Frequency Matrix'
RAW_TABLE = 'Ann Jackson Superstore_DA38632F544945748F3F47B32661262D'


def prepare_model(raw_rows):
    """Aggregate each order/category before expansion, preventing line fanout.
    Empty domain cells carry NULL order ids: COUNTD=0, with blank visible marks.
    NONE exclusively represents unmatched partners in single-category orders.
    """
    orders = defaultdict(lambda: defaultdict(float))
    for order, category, sales in raw_rows:
        if order is None or category is None:
            raise ValueError('Order/category keys must be non-null')
        orders[order][category] += float(sales or 0)
    categories = sorted({c for values in orders.values() for c in values})
    pairs, facts = [], []
    for ri, row in enumerate(categories, 1):
        for ci, col in enumerate([None] + categories):
            key = f'{ri}:{ci}'
            pairs.append([key, row, col or 'NONE', -ci])
            matches = []
            for order, values in sorted(orders.items()):
                if row not in values or col == row:
                    continue
                if (col is None and len(values) == 1) or (col is not None and col in values):
                    matches.append([key, order, values[row], values.get(col)])
            facts.extend(matches or [[key, None, None, None]])
    return pairs, facts


def build():
    out = HERE / 'outputs'
    out.mkdir(exist_ok=True)
    raw = next((HERE / 'inputs').glob('*.hyper'))
    model = out / 'matrix.hyper'
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint, str(raw)) as conn:
            raw_rows = conn.execute_list_query(f'SELECT "Order ID", "Sub-Category", "Sales" FROM "Extract"."{RAW_TABLE}"')
        pairs, facts = prepare_model(raw_rows)
        with Connection(process.endpoint, str(model), CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema('Extract')
            for name, columns, records in [
                ('Pairs', [('Pair Key', SqlType.text()), ('Row Category', SqlType.text()), ('Column Category', SqlType.text()), ('Column Sort', SqlType.big_int())], pairs),
                ('Contributions', [('Fact Key', SqlType.text()), ('Order ID', SqlType.text()), ('Row Sales', SqlType.double()), ('Column Sales', SqlType.double())], facts),
            ]:
                table = TableDefinition(TableName('Extract', name), [TableDefinition.Column(n,t) for n,t in columns])
                conn.catalog.create_table(table)
                with Inserter(conn, table) as insert:
                    insert.add_rows(records)
                    insert.execute()
    editor = TWBEditor('')
    editor.set_hyper_connection(str(model), tables=[{'name':'Pairs'}, {'name':'Contributions'}],
        relationships=[{'left':'Pairs', 'right':'Contributions', 'keys':[['Pair Key','Fact Key']]}])
    calculations = [
        ('Orders','COUNTD([Order ID])','integer','measure','quantitative'),
        ('Visible Orders','IF [Orders]>0 THEN [Orders] END','integer','measure','quantitative'),
        ('Row Index','INDEX()','integer','measure','quantitative'),
        ('Column Index','INDEX()','integer','measure','quantitative'),
        ('Triangle','[Row Index]>=[Column Index]','boolean','measure','nominal'),
        ('Average Row Sales','SUM([Row Sales])/[Orders]','real','measure','quantitative'),
        ('Average Column Sales','SUM([Column Sales])/[Orders]','real','measure','quantitative'),
        ('Second Title','IF [Column Category]="NONE" THEN "" ELSE " & " + [Column Category] END','string','dimension','nominal'),
        ('Category Word','IF [Column Category]="NONE" THEN "SUB-CATEGORY" ELSE "SUB-CATEGORIES" END','string','dimension','nominal'),
        ('Second Label','IF [Column Category]="NONE" THEN "" ELSE [Column Category]+":" END','string','dimension','nominal'),
    ]
    for name, formula, dtype, role, ft in calculations:
        editor.add_calculated_field(name,formula,datatype=dtype,role=role,field_type=ft,
            table_calc='Rows' if name in ['Row Index','Column Index','Triangle'] else None)
    for name in ['Orders','Visible Orders']:
        editor.set_field_format(name,'n#,##0')
    for name in ['Average Row Sales','Average Column Sales']:
        editor.set_field_format(name,'*"$"#,##0.00;("$"#,##0.00)')
    editor.add_worksheet(SHEET)
    editor.configure_layered_chart(SHEET,columns=['Column Category'],rows=['Row Category'],
        panes=[{'mark_type':'Square','color':'Visible Orders','label':'Visible Orders',
            'tooltip':['Orders','Average Row Sales','Average Column Sales','Second Title','Category Word','Second Label'],
            'mark_sizing_off':True,'mark_style':{'size':'1','has-stroke':'false','mark-labels-show':'true'}}],
        sort_field='Column Category',sort_descending='MIN(Column Sort)',sort_mode='computed',
        filters=[{'column':'Triangle','values':[True]}],
        table_calc_overrides={'Triangle':[
            {'ordering_type':'Rows'},
            {'field':'Row Index','ordering_type':'Field','ordering_field':'Row Category'},
            {'field':'Column Index','ordering_type':'Field','ordering_field':'Column Category'}]})
    editor.configure_worksheet_style(SHEET,hide_gridlines=True,hide_zeroline=True,
        hide_col_field_labels=True,hide_row_field_labels=True,hide_band_color=True,hide_sort_controls=True,
        pane_cell_style={'text-align':'center','vertical-align':'center'},
        pane_datalabel_style={'color-mode':'auto','font-weight':'bold','font-size':'10'},
        header_formats=[{'field':'Column Category','text-orientation':'-90','font-weight':'bold','height':'125','font-size':'9'},
                        {'field':'Row Category','font-weight':'bold','width':'140','font-size':'9'}],
        table_dividers=[{'scope':axis,'stroke-color':'#ffffff','stroke-size':'1','line-visibility':'on'} for axis in ['rows','cols']],
        color_style={'field':'Visible Orders','colors':['#f7fcfd','#e0ecf4','#bfd3e6','#9ebcda','#8c96c6','#8c6bb1','#88419d','#810f7c','#4d004b']})
    editor.configure_custom_tooltip(SHEET,[
        {'field':'Row Category','bold':True},{'field':'ATTR(Second Title)','bold':True},
        {'text':'\n'},{'field':'Orders','bold':True},{'text':' ORDERS WITH PRODUCTS FROM '},{'field':'ATTR(Category Word)'},
        {'text':'\n\nAVERAGE SALES CONTRIBUTION PER ORDER\n','bold':True},
        {'field':'Row Category'},{'text':':\t'},{'field':'Average Row Sales'},
        {'text':'\n'},{'field':'ATTR(Second Label)'},{'text':'\t'},{'field':'Average Column Sales'}])
    def box(x,y,w,h):
        return dict(x=round(x/1100*100000),y=round(y/900*100000),w=round(w/1100*100000),h=round(h/900*100000))
    def text_zone(text,x,y,w,h,size=10):
        return {'type':'text','runs':[{'text':text,'font_size':size}],'absolute':box(x,y,w,h)}
    editor.add_dashboard(DASHBOARD,width=1100,height=900,worksheet_names=[SHEET],layout={
        'type':'container','direction':'floating','children':[
            text_zone('WHICH SUB-CATEGORIES ARE FREQUENTLY ORDERED TOGETHER?',18,12,1064,40,20),
            text_zone('HOVER TO VIEW AVERAGE SALES CONTRIBUTION BY CATEGORY',18,56,1000,25),
            {'type':'worksheet','name':SHEET,'show_title':False,'fit':'entire','absolute':box(18,92,1064,735)},
            text_zone('CHALLENGE BY: ANN JACKSON | SOURCE RECREATION: DONNA COLES | #WOW2021 WEEK 49',18,842,1064,24,9),
            text_zone('https://www.workout-wednesday.com/2021w49tab/',18,868,1064,22,9)]})
    editor.set_active_dashboard(DASHBOARD)
    workbook = out/'replicated-workbook.twbx'
    editor.save(workbook)
    report = {'version':version('cwtwb'),'module':str(Path(cwtwb.__file__).resolve()),
        'module_sha256':sha256(Path(cwtwb.__file__).read_bytes()).hexdigest(),
        'raw_sha256':sha256(raw.read_bytes()).hexdigest(),'raw_rows':len(raw_rows),
        'cells':len(pairs),'contributions':len(facts),'workbook_sha256':sha256(workbook.read_bytes()).hexdigest()}
    (out/'build-provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return workbook

if __name__ == '__main__':
    print(build())
