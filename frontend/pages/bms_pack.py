import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go

from typing import Tuple
from dash import html, dcc, Input, Output

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2
from frontend.settings import RELOAD_INTERVAL

dash.register_page(__name__, path="/bms_pack", title="BMS Pack")


def load_bms_data(db_serv: DbService()):
    return preprocess(
        db_serv.query(BmsPackVoltageCurrent, 100),
    )


def preprocess(df: DataFrame) -> DataFrame:
    # convert from mV, mA to V, A
    df['battery_current'] *= 1e-3
    df['battery_voltage'] *= 1e-3

    # parse timestamps
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def bms_v_graph(df: DataFrame):
    fig: go.Figure = px.line(df,
                             title="Cell Voltages",
                             template="plotly_white",
                             x="timestamp",
                             y=["battery_voltage"],
                             ).update_yaxes(range=[0, 60])
    return fig


def bms_i_graph(df: DataFrame):
    fig: go.Figure = px.line(df,
                             title="Cell Voltages",
                             template="plotly_white",
                             x="timestamp",
                             y=["battery_current"],
                             ).update_yaxes(range=[0, 1])
    return fig


def disp_bms(df: DataFrame):
    return dbc.Row([
        dbc.Col(
            html.H2("Pack Voltage", style=H2, className="text-center"),
            dcc.Graph(figure=bms_v_graph(df)),
        ),
        # dbc.Col(
        #     html.H2("Pack Current", style=H2, className="text-center"),
        #     dcc.Graph(figure=bms_i_graph(df)),
        # )
    ])


@dash.callback(Output('live-update-div-bms-pack', 'children'), Input('interval-component', 'n_intervals'))
def refresh_data(n):
    db_serv: DbService = DbService()
    df: DataFrame = load_bms_data(db_serv)

    try:
        return html.Div([
            html.H1("BMS", style=H1, className="text-center"),
            disp_bms(df),
        ])
    except:
        print("Err: Couldn't load BMS Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))


def layout():
    return html.Div([
        html.Div(id='live-update-div-bms-pack'),
        dcc.Interval(
            id='interval-component',
            interval=RELOAD_INTERVAL,
            n_intervals=0
        )
    ])
