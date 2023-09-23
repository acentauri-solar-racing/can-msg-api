import datetime
from typing import Union

import dash
import plotly.express as px
import time

import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, dash_table

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
heartbeat_frequency = 16  # Frequency with which the heartbeats are sent [Hz] TODO: Remove this
timespan_displayed = datetime.timedelta(minutes=5)

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
                Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='pow',
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

def refresh(self):
    # This method will be added to the Class Table.DataRow, such that it can be called on instances of the class:
    # e.g.: dataRowInstance.refresh(5)

    self.min, self.max, self.mean, self.last = getMinMaxMeanLast(table_data[self.df_name].df, self.df_col,
                                                                 self.numberFormat)
    return {'': self.title,
            timespan_displayed.__str__() + ' Min': self.min,
            timespan_displayed.__str__() + ' Max': self.max,
            timespan_displayed.__str__() + ' Mean': self.mean,
            timespan_displayed.__str__() + ' Last': self.last}


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
    Output("table", "data"),
    Input("submit_button", "n_clicks"),
    [State("date", "date"),
        State("start_time", "value"),
     State("end_time", "value")]
)
def update_displayed_data(n_clicks, date, start_time, end_time):
    if (n_clicks is None or date is None or start_time is None or end_time is None):  # Ignore callback on initialization or if some information is missing
        table, _ = initialize_data()
        if n_clicks is not None:    # Do not print anything on initialization
            print("Please specify date, start time and end time")
        return table

    # Combine date out of date input and time out of time . Ignore Microseconds
    timestamp_start = date + start_time[10:18]
    timestamp_end = date + end_time[10:18]

    # convert into datetime objects
    format_string = "%Y-%m-%dT%H:%M:%S"
    timestamp_start = datetime.datetime.strptime(timestamp_start, format_string)
    timestamp_end = datetime.datetime.strptime(timestamp_end, format_string)


    # update timespan variable
    global timespan_displayed
    timespan_displayed = timestamp_end - timestamp_start

    db_serv: DbService = DbService()
    table = []

    # Refresh table data
    for key in table_data:
        table_data[key].load_from_db(db_serv, timestamp_start, timestamp_end)
        table_data[key].refresh()

    # Refresh table layout
    for row in table_layout:
        table.append(row.refresh())

    # delete shown graphs
    global graphs
    graphs = {}
    update_selected_rows(None)  # update graph view

    return table


@dash.callback(
    [Output("graphs_analyzer", "children"),
     Output("table", "active_cell")],
    Input("table", "active_cell")
)
def update_selected_rows(active_cell: {}):
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
                                       x='timestamp_dt', y=row.df_col))
                else:
                    graphs[row.title] = [html.Br(), html.Br(),
                                         html.H3('No Data available for "%s"' % row.title, style=styles.H3)]

    graphs_list = []
    for graph in graphs.values():
        graphs_list.append(graph)


    return graphs_list, None  # Reset the active cell of the table


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
            dcc.DatePickerSingle(id="date"),
            dmc.TimeInput(id="start_time", label="Start Time", format="24", withSeconds=True, value=datetime.datetime.now()),
            dmc.TimeInput(id="end_time", label="End Time", format="24", withSeconds=True, value=datetime.datetime.now()),
            dmc.Button("Submit", id="submit_button"),
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
