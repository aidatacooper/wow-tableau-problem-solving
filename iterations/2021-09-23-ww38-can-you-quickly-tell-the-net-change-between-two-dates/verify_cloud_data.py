"""Frozen-artifact Cloud comparison: original Step sheets, replica, raw Hyper.

Checks default, a July range with one-year history, and a single-day selection
with one-month history. Reconciles daily sales, endpoint dates and amounts,
net changes, percentages, and positive/negative trend classification.
"""
import argparse
import csv
from datetime import date, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
STATES = {
 'default': (date(2021,9,6), date(2021,9,20), '6 MONTHS'),
 'july-range': (date(2021,7,1), date(2021,7,31), '1 YEAR'),
 'single-day': (date(2021,9,7), date(2021,9,7), '1 MONTH'),
}

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def read_rows(path):
 with path.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.reader(f); headers=next(reader)
  for cells in reader:
   row={}
   for key,value in zip(headers,cells):
    if value:
     key=key.strip()
     assert key not in row or row[key]==value,(path.name,key,row.get(key),value)
     row[key]=value
   yield row

def number(text):
 s=text.strip(); neg=s.startswith(('▼','('))
 for c in '$,+%▲▼()':s=s.replace(c,'')
 n=float(s)
 if neg:n=-abs(n)
 return n/100 if '%' in text else n

def day(text):
 for fmt in ('%m/%d/%Y','%b %d, %Y','%Y-%m-%d','%m/%d/%Y %I:%M:%S %p'):
  try:return datetime.strptime(text,fmt).date()
  except ValueError:pass
 raise ValueError(text)

def near(actual,expected,tolerance,where):
 assert abs(number(actual)-expected)<=tolerance,(where,actual,expected)

def raw_daily():
 lock=json.loads((HERE/'inputs/source-lock.json').read_text(encoding='utf-8'))
 item=next(x for x in lock['extracted_data'] if 'Orders ' in x['file'])
 path=HERE/item['file'];assert digest(path)==item['sha256']
 with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
  with Connection(h.endpoint,str(path)) as c:
   rows=c.execute_list_query('SELECT "Order Date", "Region", "Sales" FROM "Extract"."Extract"')
 assert len(rows)==9994
 daily={}
 for d,r,s in rows:
  key=(r,date(d.year,d.month,d.day));daily[key]=daily.get(key,0.0)+float(s)
 return daily

