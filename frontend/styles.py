########################################################################################################################
# Colors
########################################################################################################################
COLOR_BACKGROUND = '#fefefe'
COLOR_BORDER = '#dddddd'
COLOR_SELECTED = '#224c82' # dark solar panel blue
COLOR_HIGHLIGHT = '#e11a27' # swiss red


########################################################################################################################
# General Styles
########################################################################################################################
CONTENT_STYLE = {
    "marginLeft": "6rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "padding": "2rem 1rem",
    "backgroundColor": "#F1F1F1",
}
########################################################################################################################
# Table Styles
########################################################################################################################

TABLE = {
        'border': '1px solid %s' % COLOR_BORDER
}

TABLE_CELL = {
    'text-align': 'center',
    'width': '{}%'.format(10)
}

TABLE_CELL_CONDITIONAL = [
    {'if': {'column_id': ''},
     'width': '60%'},
]

TABLE_DATA = {
    # "font-size": "25px", "font_weight": "heavy"
}

TABLE_DATA_CONDITIONAL = [
    {
        'if':{'column_id': ''},
        'textAlign':'left'
    },
    {'if': {'state': 'selected'},
     'backgroundColor': COLOR_BACKGROUND,
     'border-bottom': '1px solid %s' % COLOR_BORDER,
     'border-top': '1px solid %s' % COLOR_BORDER,
     'border-right': '1 px solid blue',
     'border-left': 'none',

     # 'border': 'none'
     }
]

# modules table specific
TABLE_CELL_MODULES = {
    'text-align': 'center',
    'width': '{}%'.format(9)
}

# modules table specific
TABLE_CELL_CONDITIONAL_MODULES = [
    {
        'if': {
            'filter_query': 'eq "inactive"'
        },
        'backgroundColor': '#f00',
        'color': 'white'
    }
]

########################################################################################################################
# Text Styles
########################################################################################################################
H1 = {
    'paddingBottom': '20px',
}

H2 = {
    'paddingTop': '40px',
    'paddingBottom': '10px',
}

H3 = {
    'font-size': '14px',
    'paddingTop': '10px',
    'paddingBottom': '10px',
    'text-align': 'center'
}