"""
validate the tree, check if fields are set, indices and data types are aligned
and do not exceed CAN message size.
"""

import yaml
import os

from pathlib import Path

from msg_data_types import type_lookup

# set the current working directory of script to resolve relative file path
script_cwd: str = os.path.realpath(os.path.dirname(__file__))
tree = yaml.safe_load(Path(script_cwd + '/msg-tree.yaml').read_text())

print("Validating message tree")

ids = []


def validate_fields(fields) -> bool:
    # move a cursor along 64 bits and check for overlaps or overflows
    cursor = 0
    # array representing 64 bits, we mark bits as visited
    visited = [False] * 64

    for field in fields:
        size = type_lookup[field['type']]['size']
        idx = field['idx']

        # check if the data will go out of bounds
        cursor += size
        if (cursor > 64):
            print("topic " + topic + " exceeds 64 bits")
            return False

        # check if there is overlap between fields
        start = size * idx
        for i in range(start, start + size):
            if visited[i] is True:
                print("overlapping memory allocation in " + topic)
                return False
            else:
                visited[i] = True

    return True


def validate_ids(ids) -> bool:
    return True


for namespace in tree:
    for topic in tree[namespace]:
        id = tree[namespace][topic]['id']
        ids.append(id)

        fields = []

        for f in tree[namespace][topic]['data']:
            fields.append(tree[namespace][topic]['data'][f])

        if not validate_fields(fields):
            print("data allocation error in topic: " + topic)

    if not validate_ids(fields):
        print("id error in topic, recheck: " + topic)

print("Done")
