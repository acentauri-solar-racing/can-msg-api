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
timespan_displayed = 5  # Time span that is displayed in the graphs. In minutes

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

main_table_data = {'df_speed': Table.TableDataFrame(load_from_db=load_speed),
                   'df_motorPow': Table.TableDataFrame(refresh=refresh_motorPow),
                   'df_mpptPow0': Table.TableDataFrame(load_from_db=load_mppt_power0),
                   'df_mpptPow1': Table.TableDataFrame(load_from_db=load_mppt_power1),
                   'df_mpptPow2': Table.TableDataFrame(load_from_db=load_mppt_power2),
                   'df_mpptPow3': Table.TableDataFrame(load_from_db=load_mppt_power3),
                   'df_bat_pack': Table.TableDataFrame(load_from_db=load_bms_pack_data),
                   'df_soc': Table.TableDataFrame(load_from_db=load_bms_soc),
                   'df_cellVolt': Table.TableDataFrame(load_from_db=load_bms_cell_voltage),
                   'df_cellTemp': Table.TableDataFrame(load_from_db=load_bms_cell_temp)}

main_table_layout = [Table.DataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
                     Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='pow',
                                   numberFormat='3.1f'),
                     Table.Row(),
                     # Table.DataRow(title='PV Output Power [W]',df_name='df_mpptPow', df_col='p_out', numberFormat='3.1f'),
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

def refresh(self, timespan_displayed: int):
    # This method will be added to the Class Table.DataRow, such that it can be called on instances of the class:
    # e.g.: dataRowInstance.refresh(5)
    self.min, self.max, self.mean, self.last = getMinMaxMeanLast(main_table_data[self.df_name].df, self.df_col,
                                                                 self.numberFormat)
    return {'': self.title,
            # '{:d}\' Min'.format(timespan_displayed): self.min,
            # '{:d}\' Max'.format(timespan_displayed): self.max,
            # '{:d}\' Mean'.format(timespan_displayed): self.mean,
            'Min': self.min,
            'Max': self.max,
            'Mean': self.mean,
            'Last': self.last}


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
            # '{:d}\' Min'.format(timespan_displayed): 'No Data',
            # '{:d}\' Max'.format(timespan_displayed): 'No Data',
            # '{:d}\' Mean'.format(timespan_displayed): 'No Data',
            'Min': 'No Data',
            'Max': 'No Data',
            'Mean': 'No Data',
            'Last': 'No Data',
        },
    ]

    # Module Table
    module_table = [{'': 'Status'}]
    for m in module_heartbeats:
        module_table[0].update({m: 'No Data'})

    # Graphs Div
    for row in main_table_layout:
        if row is Table.DataRow:
            graphs.append(dcc.Graph(
                figure=px.line(main_table_data[row.df_name], title=row.title, template='plotly_white', x='timestamp_dt',
                               y=row.df_col)))

    return main_table, module_table, graphs


@dash.callback(
    Output("placeholder_id", "id"),
    [Input("submit_button", "n_clicks"),
     Input("start_time", "timePlaceholder")],
)
def update_time_frame(n_clicks, timePlaceholder):
    if(n_clicks is not None):   # Ignore callback on initialization
        print("clicks: ", n_clicks)
        db_serv: DbService = DbService()
        print("Minutes Label: ", timePlaceholder)
        db_serv.queryTime(datetime.datetime.now(), datetime.datetime.now())

    return "placeholder_id"


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
        main_table_data[key].load_from_db(db_serv)
        main_table_data[key].refresh()

    # Refresh table layout
    for row in main_table_layout:
        main_table.append(row.refresh(timespan_displayed))

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
            html.P(id="placeholder_id"),
            html.H1('Overview', style=styles.H1, className='text-center'),
            dmc.SegmentedControl(id='live_slider', value='live',
                                 data=[{'value': 'live', 'label': 'live'}, {'value': 'paused', 'label': 'paused'}]),
            dmc.TimeInput(id="start_time", label="Start Time", format="12", value=datetime.datetime.now()),
            dmc.TimeInput(id="end_time", label="End Time", format="12", value=datetime.datetime.now()),
            dmc.Button("Submit", id="submit_button"),
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
