"""
decode data from a log file and read the information therein
"""

import os

from pathlib import Path

# set the current working directory of script to resolve relative file path
script_cwd: str = os.path.realpath(os.path.dirname(__file__))