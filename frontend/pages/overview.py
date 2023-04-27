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

main_data = [
    {'Speed': f"{speed} km/h", 'Power Consumption of Motor': f"{power} W",
        'SOC of Battery': f"{soc} %"},
]


def load_icu_data(db_serv: DbService) -> DataFrame:
    return preprocess(
        db_serv.query(IcuHeartbeat, 100)
    )


def load_power_data(db_serv: DbService) -> DataFrame:
    return preprocess(
        db_serv.query(BmsPackSoc, 100)
    )


def load_soc_data(db_serv: DbService) -> DataFrame:
    return preprocess(
        db_serv.query(BmsPackSoc, 100)
    )


def preprocess(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6
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


def disp_speed(df: DataFrame):
    dbc.Col(
        [
            html.H2("Speed", style=H2, className="text-center"),
            dcc.Graph(figure=speed_graph(df)),
        ]
    )


def disp_speed(df: DataFrame):
    return dbc.Row(
        [
            dbc.Col(
                [
                    dcc.Graph(figure=speed_graph(df)),
                ]
            ),
        ]
    )


show_speed = False
show_power = False
show_soc = True


@dash.callback(
    Output("live-update-speed", "children"),
    Input("interval-component", "n_intervals"),
)
def refresh_data(n):
    db_serv: DbService = DbService()
    df: DataFrame = load_icu_data(db_serv)

    try:
        return html.Div(
            [
                html.H1("Overview", style=H1, className="text-center"),
                html.H2("Car Status"),
                dash_table.DataTable(data=main_data,
                                     id='main_table',
                                     style_data={
                                        'font_size': '25px',
                                        'font_weight': 'heavy'
                                     },
                                     style_as_list_view=True,
                                     ),
                disp_speed(df),
                html.H2("Module Status"),
                dash_table.DataTable(data=module_data,
                                     id='activity_table',
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
                                     )
            ]
        )
    except:
        print("Err: Couldn't load BMS Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))


def layout():
    return html.Div(
        [
            html.Div(id="live-update-speed"),
            dcc.Interval(
                id="interval-component", interval=RELOAD_INTERVAL, n_intervals=0
            ),
        ]
    )
