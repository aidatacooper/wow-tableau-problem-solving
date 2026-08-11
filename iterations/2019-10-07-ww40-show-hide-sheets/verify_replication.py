from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE=Path(__file__).resolve().parent
def c(r):
 assert {'Area','Bar','Line','Preview:Area','Preview:Bar','Preview:Line'} <= {x.get('name') for x in r.xpath('./worksheets/worksheet')}
 assert any(x.get('caption')=='Choose Display Type' for x in r.xpath(".//datasource[@name='Parameters']/column"));assert r.xpath("./dashboards/dashboard[@name='WW40 Show Hide Charts']")
def main():
 c(etree.parse(str(HERE/'outputs/2019-10-07-ww40-show-hide-sheets-replicated-workbook.twb')).getroot())
 with ZipFile(HERE/'outputs/2019-10-07-ww40-show-hide-sheets-replicated-workbook.twbx') as z:assert any(x.endswith('.hyper') for x in z.namelist());c(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith('.twb')))))
 print('PASS: WW40 selectable chart presentations')
if __name__=='__main__':main()

