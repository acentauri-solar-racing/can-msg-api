import dash

from dash import html, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame, read_csv
from collections import OrderedDict


# set as default route
dash.register_page(__name__, path='/', title='Overview')


data = [
    {'module': 'vcu', 'status': "active", 'last activity': "active"},
    {'module': 'icu', 'status': "inactive", 'last activity': "active"},
    {'module': 'mppt', 'status': "active", 'last activity': "active"},
]


def layout():
    return html.Div([
        html.H1("Overview"),
        html.H2("Speed"),
        html.B("Speed and some graph"),

        html.H2("Module Status"),
        dash_table.DataTable(data=data,
                             id='activity_table',
                             style_data_conditional=[

                                 {
                                     'if': {
                                         'filter_query': '{status} contains inactive',
                                         'column_type': 'any',
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'
                                 },

                             ])
    ])
