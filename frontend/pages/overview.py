import datetime
from typing import Union

import dash
import plotly.express as px
import time

import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, dash_table

from db.db_service import DbService
from pandas import DataFrame
import frontend.styles as styles
from frontend.settings import RELOAD_INTERVAL
from db.load_data import *
import datetime as dt
from .. import Table

dash.register_page(__name__, path="/", title="Overview")

########################################################################################################################
# Global Variables
########################################################################################################################

max_idle_time = 2  # Time allowed until a module is flagged as inactive. In seconds
max_time_offset = 2  # Time offset between two measurements such that they are considered simultaneously. This is used
# for summing the MPPT-measurements together.
timespan_loaded = datetime.timedelta(minutes=5)  # Maximum time between the first and last displayed entry

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

main_table_data = {'df_speed': Table.TableDataFrame(append_from_db=append_speed_data, max_timespan=timespan_loaded),
                   'df_motorPow': Table.TableDataFrame(refresh=refresh_motorPow, max_timespan=timespan_loaded),
                   'df_mpptPow': Table.TableDataFrame(max_timespan=timespan_loaded),
                   'df_mpptPow0': Table.TableDataFrame(append_from_db=append_mppt_power0_data,
                                                       max_timespan=timespan_loaded),
                   'df_mpptPow1': Table.TableDataFrame(append_from_db=append_mppt_power1_data,
                                                       max_timespan=timespan_loaded),
                   'df_mpptPow2': Table.TableDataFrame(append_from_db=append_mppt_power2_data,
                                                       max_timespan=timespan_loaded),
                   'df_mpptPow3': Table.TableDataFrame(append_from_db=append_mppt_power3_data,
                                                       max_timespan=timespan_loaded),
                   'df_bat_pack': Table.TableDataFrame(append_from_db=append_bms_pack_data,
                                                       max_timespan=timespan_loaded),
                   'df_soc': Table.TableDataFrame(append_from_db=append_bms_soc_data, max_timespan=timespan_loaded),
                   'df_cellVolt': Table.TableDataFrame(append_from_db=append_bms_cell_voltage_data,
                                                       max_timespan=timespan_loaded),
                   'df_cellTemp': Table.TableDataFrame(append_from_db=append_bms_cell_temp_data,
                                                       max_timespan=timespan_loaded)}

main_table_layout = [Table.DataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
                     Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='p_out',
                                   numberFormat='3.1f'),
                     Table.Row(),
                     Table.DataRow(title='PV Output Power [W]', df_name='df_mpptPow', df_col='p_out',
                                   numberFormat='3.1f'),
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

graphs = []  # Will be filled in the function 'initialize_data'


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

    df_batPower = main_table_data['df_bat_pack'].df
    df_mpptPow = main_table_data['df_mpptPow'].df

    if df_batPower is None or df_batPower.empty or df_mpptPow is None or df_mpptPow.empty:
        print("Couldn't load motor output power")
        return main_table_data['df_motorPow'].df

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

    df_mppt0 = main_table_data['df_mpptPow0'].df
    df_mppt1 = main_table_data['df_mpptPow1'].df
    df_mppt2 = main_table_data['df_mpptPow2'].df
    df_mppt3 = main_table_data['df_mpptPow3'].df

    if df_mppt0 is None or df_mppt0.empty or df_mppt1 is None or df_mppt1.empty or df_mppt2 is None or df_mppt2.empty or df_mppt3 is None or df_mppt3.empty:
        print("Couldn't load total power of MPPTs")
        return main_table_data['df_mpptPow'].df

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


def refresh_timespan(self, timespan_displayed: datetime.timedelta):
    # This method will be added to the Class Table.DataRow, such that it can be called on instances of the class:
    # e.g.: dataRowInstance.refresh(5)

    self.min, self.max, self.mean, self.last = getMinMaxMeanLast(main_table_data[self.df_name].df, self.df_col,
                                                                 self.numberFormat)
    return {'': self.title,
            timespan_displayed.__str__() + ' Min': self.min,
            timespan_displayed.__str__() + ' Max': self.max,
            timespan_displayed.__str__() + ' Mean': self.mean,
            timespan_displayed.__str__() + ' Last': self.last}


