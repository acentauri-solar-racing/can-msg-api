import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import time

from dash import html, dcc, Input, Output, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1
from frontend.settings import RELOAD_INTERVAL
from utils.load_data import *
import datetime as dt
import copy

dash.register_page(__name__, path="/", title="Overview")

# Global data for page settings:

# Time allowed until the module is flagged as inactive
max_idle_time = 2  # seconds

# Amount of datapoints shown on graph
nr_data_points = 100

# List of tracked modules and their heartbeats. Append here.
module_heartbeats = {'vcu': VcuHeartbeat,
                     'icu': IcuHeartbeat,
                     'mppt0': MpptStatus0,
                     'mppt1': MpptStatus1,
                     'mppt2': MpptStatus2,
                     'bms': BmsHeartbeat,
                     'stwheel': StwheelHeartbeat,
                     'logger': LoggerHeartbeat,
                     'fsensors': FsensorsHeartbeat,
                     'dsensors': DsensorsHeartbeat
                     }


# INITIAL DISPLAY DATA:

def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed
    """
    # Initialize the main table
    main_data = [{'Speed': f"no data", 'Power Consumption of Motor': f"no data",
                  'SOC of Battery': f"no data"},
                 ]
    main_df = pd.DataFrame()

    # Initialize the activity status of all modules
    state = {'module': 'n/a', 'status': "inactive", 'last activity': "no data"}
    module_data = []
    for module in module_heartbeats:
        state['module'] = module
        module_data.append(copy.deepcopy(state))

    # Don't show a graph until requested by a click.
    # Can be 'none', 'speed', 'power' or 'soc'
    show_graph = 'none'

    return main_data, main_df, module_data, show_graph


def optional_graph(df: DataFrame,
                   title: str,
                   column_name: str,
                   xlabel: str,
                   ylabel: str) -> go.Figure:
    """Settings for the optional graph that is triggered by a click on the main
    table.

    Args:
        df (DataFrame): DataFrame to be displayed
        title (str): Title of the Graph
        column_name (str): Column name of the DataFrame to be displayed
        xlabel (str): Label of the x-axis
        ylabel (str): Label of the y-axis

    Returns:
        go.Figure: Graph
    """
    fig: go.Figure = px.line(df,
                             title=title,
                             template="plotly_white",
                             y=column_name,
                             x='timestamp_dt',
                             color_discrete_sequence=["tomato"],
                             markers=True
                             ).update_yaxes()
    fig.update_layout(xaxis_title=xlabel,
                      yaxis_title=ylabel,
                      showlegend=False
                      )
    return fig


def choose_graph(df: DataFrame, type: str) -> html.Div:
    """Adds the chosen graph to a dividor

    Args:
        df (DataFrame): _description_
        type (str): 'none', 'speed', 'power' or 'soc'

    Returns:
        html.Div: Div with the corresponding dcc.Graph
    """
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
                                            "p_sum",
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
    else:
        return html.Div(children=[
            html.H3(f"Error, cannot display {type}"),
        ],
        )


def calculate_power(db_serv: DbService):

    # lowest index is most recent value
    (df_mppt0, df_mppt1, df_mppt2) = load_mppt_power(db_serv, nr_data_points)
    df_bms = load_bms_power(db_serv, nr_data_points)

    df_mppt0 = df_mppt0.rename(columns={'p_out': 'p_out0'})
    df_mppt1 = df_mppt1.rename(columns={'p_out': 'p_out1'})
    df_mppt2 = df_mppt2.rename(columns={'p_out': 'p_out2'})

    # values should not be matched if they have a time difference larger than 2 s
    max_timediff = dt.timedelta(seconds=2)
    # add all the data to one table with the closest timestamp
    df_synch = pd.merge_asof(df_mppt0[['p_out0', 'timestamp_dt', ]
                                      ].sort_values('timestamp_dt'),
                             df_mppt1[['p_out1', 'timestamp_dt', ]
                                      ].sort_values('timestamp_dt'),
                             on='timestamp_dt',
                             tolerance=max_timediff
                             )
    df_synch = pd.merge_asof(df_synch,
                             df_mppt2[['p_out2', 'timestamp_dt', ]
                                      ].sort_values('timestamp_dt'),
                             on='timestamp_dt',
                             tolerance=max_timediff
                             )
    df_synch = pd.merge_asof(df_synch,
                             df_bms[['p_out', 'timestamp_dt', ]
                                    ].sort_values('timestamp_dt'),
                             on='timestamp_dt',
                             tolerance=max_timediff
                             )
    # drop all the rows with nan values
    df_synch = df_synch.dropna()
    df_synch['p_sum'] = df_synch['p_out']+df_synch['p_out0'] + \
        df_synch['p_out1']+df_synch['p_out2']

    # rerverse order of timestamps to start with newest
    return df_synch[::-1]


def determine_activity(db_serv: DbService, module_data: list) -> list:
    """Updates the module_data list for all modules by checking if the last
    data entry of the corresponding heartbeats is more than max_idle_time ago.

    Args:
        db_serv (DbService): SQL database
        module_data (list): List describing activity status of all modules

    Returns:
        list: List describing activity status of all modules
    """

    for i, orm_model in enumerate(module_heartbeats.values()):
        df = load_heartbeat(db_serv, orm_model)
        module_data = update_activity(module_data, i, df)

    return module_data


def update_activity(module_data: list, index: int, df: DataFrame) -> list:
    """Updates a single entry in the module_data list by checking if the last
    data entry of the corresponding heartbeats is more than max_idle_time ago.

    Args:
        module_data (list): List describing activity status of all modules
        index (int): Index of the corresponding module in the module_data list
        df (DataFrame): Table with the module heartbeat data

    Returns:
        list: List describing activity status of all modules
    """
    # set status to 'no data' if the table is empty
    if df.empty:
        module_data[index]['last activity'] = 'no data'
        module_data[index]['status'] = 'inactive'
        return module_data

    # check if the last data entry is more than max_idle_time ago
    last_time = df['timestamp'][0]
    if ((int(time.time())-last_time) > max_idle_time):
        module_data[index]['status'] = 'inactive'
    else:
        module_data[index]['status'] = 'active'

    # update timestamp
    module_data[index]['last activity'] = dt.datetime.fromtimestamp(
        last_time).strftime('%Y-%m-%d %H:%M:%S')
    return module_data


@dash.callback(
    Output("main-table", "data"),
    Output("activity-table", "data"),
    Output("extra-graph", "children"),

    # Triggers after the time interval is over
    Input("interval-component", "n_intervals"),

    # Triggers when a new active cell is selected in the main table
    Input("main-table", "active_cell"),

    # Do not trigger callbacks, but the data is needed for refresh:
    Input("activity-table", "data"),
    Input("main-table", "data")
)
def refresh_data(n, active_cell, module_data, main_data):
    # Refresh data from databank
    db_serv: DbService = DbService()
    df_speed: DataFrame = load_icu_heartbeat(db_serv, nr_data_points)
    df_soc: DataFrame = load_bms_soc(db_serv, nr_data_points)
    df_power: DataFrame = calculate_power(db_serv)

    # Update data in main table
    main_data[0]['Speed'] = f"{'{:.1f}'.format(df_speed['speed'][0])} km/h"
    main_data[0]['Power Consumption of Motor'] = f"{'{:.1f}'.format(df_power['p_sum'][0])} W"
    main_data[0]['SOC of Battery'] = f"{'{:.1f}'.format(df_soc['soc_percent'][0])} %"

    # Update data in activity table
    module_data = determine_activity(
        db_serv, module_data)

    # Update graph and return
    if (active_cell == None):
        return main_data, module_data, choose_graph(df_speed, 'none')
    elif active_cell['column'] == 0:
        return main_data, module_data, choose_graph(df_speed, 'speed')
    elif active_cell['column'] == 1:
        return main_data, module_data, choose_graph(df_power, 'power')
    elif active_cell['column'] == 2:
        return main_data, module_data, choose_graph(df_soc, 'soc')


def layout():
    main_data, main_df, module_data, show_graph = initialize_data()

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
                                         'state': 'active'
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'

                                 },
                                 {
                                     'if': {
                                         'state': 'selected'
                                     },
                                     'backgroundColor': 'tomato',
                                     'color': 'white'

                                 },
                             ],
                             ),
        html.Br(),
        html.Br(),
        html.Div(children=choose_graph(main_df, show_graph),
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
