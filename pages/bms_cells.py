import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import time
import pandas as pd
import plotly.graph_objs as go

from typing import Tuple
from dash import html, dcc

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2

dash.register_page(__name__, path="/bms", title="BMS Cells")


def load_cmu_data(db_serv: DbService()):
    (df1, df2) = preprocess(
        db_serv.query(BmsCmu1Cells1, 100),
        db_serv.query(BmsCmu1Cells2, 100)
    )
    return (db_serv.latest(BmsCmu1Stat), df1, df2)


def preprocess(df1: DataFrame, df2: DataFrame) -> DataFrame:
    # convert from mV to V
    df1['cell_0_volt'] *= 1e-3
    df1['cell_1_volt'] *= 1e-3
    df1['cell_2_volt'] *= 1e-3
    df1['cell_3_volt'] *= 1e-3

    df2['cell_4_volt'] *= 1e-3
    df2['cell_5_volt'] *= 1e-3
    df2['cell_6_volt'] *= 1e-3
    df2['cell_7_volt'] *= 1e-3

    # parse timestamps
    df1['timestamp'] = pd.to_datetime(
        df1['timestamp'], unit='s', origin="unix", utc=True)
    df2['timestamp'] = pd.to_datetime(
        df2['timestamp'], unit='s', origin="unix", utc=True)
    return (df1, df2)


def disp_mppt(power_df: DataFrame, stat) -> html.Div:
    return html.Div([])


def cell_volt_graph(df1: DataFrame, df2: DataFrame):
    # create plot using first dataframe (cells 0 - 3)
    fig: go.Figure = px.line(df1,
                             title="Cell Voltages",
                             template="plotly_white",
                             x="timestamp",
                             y=["cell_0_volt", "cell_1_volt",
                                "cell_2_volt", "cell_3_volt"],
                             ).update_yaxes(range=[0, 5])
    # then add the remaining cells in second dataframe
    fig.add_trace(
        go.Scatter(x=df2["timestamp"], y=df2['cell_4_volt'], name="cell_4_volt")).add_trace(
        go.Scatter(x=df2["timestamp"], y=df2['cell_5_volt'], name="cell_5_volt")).add_trace(
        go.Scatter(x=df2["timestamp"], y=df2['cell_6_volt'], name="cell_6_volt")).add_trace(
        go.Scatter(x=df2["timestamp"], y=df2['cell_7_volt'], name="cell_7_volt"))
    return fig


def disp_cmu1(cmu_stat1, df1: DataFrame, df2: DataFrame):
    return html.Div([
        dcc.Graph(figure=cell_volt_graph(df1, df2)),
    ])


def layout():
    db_serv: DbService = DbService()
    (cmu1_stat, cmu1_cell_df1, cmu1_cell_df2) = load_cmu_data(db_serv)

    try:
        return html.Div([
            html.H1("BMS", style=H1, className="text-center"),
            html.H2("CMU 1 Cells", style=H2, className="text-center"),
            disp_cmu1(cmu1_stat, cmu1_cell_df1, cmu1_cell_df2),
        ])
    except:
        print("Err: Couldn't load BMS Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))

    return html.Div()
