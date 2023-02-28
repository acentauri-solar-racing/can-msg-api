from utils.type_lookup import type_lookup
from typing import List


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