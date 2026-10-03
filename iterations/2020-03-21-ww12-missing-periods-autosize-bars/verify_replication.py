"""Independent source-data oracle and generated-artifact contracts.
Acceptance: ww12-independent-data, ww12-artifact-contracts, ww12-cloud-states.
No browser interaction is claimed.
"""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
import calendar, json, math, csv
from lxml import etree
from tableauhyperapi import Connection, HyperProcess, Telemetry
HERE=Path(__file__).resolve().parent

def source_records(columns):
 lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
 item=lock['extracted_data'][0];inputfile=HERE/item['file']
 assert sha256(inputfile.read_bytes()).hexdigest()==item['sha256']
 with ZipFile(HERE/'outputs/replicated-workbook.twbx') as z:
  packaged=[name for name in z.namelist() if name.endswith('.hyper')]
  assert len(packaged)==1 and sha256(z.read(packaged[0])).hexdigest()==item['sha256']
 with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp, Connection(hp.endpoint,str(inputfile)) as c:
  table=next(t for schema in c.catalog.get_schema_names() for t in c.catalog.get_table_names(schema))
  return c.execute_list_query('SELECT '+', '.join('"'+name+'"' for name in columns)+' FROM '+str(table))

def artifact():
 with ZipFile(HERE/'outputs/replicated-workbook.twbx') as z:
  r=etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb'))))
 assert r.find('dashboards/dashboard') is not None
 return r

def cloud_binding():
 path=HERE/'evidence/cloud-verification.json'
 if not path.exists():return {'status':'pending','states':[]}
 report=json.loads(path.read_text(encoding='utf-8'))
 assert report['source_hashes']['replica']==sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest()
 provenance=json.loads((HERE/'evidence/export-provenance.json').read_text(encoding='utf-8'))
 assert report['source_hashes']['author']==provenance['comparison_sha256']
 def check(value):
  if isinstance(value,dict):
   if 'path' in value and 'sha256' in value:assert sha256((HERE/value['path']).read_bytes()).hexdigest()==value['sha256']
   for child in value.values():check(child)
  elif isinstance(value,list):
   for child in value:check(child)
 check(report['states']);assert report['browser_interaction_executed'] is False
 return report

def parse_date(text):
 for fmt in ['%Y-%m-%d','%B %d, %Y','%m/%d/%Y','%d/%m/%Y','%b %d, %Y','%d %b %y','%Y-%m-%d %H:%M:%S','%B %d, %Y %H:%M:%S']:
  try:return datetime.strptime(text,fmt).date()
  except ValueError:pass
 raise AssertionError(('Unrecognized date',text))

def number(text):
 text=text.strip().replace('$','').replace(',',''); negative=text.startswith('(');text=text.strip('()')
 return float(text.rstrip('%'))*(-1 if negative else 1)/(100 if text.endswith('%') else 1)

def numeric_equal(text,expected):
 cleaned=text.strip().replace('$','').replace(',','').strip('()').rstrip('%')
 places=len(cleaned.split('.')[1]) if '.' in cleaned else 0
 tolerance=0.5*10**(-places)/(100 if text.strip().endswith('%') else 1)+1e-7
 assert abs(number(text)-expected)<=tolerance,(text,expected,tolerance)

