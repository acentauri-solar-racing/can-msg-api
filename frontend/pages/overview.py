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


def getMinMaxMeanLast(df: DataFrame, col: str, numberFormat: str) -> Tuple[str, str, str, str]:
    if (df.empty):
        return ('No Data','No Data','No Data','No Data')
    else:
        return (('{:' + numberFormat + '}').format(df[col][0]), ('{:' + numberFormat + '}').format(df[col].min()),
                ('{:' + numberFormat + '}').format(df[col].max()), ('{:' + numberFormat + '}').format(df[col].mean()))


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

    return main_data, module_data


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
    speed_min, speed_max, speed_mean, speed_last = getMinMaxMeanLast(df_speed, 'speed', '3.1f')

    # PV String voltage, String current, output power
    df_pv, df_pv_string_0, df_pv_string_1, df_pv_string_2, df_pv_string_3 = load_mppt_power(db_serv,
                                                                                            timespan_displayed * 60 * heartbeat_frequency)
    pv0Volt_min,pv0Volt_max,pv0Volt_mean,pv0Volt_last = getMinMaxMeanLast(df_pv_string_0, 'v_in', '3.1f')
    pv1Volt_min,pv1Volt_max,pv1Volt_mean,pv1Volt_last = getMinMaxMeanLast(df_pv_string_1, 'v_in', '3.1f')
    pv2Volt_min,pv2Volt_max,pv2Volt_mean,pv2Volt_last = getMinMaxMeanLast(df_pv_string_2, 'v_in', '3.1f')
    pv3Volt_min,pv3Volt_max,pv3Volt_mean,pv3Volt_last = getMinMaxMeanLast(df_pv_string_3, 'v_in', '3.1f')

    pv0Curr_min,pv0Curr_max,pv0Curr_mean,pv0Curr_last = getMinMaxMeanLast(df_pv_string_0, 'i_in', '6.1f')
    pv1Curr_min,pv1Curr_max,pv1Curr_mean,pv1Curr_last = getMinMaxMeanLast(df_pv_string_1, 'i_in', '6.1f')
    pv2Curr_min,pv2Curr_max,pv2Curr_mean,pv2Curr_last = getMinMaxMeanLast(df_pv_string_2, 'i_in', '6.1f')
    pv3Curr_min,pv3Curr_max,pv3Curr_mean,pv3Curr_last = getMinMaxMeanLast(df_pv_string_3, 'i_in', '6.1f')

    pvPow_min,pvPow_max,pvPow_mean,pvPow_last = getMinMaxMeanLast(df_pv, 'p_out', '3.1f')
    pv0Pow_min,pv0Pow_max,pv0Pow_mean,pv0Pow_last = getMinMaxMeanLast(df_pv_string_0, 'p_out', '3.1f')
    pv1Pow_min,pv1Pow_max,pv1Pow_mean,pv1Pow_last = getMinMaxMeanLast(df_pv_string_1, 'p_out', '3.1f')
    pv2Pow_min,pv2Pow_max,pv2Pow_mean,pv2Pow_last = getMinMaxMeanLast(df_pv_string_2, 'p_out', '3.1f')
    pv3Pow_min,pv3Pow_max,pv3Pow_mean,pv3Pow_last = getMinMaxMeanLast(df_pv_string_3, 'p_out', '3.1f')

    # Battery State of Charge
    df_soc: DataFrame = load_bms_soc(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    soc_min,soc_max,soc_mean,soc_last = getMinMaxMeanLast(df_soc, 'soc_percent', '3.1f')

    # Battery Voltage, Current and Power
    df_bat_pack = load_bms_pack_data(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    batPow_min,batPow_max,batPow_mean,batPow_last = getMinMaxMeanLast(df_bat_pack,'battery_power','3.1f')
    batVolt_min,batVolt_max,batVolt_mean,batVolt_last = getMinMaxMeanLast(df_bat_pack,'battery_voltage','3.1f')
    batCurr_min,batCurr_max,batCurr_mean,batCurr_last = getMinMaxMeanLast(df_bat_pack,'battery_current','6.1f')

    # Battery Maximum Cell Voltage, Minimum Cell Voltage
    df_cellVolt = load_bms_cell_voltage(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    maxCellVolt_min,maxCellVolt_max,maxCellVolt_mean,maxCellVolt_last = getMinMaxMeanLast(df_cellVolt, 'max_cell_voltage', '2.3f')
    minCellVolt_min,minCellVolt_max,minCellVolt_mean,minCellVolt_last = getMinMaxMeanLast(df_cellVolt, 'min_cell_voltage', '2.3f')

    # Battery Maximum Cell Temperature, Minimum Cell Temperature
    df_cellTemp= load_bms_cell_temp(db_serv, timespan_displayed * 60 * heartbeat_frequency)
    maxCellTemp_min,maxCellTemp_max,maxCellTemp_mean,maxCellTemp_last = getMinMaxMeanLast(df_cellVolt, 'max_cell_temp', '2.3f')
    minCellTemp_min,minCellTemp_max,minCellTemp_mean,minCellTemp_last = getMinMaxMeanLast(df_cellVolt, 'min_cell_temp', '2.3f')

    # Motor Power = Power from Solar Array + Power from Battery
    df_motorPow = DataFrame()
    df_motorPow['pow'] = df_pv['p_out'] + df_bat_pack['battery_power']
    motorPow_min,motorPow_max,motorPow_mean,motorPow_last = getMinMaxMeanLast(df_motorPow,'pow', '3.1f')

    # Update data in main table
    performance_data = [{'': 'Speed [km/h]', '{:d}\' Min'.format(timespan_displayed): speed_min,
                         '{:d}\' Max'.format(timespan_displayed): speed_max,
                         '{:d}\' Mean'.format(timespan_displayed): speed_mean,
                         'Last': speed_last},
                        {'': 'Motor Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): motorPow_min,
                         '{:d}\' Max'.format(timespan_displayed):motorPow_max,
                         '{:d}\' Mean'.format(timespan_displayed): motorPow_mean,
                         'Last': motorPow_last}, {},
                        {'': 'PV Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): pvPow_min,
                         '{:d}\' Max'.format(timespan_displayed): pvPow_max,
                         '{:d}\' Mean'.format(timespan_displayed): pvPow_mean,
                         'Last': pvPow_last},
                        {'': 'PV String 0 Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): pv0Pow_min,
                         '{:d}\' Max'.format(timespan_displayed): pv0Pow_max,
                         '{:d}\' Mean'.format(timespan_displayed): pv0Pow_mean,
                         'Last': pv0Pow_last},
                        {'': 'PV String 1 Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): pv1Pow_min,
                         '{:d}\' Max'.format(timespan_displayed): pv1Pow_max,
                         '{:d}\' Mean'.format(timespan_displayed): pv1Pow_mean,
                         'Last': pv1Pow_last},
                        {'': 'PV String 2 Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): pv2Pow_min,
                         '{:d}\' Max'.format(timespan_displayed): pv2Pow_max,
                         '{:d}\' Mean'.format(timespan_displayed): pv2Pow_mean,
                         'Last': pv2Pow_last},
                        {'': 'PV String 3 Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): pv3Pow_min,
                         '{:d}\' Max'.format(timespan_displayed): pv3Pow_max,
                         '{:d}\' Mean'.format(timespan_displayed): pv3Pow_mean,
                         'Last': pv3Pow_last}, {},
                        {'': 'Battery Output Power [W]',
                         '{:d}\' Min'.format(timespan_displayed): batPow_min,
                         '{:d}\' Max'.format(timespan_displayed): batPow_max,
                         '{:d}\' Mean'.format(timespan_displayed): batPow_mean,
                         'Last': batPow_last},
                        {'': 'Battery SOC [%]', '{:d}\' Min'.format(timespan_displayed): soc_min,
                         '{:d}\' Max'.format(timespan_displayed): soc_max,
                         '{:d}\' Mean'.format(timespan_displayed): soc_mean,
                         'Last': soc_last},
                        {'': 'Battery Voltage [V]',
                         '{:d}\' Min'.format(timespan_displayed): batVolt_min,
                         '{:d}\' Max'.format(timespan_displayed): batVolt_max,
                         '{:d}\' Mean'.format(timespan_displayed): batVolt_mean,
                         'Last': batVolt_last},
                        {'': 'Battery Output Current [mA]',
                         '{:d}\' Min'.format(timespan_displayed): batCurr_min,
                         '{:d}\' Max'.format(timespan_displayed): batCurr_max,
                         '{:d}\' Mean'.format(timespan_displayed): batCurr_mean,
                         'Last': batCurr_last},
                        {'': 'Battery Minimum Cell Voltage [mV]',
                         '{:d}\' Min'.format(timespan_displayed): minCellVolt_min,
                         '{:d}\' Max'.format(timespan_displayed): minCellVolt_max,
                         '{:d}\' Mean'.format(timespan_displayed): minCellVolt_mean,
                         'Last': minCellVolt_last},
                        {'': 'Battery Maximum Cell Voltage [mV]',
                         '{:d}\' Min'.format(timespan_displayed): maxCellVolt_min,
                         '{:d}\' Max'.format(timespan_displayed): maxCellVolt_max,
                         '{:d}\' Mean'.format(timespan_displayed): maxCellVolt_mean,
                         'Last': maxCellVolt_last},
                        {'': 'Battery Minimum Cell Temperature [°C]',
                         '{:d}\' Min'.format(timespan_displayed): minCellTemp_min,
                         '{:d}\' Max'.format(timespan_displayed): minCellTemp_max,
                         '{:d}\' Mean'.format(timespan_displayed): minCellTemp_mean,
                         'Last': minCellTemp_last},
                        {'': 'Battery Maximum Cell Temperature [°C]',
                         '{:d}\' Min'.format(timespan_displayed): maxCellTemp_min,
                         '{:d}\' Max'.format(timespan_displayed): maxCellTemp_max,
                         '{:d}\' Mean'.format(timespan_displayed): maxCellTemp_mean,
                         'Last': maxCellTemp_last}]

    module_data = [{'': 'Status'}]
    for m in module_heartbeats:
        module_data[0].update({m: 'active'})

    # {'id': c, 'name': c} for c in module_df.columns]
    # Update data in activity table
    return performance_data, module_data


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
    performance_data, module_data = initialize_data()

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
                id="module-table",
                columns=getCols_moduleTable(),
                data=module_data,
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
