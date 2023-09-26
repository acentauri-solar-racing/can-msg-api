import datetime
from typing import Union, List

import dash
import plotly.express as px
import time

import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, dash_table, ctx

from db.db_service import DbService
from pandas import DataFrame
import frontend.styles as styles
from frontend.settings import RELOAD_INTERVAL
from db.load_data import *
from datetime import *
import datetime
from .. import Table

dash.register_page(__name__, path="/analyzer", title="Analyzer")

########################################################################################################################
# Global Variables
########################################################################################################################

max_idle_time = 2  # Time allowed until a module is flagged as inactive. In seconds
max_time_offset = 2  # Time offset between two measurements such that they are considered simultaneously. This is used
# for summing the MPPT-measurements together.
timespan_loaded = datetime.timedelta(minutes=5)
timespan_loaded_min = datetime.datetime.now()
timespan_loaded_max = datetime.datetime.now()

########################################################################################################################
# Data and Layout
########################################################################################################################
# List of tracked modules and their heartbeats. Append / update here.
module_heartbeats = {
    "vcu": VcuHeartbeat,
    "icu": IcuHeartbeat,
    "mppt0": MpptStatus0,
    "mppt1": MpptStatus1,
    "mppt2": MpptStatus2,
    "mppt3": MpptStatus3,
    "bms": BmsHeartbeat,
    "stwheel": StwheelHeartbeat,
    "tele": TeleSolarHeartbeat,
    "sensors": DsensorsHeartbeat,
    "logger": LoggerHeartbeat,
}

table_data = {'df_speed': Table.TableDataFrame(load_from_db=load_speed_data),
              'df_motorPow': Table.TableDataFrame(refresh=refresh_motorPow),
              'df_mpptPow': Table.TableDataFrame(refresh=refresh_mpptPow),
              'df_mpptPow0': Table.TableDataFrame(load_from_db=load_mppt_power0_data),
              'df_mpptPow1': Table.TableDataFrame(load_from_db=load_mppt_power1_data),
              'df_mpptPow2': Table.TableDataFrame(load_from_db=load_mppt_power2_data),
              'df_mpptPow3': Table.TableDataFrame(load_from_db=load_mppt_power3_data),
              'df_bat_pack': Table.TableDataFrame(load_from_db=load_bms_pack_data),
              'df_soc': Table.TableDataFrame(load_from_db=load_bms_soc_data),
              'df_cellVolt': Table.TableDataFrame(load_from_db=load_bms_cell_voltage_data),
              'df_cellTemp': Table.TableDataFrame(load_from_db=load_bms_cell_temp_data)}

table_layout = [Table.DataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
                Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='p_out',
                              numberFormat='3.1f'),
                Table.Row(),
                Table.DataRow(title='PV Output Power [W]', df_name='df_mpptPow', df_col='p_out', numberFormat='3.1f'),
                Table.DataRow(title='PV String 0 Output Power [W]', df_name='df_mpptPow0', df_col='p_out',
                              numberFormat='3.1f'),
                Table.DataRow(title='PV String 1 Output Power [W]', df_name='df_mpptPow1', df_col='p_out',
                              numberFormat='3.1f'),
                Table.DataRow(title='PV String 2 Output Power [W]', df_name='df_mpptPow2', df_col='p_out',
                              numberFormat='3.1f'),
                Table.DataRow(title='PV String 3 Output Power [W]', df_name='df_mpptPow3', df_col='p_out',
                              numberFormat='3.1f'),
                Table.Row(),
                Table.DataRow(title='Battery Output Power [W]', df_name='df_bat_pack', df_col='battery_power',
                              numberFormat='3.1f'),
                Table.DataRow(title='Battery SOC [%]', df_name='df_soc', df_col='soc_percent',
                              numberFormat='3.1f'),
                Table.DataRow(title='Battery Voltage [V]', df_name='df_bat_pack', df_col='battery_voltage',
                              numberFormat='3.1f'),
                Table.DataRow(title='Battery Output Current [mA]', df_name='df_bat_pack', df_col='battery_current',
                              numberFormat='3.1f'),
                Table.DataRow(title='Battery Minimum Cell Voltage [mV]', df_name='df_cellVolt',
                              df_col='min_cell_voltage', numberFormat='3.1f'),
                Table.DataRow(title='Battery Maximum Cell Voltage [mV]', df_name='df_cellVolt',
                              df_col='max_cell_voltage', numberFormat='3.1f'),
                Table.DataRow(title='Battery Minimum Cell Temperature [°C]', df_name='df_cellTemp',
                              df_col='min_cell_temp', numberFormat='3.1f'),
                Table.DataRow(title='Battery Maximum Cell Temperature [°C]', df_name='df_cellTemp',
                              df_col='max_cell_temp', numberFormat='3.1f')]

