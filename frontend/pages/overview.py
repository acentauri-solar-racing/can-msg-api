import dash
import plotly.express as px
import plotly.graph_objs as go
import time

from dash import html, dcc, Input, Output, dash_table

from db.db_service import DbService
from pandas import DataFrame
import frontend.styles as styles
from frontend.settings import RELOAD_INTERVAL
from db.load_data import *
import datetime as dt
import copy
from collections import deque

dash.register_page(__name__, path="/", title="Overview")

# Global data for page settings:

# Time allowed until the module is flagged as inactive
max_idle_time = 2  # seconds

# Time span that is displayed in the graphs (e.g. if it's set to 5, then the values of the last five minutes are displayed)
timespan_displayed = 5  # minutes
# Frequency with which the heartbeats are sent
heartbeat_frequency = 16  # [Hz]

# List of tracked modules and their heartbeats. Append here.
module_heartbeats = {
    "vcu": VcuHeartbeat,
    "icu": IcuHeartbeat,
    "mppt0": MpptStatus0,
    "mppt1": MpptStatus1,
    "mppt2": MpptStatus2,
    "bms": BmsHeartbeat,
    "stwheel": StwheelHeartbeat,
    "logger": LoggerHeartbeat,
    "fsensors": FsensorsHeartbeat,
    "dsensors": DsensorsHeartbeat,
}


speed_data = deque()


