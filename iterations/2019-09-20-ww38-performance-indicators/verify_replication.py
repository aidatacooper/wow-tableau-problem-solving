from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE=Path(__file__).resolve().parent
def check(r):
 assert {'Chart','BAN','BAN:KPI','SubTitle'} <= {w.get('name') for w in r.xpath('./worksheets/worksheet')}
 f={c.get('caption'):c.find('calculation').get('formula') for c in r.xpath('.//column[calculation]')}
 assert 'MAKEDATE' in f['Date Aligned'] and 'RUNNING_SUM' in f['Running Sum Sales MTD This Year'] and 'IF ' in f['Colour BAN']
 assert '[Parameters].[Parameter 1]' in f['Category Filter']
 chart=r.xpath("./worksheets/worksheet[@name='Chart']")[0]
 assert {'Area','Line'} <= {m.get('class') for m in chart.xpath('.//pane/mark')}
 assert chart.xpath('.//reference-line[@label="TODAY"]')
 assert chart.xpath("./table/cols[contains(., '[none:')]")
 assert r.xpath("./dashboards/dashboard[@name='WW38 Performance Indicators']")
 assert r.xpath(".//dashboard[@name='WW38 Performance Indicators']//zone[@type-v2='paramctrl']")
def main():
 check(etree.parse(str(HERE/'outputs/2019-09-20-ww38-performance-indicators-replicated-workbook.twb')).getroot())
 with ZipFile(HERE/'outputs/2019-09-20-ww38-performance-indicators-replicated-workbook.twbx') as z: assert any(x.endswith('.hyper') for x in z.namelist()); check(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith('.twb')))))
 print('PASS: WW38 current/prior performance indicators')
if __name__=='__main__': main()

