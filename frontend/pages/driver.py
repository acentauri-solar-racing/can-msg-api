import datetime

import dash
from dash import html, dcc, dash_table, Output, Input
from pandas import DataFrame

from db.db_service import DbService
from db.load_data import append_driverResponse
from frontend import styles
from frontend.settings import RELOAD_INTERVAL

dash.register_page(__name__, path="/driver", title="Driver")


# Global variable
timestamp_lastResponse = 0
button_yes_prev = False
button_no_prev = False
button_unclear_prev = False
table_data = [{'Timestamp': '', 'Response': '', 'Delta': ''}]


@dash.callback(
    Output('driver_table', 'data'),
    Input('interval-component', 'n_intervals'))
def refresh(n_intervals: int) -> []:

    global timestamp_lastResponse, table_data, button_yes_prev, button_no_prev, button_unclear_prev
    db_service = DbService()

    # Querry driver responsees
    df = append_driverResponse(db_service, 100)

    # Extract new entries
    new_entries : DataFrame = df.loc[df['timestamp'] > timestamp_lastResponse]

    # Append entries to output list
    for idx, row in new_entries.iterrows():
        if row['button_yes'] and not button_yes_prev:
            table_data.insert(0,{'Timestamp': row['timestamp_dt'].tz_convert('Australia/Darwin').strftime('%y/%m/%d, %H:%M:%S'), 'Response': 'YES', 'Delta': ''})
            button_yes_prev = True
        elif not row['button_yes']:
            button_yes_prev = False
        if row['button_no'] and not button_no_prev:
            table_data.insert(0,{'Timestamp': row['timestamp_dt'].tz_convert('Australia/Darwin').strftime('%y/%m/%d, %H:%M:%S'), 'Response': 'NO', 'Delta': ''})
            button_no_prev  = True
        elif not row['button_no']:
            button_no_prev = False
        if row['button_unclear'] and not button_unclear_prev:
            table_data.insert(0,{'Timestamp': row['timestamp_dt'].tz_convert('Australia/Darwin').strftime('%y/%m/%d, %H:%M:%S'), 'Response': 'UNCLEAR', 'Delta': ''})
            button_unclear_prev  = True
        elif not row['button_unclear']:
            button_unclear_prev = False

    # Update Delta Time
    for row in table_data:
        if row['Timestamp'] != '':
            row['Delta'] = str((datetime.datetime.now() - datetime.datetime.strptime(row['Timestamp'],'%y/%m/%d, %H:%M:%S')))

    # the latest timestamp is at position 0
    timestamp_lastResponse = df['timestamp'][0]

    return table_data

def layout():

    return html.Div(
        children=[
            dash_table.DataTable(
                id='driver_table',
                data=table_data,
                cell_selectable=True,
                style_table=styles.TABLE,
                style_cell=styles.TABLE_CELL,
                style_cell_conditional=styles.TABLE_CELL_CONDITIONAL,
                style_as_list_view=True,
                style_data_conditional=styles.TABLE_DATA_CONDITIONAL),
            dcc.Interval(
                id='interval-component',
                interval=RELOAD_INTERVAL,
            )
    ])