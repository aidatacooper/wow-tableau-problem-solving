from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE=Path(__file__).resolve().parent
def c(r):
 assert {'Map','Data'} <= {x.get('name') for x in r.xpath('./worksheets/worksheet')};f={x.get('caption'):x.find('calculation').get('formula') for x in r.xpath('.//column[calculation]')};assert 'DISTANCE' in f['Distance (miles)'] and {'Selected Casino Lat','Selected Casino Long'} <= set(f)
 assert r.xpath("./actions/edit-parameter-action[@caption='Select Casino']")
def main():
 c(etree.parse(str(HERE/'outputs/2019-10-25-ww43-las-vegas-casinos-replicated-workbook.twb')).getroot())
 with ZipFile(HERE/'outputs/2019-10-25-ww43-las-vegas-casinos-replicated-workbook.twbx') as z:assert any(x.endswith('.hyper') for x in z.namelist());c(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith('.twb')))))
 print('PASS: WW43 casino-distance map')
if __name__=='__main__':main()

