import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd

from typing import Tuple
from dash import html, dcc, Input, Output

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1, H2
from frontend.settings import RELOAD_INTERVAL
import plotly.graph_objs as go

from utils.load_data import load_mppt_power, load_mppt_status_data

dash.register_page(__name__, path="/mppt", title="MPPT")


def v_i_graph(df: DataFrame):
    fig: go.Figure  = px.line(df,
                            title="Voltage & Current",
                            template="plotly_white",
                            x="timestamp_dt",
                            y=["v_in", "i_in", "v_out", "i_out"],
                            ).update_yaxes(range=[0, 15])
    fig.update_layout(xaxis_title='Timestamp')
    return fig


def power_graph(df: DataFrame):
    fig: go.Figure = px.line(df,
                        title="Power",
                        template="plotly_white",
                        x="timestamp_dt",
                        y=["p_in", "p_out"]
                        ).update_yaxes(range=[0, 15])
    fig.update_layout(xaxis_title='Timestamp')
    return fig

def disp_mppt(power_df: DataFrame, stat) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([html.H3("Status")], className="col-3"),
            dbc.Col([html.H3("Power")], ),
        ], className="text-center"),
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
                ])
            ], className="col-3"),
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=v_i_graph(power_df)),
                    ]),
                    dbc.Col([
                        dcc.Graph(figure=power_graph(power_df),
                                  )
                    ])
                ])
            ]),
        ], className="align-items-center"),
    ])


@dash.callback(Output('live-update-div-mppt', 'children'), Input('interval-component', 'n_intervals'))
def refresh_data(n):
    db_serv: DbService = DbService()

    try:
        (power_df0, power_df1, power_df2) = load_mppt_power(db_serv, 100)
        (stat0, stat1, stat2) = load_mppt_status_data(db_serv)

        return html.Div([
            html.H1(["MPPT"], style=H1, className="text-center"),
            html.H2(["MPPT 0"], style=H2, className="text-center"),
            disp_mppt(power_df0, stat0),
            html.Hr(),
            html.H2(["MPPT 1"], style=H2, className="text-center"),
            disp_mppt(power_df1, stat1),
            html.Hr(),
            html.H2(["MPPT 2"], style=H2, className="text-center"),
            disp_mppt(power_df2, stat2),
        ])
    except:
        print("Err: Couldn't load MPPT Tables")

        return html.Div(html.H2("Data load failed", className="text-center"))


def layout():
    return html.Div([
        html.Div(id='live-update-div-mppt'),
        dcc.Interval(
            id='interval-component',
            interval=RELOAD_INTERVAL,
            n_intervals=0
        )
    ])
