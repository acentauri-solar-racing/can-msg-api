import time
import dash
from dash import html, dcc, Input, Output, dash_table
import plotly.express as px

import frontend.styles as styles
from frontend.settings import RELOAD_INTERVAL
from db.load_data import *
from .. import Table
from ..Data_Section import DataSection

dash.register_page(__name__, path="/", title="Overview")

########################################################################################################################
# Activity monitoring
########################################################################################################################

max_idle_time = datetime.timedelta(seconds=2)  # Time allowed until a module is flagged as inactive. In seconds

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

########################################################################################################################
# Layout
########################################################################################################################
graphs = []  # Will be filled in the function 'initialize_data' and updated by 'refresh_page'
dataSection = DataSection(timespan_loaded=datetime.timedelta(minutes=5), max_time_offset=datetime.timedelta(minutes=1))

def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed"""

    # Main Table
    main_table = [
        {
            "": 'No Data',
            dataSection.timespan_loaded.__str__() + ' Min': 'No Data',
            dataSection.timespan_loaded.__str__() + ' Max': 'No Data',
            dataSection.timespan_loaded.__str__() + ' Mean': 'No Data',
            dataSection.timespan_loaded.__str__() + ' Last': 'No Data'
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
        row = dataSection.table_layout[active_cell['row']]
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
    dataSection.refresh_append(db_serv, 100)

    # Refresh table layout
    for row in dataSection.table_layout:
        main_table.append(row.get_row())

        # Draw graphs of selected rows
        if type(row) == Table.DataRow and row.selected:
            df = dataSection.table_data[row.df_name].df
            if df is not None and not df.empty:
                graphs_out.append(dcc.Graph(
                    figure=px.line(df, title=row.title, template='plotly_white', x='timestamp_dt', y=row.df_col)))
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
            if (int(time.time()) - entry.timestamp) < max_idle_time.total_seconds():
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
