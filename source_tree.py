"""
validate the tree, check if fields are set, indices and data types are aligned
and do not exceed CAN message size.
"""

import os

from utils import helpers
from utils.type_lookup import type_lookup

from yaml import safe_load
from jinja2 import Environment, FileSystemLoader

from pathlib import Path
from typing import List

# set the current working directory of script to resolve relative file path
script_cwd: str = os.path.realpath(os.path.dirname(__file__))

# flatten the tree into lists of topic and field dicts
## slightly confusing that it says -> dict and outputs lists
def flatten_tree() -> dict: 
    """Takes yaml tree and returns list of all the IDs and a corresponding list 
    of the data. Each data dictionary has an added entry "name" with the topic 
    name of the corresponding id.

    Returns:
        List: IDs stored as strings
        List: Data stored as dictionaries
    """
    tree = safe_load(Path(script_cwd + "/msg-tree.yaml").read_text())
    topics: List = []
    ids: List = []

    for namespace in tree:
        for topic in tree[namespace]:
            ids.append(str(tree[namespace][topic]["id"]))

            # insert name manually in dict for convenience
            tree[namespace][topic]["name"] = topic

            topics.append(tree[namespace][topic])
    return ids, topics


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

    def validate_fields(topic: dict) -> bool:
        """Checks that the data fits into 64 bits, and that these bits are distributed correctly.

        Args:
            topic (dict): A dictionary with the data for one topic.

        Returns:
            bool: True if the data allocation is valid.
        """
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
    ##what does this actually do? what are these files used for?
    env = Environment(loader=FileSystemLoader("templates/"))
    env.globals["helpers"] = helpers
    ids, topics = flatten_tree()

    def generate_type_index_file() -> None:
        template = env.get_template("type_lookup.txt.j2")

        #create string from the template
        content = template.render(
            topics=topics,
            type_lookup=type_lookup,
        )
        #write the string into a txt filecalled type_lookup.txt
        with open(
            script_cwd + "/type_lookup.txt", mode="w", encoding="utf-8"
        ) as results:
            results.write(content)

    def generate_model_file() -> None:
        template = env.get_template("models.py.j2")

        content = template.render(
            topics=topics,
            type_lookup=type_lookup,
        )

        with open(script_cwd + "/db/models.py", mode="w", encoding="utf-8") as results:
            results.write(content)

    generate_type_index_file()
    generate_model_file()


if __name__ == "__main__":
    if validate_tree():
        write_tree_to_fs()
    else:
        print("Done, ERROR state, invalid tree")

    print("Done, messaging tree sourced to file system")
