import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go

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


def load_power_data(db_serv: DbService) -> Tuple[DataFrame]:
    return (preprocess_power(
        db_serv.query(MpptPowerMeas0, 100),
    ),
        preprocess_power(
        db_serv.query(MpptPowerMeas1, 100)
    ),
        preprocess_power(
        db_serv.query(MpptPowerMeas2, 100)
    ))


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


def preprocess_power(df: DataFrame) -> DataFrame:
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
                             y=["v_in", "v_out"]
                             ).update_yaxes(range=[0, 15])
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


@dash.callback(
    Output("main-table", "data"),
    Output("activity-table", "data"),
    Output("extra-graph", "children"),
    Input("interval-component", "n_intervals"),
    Input("main-table", "active_cell"),

)
def refresh_data(n, active_cell):
    db_serv: DbService = DbService()
    df_speed: DataFrame = load_icu_data(db_serv)
    (df_power1, df_power2, df_power3) = load_power_data(db_serv)
    df_soc: DataFrame = load_soc_data(db_serv)

    if (active_cell == None):
        show_graph = 'none'
        df = df_speed
        active_column = 4
        active_column_id = 'nope'
    elif active_cell['column'] == 0:
        print('speed')
        show_graph = 'speed'
        df = df_speed
        active_column = 0
        active_column_id = active_cell['column_id']
    elif active_cell['column'] == 1:
        print('power')
        show_graph = 'power'
        df = df_power1
        active_column = 1
        active_column_id = active_cell['column_id']
    elif active_cell['column'] == 2:
        print('soc')
        show_graph = 'soc'
        df = df_soc
        active_column = 2
        active_column_id = active_cell['column_id']

    # TODO: implement actual data update
    speed = 0
    power = 12
    soc = 'batshit'
    main_data = [{'Speed': f"{speed} km/h", 'Power Consumption of Motor': f"{power} W",
                  'SOC of Battery': f"{soc} %"}]

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
