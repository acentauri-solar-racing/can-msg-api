import dash

from dash import html, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame, read_csv
from collections import OrderedDict


# set as default route
dash.register_page(__name__, path='/', title='Overview')


module_data = [
    {'module': 'vcu', 'status': "active", 'last activity': "no idea"},
    {'module': 'icu', 'status': "inactive", 'last activity': "don't really care"},
    {'module': 'mppt', 'status': "active", 'last activity': "stop asking"},
]

speed = 300000000 * 3.6  # km/h
power = 3000
soc = 110

# main_info = [f"Speed: {speed} km/h",
#              f"Power Consumption Motor: {power} W",
#              f"SOC Battery: {soc} %"]

main_data = [
    {'Speed': f"{speed} km/h", 'Power Consumption of Motor': f"{power} W",
        'SOC of Battery': f"{soc} %"},
]


def layout():
    return html.Div([
        html.H1("Overview"),
        html.H2("Car Status"),
        # html.Ul(children=[html.Li(i) for i in main_info], style={'backgroundColor': 'black',
        #                                                          'list-style-type': 'square',
        #                                                          'color': 'white',
        #                                                          'font_size': '30px', }),
        dash_table.DataTable(data=main_data,
                             id='main_table',
                             style_data={
                                 'font_size': '25px',
                                 'font_weight': 'heavy'
                             },
                             style_as_list_view=True,
                             ),

        html.H2("Module Status"),
        dash_table.DataTable(data=module_data,
                             id='activity_table',
                             style_as_list_view=True,
                             style_data_conditional=[

                                 {
                                     'if': {
                                         'filter_query': '{status} contains inactive',
                                         'column_type': 'any',
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'
                                 },

                             ],
                             )
    ])
