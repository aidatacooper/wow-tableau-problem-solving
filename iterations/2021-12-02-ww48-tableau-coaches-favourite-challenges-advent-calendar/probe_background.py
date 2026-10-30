"""Narrow historical probe: Cartesian configure_chart map_layers ignores raster.

This does NOT establish SDK incapability: public native-JSON conversion works.
Use the main builder/verifier for that structural authoring and roundtrip route.
The old probe artifacts/reports are immutable evidence; new executions use new names.
"""
from pathlib import Path
import tempfile,base64,json,inspect,importlib.metadata
from cwtwb import TWBEditor
from cwtwb.capability_registry import list_capabilities

HERE=Path(__file__).resolve().parent

def build_probe():
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        (folder/'points.csv').write_text('Horizontal,Vertical\n0,0\n4,6\n',encoding='utf-8')
        image=folder/'pixel.png'
        image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=='))
        e=TWBEditor('');e.set_csv_connection(str(folder/'points.csv'));e.add_worksheet('Synthetic')
        # Test the existing layer entry point rather than assuming a missing method.
        # On a Cartesian chart it accepts this payload but emits no mapped image.
        e.configure_chart('Synthetic',mark_type='Circle',columns=['AVG(Horizontal)'],rows=['AVG(Vertical)'],map_layers=[{'name':'synthetic raster','type':'background-image','path':str(image),'x':'Horizontal','y':'Vertical','left':0,'right':4,'bottom':0,'top':6}])
        e.add_calculated_field('Image Category', '"fixture"', 'string', role='dimension', field_type='nominal')
        e.set_shape_palette('Image Category', {'fixture':str(image)}, palette='SyntheticControl')
        e.save(HERE/'outputs/chart-map-layers-reprobe.twbx')
        methods={n:str(inspect.signature(getattr(TWBEditor,n))) for n in dir(TWBEditor) if not n.startswith('_') and callable(getattr(TWBEditor,n)) and any(t in n for t in ('map','image','shape','chart','style'))}
        caps=[str(c) for c in list_capabilities() if any(t in str(c).lower() for t in ('image','shape','layer','map'))]
        report={'version':importlib.metadata.version('cwtwb'),'expected':'Datasource mapped-images/mapped-image with field-bound rectangle, and portable PNG in package','public_methods':methods,'related_capabilities':caps,'candidate_result':'configure_chart accepts map_layers on Circle; verifier checks whether mapped-image and PNG were emitted'}
        (HERE/'outputs/chart-map-layers-reprobe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':build_probe()