def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed"""
    # Initialize the main table
    main_data = [
        {
            "Speed": "no data",
            "Power Consumption": "no data",
            "SOC of Battery": "no data",
        },
    ]
    main_df = pd.DataFrame()

    # Initialize the activity status of all modules
    state = {"module": "n/a", "status": "inactive", "last activity": "no data"}
    module_data = []
    for module in module_heartbeats:
        state["module"] = module
        module_data.append(copy.deepcopy(state))

    module_df = pd.DataFrame(module_data)

    # Don't show a graph until requested by a click.
    # Can be 'none', 'speed', 'power' or 'soc'
    show_graph = "none"

    return main_data, main_df, module_data, show_graph, module_df


def optional_graph(
        df: DataFrame, title: str, column_name: str, xlabel: str, ylabel: str
) -> go.Figure:
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
    fig: go.Figure = px.line(
        df,
        title=title,
        template="plotly_white",
        y=column_name,
        x="timestamp_dt",
        color_discrete_sequence=[styles.COLOR_SELECTED],
        markers=True,
    ).update_yaxes()
    fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel, showlegend=False)
    return fig


def choose_graph(df: DataFrame, type: str) -> html.Div:
    """Adds the chosen graph to a dividor

    Args:
        df (DataFrame): SQL database
        type (str): 'none', 'speed', 'power' or 'soc'

    Returns:
        html.Div: Div with the corresponding dcc.Graph
    """
    if type == "none":
        return html.Div(
            children=[],
        )
    elif type == "speed":
        return html.Div(
            children=[
                dcc.Graph(
                    figure=optional_graph(
                        df, "Speed", "speed", "Time of data entry", "Speed / km/h"
                    )
                ),
            ],
        )
    elif type == "power":
        return html.Div(
            children=[
                dcc.Graph(
                    figure=optional_graph(
                        df, "Power", "p_sum", "Time of data entry", "Power consumed / W"
                    )
                ),
            ],
        )
    elif type == "soc":
        return html.Div(
            children=[
                dcc.Graph(
                    figure=optional_graph(
                        df,
                        "State of Charge",
                        "soc_percent",
                        "Time of data entry",
                        "State of charge / %",
                    )
                ),
            ],
        )
    else:
        return html.Div(
            children=[
                html.H3(f"Error, cannot display {type}"),
            ],
        )


def calculate_power(db_serv: DbService, max_timediff: int = 2) -> DataFrame:
    """Returns a the sum of the power consumption measured by the 3 MPPTs and
    the BMS. The timestamp of the data is found with the merge_asof method
    (the data measured most recently after the timestamp is considered).
    Datapoints more than max_diff seconds apart are not linked.

    Args:
        db_serv (DbService): SQL database
        max_timediff (int): Optional. Maximum time difference until power measurements are no longer added.

    Returns:
        DataFrame: Synchronised dataframe with p_sum column for total power
    """

    # lowest index is most recent value
    (df_mppt0, df_mppt1, df_mppt2) = load_mppt_power(db_serv, timespan_displayed)
    df_bms = load_bms_pack_data(db_serv, timespan_displayed)

    df_mppt0 = df_mppt0.rename(columns={"p_out": "p_out0"})
    df_mppt1 = df_mppt1.rename(columns={"p_out": "p_out1"})
    df_mppt2 = df_mppt2.rename(columns={"p_out": "p_out2"})

    # values should not be matched if they have a time difference larger than 2 s
    max_timediff = dt.timedelta(seconds=max_timediff)
    # add all the data to one table with the closest timestamp
    df_synch = pd.merge_asof(
        df_mppt0[
            [
                "p_out0",
                "timestamp_dt",
            ]
        ].sort_values("timestamp_dt"),
        df_mppt1[
            [
                "p_out1",
                "timestamp_dt",
            ]
        ].sort_values("timestamp_dt"),
        on="timestamp_dt",
        tolerance=max_timediff,
    )
    df_synch = pd.merge_asof(
        df_synch,
        df_mppt2[
            [
                "p_out2",
                "timestamp_dt",
            ]
        ].sort_values("timestamp_dt"),
        on="timestamp_dt",
        tolerance=max_timediff,
    )
    df_synch = pd.merge_asof(
        df_synch,
        df_bms[
            [
                "p_out",
                "timestamp_dt",
            ]
        ].sort_values("timestamp_dt"),
        on="timestamp_dt",
        tolerance=max_timediff,
    )
    # drop all the rows with nan values
    df_synch = df_synch.dropna()
    df_synch["p_sum"] = (
            df_synch["p_out"] + df_synch["p_out0"] + df_synch["p_out1"] + df_synch["p_out2"]
    )

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
        try:
            df = load_heartbeat(db_serv, orm_model)
            module_data = update_activity(module_data, i, df)
        except:
            module_data[i]["last activity"] = "n/a"
            module_data[i]["status"] = "error in databank"
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
        module_data[index]["last activity"] = "no data"
        module_data[index]["status"] = "inactive"
        return module_data

    # check if the last data entry is more than max_idle_time ago
    last_time = df["timestamp"][0]
    if (int(time.time()) - last_time) > max_idle_time:
        module_data[index]["status"] = "inactive"
    else:
        module_data[index]["status"] = "active"

    # update timestamp
    module_data[index]["last activity"] = dt.datetime.fromtimestamp(last_time).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return module_data


@dash.callback(
    Output("performance-table", "data"),
    Output("battery-table", "data"),
    Output("module-table", "data"),
    Input("interval-component", "n_intervals"))  # Triggers after the time interval is over
def refresh_data(n: int):
    """Refreshes the data in the tables & graphs, and chooses whether a graph
    should be displayed dependent on the active cell.

    Args:
        n (int): unused
        active_cell (dict): Cell selected by user in the main table
        module_data (list): Data in the table showing the module activity
        main_data (list): Data in the table showing the main data

    Returns:
        tuple: Updated data and optional graph
    """
    # Refresh data from databank
    db_serv: DbService = DbService()

    # Car Speed
    df_speed: DataFrame = load_speed(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    speed_last = df_speed['speed'][0]
    speed_max = df_speed['speed'].max()
    speed_min = df_speed['speed'].min()
    speed_mean = df_speed['speed'].mean()

    # PV String voltage, current, power
    df_pv_string_1, df_pv_string_2, df_pv_string_3 = load_mppt_power(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    pv1Volt_last = df_pv_string_1['v_in'][0]
    pv1Volt_max = df_pv_string_1['v_in'].max()
    pv1Volt_min = df_pv_string_1['v_in'].min()
    pv1Volt_mean = df_pv_string_1['v_in'].mean()

    pv2Volt_last = df_pv_string_2['v_in'][0]
    pv2Volt_max = df_pv_string_2['v_in'].max()
    pv2Volt_min = df_pv_string_2['v_in'].min()
    pv2Volt_mean = df_pv_string_2['v_in'].mean()

    pv3Volt_last = df_pv_string_3['v_in'][0]
    pv3Volt_max = df_pv_string_3['v_in'].max()
    pv3Volt_min = df_pv_string_3['v_in'].min()
    pv3Volt_mean = df_pv_string_3['v_in'].mean()

    pv1Curr_last = df_pv_string_1['i_in'][0]
    pv1Curr_max = df_pv_string_1['i_in'].max()
    pv1Curr_min = df_pv_string_1['i_in'].min()
    pv1Curr_mean = df_pv_string_1['i_in'].mean()

    pv2Curr_last = df_pv_string_2['i_in'][0]
    pv2Curr_max = df_pv_string_2['i_in'].max()
    pv2Curr_min = df_pv_string_2['i_in'].min()
    pv2Curr_mean = df_pv_string_2['i_in'].mean()

    pv3Curr_last = df_pv_string_3['i_in'][0]
    pv3Curr_max = df_pv_string_3['i_in'].max()
    pv3Curr_min = df_pv_string_3['i_in'].min()
    pv3Curr_mean = df_pv_string_3['i_in'].mean()

    # Battery State of Charge
    df_soc: DataFrame = load_bms_soc(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    soc_last = df_soc['soc_percent'][0]
    soc_max = df_soc['soc_percent'].max()
    soc_min = df_soc['soc_percent'].min()
    soc_mean = df_soc['soc_percent'].mean()

    # Battery Voltage, Current and Power
    df_bat_pack = load_bms_pack_data(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    batPow_last = df_bat_pack['battery_power'][0]
    batPow_max = df_bat_pack['battery_power'].max()
    batPow_min = df_bat_pack['battery_power'].min()
    batPow_mean = df_bat_pack['battery_power'].mean()

    batVolt_last = df_bat_pack['battery_voltage'][0]
    batVolt_max = df_bat_pack['battery_voltage'].max()
    batVolt_min = df_bat_pack['battery_voltage'].min()
    batVolt_mean = df_bat_pack['battery_voltage'].mean()

    batCurr_last = df_bat_pack['battery_current'][0]
    batCurr_max = df_bat_pack['battery_current'].max()
    batCurr_min = df_bat_pack['battery_current'].min()
    batCurr_mean = df_bat_pack['battery_current'].mean()
    # df_mppt_power : DataFrame = calculate_power(db_serv)

    # Update data in main table
    performance_data = [{'': 'Speed [km/h]', '{:d}\' Min'.format(timespan_displayed): '{:3.1f}'.format(speed_min),
                         '{:d}\' Max'.format(timespan_displayed): '{:3.1f}'.format(speed_max),
                         '{:d}\' Mean'.format(timespan_displayed): '{:3.1f}'.format(speed_mean),
                         'Last': '{:3.1f}'.format(speed_last)},
                        {'': 'Battery Power [W]', '{:d}\' Min'.format(timespan_displayed): '{:6.1f}'.format(batPow_min),
                         '{:d}\' Max'.format(timespan_displayed): '{:6.1f}'.format(batPow_max),
                         '{:d}\' Mean'.format(timespan_displayed): '{:6.1f}'.format(batPow_mean),
                         'Last': '{:6.1f}'.format(batPow_last)},
                        {'': 'Battery SOC [%]', '{:d}\' Min'.format(timespan_displayed): '{:3.1f}'.format(soc_min),
                         '{:d}\' Max'.format(timespan_displayed): '{:3.1f}'.format(soc_max),
                         '{:d}\' Mean'.format(timespan_displayed): '{:3.1f}'.format(soc_mean),
                         'Last': '{:3.1f}'.format(soc_last)},
                        {'': 'Battery Voltage [V]', '{:d}\' Min'.format(timespan_displayed): '{:3.1f}'.format(batVolt_min),
                         '{:d}\' Max'.format(timespan_displayed): '{:3.1f}'.format(batVolt_max),
                         '{:d}\' Mean'.format(timespan_displayed): '{:3.1f}'.format(batVolt_mean),
                         'Last': '{:3.1f}'.format(batVolt_last)},
                        {'': 'Battery Current [mA]', '{:d}\' Min'.format(timespan_displayed): '{:6.1f}'.format(batCurr_min),
                         '{:d}\' Max'.format(timespan_displayed): '{:6.1f}'.format(batCurr_max),
                         '{:d}\' Mean'.format(timespan_displayed): '{:6.1f}'.format(batCurr_mean),
                         'Last': '{:6.1f}'.format(batCurr_last)}]

    battery_data = [{'': 'Battery Cell Temperature [°C]', 'Min': '38', 'Max': '45', '5\' Diff': '1'},
                    {'': 'Battery Cell Voltage [mV]', 'Min': '3900', 'Max': '4200', '5\' Diff': '20'}]

    module_data = [{'': 'Status'}]
    for m in module_heartbeats:
        module_data[0].update({m: 'active'})

    # {'id': c, 'name': c} for c in module_df.columns]
    # Update data in activity table
    return performance_data, battery_data, module_data


def get_graph():
    pass


def getCols_moduleTable() -> list[str]:
    cols = [{'name': '', 'id': ''}]
    for col in module_heartbeats:
        cols.append({'name': col, 'id': col})

    return cols


def layout() -> html.Div:
    """Defines the layout of the page and returns it as a div

    Returns:
        html.Div: Div with the page layout
    """
    performance_data, main_df, battery_data, show_graph, module_df = initialize_data()

    return html.Div(
        children=[
            html.H1("Overview", style=styles.H1, className="text-center"),
            dash_table.DataTable(
                id="performance-table",
                data=performance_data,
                cell_selectable=False,
                style_cell=styles.PERFORMANCE_CELL,
                style_cell_conditional=styles.PERFORMANCE_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.DATA_CONDITIONAL),
            html.Br(),
            html.Br(),
            dash_table.DataTable(
                id="battery-table",
                data=battery_data,
                cell_selectable=False,
                style_cell=styles.BATTERY_CELL,
                style_cell_conditional=styles.BATTERY_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.DATA_CONDITIONAL),
            html.Br(),
            html.Br(),
            dash_table.DataTable(
                id="module-table",
                columns=getCols_moduleTable(),
                data=battery_data,
                cell_selectable=False,
                style_cell=styles.MODULE_CELL,
                style_cell_conditional=styles.MODULE_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.DATA_CONDITIONAL),
            dcc.Graph(figure=get_graph()),
            dcc.Interval(
                id="interval-component", interval=RELOAD_INTERVAL, n_intervals=0
            ),
        ]
    )
