import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import numpy as np

from typing import Tuple
from dash import html, dcc, Input, Output, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2
from frontend.settings import RELOAD_INTERVAL

dash.register_page(__name__, path="/", title="Overview")

# fake
module_data = [
    {'module': 'vcu', 'status': "active", 'last activity': "no idea"},
    {'module': 'icu', 'status': "inactive", 'last activity': "don't really care"},
    {'module': 'mppt', 'status': "active", 'last activity': "stop asking"},
]

speed = 300000000 * 3.6  # km/h
power = 3000
soc = 110

show_graph = 'none'  # can be 'none', 'speed', 'power' or 'soc'

main_data = [
    {'Speed': f"{speed} km/h", 'Power Consumption of Motor': f"{power} W",
        'SOC of Battery': f"{soc} %"},
]

main_df = pd.DataFrame.from_dict(main_data)


def load_icu_data(db_serv: DbService) -> DataFrame:
    return preprocess_speed(
        db_serv.query(IcuHeartbeat, 100)
    )


def load_mppt_power_data(db_serv: DbService) -> Tuple[DataFrame]:
    return (preprocess_mppt_power(
        db_serv.query(MpptPowerMeas0, 100),
    ),
        preprocess_mppt_power(
        db_serv.query(MpptPowerMeas1, 100)
    ),
        preprocess_mppt_power(
        db_serv.query(MpptPowerMeas2, 100)
    ))


def load_bms_power_data(db_serv: DbService) -> DataFrame:
    return preprocess_bms_power(
        db_serv.query(BmsPackVoltageCurrent, 100),
    )


def load_soc_data(db_serv: DbService) -> DataFrame:
    return preprocess_soc(
        db_serv.query(BmsPackSoc, 100),
    )


def preprocess_speed(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6
    # parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_mppt_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages since given in mV. Only relevant quantities are adjusted!
    df['v_out'] *= 1e-3
    df['i_out'] *= 1e-3

    # P = UI
    df['p_out'] = df['v_out'] * df['i_out']

    # parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_bms_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages since given in mV
    df['battery_voltage'] *= 1e-3
    df['battery_current'] *= 1e-3

    # P = UI
    df['p_out'] = df['battery_voltage'] * df['battery_current']

    # parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_soc(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def speed_graph(df: DataFrame):
    fig: go.Figure = px.line(
        df,
        title="Speed",
        template="plotly_white",
        x="timestamp",
        y=["speed"],
    ).update_yaxes(range=[0, 100])
    return fig


def power_graph(df: DataFrame):
    fig: go.Figure = px.line(df,
                             title="Power",
                             template="plotly_white",
                             x="timestamp",
                             y=["power"]
                             ).update_yaxes()
    return fig


def soc_graph(df: DataFrame):
    fig: go.Figure = px.line(
        df,
        title="State of Charge",
        template="plotly_white",
        x="timestamp",
        y=["soc_percent"],
    ).update_yaxes(range=[0, 100])
    return fig


def disp(df: DataFrame, type: str):
    if type == 'none':
        return html.Div(children=[],
                        )
    elif type == 'speed':
        return html.Div(children=[
            dcc.Graph(figure=speed_graph(df)),
        ],
        )
    elif type == 'power':
        return html.Div(children=[
            dcc.Graph(figure=power_graph(df)),
        ],
        )
    elif type == 'soc':
        return html.Div(children=[
            dcc.Graph(figure=soc_graph(df)),
        ],
        )


def calculate_power(df_mppt1, df_mppt2, df_mppt3, df_bms):
    # this needs to be checked by someone that actually knows what they're doing
    # kinda wack, but I'm just adding the most recent values without checking if
    # they're actually synchronous. feel free to improve ;)

    # lowest index is most recent value

    timestamps = df_bms['timestamp'].to_numpy()
    mppt1 = df_mppt1['p_out'].to_numpy()
    mppt2 = df_mppt2['p_out'].to_numpy()
    mppt3 = df_mppt3['p_out'].to_numpy()

    bms = df_bms['p_out'].to_numpy()

    n = min(mppt1.size, mppt2.size, mppt3.size, bms.size)
    power = mppt1[:n]+mppt2[:n]+mppt3[:n]+bms[:n]
    combined = np.vstack((power, timestamps[:n])).T

    df = pd.DataFrame(data=combined, columns=['power', 'timestamp'])
    return df


def determine_activity(db_serv: DbService):
    df_speed: DataFrame = load_icu_data(db_serv)
    df_soc: DataFrame = load_soc_data(db_serv)
    (df_mppt1, df_mppt2, df_mppt3) = load_mppt_power_data(db_serv)
    df_bms = load_bms_power_data(db_serv)

    return df_speed, df_mppt1, df_mppt2, df_mppt3, df_bms, df_soc, module_data


@ dash.callback(
    Output("main-table", "data"),
    Output("activity-table", "data"),
    Output("extra-graph", "children"),
    Input("interval-component", "n_intervals"),
    Input("main-table", "active_cell"),

)
def refresh_data(n, active_cell):
    db_serv: DbService = DbService()
    df_speed, df_mppt1, df_mppt2, df_mppt3, df_bms, df_soc, module_data = determine_activity(
        db_serv)

    df_power: DataFrame = calculate_power(df_mppt1, df_mppt2, df_mppt3, df_bms)

    if (active_cell == None):
        show_graph = 'none'
        df = df_speed

    elif active_cell['column'] == 0:
        show_graph = 'speed'
        df = df_speed

    elif active_cell['column'] == 1:
        show_graph = 'power'
        df = df_power

    elif active_cell['column'] == 2:
        show_graph = 'soc'
        df = df_soc

    # TODO: implement actual data update
    speed = 0
    power = 12
    soc = 'batshit'
    main_data = [{'Speed': f"{df_speed['speed'][0]} km/h", 'Power Consumption of Motor': f"{df_power['power'][0]} W",
                  'SOC of Battery': f"{df_soc['soc_percent'][0]} %"}]

    updated_module_data = [
        {'module': 'vcu', 'status': "active", 'last activity': "no idea"},
        {'module': 'icu', 'status': "inactive",
            'last activity': "don't really care"},
        {'module': 'mppt', 'status': "active", 'last activity': "stop asking"},
    ]
    return main_data, updated_module_data, disp(df, show_graph)


def layout():
    return html.Div(children=[
        html.H1("Overview", style=H1, className="text-center"),
        html.H2("Car Status"),
        dash_table.DataTable(data=main_data,
                             id='main-table',
                             style_data={
                                 'font_size': '25px',
                                 'font_weight': 'heavy'
                             },
                             style_as_list_view=True,
                             column_selectable="single",
                             selected_columns=[],
                             style_data_conditional=[
                                 {
                                     'if': {
                                         'state': 'active'  # 'active' | 'selected'
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'

                                 },
                                 {
                                     'if': {
                                         'state': 'selected'  # 'active' | 'selected'
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'

                                 },
                             ],
                             ),
        html.Br(),
        html.Br(),
        html.Div(children=disp(main_df, show_graph),
                 id='extra-graph'),
        html.H2("Module Status"),
        dash_table.DataTable(data=module_data,
                             id='activity-table',
                             style_as_list_view=True,
                             style_data_conditional=[

                                 {
                                     'if': {
                                         'filter_query': '{status} contains inactive',
                                         'column_type': 'any',
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'
                                 },

                             ],
                             ),
        dcc.Interval(id="interval-component",
                     interval=RELOAD_INTERVAL,
                     n_intervals=0
                     ),
    ]
    )
