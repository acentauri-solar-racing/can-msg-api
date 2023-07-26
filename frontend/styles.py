########################################################################################################################
# Colors
########################################################################################################################
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

PERFORMANCE_CELL = {
    'text-align': 'center',
    'width': '{}%'.format(10)
}

PERFORMANCE_CELL_CONDITIONAL = [
    {'if': {'column_id': ''},
     'width': '60%'}
]

BATTERY_CELL = {
    'text-align': 'center',
    'width': '{}%'.format(10)
}

BATTERY_CELL_CONDITIONAL = [
    {'if': {'column_id': ''},
     'width': '70%'}
]


MODULE_CELL = {
    'text-align': 'center',
    'width': '{}%'.format(9)
}

MODULE_CELL_CONDITIONAL = [
    {'if': {'column_id': ''},
     'width': '10%'}
]


TABLE_DATA = {
    # "font_size": "25px", "font_weight": "heavy"
}

DATA_CONDITIONAL = [
    {
        'if':{'column_id': ''},
        'textAlign':'left'
    }
]

########################################################################################################################
# Text Styles
########################################################################################################################
H1 = {
    "paddingBottom": "20px",
}

H2 = {
    "paddingTop": "40px",
    "paddingBottom": "10px",
}