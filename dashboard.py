import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, Output, Input

from frontend.styles import CONTENT_STYLE
from frontend.router import route
from frontend.sidebar import sidebar


def layout() -> dbc.Container:
    """Set global container with sidebar and main content window"""

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    return html.Div(
        [dcc.Location(id="url"), sidebar, content])


def main():
    # spawn new plotly instance
    app: Dash = Dash(name="Dashboard", external_stylesheets=[
                     dbc.themes.LUX, dbc.icons.BOOTSTRAP])
    app.layout: dbc.Container = layout()  # set the global layout

    # set router decorator to select main content based on sideboard
    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        return route(pathname)

    # finally start app
    app.run(debug=True, port=8080)


if __name__ == "__main__":
    print("::::::: aCe Dashboard :::::::::")
    main()
    print("Done")
