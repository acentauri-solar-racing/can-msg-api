import dash
import plotly.express as px

import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, dash_table, ctx

import frontend.styles as styles
from frontend.settings import RELOAD_INTERVAL
from db.load_data import *
from .. import Table
from ..Data_Section import DataSection

dash.register_page(__name__, path="/analyzer", title="Analyzer")

########################################################################################################################
# Global Variables
########################################################################################################################

time_loaded_min: datetime.datetime  # Minimum displayed time in the graphs. Updated by the function 'reload_table_data'
time_loaded_max: datetime.datetime  # Maximum displayed time in the graphs. Updated by the function 'reload_table_data'

########################################################################################################################
# Layout
########################################################################################################################

dataSection = DataSection(timespan_loaded=datetime.timedelta(minutes=0), max_time_offset=datetime.timedelta(seconds=30))
graphs = {}  # Will be filled in the function 'initialize_data'

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
     State("end_time", "value"),
     State("density_slider", "value")],
    config_prevent_initial_callbacks=True
)
def update_displayed_data(n_clicks: int, active_cell: {}, table_data: [], date: str, start_time: str, end_time: str,
                          loading_interval: int):
    table = []
    graph_list = []

    if (ctx.triggered_id == "submit_button"):
        table, graph_list = reload_table_data(date, start_time, end_time, int(10 ** loading_interval))   # Logarithmic slider for loading interval
    elif (ctx.triggered_id == "table"):
        graph_list, active_cell = reload_graphs(active_cell)
        table = table_data

    return table, graph_list, active_cell  # Reset the active cell of the table


def reload_table_data(date: str, start_time: str, end_time: str, loading_interval: int):
    # Combine date out of date input and time out of time . Ignore Microseconds
    start_time = date[:10] + start_time[10:19]
    end_time = date[0:10] + end_time[10:19]

    # Get new timespan
    global time_loaded_min, time_loaded_max
    format_string = "%Y-%m-%dT%H:%M:%S"
    time_loaded_min = datetime.datetime.strptime(start_time, format_string)
    time_loaded_max = datetime.datetime.strptime(end_time, format_string)
    dataSection.timespan_loaded = time_loaded_max - time_loaded_min

    # get rid of timezone shift -> get timestamp as if the date was at UTC+0
    diff = time_loaded_min - time_loaded_min.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    timestamp_start = time_loaded_min + diff
    timestamp_end = time_loaded_max + diff

    db_serv: DbService = DbService()
    table = []

    # Refresh table data
    dataSection.refresh(db_serv, timestamp_start, timestamp_end, loading_interval)

    # Refresh table layout
    for row in dataSection.table_layout:
        table.append(row.get_row())
        row.selected = False  # reset selected view

    # delete shown graphs
    global graphs
    graphs = {}

    return table, None


def reload_graphs(active_cell: {}):
    # Toggles the 'selected' variable of a given Table.DataRow, if the user selected it. 'Consumes' the reference to the
    # active cell, in the sense that it is set to None
    if active_cell is not None:
        row = dataSection.table_layout[active_cell['row']]

        if type(row) == Table.DataRow:
            if row.selected:
                row.selected = False
                graphs.pop(row.title)
            else:
                row.selected = True
                df = dataSection.table_data[row.df_name].df
                if df is not None and not df.empty:
                    graphs[row.title] = dcc.Graph(
                        figure=px.line(df, title=row.title, template='plotly_white',
                                       x='timestamp_dt', y=row.df_col,
                                       range_x=[time_loaded_min, time_loaded_max]))
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
                            dbc.Col(dcc.DatePickerSingle(id="date", date=datetime.datetime.now()), width="auto",
                                    align="center"),
                            dbc.Col(html.P("Start Time"), width="auto", align="center"),
                            dbc.Col(dmc.TimeInput(id="start_time", format="24", withSeconds=True,
                                                  value=datetime.datetime.now()), width="auto", align="center"),
                            dbc.Col(html.P("End Time"), width="auto", align="center"),
                            dbc.Col(dmc.TimeInput(id="end_time", format="24", withSeconds=True,
                                                  value=datetime.datetime.now()), width="auto", align="center"),
                            dbc.Col(html.P("Loading Interval"), width="auto", align="center"),
                            dcc.Slider(0, 4, 0.01, id='density_slider',
                                       marks={i: '{}'.format(10 ** i) for i in range(5)}, value=0),
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
