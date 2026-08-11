"""Verify WW37's selected-region contribution comparison."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
HERE = Path(__file__).resolve().parent
def check(root):
    assert root.xpath("./worksheets/worksheet[@name='Viz']")
    assert root.xpath("./dashboards/dashboard[@name='WW37 Rounded Bar Chart']")
    params={c.get('caption') for c in root.xpath(".//datasource[@name='Parameters']/column")}
    assert 'Region Param' in params
    formulas={c.get('caption'):c.find('calculation').get('formula') for c in root.xpath('.//column[calculation]')}
    assert '[Parameters].[Parameter 1]' in formulas['Region Sales']
    assert 'SUM(' in formulas['Region % of Sales']
    assert root.xpath(".//worksheet[@name='Viz']//pane/mark[@class='Bar']")
def main():
    twb=HERE/'outputs'/'2019-09-13-ww37-rounded-bar-chart-replicated-workbook.twb'; twbx=HERE/'outputs'/'2019-09-13-ww37-rounded-bar-chart-replicated-workbook.twbx'
    check(etree.parse(str(twb)).getroot())
    with ZipFile(twbx) as z:
        assert any(n.endswith('.hyper') for n in z.namelist())
        check(etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.twb')))))
    print('PASS: WW37 selected-region rounded-bar comparison')
if __name__ == '__main__': main()

