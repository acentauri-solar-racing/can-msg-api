from dash import html

from db.models import *
from db.db_service import DbService
from pandas import DataFrame


def content():
    return html.Div([
        html.H1("Overview"),
        html.P("Speed and stuff idk"),
    ])
