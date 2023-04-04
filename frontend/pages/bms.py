import plotly.express as px
import dash_bootstrap_components as dbc
import time
import pandas as pd

from typing import Tuple
from dash import html, dcc

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2


def disp_mppt(power_df: DataFrame, stat) -> html.Div:
    return html.Div([])


def content():
    db_serv: DbService = DbService()

    try:
        return html.Div([
            html.H1("BMS"),
        ])
    except:
        print("Err: Couldn't load BMS Tables")

        return html.Div()
