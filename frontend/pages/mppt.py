import plotly.express as px
import dash_bootstrap_components as dbc
import time
import pandas as pd

from dash import html, dcc
from db.models import *
from db.db_service import DbService
from pandas import DataFrame


def preprocess(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale all voltages since given in mV
    df['v_in'] *= 1e-3
    df['i_in'] *= 1e-3
    df['v_out'] *= 1e-3
    df['i_out'] *= 1e-3

    # P = UI
    df['p_in'] = df['v_in'] * df['i_in']
    df['p_out'] = df['v_out'] * df['i_out']

    # parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def v_i_graph(df: DataFrame):
    return px.line(df,
                   title="Voltage & Current",
                   template="plotly_white",
                   x="timestamp",
                   y=["v_in", "i_in", "v_out", "i_out"],
                   ).update_yaxes(range=[0, 15])


def power_graph(df: DataFrame):
    return px.line(df,
                   title="Power",
                   template="plotly_white",
                   x="timestamp",
                   y=["p_in", "p_out"]
                   ).update_yaxes(range=[0, 15])


def content():
    db_serv: DbService = DbService()

    df0: DataFrame = preprocess(
        db_serv.query(MpptPowerMeas0, 100)
    )

    df1: DataFrame = db_serv.query(MpptPowerMeas1, 100)
    fig1 = v_i_graph(df1)

    df2: DataFrame = db_serv.query(MpptPowerMeas2, 100)
    fig2 = v_i_graph(df2)

    return html.Div([
        html.H1(["MPPT"]),
        html.H2(["MPPT 1"], className="text-center"),
        dbc.Row([
            dbc.Col([html.H3("Power", className="text-center"),
                    dcc.Graph(figure=v_i_graph(df0)),
                    dcc.Graph(figure=power_graph(df0))]),
            dbc.Col([html.H3("Status", className="text-center")]),
        ]),
    ])