graphs = {}  # Will be filled in the function 'initialize_data'


########################################################################################################################
# Helper Functions
########################################################################################################################

def get_nearest_index(df: DataFrame, current_idx: int, target_timestamp: float) -> int:
    idx_max = len(df.index)
    current_timestamp = df['timestamp'].values[current_idx]

    # Move to next timestamp, if it is closer
    while current_timestamp > target_timestamp and current_idx < idx_max - 1:

        new_timestamp = df['timestamp'].values[current_idx + 1]

        if abs(new_timestamp - target_timestamp) < (current_timestamp - target_timestamp):
            current_idx += 1
            current_timestamp = new_timestamp
        else:
            break

    return current_idx

def refresh_motorPow() -> Union[DataFrame, None]:
    # Calculate the total motor output power, based on the output power of battery and pv.
    # This function needs the elements to be chronologically ordered with the most recent entry at index 0

    df_batPower = table_data['df_bat_pack'].df
    df_mpptPow = table_data['df_mpptPow'].df

    if df_batPower is None or df_batPower.empty or df_mpptPow is None or df_mpptPow.empty:
        print("Couldn't load motor output power")
        return table_data['df_motorPow'].df

    df_motorPow = pd.DataFrame(columns=['timestamp', 'p_out'])
    df_motorPow['timestamp'] = df_batPower['timestamp']

    bat_index = mppt_index = 0

    for i in range(len(df_motorPow.index)):
        timestamp = df_motorPow['timestamp'][i]

        # get index of the nearest timestamp to the one in the output dataframe
        bat_index = get_nearest_index(df_batPower,bat_index,timestamp)
        mppt_index = get_nearest_index(df_mpptPow,mppt_index,timestamp)

        timestamp_bat = df_batPower['timestamp'][bat_index]
        timestamp_mppt = df_mpptPow['timestamp'][mppt_index]

        # Calculate motor power if timestamps are close enough together
        if abs(timestamp - timestamp_bat) < max_time_offset and abs(timestamp - timestamp_mppt) < max_time_offset:
            df_motorPow.at[i, 'p_out'] = df_batPower['battery_power'][bat_index] + df_mpptPow['p_out'][mppt_index]


    return preprocess_generic(df_motorPow)


def refresh_mpptPow() -> Union[DataFrame, None]:
    # Calculate the total power of the MPPTs, based on the individual measurements of the MPPTs
    # This function needs the elements to be chronologically ordered with the most recent entry at index 0

    df_mppt0 = table_data['df_mpptPow0'].df
    df_mppt1 = table_data['df_mpptPow1'].df
    df_mppt2 = table_data['df_mpptPow2'].df
    df_mppt3 = table_data['df_mpptPow3'].df

    if df_mppt0 is None or df_mppt0.empty or df_mppt1 is None or df_mppt1.empty or df_mppt2 is None or df_mppt2.empty or df_mppt3 is None or df_mppt3.empty:
        print("Couldn't load total power of MPPTs")
        return table_data['df_mpptPow'].df

    df_mpptPow = pd.DataFrame(columns=['timestamp', 'p_out'])
    df_mpptPow['timestamp'] = df_mppt0['timestamp']

    mppt0_index = mppt1_index = mppt2_index = mppt3_index =0

    for i in range(len(df_mpptPow.index)):
        timestamp = df_mpptPow['timestamp'].values[i]

        # get index of the nearest timestamp to the one in the output dataframe
        mppt0_index = get_nearest_index(df_mppt0, mppt0_index, timestamp)
        mppt1_index = get_nearest_index(df_mppt1, mppt1_index, timestamp)
        mppt2_index = get_nearest_index(df_mppt2, mppt2_index, timestamp)
        mppt3_index = get_nearest_index(df_mppt3, mppt3_index, timestamp)

        timestamp_mppt0 = df_mppt0['timestamp'].values[mppt0_index]
        timestamp_mppt1 = df_mppt1['timestamp'].values[mppt1_index]
        timestamp_mppt2 = df_mppt2['timestamp'].values[mppt2_index]
        timestamp_mppt3 = df_mppt3['timestamp'].values[mppt3_index]

        # Calculate Power, if timestamps are close enough together
        if abs(timestamp_mppt0 - timestamp) < max_time_offset and abs(
                timestamp_mppt1 - timestamp) < max_time_offset and abs(
            timestamp_mppt2 - timestamp) < max_time_offset and abs(timestamp_mppt3 - timestamp) < max_time_offset:
            df_mpptPow.at[i, 'p_out'] = df_mppt0['p_out'].values[mppt0_index] + df_mppt1['p_out'].values[mppt1_index] + \
                                        df_mppt2['p_out'].values[mppt2_index] + df_mppt3['p_out'].values[mppt3_index]

    return preprocess_generic(df_mpptPow)


