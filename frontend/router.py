from dash import html
from frontend.pages import overview, mppt, bms


def route(pathname: str):
    if pathname == "/":
        return overview.content
    elif pathname == "/bms":
        return bms.content
    elif pathname == "/mppt":
        return mppt.content
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )
