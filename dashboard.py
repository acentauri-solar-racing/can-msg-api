import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, Output, Input
from db.models import *
from db.db_service import DbService
from pandas import DataFrame


def layout():
    return dbc.Container(
        [
            dbc.Row([dbc.Col([html.H1("Dashboard", className="text-center")])]),
        ]
    )


if __name__ == "__main__":
    app: Dash = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout: dbc.Container = layout()
    app.run(debug=True, port=8080)

    db: DbService = DbService()
