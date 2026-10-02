from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE=Path(__file__).resolve().parent
def c(r):
 f={x.get('caption'):x.find('calculation').get('formula') for x in r.xpath('.//column[calculation]')};assert 'DATEADD' in f['Start Date Prior Period'] and {'Viz','Date Selector','Pick Time Selector','Title'} <= {x.get('name') for x in r.xpath('./worksheets/worksheet')}
def main():
 c(etree.parse(str(HERE/'outputs/2019-10-19-ww42-comparative-line-dynamic-inputs-replicated-workbook.twb')).getroot())
 with ZipFile(HERE/'outputs/replicated-workbook.twbx') as z:assert any(x.endswith('.hyper') for x in z.namelist());c(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith('.twb')))))
 print('PASS: WW42 dynamic period comparison')
if __name__=='__main__':main()

