"""Native order timeline and nested reorder table calculations."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = '2020_02_26_WW09_90_Day_Reorder_Rate'


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / 'inputs/Orders (Sample - Superstore).hyper'))
    calculations = [
        ('Total Orders', '{FIXED [Customer Name]: COUNTD([Order ID])}', 'integer', 'measure', 'ordinal'),
        ('Display Total Orders', '[Total Orders]', 'integer', 'dimension', 'ordinal'),
        ('Previous Order Date', 'LOOKUP(ATTR([Order Date]),-1)', 'date', 'measure', 'ordinal'),
        ('Days Since Previous Order', "DATEDIFF('day',[Previous Order Date],ATTR([Order Date]))", 'integer', 'measure', 'quantitative'),
        ('Reorder Within 90 Days', 'IF ISNULL([Previous Order Date]) THEN NULL ELSEIF [Days Since Previous Order]<=90 THEN 1 ELSE 0 END', 'integer', 'measure', 'ordinal'),
        ('Connection Duration', '-[Days Since Previous Order]', 'integer', 'measure', 'quantitative'),
        ('90-Day Reorder Rate', 'ZN(WINDOW_SUM([Reorder Within 90 Days])/WINDOW_COUNT([Reorder Within 90 Days]))', 'real', 'measure', 'ordinal'),
        ('Count Reorders <90 days per Customer', 'IF FIRST()=0 THEN WINDOW_SUM([Reorder Within 90 Days]) END', 'integer', 'measure', 'quantitative'),
        ('Count Customers', 'IF FIRST()=0 THEN COUNTD([Customer Name]) END', 'integer', 'measure', 'quantitative'),
        ('Total Reorders <90 days', 'IF FIRST()=0 THEN WINDOW_SUM([Count Reorders <90 days per Customer]) END', 'integer', 'measure', 'quantitative'),
        ('Total Customers', 'IF FIRST()=0 THEN WINDOW_SUM([Count Customers]) END', 'integer', 'measure', 'quantitative'),
        ('Count All Reorders', 'IF FIRST()=0 THEN WINDOW_COUNT([Reorder Within 90 Days]) END', 'integer', 'measure', 'quantitative'),
        ('Overall Reorder Rate', '[Total Reorders <90 days]/[Count All Reorders]', 'real', 'measure', 'quantitative'),
        ('Avg Reorders per Customer', '[Count All Reorders]/[Total Customers]', 'real', 'measure', 'quantitative'),
        ('First Row', 'FIRST()=0', 'boolean', 'dimension', 'nominal'),
        ('Zero Rate', '0', 'integer', 'measure', 'quantitative'),
        ('Zero Average', '0', 'integer', 'measure', 'quantitative'),
    ]
    for name, formula, datatype, role, kind in calculations:
        e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=kind, table_calc='Rows' if name not in ['Total Orders', 'Display Total Orders', 'Zero Rate', 'Zero Average'] else None, default_format='p0%' if 'Rate' in name else 'n#,##0.0;-#,##0.0' if name=='Avg Reorders per Customer' else '')
    per_customer = {'ordering_type': 'Field', 'order': ['Order ID', '[Order Date]'], 'sort': {'direction': 'ASC', 'using': 'MIN(Order Date)'}}
    all_orders = {'ordering_type': 'Field', 'order': ['Customer Name', '[Order Date]', 'Order ID']}
    previous = dict(per_customer, level_address='[Order Date]', sort={'direction': 'ASC', 'using': 'MIN(Order Date)'})
    nested = [dict(previous, field='Previous Order Date'), dict(per_customer, field='Days Since Previous Order'), dict(per_customer, field='Reorder Within 90 Days')]
    overrides = {
        'Previous Order Date': [previous],
        'Days Since Previous Order': [per_customer, dict(previous, field='Previous Order Date')],
        'Reorder Within 90 Days': [per_customer, *nested[:2]],
        'Connection Duration': [per_customer, dict(per_customer, field='Days Since Previous Order'), dict(previous, field='Previous Order Date')],
        '90-Day Reorder Rate': [per_customer, *nested],
        'Count Reorders <90 days per Customer': [per_customer, *nested],
        'Count Customers': [per_customer],
        'Count All Reorders': [all_orders, *nested],
        'Total Reorders <90 days': [all_orders, dict(per_customer, field='Count Reorders <90 days per Customer'), *nested],
        'Total Customers': [all_orders, dict(per_customer, field='Count Customers')],
        'Overall Reorder Rate': [all_orders, dict(all_orders, field='Total Reorders <90 days'), dict(per_customer, field='Count Reorders <90 days per Customer'), dict(all_orders, field='Count All Reorders'), *nested],
        'Avg Reorders per Customer': [all_orders, dict(all_orders, field='Count All Reorders'), dict(all_orders, field='Total Customers'), dict(per_customer, field='Count Customers'), *nested],
        'First Row': [all_orders],
    }
    e.add_worksheet('Table')
    e.configure_layered_chart('Table', rows=['Customer Name', '90-Day Reorder Rate', 'Display Total Orders'], columns=['EXACTDATE(Order Date)', 'EXACTDATE(Order Date)'], axis_shelf='columns', panes=[
        {'axis': 'EXACTDATE(Order Date)', 'mark_type': 'Shape', 'mark_sizing_off': True, 'selection_relaxation': 'selection-relaxation-disallow', 'shape': 'Reorder Within 90 Days', 'shape_map': {'0': ':filled/diamond', '1': ':filled/diamond', '%null%': ':filled/right-triangle'}, 'color': 'Reorder Within 90 Days', 'color_map': {'0': '#cac4be', '1': '#5557eb', '%null%': '#cac4be'}, 'detail': 'Order ID', 'detail_extra': ['Previous Order Date', 'MIN(Order Date)'], 'tooltip': ['Customer Name', '[Order Date]', 'Order ID', 'Previous Order Date', 'Days Since Previous Order', 'Reorder Within 90 Days', '90-Day Reorder Rate'], 'mark_style': {'size': '0.44977900385856628'}},
        {'axis': 'EXACTDATE(Order Date)', 'mark_type': 'GanttBar', 'mark_sizing_off': True, 'selection_relaxation': 'selection-relaxation-disallow', 'size': 'Connection Duration', 'detail': 'Order ID', 'detail_extra': [], 'tooltip': ['Previous Order Date', 'Days Since Previous Order', 'Connection Duration'], 'mark_style': {'size': '0.01', 'mark-color': '#cac4be'}}], sort_descending='SUM(Total Orders)', sort_field='Customer Name', table_calc_overrides={k:v for k,v in overrides.items() if k in ['Previous Order Date','Days Since Previous Order','Reorder Within 90 Days','Connection Duration','90-Day Reorder Rate']})
    e.configure_worksheet_style('Table', background_color='#f5f5f5', hide_gridlines=True, hide_zeroline=True, hide_col_field_labels=True, hide_row_field_labels=False,
        label_formats=[{'field': '90-Day Reorder Rate', 'text-format': 'p0%'}, {'field': 'Customer Name', 'font-size': '9'}],
        cell_formats=[{'field': 'Display Total Orders', 'height': '35'}],
        header_formats=[{'field': 'Customer Name', 'width': '140'}, {'field': '90-Day Reorder Rate', 'width': '92'}, {'field': 'Display Total Orders', 'width': '84'}],
        axis_style={'render-fold-reversed': 'true', 'per_field': [{'field': 'EXACTDATE(Order Date)', 'attr': 'title', 'value': '', 'class': '0', 'scope': 'cols'}]})
    e.add_worksheet('BAN')
    e.configure_layered_chart('BAN', rows=['Customer Name'], columns=['MIN(Zero Rate)', 'MIN(Zero Average)'], axis_shelf='columns', fold_axes=False, panes=[
        {'axis': 'MIN(Zero Rate)', 'mark_type': 'Text', 'label': 'Overall Reorder Rate', 'detail': '[Order Date]', 'detail_extra': ['Order ID', 'MIN(Order Date)'], 'label_runs': [{'field': 'Overall Reorder Rate', 'bold': True, 'font_size': 28}, {'text': '\nOverall 90-day reorder rate', 'font_size': 11}]},
        {'axis': 'MIN(Zero Average)', 'mark_type': 'Text', 'label': 'Avg Reorders per Customer', 'detail': '[Order Date]', 'detail_extra': ['Order ID', 'MIN(Order Date)'], 'label_runs': [{'field': 'Avg Reorders per Customer', 'bold': True, 'font_size': 28}, {'text': '\nAverage reorders per customer', 'font_size': 11}]}], filters=[{'column': 'First Row', 'values': [True]}], table_calc_overrides={k:v for k,v in overrides.items() if k in ['Overall Reorder Rate','Avg Reorders per Customer','First Row']})
    e.configure_worksheet_style('BAN', hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_row_field_labels=True, label_formats=[{'field': 'Customer Name', 'display': 'false'}], axis_style={'per_field': [{'field': axis, 'attr': 'display', 'value': 'false'} for axis in ['MIN(Zero Rate)', 'MIN(Zero Average)']]})
    layout = {'type': 'container', 'direction': 'vertical', 'style': {'padding': 8}, 'children': [
        {'type': 'text', 'text': 'WHAT IS THE 90-DAY REORDER RATE?', 'font_size': 18, 'bold': True, 'fixed_size': 50},
        {'type': 'worksheet', 'name': 'BAN', 'show_title': False, 'fit': 'entire', 'fixed_size': 105},
        {'type': 'worksheet', 'name': 'Table', 'show_title': False, 'fit': 'width'},
        {'type': 'text', 'text': '#WOW2020 WEEK 9 | Luke Stanke | Recreated with cwtwb', 'font_size': 8, 'fixed_size': 35}]}
    e.add_dashboard(DASHBOARD, width=600, height=800, worksheet_names=['BAN','Table'], layout=layout)
    e.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / 'outputs/replicated-workbook.twbx')
    path.parent.mkdir(parents=True, exist_ok=True)
    e.save(path, validate=False)
    return path


if __name__ == '__main__':
    print(build())
