import os

from utils.type_lookup import type_lookup
from typing import List

import yaml
from yaml.constructor import ConstructorError
from pathlib import Path

# flatten the tree into lists of topic and field dicts
## slightly confusing that it says -> dict and outputs lists
def flatten_tree(path: str = "msg-tree.yaml") -> tuple:
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    def no_duplicates_constructor(loader, node, deep=False):
        """Check for duplicate keys."""
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            value = loader.construct_object(value_node, deep=deep)
            if key in mapping:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found duplicate key (%s)" % key,
                    key_node.start_mark,
                )
            mapping[key] = value

        return loader.construct_mapping(node, deep)

    yaml.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates_constructor
    )

    tree = yaml.full_load(Path(path).read_text())
    ids: List = []
    topics_list: List = []
    topics_dict: dict = {}

    for namespace in tree:
        # then flatten the tree into a list of all topics
        for topic in tree[namespace]:
            ids.append(str(tree[namespace][topic]["id"]))

            # insert simple name manually in dict for convenience
            tree[namespace][topic]["name"] = topic

            # gen topic string with the full path, ex: cmu -> /bms/cmu
            topic_str: str = "/" + namespace + "/" + topic

            # return two flattened trees, a dict keyed with topics string and simple list
            topics_list.append(tree[namespace][topic])
            topics_dict[topic_str] = tree[namespace][topic]

    return (ids, topics_list, topics_dict)


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