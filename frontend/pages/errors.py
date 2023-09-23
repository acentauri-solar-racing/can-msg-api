import dash
import pandas as pd

from dash import html, dcc, Input, Output, dash_table

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
from frontend.styles import H1
from frontend.settings import RELOAD_INTERVAL
from db.load_data import append_error_data
from utils.helpers import flatten_tree
import datetime as dt

dash.register_page(__name__, path="/errors", title="Errors")

# List of tracked modules and their heartbeats. Append here.
module_errors = {
    "vcu": VcuError,
    "icu": IcuError,
    "stwheel": StwheelError,
    "logger": LoggerError,
    "fsensors": FsensorsError,
    "dsensors": DsensorsError,
}

_, error_types, _ = flatten_tree(path = "error-tree.yaml")


def initialize_data() -> tuple:
    """Produces the default data to be displayed before the page is refreshed"""
    # Initialize the error status of all modules
    error_data = [{"module":"", "error message": "", "additional data": "", "time":""}]
    return error_data


@dash.callback(
    Output('error-table', 'data'), 
    Input('interval-component', 'n_intervals'),
    )
def refresh_data(n):
    db_serv: DbService = DbService()
    errors = DataFrame()
    error_data = []
    for key, value in module_errors.items():
        df = append_error_data(db_serv, value, 100)
        df.insert(1,'module',key)
        errors = pd.concat([df, errors], ignore_index = True)

    errors.sort_values(by='timestamp', ascending = False, inplace =True)
    #errors = pd.DataFrame.to_dict(errors)
    #print(errors)

    for index, error in errors.iterrows():
        #print(error)
        error_data.append({"module": error["module"], 
                           "error message": next(error_type["message"] for error_type in error_types if error_type["id"] == error["err_code"]),
                           "time": dt.datetime.fromtimestamp(error["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"), 
                           "additional data": ['', error["additional_data"]][error["additional_data"]!=0],})
    return error_data


def layout():
    error_data = initialize_data()
    return html.Div([
        html.Div(id='live-update-errors',
                 children = [
                    html.H1("Errors", style=H1, className="text-center"),
                    dash_table.DataTable(
                        data=error_data,
                        id="error-table",
                        style_as_list_view=True,
                        style_cell={
                            'text-align': 'center',
                        },
                    ),],),
        dcc.Interval(
            id='interval-component',
            interval=RELOAD_INTERVAL,
            n_intervals=0
    )
    ])
