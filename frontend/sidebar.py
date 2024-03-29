import dash_bootstrap_components as dbc
from dash import dcc, html
from frontend.styles import SIDEBAR_STYLE


def sidebar():
    return html.Div([
        dbc.Nav([
                # home
                dbc.NavLink(html.I(className="bi bi-house fs-4"), id="home-tt",
                            href="/", active="exact"),
                # Driver
                dbc.NavLink(html.I(className="bi bi-chat-right-dots"), id="driver-tt",
                        href="/driver", active="exact"),
                # MPPT
                dbc.NavLink(html.I(className="bi bi-hdd-stack fs-4"), id="mppt-tt",
                            href="/mppt", active="exact"),
                # BMS Pack
                dbc.NavLink(html.I(className="bi bi-motherboard fs-4"), id="bms-pack-tt",
                            href="/bms_pack", active="exact"),
                # BMS Cells
                dbc.NavLink(html.I(className="bi bi-grid-3x2 fs-4"), id="bms-cells-tt",
                            href="/bms_cells", active="exact"),
                # BMS Cells
                dbc.NavLink(html.I(className="bi bi-exclamation-diamond fs-4"), id="errors-tt",
                            href="/errors", active="exact"),
                # Analyzer
                dbc.NavLink(html.I(className="bi bi-graph-up"), id="analyzer-tt",
                            href="/analyzer", active="exact")
                ],
                vertical=True,
                pills=True,
                ),
        dbc.Tooltip(
            "Overview",
            target="home-tt",
        ),
       dbc.Tooltip(
           "Driver Responses",
           target="driver-tt",
       ),
        dbc.Tooltip(
            "MPPT Status",
            target="mppt-tt",
        ),
        dbc.Tooltip(
            "BMS Pack Status",
            target="bms-pack-tt",
        ),
        dbc.Tooltip(
            "BMS Cell Status",
            target="bms-cells-tt",
        ),
        dbc.Tooltip(
            "Errors",
            target="errors-tt",
        ),
        dbc.Tooltip(
            "Analyzer",
            target="analyzer-tt",
        )
    ], style=SIDEBAR_STYLE,)
