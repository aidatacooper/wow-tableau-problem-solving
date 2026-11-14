"""2023 week 08 standard LOD solution; public SDK and extracted Hyper only."""
from pathlib import Path
from cwtwb import TWBEditor
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'outputs' / 'replicated-workbook.twbx'
SHEET = 'Comet Chart'
DASHBOARD = '2023 Week 08 - Comet Chart'

def build():
    OUTPUT.parent.mkdir(exist_ok=True)
    e = TWBEditor('')
    e.set_hyper_connection(str(HERE / 'inputs' / 'Sample _ Superstore.hyper'), table_name='Orders_ECFCA1FB690A41FE803BC071773BA862')
    e.add_calculated_field('Latest Sales', '{FIXED [Sub-Category]: SUM(IF YEAR([Order Date]) = 2022 THEN [Sales] END)}')
    e.add_calculated_field('Previous Sales', '{FIXED [Sub-Category]: SUM(IF YEAR([Order Date]) = 2021 THEN [Sales] END)}')
    e.add_calculated_field('Sales Increased', '[Latest Sales] > [Previous Sales]', datatype='boolean', role='dimension', field_type='nominal')
    e.add_calculated_field('Order Date (Years)', 'YEAR([Order Date])', datatype='integer', role='dimension', field_type='ordinal')
    e.set_field_format('Sales', '#,##0')
    e.set_field_format('Latest Sales', '#,##0')
    e.set_datasource_color_palette('Sales Increased', {'true': '#b9b0ab', 'false': '#d95657'})
    e.add_worksheet(SHEET)
    e.configure_layered_chart(SHEET, columns=['SUM(Sales)', 'MIN(Latest Sales)'], rows=['Sub-Category'], axis_shelf='columns', synchronized=True, fold_axes=True, hide_axes=True, sort_descending='MIN(Latest Sales)', sort_field='Sub-Category', sort_mode='computed', filters=[{'column': 'YEAR(Order Date)', 'values': [2021, 2022]}], panes=[
        {'axis': 'SUM(Sales)', 'mark_type': 'Line', 'path': 'YEAR(Order Date)', 'size': 'YEAR(Order Date)', 'color': 'Sales Increased', 'mark_sizing_off': True, 'mark_style': {'size': '2', 'mark-labels-show': 'true', 'mark-labels-cull': 'false', 'mark-labels-mode': 'line-ends', 'mark-labels-line-first': 'false', 'mark-labels-line-last': 'true', 'mark-labels-range-field': 'SUM(Sales)'}},
        {'axis': 'MIN(Latest Sales)', 'mark_type': 'Circle', 'size': 'Order Date (Years)', 'detail': 'YEAR(Order Date)', 'tooltip': 'SUM(Sales)', 'mark_sizing_off': True, 'mark_style': {'size': '0.91154694557189941', 'mark-color': '#ffffff', 'has-stroke': 'false', 'mark-labels-show': 'false'}}])
    e.configure_worksheet_style(SHEET, background_color='#f5f5f5', hide_axes=True, hide_gridlines=True, hide_zeroline=True, hide_row_field_labels=True, hide_sort_controls=True, table_dividers=[{'scope': 'rows', 'div-level': '1'}, {'scope': 'cols', 'stroke-size': '0', 'line-visibility': 'off'}], size_style={'field': 'Order Date (Years)', 'type': 'catsize', 'min_size': 0.340962, 'max_size': 1}, panes_style={'1': {'pane_datalabel_style': {'font-size': '9'}}})
    e.add_percentage_band(SHEET, axis_field='SUM(Sales)', value_field='SUM(Sales)', percentage=110, formula='max', scope='per-table', pane_index=0, probability=None)
    for pane in (0, 1):
        e.configure_custom_tooltip(SHEET, [{'text': 'Sub-Category: '}, {'field': 'Sub-Category', 'bold': True}, {'text': '\nYear: '}, {'field': 'YEAR(Order Date)', 'bold': True}, {'text': '\nSales: '}, {'field': 'SUM(Sales)', 'bold': True}], pane_index=pane)
    e.add_dashboard(DASHBOARD, width=800, height=700, layout={'type': 'container', 'direction': 'vertical', 'layout_strategy': 'free-form', 'children': [
        {'type': 'text', 'text': 'Can you build a comet chart as an alternative to a side-by-side bar chart?', 'font_size': 15, 'font_color': '#333333', 'font_align': 'center', 'absolute': {'x': 1000, 'y': 1143, 'w': 98000, 'h': 11714}},
        {'type': 'size', 'worksheet': SHEET, 'field': 'Order Date (Years)', 'pane_index': 2, 'absolute': {'x': 1125, 'y': 13000, 'w': 97750, 'h': 12714}, 'style': {'background-color': '#f5f5f5', 'padding': '15', 'margin': '0'}},
        {'type': 'worksheet', 'name': SHEET, 'show_title': False, 'fit': 'entire', 'absolute': {'x': 1125, 'y': 25714, 'w': 97750, 'h': 68425}, 'style': {'background-color': '#f5f5f5', 'padding': '15', 'padding-top': '0', 'margin': '0'}},
        {'type': 'text', 'text': 'CHALLENGE: LUKE STANKE     |     #WOW2023 WEEK 8     |     RECREATED WITH CWTWB', 'font_size': 8, 'font_color': '#333333', 'absolute': {'x': 1000, 'y': 94286, 'w': 98000, 'h': 4571}}
    ]})
    e.set_window_state(SHEET, zoom_entire_view=True)
    e.set_window_state(DASHBOARD, zoom_entire_view=True)
    e.set_active_dashboard(DASHBOARD)
    e.save(OUTPUT)
    return OUTPUT

if __name__ == '__main__':
    print(build())
