import dash

from dash import html

from db.models import *
from db.db_service import DbService
from pandas import DataFrame

# set as default route
dash.register_page(__name__, path='/', title='Overview')


def layout():
    return html.Div([
        html.H1("Overview"),
        html.P("Speed and stuff idk"),
    ])