def csv_rows(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def oracle():
 records=source_records(['Order Date','Order ID','Sub-Category','Profit']);latest=max(d.year for d,_,_,_ in records);assert len(records)==9994 and latest==2019
 states={}
 for state,period,years in [('default','week',2),('daily','day',2),('monthly','month',2),('four-years','month',4)]:
  buckets=defaultdict(lambda:{'orders':set(),'profits':[]})
  for day,order,category,profit in records:
   if category!='Tables' or day.year<latest-years+1:continue
   day=date(day.year,day.month,day.day)
   key=day if period=='day' else (day-timedelta(days=(day.weekday()+1)%7) if period=='week' else day.replace(day=1))
   buckets[key]['orders'].add(order);buckets[key]['profits'].append(float(profit))
  data={day.isoformat():{'orders':len(v['orders']),'profit':math.fsum(v['profits'])} for day,v in sorted(buckets.items())}
  assert data and len(data)<(max(buckets)-min(buckets)).days+1
  states[state]={'period':period,'years':years,'selected_category':'Tables','size':{'day':1,'week':5,'month':10}[period],'periods':data,'distinct_period_count':len(data)}
 return {'source_rows':len(records),'latest_year':latest,'subcategories':sorted({row[2] for row in records}),'states':states}

def verify_cloud(data,report):
 checks=[]
 if not report.get('states'):return checks
 for state in report['states']:
  expected=data['states'][state['name']]['periods'];suffix='' if state['name']=='default' else '-'+state['name']
  for role in ['author','replica']:
   rows=csv_rows(HERE/f'outputs/cloud-{role}-chart{suffix}.csv');actual={}
   for row in rows:
    day=parse_date(row[next(k for k in row if 'Date to Plot' in k)]).isoformat()
    orderskey=next(k for k in row if 'Number of Orders' in k);profitkey=next(k for k in row if k=='Profit' or 'SUM(Profit)' in k)
    assert day not in actual;actual[day]=row
    assert int(number(row[orderskey]))==expected[day]['orders'];numeric_equal(row[profitkey],expected[day]['profit'])
    assert int(number(row['Size']))==data['states'][state['name']]['size']
   assert set(actual)==set(expected),(state['name'],role,len(actual),len(expected))
   selector=csv_rows(HERE/f'outputs/cloud-{role}-selector{suffix}.csv')
   assert len(selector)==17 and {row['Sub-Category'] for row in selector}==set(data['subcategories'])
   for row in selector:
    assert row['True']=='True' and row['False']=='False'
    if role=='author':assert row['In / Out of Selected Sub-Category']==('In' if row['Sub-Category']=='Tables' else 'Out')
    else:assert row['Selector Label']==((chr(0x25cf) if row['Sub-Category']=='Tables' else chr(0x25cb))+' '+row['Sub-Category'])
   checks.append({'state':state['name'],'role':role,'selector_domain_count':17,'period_count':len(actual),'scope':'Every selected Tables date-period mark, distinct orders and profit; gaps remain absent marks on continuous axis.'})
 return checks

def verify():
 data=oracle();r=artifact();sheet=r.find('.//worksheet[@name="Chart"]')
 date_field=r.find('.//datasources/datasource/column[@caption="Date to Plot"]').get('name').strip('[]')
 assert f'none:{date_field}:qk' in (sheet.find('table/cols').text or '')
 size_field=r.find('.//datasources/datasource/column[@caption="Size"]').get('name').strip('[]')
 assert f'none:{size_field}:qk' in sheet.find('.//encodings/size').get('column')
 sizing=sheet.find('.//mark-sizing')
 assert sizing is not None and sizing.get('mark-sizing-setting')=='marks-scaling-on' and sizing.get('mark-alignment')=='mark-alignment-center'
 names=[child.get('name') for parent in r.findall('.//actions') for child in parent if child.get('name')]
 assert len(names)==len(set(names)),('Duplicate action identity',names)
 assert r.find('document-format-change-manifest/GroupActionSingleSelect') is not None
 action=r.find('.//edit-group-action');assert action is not None
 text=etree.tostring(action).decode();assert 'on-select' in text and 'Selector' in text and 'Selected Sub-Category' in text and 'do-nothing' in text and 'assign' in text
 title=etree.tostring(r.find('.//worksheet[@name="Chart"]/layout-options/title')).decode()
 assert '[Parameters].[Parameter 1]' in title and 'Profit by Orders' in title
 assert 'DESIGNED BY: LORNA BROWN' in etree.tostring(r).decode()
 hidden=r.find('.//dashboard/zones//zone[@hidden-by-user="true"]')
 assert hidden.find('zone-style/format[@attr="border-style"]').get('value')=='dashed'
 assert hidden.find('zone-style/format[@attr="border-width"]').get('value')=='1'
 assert all(n.get('hidden-by-user')=='true' for n in hidden.findall('zone'))
 toggle=r.find('.//toggle-action');assert toggle is not None and 'zone-ids=' in toggle.text
 assert r.find('.//zone[@hidden-by-user="true"]') is not None
 for zone in r.findall('.//dashboard/zones//zone'):
  values={key:int(zone.get(key,'0')) for key in ['x','y','w','h']}
  assert all(0<=v<=100000 for v in values.values()),('Out-of-bounds dashboard zone',zone.attrib)
  assert values['x']+values['w']<=100000 and values['y']+values['h']<=100000,zone.attrib
 report=cloud_binding();checks=verify_cloud(data,report)
 result={'case':'ww12','passed':['ww12-independent-data','ww12-artifact-contracts']+(['ww12-cloud-states'] if checks else []),'cloud_status':'passed' if checks else 'pending','oracle':data,'cloud_checks':checks,'browser_interaction_executed':False}
 (HERE/'outputs/data-oracle.json').write_text(json.dumps(data,indent=2),encoding='utf-8');(HERE/'evidence/functional-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps({'passed':result['passed'],'cloud':result['cloud_status']}));return result
if __name__=='__main__':verify()
