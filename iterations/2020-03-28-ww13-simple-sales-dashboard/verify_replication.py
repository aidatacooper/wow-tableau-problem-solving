"""Independent source-data oracle and generated-artifact contracts.
Acceptance: ww13-independent-data, ww13-artifact-contracts, ww13-cloud-states.
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
 for fmt in ['%Y-%m-%d','%B %d, %Y','%m/%d/%Y','%d/%m/%Y','%b %d, %Y','%Y-%m-%d %H:%M:%S','%B %d, %Y %H:%M:%S']:
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

def oracle(mapped_yesterday=None):
 records=source_records(['Order Date','Sales','Profit']);latest=max(d.year for d,_,_ in records);assert len(records)==9994 and latest==2019
 today=date.today();yesterday=mapped_yesterday or (date(latest,today.month,today.day)-timedelta(days=1));month=yesterday.replace(day=1)
 prev_year=yesterday.year-(1 if yesterday.month==1 else 0);prev_month=12 if yesterday.month==1 else yesterday.month-1
 previous_yesterday=date(prev_year,prev_month,min(yesterday.day,calendar.monthrange(prev_year,prev_month)[1]));previous_month=previous_yesterday.replace(day=1)
 rows=[(date(d.year,d.month,d.day),float(s),float(p)) for d,s,p in records];included=[r for r in rows if r[0].year>=latest-1 and r[0]<=yesterday]
 metrics={};monthly=defaultdict(list)
 for day,sales,profit in included:monthly[(day.year,day.month)].append((sales,profit))
 for metric,index in [('Sales',1),('Profit',2)]:
  current=math.fsum(r[index] for r in included if month<=r[0]<=yesterday);previous=math.fsum(r[index] for r in included if previous_month<=r[0]<=previous_yesterday)
  metrics.update({f'Current MTD {metric}':current,f'Previous MTD {metric}':previous,f'MoM {metric}':current-previous,f'Run Rate {metric}':current/yesterday.day*calendar.monthrange(yesterday.year,yesterday.month)[1],f'Current YTD {metric}':math.fsum(r[index] for r in included if r[0].year==latest)})
 return {'source_rows':len(rows),'latest_year':latest,'local_execution_date':today.isoformat(),'mapped_yesterday':yesterday.isoformat(),'day_counts':{'Days in Current MTD':yesterday.day,'Days in Current Full Month':calendar.monthrange(yesterday.year,yesterday.month)[1]},'metrics':metrics,'monthly':{f'{year}-{month:02d}':{'Sales':math.fsum(v[0] for v in values),'Profit':math.fsum(v[1] for v in values)} for (year,month),values in sorted(monthly.items())},'official_reference_2020_03_24':{'mapped_yesterday':'2019-03-23','scope':'Original challenge date context only; paired runtime acceptance retains author TODAY and is independently mapped from Date CSV.'}}

def verify_cloud(data,report):
 checks=[]
 if not report.get('states'):return data,checks
 for role in ['author','replica']:
  dates=csv_rows(HERE/f'outputs/cloud-{role}-date.csv');assert len(dates)==1
  row=dates[0];key=next(k for k in row if 'Yesterday' in k);mapped=parse_date(row[key]);expected=oracle(mapped)
  assert mapped.year==expected['latest_year'];capture_date=datetime.fromisoformat(report['captured_at']).date()
  mapped_capture=date(expected['latest_year'],capture_date.month,capture_date.day)-timedelta(days=1)
  assert abs((mapped-mapped_capture).days)<=1 # Cloud/site timezone may differ from local Asia/Shanghai.
  metrics=csv_rows(HERE/f'outputs/cloud-{role}-metrics.csv');seen=set()
  for row in metrics:
   name=row['Measure Names'];assert name in expected['metrics'] or name in expected['day_counts']
   numeric_equal(row['Measure Values'],expected['metrics'][name] if name in expected['metrics'] else expected['day_counts'][name]);seen.add(name)
  assert set(expected['metrics'])<=seen and seen<=set(expected['metrics'])|set(expected['day_counts'])
  for metric in ['Sales','Profit']:
   rows=csv_rows(HERE/f'outputs/cloud-{role}-{metric.lower()}.csv');seen=set()
   for row in rows:
    year=int(row[next(k for k in row if 'Year' in k or 'YEAR' in k)]);monthtext=row[next(k for k in row if 'Month' in k or 'MONTH' in k)]
    try:month=int(monthtext)
    except ValueError:
     month=(list(calendar.month_name).index(monthtext) if monthtext in calendar.month_name else list(calendar.month_abbr).index(monthtext))
    bucket=f'{year}-{month:02d}';assert bucket not in seen;numeric_equal(row[metric],expected['monthly'][bucket][metric]);seen.add(bucket)
   assert seen==set(expected['monthly'])
  checks.append({'role':role,'mapped_yesterday_from_date_view':mapped.isoformat(),'metrics':len(expected['metrics']),'monthly_marks':len(expected['monthly']),'scope':'All ten KPI calculations and every included year/month Sales and Profit mark; Date export provides independent TODAY mapping baseline.'})
  data[role+'_cloud_oracle']=expected
 return data,checks

def verify():
 data=oracle();r=artifact();formulas=[n.get('formula','') for n in r.findall('.//datasources/datasource/column/calculation')];assert any('TODAY()' in f and 'MAKEDATE' in f for f in formulas)
 assert len(r.findall('.//worksheet[@name="KPI"]/table/panes/pane'))==2
 date_column=r.find('.//datasources/datasource/column[@caption="Yesterday"]')
 assert date_column.get('datatype')=='date'
 date_ref=r.find('.//worksheet[@name="Date"]//encodings/text').get('column')
 assert f'none:{date_column.get("name").strip("[]")}:qk' in date_ref
 buckets=[n.text for n in r.findall('.//datasources/datasource/style//bucket')]
 assert '"Current"' in buckets and '"Previous"' in buckets
 for sheet in ['Sales','Profit']:assert r.find(f'.//worksheet[@name="{sheet}"]//breakdown').get('value')=='off'
 assert len(data['metrics'])==10 and len(data['monthly'])>=12
 report=cloud_binding();data,checks=verify_cloud(data,report)
 result={'case':'ww13','passed':['ww13-independent-data','ww13-artifact-contracts']+(['ww13-cloud-states'] if checks else []),'cloud_status':'passed' if checks else 'pending','oracle':data,'cloud_checks':checks,'browser_interaction_executed':False}
 (HERE/'outputs/data-oracle.json').write_text(json.dumps(data,indent=2),encoding='utf-8');(HERE/'evidence/functional-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'passed':result['passed'],'cloud':result['cloud_status']}));return result
if __name__=='__main__':verify()
