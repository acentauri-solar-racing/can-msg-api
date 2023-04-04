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


def load_power_data(db_serv: DbService) -> Tuple[DataFrame]:
    return (preprocess(
        db_serv.query(MpptPowerMeas0, 100)
    ),
        preprocess(
        db_serv.query(MpptPowerMeas1, 100)
    ),
        preprocess(
        db_serv.query(MpptPowerMeas2, 100)
    ))


def load_status_data(db_serv: DbService) -> Tuple[MpptStatus0, MpptStatus1, MpptStatus2]:
    return (
        db_serv.latest(MpptStatus0),
        db_serv.latest(MpptStatus1),
        db_serv.latest(MpptStatus2),
    )


def disp_mppt(power_df: DataFrame, stat) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([html.H3("Status")], className="col-3"),
            dbc.Col([html.H3("Power")]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(html.P("Mode:")),
                    dbc.Col(html.P(stat.mode))
                ]),
                dbc.Row([
                    dbc.Col(html.P("Fault:")),
                    dbc.Col(html.P(stat.fault))
                ]),
                dbc.Row([
                    dbc.Col(html.P("Enabled:")),
                    dbc.Col(html.P(stat.enabled))
                ]),
                dbc.Row([
                    dbc.Col(html.P("Ambient Temp.:")),
                    dbc.Col(html.P(stat.ambient_temp))
                ]),
                dbc.Row([
                    dbc.Col(html.P("Heatsink Temp.:")),
                    dbc.Col(html.P(stat.heatsink_temp))
                ]),
            ], className="col-3"),
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=v_i_graph(power_df)),
                    ]),
                    dbc.Col([
                        dcc.Graph(figure=power_graph(power_df))
                    ]),
                ])
            ]),
        ], className="align-items-center"),
    ])


def content():
    db_serv: DbService = DbService()

    try:
        (power_df0, power_df1, power_df2) = load_power_data(db_serv)
        (stat0, stat1, stat2) = load_status_data(db_serv)
        return html.Div([
            html.H1(["MPPT"], style=H1),
            html.H2(["MPPT 0"], style=H2),
            disp_mppt(power_df0, stat0),
            html.H2(["MPPT 1"], style=H2),
            disp_mppt(power_df1, stat1),
            html.H2(["MPPT 2"], style=H2),
            disp_mppt(power_df2, stat2),
        ])
    except:
        print("Err: Couldn't load MPPT Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))

    return
