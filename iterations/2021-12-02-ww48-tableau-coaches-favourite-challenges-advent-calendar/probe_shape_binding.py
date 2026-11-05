"""Synthetic released-SDK custom-shape binding reproducer; no reference assets/data."""
from pathlib import Path
import base64,hashlib,json,tempfile,importlib.metadata
from cwtwb import TWBEditor,convert_workbook,read_workbook
from build_replication import repair_shape_bindings

HERE=Path(__file__).resolve().parent

def probe():
    with tempfile.TemporaryDirectory(prefix='shape-binding-') as directory:
        folder=Path(directory)
        (folder/'points.csv').write_text('Category,X,Y\na,0,0\nb,1,1\n',encoding='utf-8')
        (folder/'pixel.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=='))
        e=TWBEditor('');e.set_csv_connection(str(folder/'points.csv'))
        e.add_calculated_field('Flag','[Category] = "b"','boolean',role='dimension',field_type='nominal')
        e.set_shape_palette('Flag',{'false':str(folder/'pixel.png'),'true':str(folder/'pixel.png')},palette='Synthetic')
        e.add_worksheet('Synthetic')
        e.configure_layered_chart('Synthetic',columns=['AVG(X)'],rows=['AVG(Y)'],panes=[{'axis':'AVG(Y)','mark_type':'Shape','shape':'Flag','detail':'Category'}])
        before=HERE/'outputs/shape-binding-before.twbx';after=HERE/'outputs/shape-binding-corrected.twbx'
        e.save(before);convert_workbook(before,folder/'own.json')
        payload=json.loads((folder/'own.json').read_text(encoding='utf-8'));repair_shape_bindings(payload)
        (folder/'corrected.json').write_text(json.dumps(payload),encoding='utf-8')
        convert_workbook(folder/'corrected.json',after,force=True)
        results=[]
        for path in (before,after):
            tree=read_workbook(path).tree
            datasource=tree.find('datasources/datasource')
            encoding=datasource.find('style/style-rule/encoding[@attr="shape"]')
            declared={n.get('name') for n in datasource.findall('column-instance')}
            results.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'shape_style_field':encoding.get('field'),'datasource_binding_present':encoding.get('field') in declared,'palette':encoding.get('palette'),'embedded_shapes':len(tree.findall('external/shapes/shape'))})
        assert results[0]['datasource_binding_present'] is False
        assert results[1]['datasource_binding_present'] is True and results[1]['palette'] is None
        report={'sdk_version':importlib.metadata.version('cwtwb'),'cause':'set_shape_palette emits datasource style field without declaring its column-instance at datasource scope','repair':'Declare instance from own worksheet dependency and use explicit embedded-shape mapping without unregistered custom palette name','runtime':'Not executed; static reproducer plus parent case failure evidence, recapture required','results':results}
        (HERE/'evidence/shape-binding-reproducer.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps(report,indent=2))

if __name__=='__main__':probe()
