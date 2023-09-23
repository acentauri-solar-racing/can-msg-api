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

dash.register_page(__name__, path="/bms_cells", title="BMS Cells")

# for cell graph
def load_cmu_data(db_serv: DbService(), cmu_stat, cmu_class1, cmu_class2, n_entries):
    (df1, df2) = preprocess_cmu(
        db_serv.query_latest(cmu_class1, n_entries),
        db_serv.query_latest(cmu_class2, n_entries)
    )
    return db_serv.latest(cmu_stat), df1, df2


def preprocess_cmu(df1: DataFrame, df2: DataFrame) -> Tuple[DataFrame,DataFrame]:
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
    df1['timestamp_dt'] = pd.to_datetime(
        df1['timestamp'], unit='s', origin="unix", utc=True)
    df2['timestamp_dt'] = pd.to_datetime(
        df2['timestamp'], unit='s', origin="unix", utc=True)
    return (df1, df2)



def cell_volt_graph(df1: DataFrame, df2: DataFrame):
    # create plot using first dataframe (cells 0 - 3)
    fig: go.Figure = px.line(df1,
                             title="Cell Voltages",
                             template="plotly_white",
                             x="timestamp_dt",
                             y=["cell_0_volt", "cell_1_volt",
                                "cell_2_volt", "cell_3_volt"],
                             )
    # then add the remaining cells in second dataframe. cell_7_volt is always -32768
    fig.add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_4_volt'], name="cell_4_volt")).add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_5_volt'], name="cell_5_volt")).add_trace(
        go.Scatter(x=df2["timestamp_dt"], y=df2['cell_6_volt'], name="cell_6_volt"))
    return fig


def disp_cmu(cmu_stat, df1: DataFrame, df2: DataFrame):
    return html.Div([
        html.P("PCB temp [°C]: " + str(cmu_stat.pcb_temp / 10)),
        html.P("Cell temp [°C]: " + str(cmu_stat.cell_temp / 10)),
        dcc.Graph(figure=cell_volt_graph(df1, df2)),
    ])


@dash.callback(Output('live-update-div-bms-cells', 'children'), Input('interval-component', 'n_intervals'))
def refresh_data(n):

    try:
        db_serv: DbService = DbService()
        (cmu1_stat, cmu1_cell_df1, cmu1_cell_df2) = load_cmu_data(db_serv, BmsCmu1Stat, BmsCmu1Cells1, BmsCmu1Cells2,  100)
        (cmu2_stat, cmu2_cell_df1, cmu2_cell_df2) = load_cmu_data(db_serv, BmsCmu2Stat, BmsCmu2Cells1, BmsCmu2Cells2,  100)
        (cmu3_stat, cmu3_cell_df1, cmu3_cell_df2) = load_cmu_data(db_serv, BmsCmu3Stat, BmsCmu3Cells1, BmsCmu3Cells2,  100)
        (cmu4_stat, cmu4_cell_df1, cmu4_cell_df2) = load_cmu_data(db_serv, BmsCmu4Stat, BmsCmu4Cells1, BmsCmu4Cells2,  100)
        (cmu5_stat, cmu5_cell_df1, cmu5_cell_df2) = load_cmu_data(db_serv, BmsCmu5Stat, BmsCmu5Cells1, BmsCmu5Cells2,  100)
        # print()
        return html.Div([
            html.H1("BMS", style=H1, className="text-center"),
            html.H2("CMU 1 Cells", style=H2),
            disp_cmu(cmu1_stat, cmu1_cell_df1, cmu1_cell_df2),

            html.H2("CMU 2 Cells", style=H2),
            disp_cmu(cmu2_stat, cmu2_cell_df1, cmu2_cell_df2),

            html.H2("CMU 3 Cells", style=H2),
            disp_cmu(cmu3_stat, cmu3_cell_df1, cmu3_cell_df2),

            html.H2("CMU 4 Cells", style=H2),
            disp_cmu(cmu4_stat, cmu4_cell_df1, cmu4_cell_df2),

            html.H2("CMU 5 Cells", style=H2),
            disp_cmu(cmu5_stat, cmu5_cell_df1, cmu5_cell_df2),
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
