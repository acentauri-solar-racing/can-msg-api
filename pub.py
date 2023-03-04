"""
publish data to a topic in order to send data.
"""

import os
import argparse

from utils import helpers
from utils.type_lookup import type_lookup

from yaml import safe_load

from pathlib import Path
from typing import List


def gen_topic_strings() -> List[str]:
    ids, topics = helpers.flatten_tree()
    print(ids)


def create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

    parser.add_argument(
        "topic",
        help=r"Topic that should be published to, ex: /bms/cmu_1_stat",
        choices="",
    )

    parser.add_argument(
        "data",
        help=r"Drop DB tables and reinstantiate",
    )


if __name__ == "__main__":
    # read args from CLI
    # parser = argparse.ArgumentParser(description="Manage database connection")
    # create_base_argument_parser(parser)
    # results, unknown_args = parser.parse_known_args()

    gen_topic_strings()
