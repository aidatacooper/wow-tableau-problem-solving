"""Build from locked data and public SDK APIs; never reads author workbooks."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent

def build():
    editor = TWBEditor('')
    editor.set_hyper_connection(str(HERE / 'inputs/sales-with-spacer.hyper'))
    calculations = [
        ('Current Year', 'YEAR({FIXED:MAX([Order Date])})', 'integer', 'dimension', 'ordinal'),
        ('Previous Year', '[Current Year]-1', 'integer', 'dimension', 'ordinal'),
        ('CY Sales', 'IF YEAR([Order Date])=[Current Year] THEN [Sales] END', 'real', 'measure', 'quantitative'),
        ('PY Sales', 'IF YEAR([Order Date])=[Previous Year] THEN [Sales] END', 'real', 'measure', 'quantitative'),
        ('Difference', 'SUM([CY Sales])-SUM([PY Sales])', 'real', 'measure', 'quantitative'),
        ('Is Loss?', 'MAX(0,[Difference])=0', 'boolean', 'dimension', 'nominal'),
        ('PY Sales (copy)', '[PY Sales]', 'real', 'measure', 'quantitative'),
    ]
    for name, formula, datatype, role, field_type in calculations:
        editor.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=field_type)
    for name in ('CY Sales', 'PY Sales', 'PY Sales (copy)'):
        editor.set_field_format(name, '#,##0')
    editor.set_field_format('Difference', '*\u25b3#,##0;\u25bd#,##0')
    editor.add_worksheet('Viz')
    common = dict(detail_extra=['Current Year', 'Previous Year'],
                  tooltip=['SUM(CY Sales)', 'SUM(PY Sales)', 'AGG(Difference)'], mark_sizing_off=True)
    editor.configure_layered_chart('Viz',
        columns=['Category', 'Multiple Values', 'SUM(PY Sales (copy))'],
        rows=['Segment', 'Measure Names'], axis_shelf='columns', synchronized=True,
        measure_names_order=['SUM(PY Sales)', 'SUM(CY Sales)', 'SUM(PY Sales (copy))', 'MIN(Spacer)'],
        fold_axes=True, hide_axes=True, panes=[
            dict(common, axis='Multiple Values', mark_type='Bar',
                 measure_values=['SUM(PY Sales)', 'SUM(CY Sales)', 'MIN(Spacer)'],
                 color='Measure Names', label='Multiple Values',
                 color_map={'SUM(PY Sales)': '#b8cce4', 'SUM(CY Sales)': '#4472c4', 'MIN(Spacer)': '#ffffff'},
                 cell_style={'text-align': 'left'},
                 mark_style={'size': '2', 'has-stroke': 'true', 'stroke-color': '#ffffff', 'mark-labels-show': 'true'}),
            dict(common, axis='SUM(PY Sales (copy))', mark_type='GanttBar',
                 size='AGG(Difference)', color='AGG(Is Loss?)', label='AGG(Difference)',
                 color_map={True: '#c0504d', False: '#548235'}, cell_style={'text-align': 'right'},
                 mark_style={'size': '0.01', 'mark-labels-show': 'true', 'has-stroke': 'false'}),
        ])
    tooltip = [
        {'field': 'Segment', 'bold': True}, {'text': ' | '}, {'field': 'Category', 'bold': True},
        {'text': '\n'}, {'field': 'Previous Year'}, {'text': ' sales: '}, {'field': 'SUM(PY Sales)'},
        {'text': '\n'}, {'field': 'Current Year'}, {'text': ' sales: '}, {'field': 'SUM(CY Sales)'},
        {'text': '\nDifference: '}, {'field': 'AGG(Difference)'},
    ]
    for pane_index in (0, 1):
        editor.configure_custom_tooltip('Viz', tooltip, pane_index=pane_index)
    editor.set_worksheet_rich_title('Viz', runs=[
        {'text': 'Sales by Category and Segment\n', 'bold': True, 'fontsize': '14'},
        {'text': '<Current Year> compared with <Previous Year>', 'fontsize': '11'},
    ])
    editor.configure_worksheet_style('Viz', hide_gridlines=True, hide_zeroline=True,
        hide_borders=True, hide_table_dividers=True, hide_col_field_labels=True,
        hide_row_field_labels=True, hide_row_label='Measure Names', pane_datalabel_style={'color-mode': 'match'})
    editor.add_dashboard('Sales Difference', width=800, height=400, layout={
        'type': 'container', 'direction': 'floating', 'children': [
            {'type': 'worksheet', 'name': 'Viz', 'fit': 'entire',
             'absolute': {'x': 0, 'y': 0, 'w': 100000, 'h': 100000}}
        ]})
    output = HERE / 'outputs/replicated-workbook.twbx'
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output), validate=False)  # Offline XSD is mandatory in verifier.
    return output
if __name__ == '__main__': print(build())