setattr(Table.DataRow, "refresh_timespan", refresh_timespan)  # Add method to the class DataRow


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
            timespan_loaded.__str__() + ' Min': 'No Data',
            timespan_loaded.__str__() + ' Max': 'No Data',
            timespan_loaded.__str__() + ' Mean': 'No Data',
            timespan_loaded.__str__() + ' Last': 'No Data'
        },
    ]

    # Module Table
    module_table = [{'': 'Status'}]
    for m in module_heartbeats:
        module_table[0].update({m: 'No Data'})

    return main_table, module_table, None


@dash.callback(
    Output("main_table", "active_cell"),
    Input("main_table", "active_cell")
)
def update_selected_rows(active_cell: {}):
    # Toggles the 'selected' variable of a given Table.DataRow, if the user selected it. 'Consumes' the reference to the
    # active cell, in the sense that it is set to None
    if active_cell is not None:
        row = main_table_layout[active_cell['row']]
        if type(row) == Table.DataRow:
            row.selected ^= True  # Toggle row Selected

    refresh_page(0)  # Refresh view

    return None  # Reset the active cell


@dash.callback(
    Output('main_table', 'data'),
    Output('module-table', 'data'),
    Output('graphs', 'children'),
    Input('interval-component', 'n_intervals'))  # Triggers after the time interval is over
def refresh_page(n_intervals: int):
    """Refreshes the data in the tables & graph
    Args:
        n (int): unused

    Returns:
        tuple: Updated data
    """

    db_serv: DbService = DbService()
    main_table = []
    graphs_out = []

    # Refresh table data
    for key in main_table_data:
        main_table_data[key].append_from_db(db_serv, 100)

    # Refresh table data that depends on different table data
    main_table_data['df_mpptPow'].df = refresh_mpptPow()
    main_table_data['df_motorPow'].df = refresh_motorPow()

    # Refresh table layout
    for row in main_table_layout:
        main_table.append(row.refresh_timespan(timespan_loaded))

        # Draw graphs of selected rows
        if type(row) == Table.DataRow and row.selected:
            df = main_table_data[row.df_name].df
            if df is not None and not df.empty:
                graphs_out.append(dcc.Graph(
                    figure=px.line(main_table_data[row.df_name].df, title=row.title, template='plotly_white',
                                   x='timestamp_dt', y=row.df_col)))
            else:
                graphs_out.append(html.Br())
                graphs_out.append(html.Br())
                graphs_out.append(html.H3('No Data available for "%s"' % row.title, style=styles.H3))

    # Refresh module table
    module_table = [{'': 'Status'}]
    for m in module_heartbeats:
        module_table[0].update({m: 'n/a'})

        entry = db_serv.latest(module_heartbeats[m])

        if entry is not None:
            # check if the last data entry is more than max_idle_time ago
            if (int(time.time()) - entry.timestamp) < max_idle_time:
                module_table[0].update({m: 'ACTIVE'})

    return main_table, module_table, graphs_out


def layout() -> html.Div:
    """Defines the layout of the page and returns it as a div

    Returns:
        html.Div: Div with the page layout
    """
    main_data, module_data, graphs = initialize_data()

    return html.Div(
        children=[
            html.H1('Overview', style=styles.H1, className='text-center'),
            dash_table.DataTable(
                id='main_table',
                data=main_data,
                # row_selectable="multi",
                cell_selectable=True,
                style_table=styles.TABLE,
                style_cell=styles.TABLE_CELL,
                style_cell_conditional=styles.TABLE_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.TABLE_DATA_CONDITIONAL),
            html.Br(),
            html.Br(),
            dash_table.DataTable(
                id='module-table',
                data=module_data,
                cell_selectable=False,
                style_cell=styles.TABLE_CELL_MODULES,
                style_cell_conditional=styles.TABLE_CELL_CONDITIONAL_MODULES,
                style_as_list_view=True,
                style_data_conditional=styles.TABLE_DATA_CONDITIONAL),
            html.Div(id='graphs', children=graphs),
            dcc.Interval(
                id='interval-component', interval=RELOAD_INTERVAL, n_intervals=0
            ),
        ]
    )
