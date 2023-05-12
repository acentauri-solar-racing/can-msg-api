import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go

from typing import Tuple
from dash import html, dcc, Input, Output

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2
from frontend.settings import RELOAD_INTERVAL
from utils.load_data import load_cmu_data

dash.register_page(__name__, path="/bms_cells", title="BMS Cells")


def cell_volt_graph(df1: DataFrame, df2: DataFrame):
    # create plot using first dataframe (cells 0 - 3)
    fig: go.Figure = px.line(df1,
                             title="Cell Voltages",
                             template="plotly_white",
                             x="timestamp_dt",
                             y=["cell_0_volt", "cell_1_volt",
                                "cell_2_volt", "cell_3_volt"],
                             ).update_yaxes(range=[0, 5])
    # then add the remaining cells in second dataframe
    fig.add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_4_volt'], name="cell_4_volt")).add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_5_volt'], name="cell_5_volt")).add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_6_volt'], name="cell_6_volt")).add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_7_volt'], name="cell_7_volt"))
    fig.update_layouts(xaxis_title='Timestamp')
    return fig


def disp_cmu1(cmu_stat1, df1: DataFrame, df2: DataFrame):
    return html.Div([
        dcc.Graph(figure=cell_volt_graph(df1, df2)),
    ])


@dash.callback(Output('live-update-div-bms-cells', 'children'), Input('interval-component', 'n_intervals'))
def refresh_data(n):
    db_serv: DbService = DbService()
    (cmu1_stat, cmu1_cell_df1, cmu1_cell_df2) = load_cmu_data(db_serv, 100)

    try:
        return html.Div([
            html.H1("BMS", style=H1, className="text-center"),
            html.H2("CMU 1 Cells", style=H2, className="text-center"),
            disp_cmu1(cmu1_stat, cmu1_cell_df1, cmu1_cell_df2),
        ])
    except:
        print("Err: Couldn't load BMS Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))


def layout():
    return html.Div([
        html.Div(id='live-update-div-bms-cells'),
        dcc.Interval(
            id='interval-component',
            interval=RELOAD_INTERVAL,
            n_intervals=0
        )
    ])
