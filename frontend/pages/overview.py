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
import copy

dash.register_page(__name__, path="/", title="Overview")

# Time allowed until the module is flagged as inactive
max_idle_time = 2  # seconds


# INITIAL DISPLAY DATA:

# Initialize the speed, power and soc data displayed
main_data = [{'Speed': f"no data", 'Power Consumption of Motor': f"no data",
              'SOC of Battery': f"no data"},
             ]
main_df = pd.DataFrame()

# List of tracked modules. Append here.
modules = ['vcu', 'icu', 'mppt0', 'mppt1', 'mppt2',
           'bms', 'stwheel', 'logger', 'fsensors', 'dsensors']

# Initialize the activity status of all modules
state = {'module': 'n/a', 'status': "inactive", 'last activity': "no data"}
module_data = []
for module in modules:
    state['module'] = module
    module_data.append(copy.deepcopy(state))

# Don't show a graph until requested by a click. Can be 'none', 'speed', 'power' or 'soc'
show_graph = 'none'


def optional_graph(df: DataFrame,
                   title: str,
                   column_name: str,
                   xlabel: str,
                   ylabel: str):
    fig: go.Figure = px.line(df,
                             title=title,
                             template="plotly_white",
                             y=column_name,
                             color_discrete_sequence=["tomato"],
                             markers=True
                             ).update_yaxes()
    fig.update_layout(xaxis_title=xlabel,
                      yaxis_title=ylabel,
                      showlegend=False
                      )
    return fig


def disp(df: DataFrame, type: str):
    if type == 'none':
        return html.Div(children=[],
                        )
    elif type == 'speed':
        return html.Div(children=[
            dcc.Graph(figure=optional_graph(df,
                                            "Speed",
                                            "speed",
                                            'Time of data entry',
                                            'Speed / km/h')),
        ],
        )
    elif type == 'power':
        return html.Div(children=[
            dcc.Graph(figure=optional_graph(df,
                                            "Power",
                                            "power",
                                            'Time of data entry',
                                            'Power consumed / W')),
        ],
        )
    elif type == 'soc':
        return html.Div(children=[
            dcc.Graph(figure=optional_graph(df,
                                            "State of Charge",
                                            "soc_percent",
                                            'Time of data entry',
                                            'State of charge / %')),
        ],
        )


def calculate_power(df_mppt1, df_mppt2, df_mppt3, df_bms):
    # this needs to be checked by someone that actually knows what they're doing
    # kinda wack, but I'm just adding the most recent values without checking if
    # they're actually synchronous. feel free to improve ;)

    # lowest index is most recent value

    # load data into numpy arrays for processing
    timestamps_dt = df_bms['timestamp_dt'].to_numpy()
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
    combined = np.vstack((power, timestamps[:n], timestamps_dt[:n])).T
    df = pd.DataFrame(data=combined, columns=[
                      'power', 'timestamp', 'timestamp_dt'])
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
    df_logger_hb = load_logger_heartbeat(db_serv, 1)
    df_fsensors_hb = load_fsensors_heartbeat(db_serv, 1)
    df_dsensors_hb = load_dsensors_heartbeat(db_serv, 1)

    for i, module in enumerate(modules):
        if module == 'vcu':
            update_activity(module_data, i, df_vcu_hb)
        elif module == 'icu':
            update_activity(module_data, i, df_icu_hb)
        elif module == 'mppt0':
            update_activity(module_data, i, df_mppt1_hb)
        elif module == 'mppt1':
            update_activity(module_data, i, df_mppt2_hb)
        elif module == 'mppt2':
            update_activity(module_data, i, df_mppt3_hb)
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
    if ((int(time.time())-last_time) > max_idle_time):
        module_data[index]['status'] = 'inactive'
    else:
        module_data[index]['status'] = 'active'

    return module_data


@dash.callback(
    Output("main-table", "data"),
    Output("activity-table", "data"),
    Output("extra-graph", "children"),
    Input("interval-component", "n_intervals"),
    Input("main-table", "active_cell"),
    # does not trigger callback, but data needed
    Input("activity-table", "data"),
    Input("main-table", "data")  # does not trigger callback, but data needed
)
def refresh_data(n, active_cell, module_data, main_data):
    db_serv: DbService = DbService()
    df_speed, df_mppt1, df_mppt2, df_mppt3, df_bms, df_soc, module_data = determine_activity(
        db_serv, module_data)

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

    main_data[0]['Speed'] = f"{'{:.1f}'.format(df_speed['speed'][0])} km/h"
    main_data[0]['Power Consumption of Motor'] = f"{'{:.1f}'.format(df_power['power'][0])} W"
    main_data[0]['SOC of Battery'] = f"{'{:.1f}'.format(df_soc['soc_percent'][0])} %"

    return main_data, module_data, disp(df, show_graph)


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