def verify():
 daily=raw_daily()
 spec=importlib.util.spec_from_file_location('local_verifier',HERE/'verify_replication.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cap=json.loads((HERE/'evidence/cloud-verification.json').read_text(encoding='utf-8'))
 auth=json.loads((HERE/'evidence/author-data-exports.json').read_text(encoding='utf-8'))
 rep=json.loads((HERE/'evidence/replica-data-exports.json').read_text(encoding='utf-8'))
 sha=digest(HERE/'outputs/replicated-workbook.twbx')
 assert sha==cap['source_hashes']['replica']==rep['artifact_sha256'],'Frozen replica differs from capture/export'
 assert auth['artifact_sha256']==cap['source_hashes']['author']
 result=[]; hashes={};checks=0
 for state,(start,end,timeframe) in STATES.items():
  window_start,window_end=v.timeframe_window(timeframe,date(2021,9,20))
  expected={k:x for k,x in daily.items() if window_start<=k[1]<=window_end}
  facts={}
  for region in ['South','West','Central','East']:
   dates=sorted(d for r,d in daily if r==region and start<=d<=end)
   lo,hi=dates[0],dates[-1];a,b=daily[region,lo],daily[region,hi]
   facts[region]={'first':lo,'last':hi,'min':a,'max':b,'diff':b-a,'pct':(b-a)/a}
  def source(role,view):
   manifest=auth if role=='author' else rep
   entry=next(x for x in manifest['exports'] if x['state']==state and x['view']==view)
   path=HERE/entry['path'];assert digest(path)==entry['sha256'];hashes[entry['path']]=entry['sha256']
   return list(read_rows(path))
  # Original Step 2/3 contain native endpoint LoDs and signed KPI values;
  # all populated values are checked, including the aggregated null-date rows.
  endpoint_regions=set()
  for view in ['Step 2','Step 3']:
   for row in source('author',view):
    region=row['Region'].title();f=facts[region];endpoint_regions.add(region)
    for column,key,tol in [('Min Date Sales','min',0.00001),('Max Date Sales','max',0.00001),('Range Sales Diff','diff',0.0051),('Range Sales % Diff','pct',0.0005001)]:
     if column in row:near(row[column],f[key],tol,(state,view,region,column));checks+=1
    assert day(row['Min Selected Date Per Region'])==f['first']
    assert day(row['Max Selected Date Per Region'])==f['last']
  assert endpoint_regions==set(facts)
  # Each author step and replica Trend must contain exactly the same full
  # history domain, even though a second Area pane duplicates selected dates.
  for role,view in [('author','Step 1'),('author','Step 3'),('author','Step 5'),('replica','Trend')]:
   observed={}
   for row in source(role,view):
    region=row['Region'].title();f=facts[region]
    stamp=row.get('Order Date Day') or row.get('Selected Dates to Plot')
    if not stamp:continue # null-area mark aggregates all unselected days
    d=day(stamp);key=(region,d)
    sales_col='Sales' if 'Sales' in row else 'Sum of Sales'
    near(row[sales_col],expected[key],0.0051,(state,role,view,key));checks+=1
    if key in observed:near(row[sales_col],observed[key],0.00001,(state,view,key,'duplicate'))
    observed[key]=number(row[sales_col])
    if row.get('Selected Dates to Plot'):
     assert day(row['Selected Dates to Plot'])==d and start<=d<=end
    for band_sign, positive in [('+ve',True),('-ve',False)]:
     for bound, expected_date in [('Start',start),('End',end)]:
      field=f'Ref Line {bound} Date {band_sign}'
      if row.get(field):
       assert (f['diff']>=0)==positive,(state,region,field,'wrong sign')
       assert day(row[field])==expected_date,(state,region,field,row[field],expected_date)
    if 'Colour - Trend' in row:
     expected_colour=(1 if f['diff']>=0 else -1) if start<=d<=end else 0
     assert int(row['Colour - Trend'])==expected_colour,(state,role,view,key,row['Colour - Trend'],expected_colour)
   assert set(observed)==set(expected),(state,role,view,len(observed),len(expected),list(set(observed)^set(expected))[:10])
  kpi=source('replica','KPI');assert len(kpi)==4
  assert {r['Region'].title() for r in kpi}=={'South','West','Central','East'} # REST export order is not rendered row order
  for row in kpi:
   region=row['Region'].title();f=facts[region]
   near(row['Range Sales Diff'],f['diff'],0.0051,(state,region,'KPI diff'))
   near(row['Range Sales % Diff'],f['pct'],0.0005001,(state,region,'KPI pct'))
   checks+=2
   if 'Colour - KPI' in row:assert row['Colour - KPI'].lower()==str(f['diff']>=0).lower()
  subtitle=source('replica','Subtitle')
  assert len(subtitle)==1
  assert day(subtitle[0]['Selected Range Start Date'])==start
  assert day(subtitle[0]['Selected Range End Date'])==end
  selector=source('replica','Timeframe Selector')
  assert {r['Date Range'] for r in selector}=={'1 MONTH','6 MONTHS','YTD','1 YEAR','MAX'}
  if any('Timeframe Selected' in r for r in selector):
   assert {r['Date Range'] for r in selector if r.get('Timeframe Selected','').lower()=='true'}=={timeframe}
  result.append({'state':state,'selected_range':[start.isoformat(),end.isoformat()],'timeframe':timeframe,'daily_marks':len(expected),'regions':{r:{'net_change':round(f['diff'],6),'percent_change':f['pct']} for r,f in facts.items()},'result':'PASS'})
 report={'result':'PASS','artifact_sha256':sha,'source_hashes':cap['source_hashes'],'numeric_checks':checks,'states':result,'evidence_hashes':hashes,'acceptance_scope':'Cloud REST parameter states, original native values and raw locked-extract oracle; serialized actions checked separately. No browser clicks claimed.'}
 (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS',checks,'numeric checks;',[(s['state'],s['daily_marks']) for s in result])
 return report

if __name__=='__main__':verify()
