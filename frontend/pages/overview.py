from typing import Union

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
from dataclasses import dataclass

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


class TableRow:
    title: str = ''
    min: str = ''
    max: str = ''
    mean: str = ''
    last: str = ''

    def refresh(self) -> {}:
        return {'': self.title,
                '{:d}\' Min'.format(timespan_displayed): self.min,
                '{:d}\' Max'.format(timespan_displayed): self.max,
                '{:d}\' Mean'.format(timespan_displayed): self.mean,
                'Last'.format(timespan_displayed): self.last}


class TableDataRow(TableRow):
    df_name: str
    df_col: str  # Column name in the dataframe
    numberFormat: str  # number format of the displayed values
    selected: bool  # indicates whether a row was selected

    def __init__(self, title: str, df_name: str, df_col: str, numberFormat: str = '3.1f', selected: bool = False):
        self.title = title
        self.df_name = df_name
        self.df_col = df_col
        self.numberFormat = numberFormat
        self.selected = selected

    def refresh(self) -> {}:
        self.min, self.max, self.mean, self.last = getMinMaxMeanLast(main_table_data[self.df_name].df, self.df_col,
                                                                     self.numberFormat)
        return super().refresh()


class TableDataFrame:
    df: Union[DataFrame, None]

    def _refresh(self) -> Union[DataFrame, None]:
        return None
    def refresh(self) -> None:
        new_df = self._refresh()
        if new_df is not None:
            self.df = new_df

    def _load_from_db(self, db_service: DbService, n_entries: int) -> Union[DataFrame, None]:
        print("not overwritten")    # TODO: Remove this
        return None

    def load_from_db(self, db_service: DbService, n_entries: int):
        # print("Loading from DB")    # TODO: Remove this
        self.df = self._load_from_db(db_service,n_entries)             # TODO: Adapt this to partly loading from db

    def __init__(self, refresh: (lambda : Union[None, DataFrame]) = (lambda : None), load_from_db: (lambda db_service, n_entries: Union[None, DataFrame]) = (lambda db_service, n_entries: None)):
        super().__init__()
        self._load_from_db = load_from_db
        self._refresh = refresh


main_table_data = {'df_speed': TableDataFrame(load_from_db=load_speed),
                   'df_motorPow': TableDataFrame(refresh=refresh_motorPow),
                   'df_mpptPow0' : TableDataFrame(load_from_db=load_mppt_power0),
                   'df_mpptPow1' : TableDataFrame(load_from_db=load_mppt_power1),
                   'df_mpptPow2' : TableDataFrame(load_from_db=load_mppt_power2),
                   'df_mpptPow3' : TableDataFrame(load_from_db=load_mppt_power3),
                   'df_bat_pack': TableDataFrame(load_from_db=load_bms_pack_data),
                   'df_soc': TableDataFrame(load_from_db=load_bms_soc),
                   'df_cellVolt': TableDataFrame(load_from_db=load_bms_cell_voltage),
                   'df_cellTemp': TableDataFrame(load_from_db=load_bms_cell_temp)}

main_table_layout = [TableDataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
                     TableDataRow(title='Motor Output Power [W]',df_name='df_motorPow', df_col='pow',
                                    numberFormat='3.1f'),
                     TableRow(),
                    # TableDataRow(title='PV Output Power [W]',df_name='df_mpptPow', df_col='p_out', numberFormat='3.1f'),
                    TableDataRow(title='PV String 0 Output Power [W]',df_name='df_mpptPow0', df_col='p_out', numberFormat='3.1f'),
                     TableDataRow(title='PV String 1 Output Power [W]',df_name='df_mpptPow1', df_col='p_out', numberFormat='3.1f'),
                     TableDataRow(title='PV String 2 Output Power [W]',df_name='df_mpptPow2', df_col='p_out', numberFormat='3.1f'),
                     TableDataRow(title='PV String 3 Output Power [W]',df_name='df_mpptPow3', df_col='p_out', numberFormat='3.1f'),
                    TableRow(),
                    TableDataRow(title='Battery Output Power [W]',df_name='df_bat_pack', df_col='battery_power', numberFormat='3.1f'),
                    TableDataRow(title='Battery SOC [%]', df_name='df_soc', df_col='soc_percent', numberFormat='3.1f'),
                    TableDataRow(title='Battery Voltage [V]',df_name='df_bat_pack', df_col='battery_voltage', numberFormat='3.1f'),
                    TableDataRow(title='Battery Output Current [mA]', df_name='df_bat_pack', df_col='battery_current', numberFormat='3.1f'),
                    TableDataRow(title='Battery Minimum Cell Voltage [mV]', df_name='df_cellVolt', df_col='max_cell_voltage', numberFormat='3.1f'),
                    TableDataRow(title='Battery Maximum Cell Voltage [mV]', df_name='df_cellVolt', df_col='min_cell_voltage', numberFormat='3.1f'),
                    TableDataRow(title='Battery Minimum Cell Temperature [°C]', df_name='df_cellTemp', df_col='max_cell_temp', numberFormat='3.1f'),
                    TableDataRow(title='Battery Maximum Cell Temperature [°C]', df_name='df_cellTemp', df_col='min_cell_temp', numberFormat='3.1f')]


