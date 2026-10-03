"""Independent source-data oracle and generated-artifact contracts.
Acceptance: ww14-independent-data, ww14-artifact-contracts, ww14-cloud-states.
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

def oracle():
 records=source_records(['last_stage','value']);assert len(records)==1000
 stages=['Prospect','Lead','Qualified','Opportunity','Negotiations','Closed'];totals={s:0 for s in stages};counts=Counter()
 for stage,value in records:totals[stage]+=int(value);counts[stage]+=1
 assert sum(totals.values())==1807416 and totals['Closed']==84153
 running=0;expected={}
 for i,stage in enumerate(stages):
  running+=totals[stage];cumulative=sum(totals[s] for s in stages[i:]);expected[stage]={'order':i+1,'value':totals[stage],'Running Sum':running,'Window Sum':sum(totals.values()),'Cumulative Value':cumulative,'Closed Value':totals['Closed'],'% To Close':totals['Closed']/cumulative,'record_count':counts[stage]}
 assert expected['Closed']['% To Close']==1 and expected['Prospect']['Cumulative Value']==1807416
 return {'source_rows':len(records),'stage_count':6,'total_pipeline_value':sum(totals.values()),'closed_value':totals['Closed'],'stages':expected}

def verify_cloud(data,report):
 checks=[]
 if not report.get('states'):return checks
 for role in ['author','replica']:
  rows=csv_rows(HERE/f'outputs/cloud-{role}-pipeline.csv');seen=set()
  for row in rows:
   stage=row[next(k for k in row if k=='last_stage')];expected=data['stages'][stage]
   if 'Measure Names' in row:
    metric=row['Measure Names'].split(' along ')[0];assert (stage,metric) not in seen;seen.add((stage,metric))
    if metric in expected:numeric_equal(row['Measure Values'],expected[metric])
   else:
    for metric in ['value','Running Sum','Window Sum','Cumulative Value','Closed Value','% To Close']:
     key=next((k for k in row if k.lower()==metric.lower()),None)
     if key:numeric_equal(row[key],expected[metric]);seen.add((stage,metric))
  required={(stage,metric) for stage in data['stages'] for metric in ['value','Cumulative Value','% To Close']};assert required<=seen
  checks.append({'role':role,'scope':'All six current stage sums, reverse cumulative funnel values and closed-value ratios; additional running/window/closed fields checked when present.','checked_values':len(seen)})
 return checks

def verify():
 data=oracle();r=artifact();formulas=[n.get('formula','') for n in r.findall('.//datasources/datasource/column/calculation')]
 assert any('RUNNING_SUM(SUM([value]))'==f for f in formulas) and any('WINDOW_SUM(SUM([value]))'==f for f in formulas)
 assert len(r.findall('.//worksheet[@name="Percent to Close"]/table/panes/pane[@id]'))==2
 assert r.find('.//worksheet[@name="Percent to Close"]//pane/style/style-rule/format[@value="#7cadb2"]') is not None
 assert r.find('.//worksheet[@name="Data"]') is not None
 assert all(node.get('ordering-type')=='Columns' for node in r.findall('.//table-calc')), 'Tableau Columns is native Table Down addressing across stage rows'
 background=r.find('.//datasources/datasource/column[@caption="Full Bar"]').get('name').strip('[]')
 encoding=r.find('.//worksheet[@name="Percent to Close"]/table/style/style-rule[@element="axis"]/encoding[@fold="true"]')
 assert f'usr:{background}:qk' in encoding.get('field') and encoding.get('class')=='0'
 assert encoding.get('fold')=='true' and encoding.get('synchronized')=='true'
 assert r.find('.//worksheet[@name="Percent to Close"]/table/style/style-rule[@element="axis"]/format[@attr="render-fold-reversed"]').get('value')=='true'
 for name in ['Current Status','Overall Funnel']:
  axis=r.find(f'.//worksheet[@name="{name}"]/table/style/style-rule[@element="axis"]/encoding[@range-type="fixed"]')
  assert axis.get('min')=='0'
 zones=r.findall('.//dashboard/zones//zone');sheets=[next(n for n in zones if n.get('name')==name) for name in ['Current Status','Overall Funnel','Percent to Close']]
 assert len({n.get('y') for n in sheets})==len({n.get('h') for n in sheets})==1
 for name in ['Current Status','Overall Funnel','Percent to Close']:
  divs=r.findall(f'.//worksheet[@name="{name}"]/table/style/style-rule[@element="table-div"]/format[@attr="line-visibility"][@scope="rows"]')
  assert len(divs)==1 and divs[0].get('value')=='on'
 report=cloud_binding();checks=verify_cloud(data,report)
 result={'case':'ww14','passed':['ww14-independent-data','ww14-artifact-contracts']+(['ww14-cloud-states'] if checks else []),'cloud_status':'passed' if checks else 'pending','oracle':data,'cloud_checks':checks,'browser_interaction_executed':False}
 (HERE/'outputs/data-oracle.json').write_text(json.dumps(data,indent=2),encoding='utf-8');(HERE/'evidence/functional-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'passed':result['passed'],'cloud':result['cloud_status']}));return result
if __name__=='__main__':verify()
