import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import time

from typing import Tuple
from dash import html, dcc, Input, Output, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2
from frontend.settings import RELOAD_INTERVAL
from utils.load_data import *
import datetime as dt

dash.register_page(__name__, path="/", title="Overview")

modules = ['vcu', 'icu', 'mppt0', 'mppt1', 'mppt2',
           'bms', 'stwheel', 'logger', 'fsensors', 'dsensors']

module_data = [
    {'module': modules[0], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[1], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[2], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[3], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[4], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[5], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[6], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[7], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[8], 'status': "inactive", 'last activity': "no data"},
    {'module': modules[9], 'status': "inactive", 'last activity': "no data"},
]

max_idle_time = 2

speed = 300000000 * 3.6  # km/h
power = 3000
soc = 110

show_graph = 'none'  # can be 'none', 'speed', 'power' or 'soc'

main_data = [
    {'Speed': f"{speed} km/h", 'Power Consumption of Motor': f"{power} W",
        'SOC of Battery': f"{soc} %"},
]

main_df = pd.DataFrame.from_dict(main_data)


def speed_graph(df: DataFrame):
    fig: go.Figure = px.line(
        df,
        title="Speed",
        template="plotly_white",
        x="timestamp_dt",
        y=["speed"],
    ).update_yaxes(range=[0, 100])
    return fig


def power_graph(df: DataFrame):
    fig: go.Figure = px.line(df,
                             title="Power",
                             template="plotly_white",
                             x="timestamp_dt",
                             y=["power"]
                             ).update_yaxes()
    return fig


def soc_graph(df: DataFrame):
    fig: go.Figure = px.line(
        df,
        title="State of Charge",
        template="plotly_white",
        x="timestamp_dt",
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

    # load data into numpy arrays for processing
    timestamps = df_bms['timestamp'].to_numpy()
    mppt1 = df_mppt1['p_out'].to_numpy()
    mppt2 = df_mppt2['p_out'].to_numpy()
    mppt3 = df_mppt3['p_out'].to_numpy()
    bms = df_bms['p_out'].to_numpy()

    # determine the number of data points plotted
    max_size = 200
    n = min(mppt1.size, mppt2.size, mppt3.size, bms.size, max_size)

    # calculate the power consumed
    power = mppt1[:n]+mppt2[:n]+mppt3[:n]+bms[:n]

    # transform back into dataframe
    combined = np.vstack((power, timestamps[:n])).T
    df = pd.DataFrame(data=combined, columns=['power', 'timestamp'])
    return df


def determine_activity(db_serv: DbService, module_data):
    df_speed: DataFrame = load_icu_heartbeat(db_serv, 100)
    df_soc: DataFrame = load_bms_soc(db_serv, 100)
    (df_mppt1, df_mppt2, df_mppt3) = load_mppt_power(db_serv, 100)
    df_bms = load_bms_power(db_serv, 100)
    df_bms_hb = load_bms_heartbeat(db_serv, 1)
    df_icu_hb = load_icu_heartbeat(db_serv, 1)
    df_stwheel_hb = load_stwheel_heartbeat(db_serv, 1)
    df_vcu_hb = load_vcu_heartbeat(db_serv, 1)
    df_mppt1_hb = load_mppt_status0(db_serv, 1)
    df_mppt2_hb = load_mppt_status1(db_serv, 1)
    df_mppt3_hb = load_mppt_status2(db_serv, 1)

    for i, module in enumerate(modules):
        if module == 'vcu':
            update_activity(module_data, i, df_vcu_hb)
        elif module == 'icu':
            update_activity(module_data, i, df_icu_hb)
        elif module == 'mppt0':
            update_activity(module_data, i, df_mppt1_hb)
        elif module == 'mppt1':
            update_activity(module_data, i, df_mppt1_hb)
        elif module == 'mppt2':
            update_activity(module_data, i, df_mppt1_hb)
        elif module == 'bms':
            update_activity(module_data, i, df_bms_hb)
        elif module == 'stwheel':
            update_activity(module_data, i, df_stwheel_hb)
        elif module == 'logger':
            update_activity(module_data, i, df_logger_hb)
        elif module == 'fsensors':
            update_activity(module_data, i, df_fsensors_hb)
        elif module == 'dsensors':
            update_activity(module_data, i, df_dsensors_hb)

    return df_speed, df_mppt1, df_mppt2, df_mppt3, df_bms, df_soc, module_data


def update_activity(module_data, index, df):
    if df.empty:
        module_data[index]['last activity'] = 'no data'
        module_data[index]['status'] = 'inactive'
        return module_data
    last_time = df['timestamp'][0]
    module_data[index]['last activity'] = dt.datetime.fromtimestamp(
        last_time).strftime('%Y-%m-%d %H:%M:%S')
    if ((int(time.time())-last_time) < max_idle_time):
        module_data[index]['status'] = 'inactive'
    else:
        module_data[index]['status'] = 'active'
    return module_data


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
