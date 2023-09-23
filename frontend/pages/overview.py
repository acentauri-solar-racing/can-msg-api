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
heartbeat_frequency = 16  # Frequency with which the heartbeats are sent [Hz] TODO: Remove this
timespan_displayed = datetime.timedelta(minutes=5)  # Maximum time between the first and last displayed entry

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

main_table_data = {'df_speed': Table.TableDataFrame(append_from_db=append_speed_data, max_timespan=timespan_displayed),
                   'df_motorPow': Table.TableDataFrame(refresh=refresh_motorPow, max_timespan=timespan_displayed),
                   'df_mpptPow': Table.TableDataFrame(refresh=refresh_mpptPow, max_timespan=timespan_displayed),
                   'df_mpptPow0': Table.TableDataFrame(append_from_db=append_mppt_power0_data,
                                                       max_timespan=timespan_displayed),
                   'df_mpptPow1': Table.TableDataFrame(append_from_db=append_mppt_power1_data,
                                                       max_timespan=timespan_displayed),
                   'df_mpptPow2': Table.TableDataFrame(append_from_db=append_mppt_power2_data,
                                                       max_timespan=timespan_displayed),
                   'df_mpptPow3': Table.TableDataFrame(append_from_db=append_mppt_power3_data,
                                                       max_timespan=timespan_displayed),
                   'df_bat_pack': Table.TableDataFrame(append_from_db=append_bms_pack_data,
                                                       max_timespan=timespan_displayed),
                   'df_soc': Table.TableDataFrame(append_from_db=append_bms_soc_data, max_timespan=timespan_displayed),
                   'df_cellVolt': Table.TableDataFrame(append_from_db=append_bms_cell_voltage_data,
                                                       max_timespan=timespan_displayed),
                   'df_cellTemp': Table.TableDataFrame(append_from_db=append_bms_cell_temp_data,
                                                       max_timespan=timespan_displayed)}

main_table_layout = [Table.DataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
                     Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='pow',
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
            timespan_displayed.__str__() + ' Min':'No Data',
            timespan_displayed.__str__() + ' Max': 'No Data',
            timespan_displayed.__str__() + ' Mean': 'No Data',
            timespan_displayed.__str__() + ' Last': 'No Data'
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
        main_table_data[key].append_from_db(db_serv, 200)
        main_table_data[key].refresh()

    # Refresh table layout
    for row in main_table_layout:
        main_table.append(row.refresh_timespan(timespan_displayed))

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
