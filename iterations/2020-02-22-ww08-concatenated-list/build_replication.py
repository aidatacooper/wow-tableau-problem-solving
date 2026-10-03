"""Native patient report and partitioned string accumulation, from extracted data."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = '2020_02_19_WW08_Concat_List_of_Values'


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / 'inputs/TEMP_1rbe3vv17qzn9c139axro0see4zu.hyper'))
    checks = ['Adult BMI Assessment', 'Annual Flu Vaccine', 'Blood Sugar Measurement for Diabetes', 'Breast Cancer Screening', 'Care for Older Adults - Functional Status Assessment', 'Colorectal Cancer Screening', 'Eye Exam for Diabetes Patients', 'Fall Risk Management', 'Med Adherence: Diabetes', 'Med Adherence: RAS Antagonists', 'Med Adherence: Statins', 'Medication Reconciliation after Discharge', 'Osteoporosis Management Post-Fracture', 'All']
    e.add_parameter('Health Check Name Parameter', 'string', 'Adult BMI Assessment', domain_type='list', allowed_values=checks)
    specs = [
        ('Index', 'INDEX()', 'integer', 'measure', 'ordinal'),
        ('Size', 'SIZE()', 'integer', 'measure', 'quantitative'),
        ('Index=Size?', '[Index]=[Size]', 'boolean', 'dimension', 'nominal'),
        ('Health Check Name List', "IF [Index]=1 THEN ATTR([Health Check Name]) ELSE PREVIOUS_VALUE(ATTR([Health Check Name])) + ', ' + ATTR([Health Check Name]) END", 'string', 'dimension', 'nominal'),
        ('FILTER:Health Check Names', "CONTAINS([Health Check Name List],[Health Check Name Parameter]) OR [Health Check Name Parameter]='All'", 'boolean', 'dimension', 'nominal'),
        ('Health Checks Not Complete', "'Health Checks Not Complete'", 'string', 'dimension', 'nominal'),
    ]
    for name, formula, datatype, role, kind in specs:
        e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=kind, table_calc="Rows" if name != "Health Checks Not Complete" else None)
    addressing = {'ordering_type': 'Field', 'ordering_field': 'Health Check Name'}
    overrides = {
        'Health Check Name List': [addressing, dict(addressing, field='Index')],
        'Size': [addressing],
        'Index=Size?': [addressing, dict(addressing, field='Index'), dict(addressing, field='Size')],
        'FILTER:Health Check Names': [addressing, dict(addressing, field='Health Check Name List'), dict(addressing, field='Index')],
    }
    e.add_worksheet('Report')
    e.configure_layered_chart('Report', columns=['Health Checks Not Complete'], rows=['Member ID', 'Member Name', 'Gender', 'Age Category', 'Phone Number', 'Physician'], panes=[{'mark_type': 'Automatic', 'label': 'Health Check Name List', 'detail': 'Health Check Name', 'mark_style': {'mark-labels-show': 'true'}}], filters=[{'column': 'Age Category', 'values': []}, {'column': 'Physician', 'values': []}, {'column': 'Size', 'type': 'quantitative', 'min': '1', 'max': '9'}, {'column': 'Index=Size?', 'values': [True]}, {'column': 'FILTER:Health Check Names', 'values': [True]}], table_calc_overrides=overrides)
    e.configure_worksheet_style('Report', hide_gridlines=True, hide_zeroline=True, hide_col_field_labels=True,
        cell_formats=[{'width': '420', 'font-size': '8'}, {'field': 'Physician', 'height': '53'}],
        pane_datalabel_style={'font-family': 'Tableau Book', 'font-size': '8', 'text-align': 'left'},
        label_formats=[{'field': f, 'font-family': 'Tableau Book', 'font-size': '8'} for f in ['Member ID', 'Member Name', 'Gender', 'Age Category', 'Phone Number', 'Physician']],
        header_formats=[{'field': 'Member ID', 'width': '74'}, {'field': 'Member Name', 'width': '124'}, {'field': 'Gender', 'width': '56'}, {'field': 'Age Category', 'width': '76'}, {'field': 'Phone Number', 'width': '108'}, {'field': 'Physician', 'width': '120'}, {'field': 'Health Check Name List', 'width': '420'}, {'field': 'Health Checks Not Complete', 'height': '52'}])
    layout = {'type': 'container', 'direction': 'vertical', 'style': {'padding': 8}, 'children': [
        {'type': 'text', 'text': 'Can you create a concatenated list of values?', 'font_size': 20, 'fixed_size': 60},
        {'type': 'container', 'direction': 'horizontal', 'fixed_size': 85, 'style': {'background-color': '#f4f4f4', 'padding': 6}, 'children': [
            {'type': 'filter', 'worksheet': 'Report', 'field': 'Physician', 'mode': 'dropdown'},
            {'type': 'filter', 'worksheet': 'Report', 'field': 'Age Category', 'mode': 'checkdropdown'},
            {'type': 'filter', 'worksheet': 'Report', 'field': 'Size'},
            {'type': 'paramctrl', 'parameter': 'Health Check Name Parameter', 'mode': 'compact'}]},
        {'type': 'worksheet', 'name': 'Report', 'show_title': False, 'fit': 'width'},
        {'type': 'text', 'text': 'DESIGNED BY : SEAN MILLER     |     #WOW2020 WEEK 8     |     RECREATED WITH CWTWB\nhttps://www.workout-wednesday.com/2020w08/', 'font_size': 8, 'fixed_size': 45}]}
    e.add_dashboard(DASHBOARD, width=1100, height=1000, worksheet_names=['Report'], layout=layout)
    e.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / 'outputs/replicated-workbook.twbx')
    path.parent.mkdir(parents=True, exist_ok=True)
    e.save(path, validate=False)
    return path


if __name__ == '__main__':
    print(build())
