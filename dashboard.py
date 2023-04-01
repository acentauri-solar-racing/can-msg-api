import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, Output, Input
from db.models import *
from db.db_service import DbService
from pandas import DataFrame


def set_layout():
    layout: dbc.Container = dbc.Container(
        [
            dbc.Row([dbc.Col([html.H1("Main title", className="text-center")])]),
        ]
    )


if __name__ == "__main__":
    app: Dash = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout: dbc.Container = set_layout()
    app.run(debug=True, port=8080)

    db: DbService = DbService()