def refresh(self):
    # This method will be added to the Class Table.DataRow, such that it can be called on instances of the class:
    # e.g.: dataRowInstance.refresh(5)

    self.min, self.max, self.mean, self.last = getMinMaxMeanLast(table_data[self.df_name].df, self.df_col,
                                                                 self.numberFormat)
    return {'': self.title,
            timespan_loaded.__str__() + ' Min': self.min,
            timespan_loaded.__str__() + ' Max': self.max,
            timespan_loaded.__str__() + ' Mean': self.mean,
            timespan_loaded.__str__() + ' Last': self.last}


setattr(Table.DataRow, "refresh", refresh)  # Add method to the class DataRow


def getMinMaxMeanLast(df: Union[DataFrame, None], col: str, numberFormat: str) -> Tuple[str, str, str, str]:
    # Returns the minimum, maximum, mean and last entry of a given column in a Pandas.DataFrame as a string
    if df is None:
        return ('', '', '', '')
    if df.empty:
        return 'No Data', 'No Data', 'No Data', 'No Data'
    else:
        return (('{:' + numberFormat + '}').format(df[col].min()),
                ('{:' + numberFormat + '}').format(df[col].max()),
                ('{:' + numberFormat + '}').format(df[col].mean()),
                ('{:' + numberFormat + '}').format(df[col][0]))


