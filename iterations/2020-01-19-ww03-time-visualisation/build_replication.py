"""Rebuild joined order-time small multiples with public SDK calls only."""
from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = '2020_01_15_WW03_Time_Visualisation'


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / 'inputs/Orders+ (Multiple Connections).hyper'))
    e.set_date_options(start_of_week='sunday')
    e.add_parameter('Time Selector', 'string', 'Weeks', domain_type='list', allowed_values=['Days', 'Weeks'], allowed_aliases={'Weeks': 'Weekdays'}, alias='Weekdays')
    calculations = [
        ('Month Column', "IF DATEPART('month',[Order Date])%3 = 0 THEN 3 ELSE DATEPART('month',[Order Date])%3 END", 'integer', 'dimension', 'ordinal'),
        ('Hour of Order', 'INT(TRIM(SPLIT([Time of Order], ":", 1)))', 'integer', 'dimension', 'quantitative'),
        ('Latest Year', 'YEAR([Order Date]) = {FIXED: MAX(YEAR([Order Date]))}', 'boolean', 'dimension', 'nominal'),
        ('Time Selected is Days', "[Time Selector] = 'Days'", 'boolean', 'dimension', 'nominal'),
        ('Max Hour Per Day of Month', '{FIXED [Order Date]: MAX([Hour of Order])}', 'integer', 'dimension', 'quantitative'),
        ('Min Hour Per Day of Month', '{FIXED [Order Date]: MIN([Hour of Order])}', 'integer', 'dimension', 'quantitative'),
        ('Max Hour PerWeekday of Month', "{FIXED DATEPART('weekday',[Order Date]), MONTH([Order Date]), YEAR([Order Date]): MAX([Hour of Order])}", 'integer', 'dimension', 'quantitative'),
        ('Min Hour PerWeekday of Month', "{FIXED DATEPART('weekday',[Order Date]), MONTH([Order Date]), YEAR([Order Date]): MIN([Hour of Order])}", 'integer', 'dimension', 'quantitative'),
        ('Time Range Days', '[Max Hour Per Day of Month]-[Min Hour Per Day of Month]', 'integer', 'measure', 'quantitative'),
        ('Time Range Weekdays', '[Max Hour PerWeekday of Month]-[Min Hour PerWeekday of Month]', 'integer', 'measure', 'quantitative'),
        ('Negative Range Days', 'MIN([Time Range Days])*-1', 'integer', 'measure', 'quantitative'),
        ('Negative Range Weekdays', 'MIN([Time Range Weekdays])*-1', 'integer', 'measure', 'quantitative'),
    ]
    for name, formula, datatype, role, kind in calculations:
        e.add_calculated_field(name, formula, datatype=datatype, role=role, field_type=kind)
    for sheet, day, max_hour, width in [
        ('By Day', 'DAY(Order Date)', 'Max Hour Per Day of Month', 'Negative Range Days'),
        ('By Weekday', 'WEEKDAY(Order Date)', 'Max Hour PerWeekday of Month', 'Negative Range Weekdays'),
    ]:
        e.add_worksheet(sheet)
        circle = {'axis': 'Hour of Order', 'mark_type': 'Circle', 'mark_sizing_off': True, 'color': 'COUNTD(Order ID)', 'size': 'COUNTD(Order ID)', 'detail': 'MONTH(Order Date)', 'tooltip': [day, 'MONTH(Order Date)', 'Hour of Order', 'COUNTD(Order ID)'], 'mark_style': {'size': '2.066298246383667' if sheet == 'By Day' else '0.55972373485565186', 'mark-color': '#f28e2b'}, 'trendline': {'fit': 'linear', 'enabled': True, 'enable_confidence_bands': False, 'enable_instant_analytics': True, 'exclude_color': False, 'exclude_intercept': False}, 'trendline_style': {'line-visibility': 'on', 'line-pattern-only': 'dotted', 'stroke-color': '#89898967', 'stroke-size': '1'}}
        e.configure_layered_chart(sheet, columns=['Month Column', day], rows=['QUARTER(Order Date)', 'Hour of Order', max_hour], axis_shelf='rows', panes=[
            circle,
            {'axis': max_hour, 'mark_type': 'GanttBar', 'mark_sizing_off': True, 'size': width, 'detail': 'MONTH(Order Date)', 'mark_style': {'mark-color': '#e6e6e6', 'size': '0.88955801725387573' if sheet == 'By Day' else '0.25187844038009644'}},
        ], filters=[{'column': 'Latest Year', 'values': [True]}, {'column': 'Time Selected is Days', 'values': [sheet == 'By Day']}])
        e.configure_worksheet_style(sheet, hide_gridlines=True, hide_zeroline=True, hide_borders=True, hide_col_field_labels=True, hide_row_field_labels=True,
            axis_style={'render-fold-reversed': 'true', 'encodings': [
                {'field': 'Hour of Order', 'scope': 'rows', 'class': '0', 'reverse': 'true', 'min': '-1', 'max': '25', 'range-type': 'fixed', 'major-origin': '0', 'major-spacing': '5'},
                {'field': max_hour, 'scope': 'rows', 'class': '0', 'fold': 'true', 'synchronized': 'true', 'reverse': 'true'}],
                'per_field': [{'field': 'Hour of Order', 'attr': 'title', 'scope': 'rows', 'value': 'Hours'}, {'field': max_hour, 'attr': 'display', 'scope': 'rows', 'value': 'false'}, {'field': 'Hour of Order', 'attr': 'width', 'value': '40'}, {'field': max_hour, 'attr': 'width', 'value': '40'}]},
            header_formats=[{'field': 'QUARTER(Order Date)', 'width': '24'}],
            label_formats=[{'field': 'QUARTER(Order Date)', 'font-family': 'Tableau Medium', 'font-size': '8', 'color': '#000000'}, {'field': 'Hour of Order', 'font-family': 'Tableau Medium', 'font-size': '8', 'color': '#1b1b1b'}, {'field': 'Month Column', 'display': 'false'}, {'field': day, 'font-family': 'Tableau Medium', 'font-size': '8', 'color': '#000000', 'text-format': 'ieee' if sheet == 'By Weekday' else 'n0', 'text-orientation': '0'}],
            pane_datalabel_style={'font-family': 'Tableau Medium', 'font-size': '8'},
            color_style={'field': 'COUNTD(Order ID)', 'palette': 'orange_10_0'},
            panes_style={'2': {'mark_style': {'mark-color': '#e6e6e6'}}})
    layout = {'type': 'container', 'direction': 'vertical', 'style': {'padding': 8}, 'children': [
        {'type': 'container', 'direction': 'horizontal', 'fixed_size': 72, 'children': [
            {'type': 'text', 'runs': [{'text': 'Orders by Time and Day\n', 'font_size': '14', 'bold': 'true', 'font_alignment': '0'}, {'text': 'Which <[Parameters].[Parameter 1]> should we plan for extra support staff to process orders?', 'font_size': '10', 'bold': 'true', 'font_alignment': '0'}]},
            {'type': 'paramctrl', 'parameter': 'Time Selector', 'mode': 'list', 'show_title': False, 'fixed_size': 280}]},
        {'type': 'container', 'direction': 'vertical', 'children': [{'type': 'worksheet', 'name': s, 'show_title': False, 'fit': 'entire', 'style': {'margin': 4}} for s in ['By Day', 'By Weekday']]},
        {'type': 'container', 'direction': 'horizontal', 'fixed_size': 30, 'children': [{'type': 'text', 'runs': [{'text': t, 'font_size': 8, 'font_color': '#aa5500', 'bold': 'true'}]} for t in ['DESIGNED BY : LORNA EDEN', '#WOW2020 | WEEK 3', 'RECREATED WITH CWTWB']]},
        {'type': 'text', 'text': 'https://www.workout-wednesday.com/2020w03/', 'font_size': 8, 'fixed_size': 30},
    ]}
    e.add_dashboard(DASHBOARD, width=1200, height=800, worksheet_names=['By Day', 'By Weekday'], layout=layout)
    e.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / 'outputs/replicated-workbook.twbx')
    output.parent.mkdir(parents=True, exist_ok=True)
    e.save(output, validate=False)
    return output


if __name__ == '__main__':
    print(build())
