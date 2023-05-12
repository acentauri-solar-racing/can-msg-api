import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, Output, Input, page_container

from frontend.styles import CONTENT_STYLE
from frontend.sidebar import sidebar


def layout() -> dbc.Container:
    """Set global container with sidebar and main content window"""

    content = html.Div(page_container, style=CONTENT_STYLE)
    return html.Div(
        [dcc.Location(id="url"), sidebar(), content,
         ])


def main():

    # spawn new plotly instance
    app: Dash = Dash(name="Dashboard", external_stylesheets=[
                     dbc.themes.LUX, dbc.icons.BOOTSTRAP], use_pages=True, pages_folder="frontend", update_title=None)

    # set the global layout
    app.layout: dbc.Container = layout()

    # runt
    app.run(debug=True, port=8080)


if __name__ == "__main__":
    print("::::::: aCe Dashboard :::::::::")
    main()
    print("Done")