########################################################################################################################
# Layout
########################################################################################################################
def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed"""

    # Main Table
    main_table = [
        {
            "": 'No Data',
            ' Min': 'No Data',
            ' Max': 'No Data',
            ' Mean': 'No Data',
            ' Last': 'No Data'
        },
    ]

    return main_table, None


@dash.callback(
    Output("submit_button", "disabled"),
    [Input("date", "date"),
     Input("start_time", "value"),
     Input("end_time", "value")]
)
def sanity_check(date, start_time, end_time):
    # Check whether date and time input are correct
    return (date is None) or (start_time is None) or (end_time is None) or (start_time > end_time)


@dash.callback(
    [Output("table", "data"),
     Output("graphs_analyzer", "children"),
     Output("table", "active_cell")],
    [Input("submit_button", "n_clicks"),
     Input("table", "active_cell")],
    [State("table", "data"),
     State("date", "date"),
     State("start_time", "value"),
     State("end_time", "value")],
    config_prevent_initial_callbacks=True
)
def update_displayed_data(n_clicks: int, active_cell: {}, table_data: [], date: str, start_time: str, end_time: str):
    table = []
    graph_list = []

    if (ctx.triggered_id == "submit_button"):
        table, graph_list = reload_table_data(date, start_time, end_time)
    elif (ctx.triggered_id == "table"):
        graph_list, active_cell = reload_graphs(active_cell)
        table = table_data

    return table, graph_list, active_cell  # Reset the active cell of the table


def reload_table_data(date, start_time, end_time):
    # Combine date out of date input and time out of time . Ignore Microseconds
    start_time = date[:10] + start_time[10:19]
    end_time = date[0:10] + end_time[10:19]

    # convert into datetime objects and update global variables
    global timespan_loaded, timespan_loaded_min, timespan_loaded_max
    format_string = "%Y-%m-%dT%H:%M:%S"
    timespan_loaded_min = datetime.datetime.strptime(start_time, format_string)
    timespan_loaded_max = datetime.datetime.strptime(end_time, format_string)
    timespan_loaded = timespan_loaded_max - timespan_loaded_min

    # get rid of timezone shift -> get timestamp as if the date was at UTC+0
    diff = timespan_loaded_min - timespan_loaded_min.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    timestamp_start = timespan_loaded_min + diff
    timestamp_end = timespan_loaded_max + diff

    db_serv: DbService = DbService()
    table = []

    # Refresh table data
    for key in table_data:
        table_data[key].load_from_db(db_serv, timestamp_start, timestamp_end)

    # Refresh table data that depends on different table data
    table_data['df_mpptPow'].df = refresh_mpptPow()
    table_data['df_motorPow'].df = refresh_motorPow()

    # Refresh table layout
    for row in table_layout:
        table.append(row.refresh())
        row.selected = False  # reset selected view

    # delete shown graphs
    global graphs
    graphs = {}

    return table, None


def reload_graphs(active_cell: {}):
    # Toggles the 'selected' variable of a given Table.DataRow, if the user selected it. 'Consumes' the reference to the
    # active cell, in the sense that it is set to None
    if active_cell is not None:
        row = table_layout[active_cell['row']]

        if type(row) == Table.DataRow:
            if row.selected:
                row.selected = False
                graphs.pop(row.title)
            else:
                row.selected = True
                df = table_data[row.df_name].df
                if df is not None and not df.empty:
                    graphs[row.title] = dcc.Graph(
                        figure=px.line(df, title=row.title, template='plotly_white',
                                       x='timestamp_dt', y=row.df_col,
                                       range_x=[timespan_loaded_min, timespan_loaded_max]))
                else:
                    graphs[row.title] = [html.Br(), html.Br(),
                                         html.H3('No Data available for "%s"' % row.title, style=styles.H3)]

    graphs_list = []
    for graph in graphs.values():

        # Flatten List
        if type(graph) is list:
            for item in graph:
                graphs_list.append(item)
        else:
            graphs_list.append(graph)

    return graphs_list, None


def layout() -> html.Div:
    """Defines the layout of the page and returns it as a div

    Returns:
        html.Div: Div with the page layout
    """
    table_data, graphs_analyzer = initialize_data()

    return html.Div(
        children=[
            html.P(id="placeholder_id"),
            html.H1('Analyzer', style=styles.H1, className='text-center'),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(html.P("Date"), width="auto", align="center"),
                            dbc.Col(dcc.DatePickerSingle(id="date", date=datetime.datetime.now()),width="auto", align="center"),
                            dbc.Col(html.P("Start Time"), width="auto", align="center"),
                            dbc.Col(dmc.TimeInput(id="start_time", format="24", withSeconds=True,
                                              value=datetime.datetime.now()), width="auto", align="center"),
                            dbc.Col(html.P("End Time"), width="auto", align="center"),
                            dbc.Col(dmc.TimeInput(id="end_time", format="24", withSeconds=True,
                                              value=datetime.datetime.now()), width="auto", align="center"),
                            dbc.Col(dmc.Button("Submit", id="submit_button"), width="auto", align="center"),
                        ],
                        align="center"
                    ),
                ],
                fluid=True
            ),
            html.Br(),
            dash_table.DataTable(
                id='table',
                data=table_data,
                # row_selectable="multi",
                cell_selectable=True,
                style_table=styles.TABLE,
                style_cell=styles.TABLE_CELL,
                style_cell_conditional=styles.TABLE_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.TABLE_DATA_CONDITIONAL),
            html.Br(),
            html.Br(),
            html.Div(id='graphs_analyzer', children=graphs_analyzer),
            dcc.Interval(
                id='interval-component', interval=RELOAD_INTERVAL, n_intervals=0
            ),
        ]
    )
