import dash_bootstrap_components as dbc
from dash import dcc, html
from frontend.styles import SIDEBAR_STYLE
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
