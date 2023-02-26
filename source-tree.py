"""
validate the tree, check if fields are set, indices and data types are aligned
and do not exceed CAN message size.
"""

import yaml
import os
import jinja2

from pathlib import Path
from typing import List
from msg_data_types import type_lookup

# set the current working directory of script to resolve relative file path
script_cwd: str = os.path.realpath(os.path.dirname(__file__))

# flatten the tree into lists of topic and field dicts
def flatten_tree() -> dict:
    tree = yaml.safe_load(Path(script_cwd + "/msg-tree.yaml").read_text())
    topics: List = []
    ids: List = []

    for namespace in tree:
        for topic in tree[namespace]:
            ids.append(str(tree[namespace][topic]["id"]))

            topics.append(tree[namespace][topic])
    return ids, topics


def validate_tree() -> bool:
    def validate_ids(ids: List[str]) -> bool:
        if len(set(ids)) != len(ids):
            print("ERROR: duplicated CAN ID, recheck tree")
            return False
        return True

    def validate_fields(topic: dict) -> bool:
        fields = []

        for f in topic["data"]:
            fields.append(topic["data"][f])

        # move a cursor along 64 bits and check for overlaps or overflows
        cursor = 0
        # array representing 64 bits, we mark bits as visited
        visited = [False] * 64

        for field in fields:
            size = type_lookup[field["type"]]["size"]
            idx = field["idx"]

            # check if the data will go out of bounds
            cursor += size
            if cursor > 64:
                print("\ntopic " + topic["id"] + " exceeds 64 bits")
                return False

            # check if there is overlap between fields
            start = size * idx
            for i in range(start, start + size):
                if visited[i] is True:

                    print("\noverlapping memory allocation in " + topic["id"])
                    return False
                else:
                    visited[i] = True

        return True

    # run validation code for ids and fields
    ids, topics = flatten_tree()
    for topic in topics:
        if not validate_fields(topic):
            print("ERROR: data allocation error in topic\n")
            return False

    if not validate_ids(ids):
        return False

    return True


def write_tree_to_fs():
    def conv_fields_to_type_index(can_id: str, fields: List, lines: List[str]) -> None:
        """autogenerate file for python-can with list of fields and types in type_lookup.txt"""
        cleaned_id = can_id.lstrip("0x")
        struct_types: List[str] = [
            type_lookup[field["type"]]["py_struct_t"] for field in fields
        ]

        lines.append(cleaned_id + ":<" + "".join(struct_types) + "\n")

    print("lmao")


if __name__ == "__main__":
    print("Validating message tree")

    if validate_tree():
        print("Done Validating, valid tree")

        # write_tree_to_fs()
    else:
        print("Done, ERROR state, invalid tree")
