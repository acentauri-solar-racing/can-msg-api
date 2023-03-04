import os

from utils.type_lookup import type_lookup
from typing import List

from yaml import safe_load
from pathlib import Path

# flatten the tree into lists of topic and field dicts
def flatten_tree() -> dict:
    tree = safe_load(Path("msg-tree.yaml").read_text())
    topics: List = []
    ids: List = []

    for namespace in tree:
        for topic in tree[namespace]:
            ids.append(str(tree[namespace][topic]["id"]))

            # insert name manually in dict for convenience
            tree[namespace][topic]["name"] = topic

            topics.append(tree[namespace][topic])
    return ids, topics


def conv_name_camel_case(name: str) -> str:
    words = [word.capitalize() for word in name.split(sep="_")]
    return "".join(words)


def clean_id(hex_str: str) -> str:
    return hex_str.lstrip("0x")


def gen_format_str(fields: dict) -> str:
    types_list: List[str] = []

    for f in fields:
        field = fields[f]
        typename: str = type_lookup[field["type"]]["py_struct_t"]
        types_list.append(typename)

    return "".join(types_list)


def conv_hex_str(hex_str: str) -> int:
    return int(hex_str, base=16)