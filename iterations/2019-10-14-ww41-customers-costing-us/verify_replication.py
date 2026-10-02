from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE=Path(__file__).resolve().parent
def c(r):
 assert {'Scatter','Table'} <= {x.get('name') for x in r.xpath('./worksheets/worksheet')};f={x.get('caption'):x.find('calculation').get('formula') for x in r.xpath('.//column[calculation]')};assert 'SUM([Profit])/SUM([Sales])' in f['Profit Ratio'] and 'FIXED [Customer Name]' in f['Total Customer Sales']
 assert 'MAX(INT([Selected Customer]))' in f['Show Selected Customer']
 assert r.xpath("./actions/edit-group-action[@caption='Select Customer']")
 table=r.xpath("./worksheets/worksheet[@name='Table']")[0]
 assert table.xpath(".//filter[contains(@column, 'Calculation_')]")
def main():
 c(etree.parse(str(HERE/'outputs/2019-10-14-ww41-customers-costing-us-replicated-workbook.twb')).getroot())
 with ZipFile(HERE/'outputs/replicated-workbook.twbx') as z:assert any(x.endswith('.hyper') for x in z.namelist());c(etree.fromstring(z.read(next(x for x in z.namelist() if x.endswith('.twb')))))
 print('PASS: WW41 customer profitability diagnosis')
if __name__=='__main__':main()