def getMinMaxMeanLast(df: Union[DataFrame, None], col: str, numberFormat: str) -> Tuple[str, str, str, str]:
    if df is None:
        return ('', '', '', '')
    if df.empty:
        return ('No Data', 'No Data', 'No Data', 'No Data')
    else:
        return (('{:' + numberFormat + '}').format(df[col].min()),
                ('{:' + numberFormat + '}').format(df[col].max()),
                ('{:' + numberFormat + '}').format(df[col].mean()),
                ('{:' + numberFormat + '}').format(df[col][0]),)

def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed"""
    # Initialize the main table
    main_data = [
        {
            "": 'No Data',
            '{:d}\' Min'.format(timespan_displayed): '',
            '{:d}\' Max'.format(timespan_displayed): 'No Data',
            '{:d}\' Mean'.format(timespan_displayed): 'No Data',
            'Last': 'No Data',
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


# @dash.callback(
#     Output("module-table", "selected_cells"),
#
# )
# def select_row(selected_cells) -> {}:
#     print(selected_cells)
#     print("callback")
#     return selected_cells


# @dash.callback (
#     Output("graphs", "children"),
#     Input("performance-table", "selected_rows")
# )
# def update_graphs(selected_columns):
#     print(selected_columns)
#     print("update called")
#     return html.Div([])


@dash.callback(
    Output("performance-table", "data"),
    Output("module-table", "data"),
    # Output("graph", "children"),
    Output("performance-table", "active_cell"),
    Input("interval-component", "n_intervals"),  # Triggers after the time interval is over
    Input("performance-table", "active_cell"))
def refresh_data(n_intervals: int, active_cell):
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
    db_serv: DbService = DbService()

    # df_speed: DataFrame = load_speed(db_serv, timespan_displayed * 60 * heartbeat_frequency)  # Car Speed
    # df_pv, df_pv_string_0, df_pv_string_1, df_pv_string_2, df_pv_string_3 = load_mppt_power(db_serv,
    #                                                                                         timespan_displayed * 60 * heartbeat_frequency)  # PV String voltage, String current, output power
    # df_soc: DataFrame = load_bms_soc(db_serv, timespan_displayed * 60 * heartbeat_frequency)  # Battery State of Charge
    # df_bat_pack = load_bms_pack_data(db_serv,
    #                                  timespan_displayed * 60 * heartbeat_frequency)  # Battery Voltage, Current and Power
    # df_cellVolt = load_bms_cell_voltage(db_serv,
    #                                     timespan_displayed * 60 * heartbeat_frequency)  # Battery Maximum Cell Voltage, Minimum Cell Voltage
    # df_cellTemp = load_bms_cell_temp(db_serv,
    #                                  timespan_displayed * 60 * heartbeat_frequency)  # Battery Maximum Cell Temperature, Minimum Cell Temperature
    #
    # df_motorPow = DataFrame()  # Motor Power = Power from Solar Array + Power from Battery
    # # df_motorPow['timestamp_dt'] = df_pv['timestamp_dt']
    # df_motorPow['pow'] = df_pv['p_out'] + df_bat_pack['battery_power']
    # motorPow_min, motorPow_max, motorPow_mean, motorPow_last = getMinMaxMeanLast(df_motorPow, 'pow', '3.1f')

    main_table = []

    # Refresh data
    for key in main_table_data:
        main_table_data[key].load_from_db(db_serv, timespan_displayed * 60 * heartbeat_frequency)
        main_table_data[key].refresh()

    # Refresh Layout
    for row in main_table_layout:
        main_table.append(row.refresh())

    # Draw Graphs of which the cells are selected
    # graph_df = None if active_cell == None else test[int(active_cell['row'])][0]
    # y = None if active_cell == None else test[int(active_cell['row'])][1]
    # graph = getGraph(active_cell, graph_df, y)

    module_data = [{'': 'Status'}]
    for m in module_heartbeats:
        module_data[0].update({m: 'active'})

        # {'id': c, 'name': c} for c in module_df.columns]
        # Update data in activity table

    return main_table, module_data, None


def getGraph(active_cell: {}, df: DataFrame, y: str) -> html.Div:
    if active_cell == None:
        return None
    return html.Div(
        children=[dcc.Graph(figure=px.line(df, title='Graph', template='plotly_white', x='timestamp_dt', y=y))])


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
                # row_selectable="multi",
                cell_selectable=True,
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
            html.Div(id="graph"),
            dcc.Interval(
                id="interval-component", interval=RELOAD_INTERVAL, n_intervals=0
            ),
        ]
    )
