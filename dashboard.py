import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, Output, Input
from db.models import *
from db.db_service import DbService
from pandas import DataFrame

from frontend.styles import CONTENT_STYLE, SIDEBAR_STYLE
from frontend.router import route


def layout() -> dbc.Container:
    sidebar = html.Div(
        [
            dbc.Nav(
                [
                    # home
                    dbc.NavLink(html.I(className="bi bi-house fs-4"), id="home-tt",
                                href="/", active="exact"),
                    # MPPT
                    dbc.NavLink(html.I(className="bi bi-sun fs-4"), id="mppt-tt",
                                href="/mppt", active="exact"),
                    # BMS
                    dbc.NavLink(html.I(className="bi bi-battery fs-4"), id="bms-tt",
                                href="/bms", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            dbc.Tooltip(
                "Overview",
                target="home-tt",
            ),
            dbc.Tooltip(
                "MPPT Status",
                target="mppt-tt",
            ),
            dbc.Tooltip(
                "BMS Status",
                target="bms-tt",
            ),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    return html.Div(
        [dcc.Location(id="url"), sidebar, content])


def main():
    app: Dash = Dash(__name__, external_stylesheets=[
                     dbc.themes.LUX, dbc.icons.BOOTSTRAP])
    app.layout: dbc.Container = layout()  # set the global layout

    # set router decorator to select main content based on sideboard
    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        return route(pathname)

    db: DbService = DbService()  # Init service for querying database

    # finally start app
    app.run(debug=True, port=8080)


if __name__ == "__main__":
    print("::::::: aCe Dashboard :::::::::")
    main()
    print("Done")
