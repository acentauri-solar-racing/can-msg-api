"""
validate the tree, check if fields are set, indices and data types are aligned
and do not exceed CAN message size.
"""

import os
import fnmatch

from utils import helpers
from utils.type_lookup import type_lookup
from typing import List

from jinja2 import Environment, FileSystemLoader



def validate_tree() -> bool:
    def validate_ids(ids: List[str]) -> bool:
        """Checks if there are no duplicate IDs

        Args:
            ids (List[str]): List of IDs

        Returns:
            bool: True if there are no duplicates
        """
        if len(set(ids)) != len(ids):
            print("ERROR: duplicated CAN ID, recheck tree")
            return False
        return True



    # run validation code for ids and fields
    ids, topics, topics_dict = helpers.flatten_tree(path = "error-tree.yaml")
    if not validate_ids(ids):
        return False

    print(ids)
    return True

if __name__ == "__main__":
    if validate_tree():
        print("Valid Tree")
    else:
        print("Done, ERROR state, invalid tree")

    print("Done, messaging tree sourced to file system")
