"""
publish data to a topic in order to send data.
"""

import os
import argparse
import can
import time

from utils import helpers
from utils.type_lookup import type_lookup

from yaml import safe_load

from pathlib import Path
from typing import List

from struct import pack


def create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-t",
        "--topic",
        dest="topic_str",
        required=True,
        help="Topic that should be published to, ex: /bms/cmu_1_stat",
    )

    parser.add_argument(
        "-b",
        "--baudrate",
        dest="baudrate",
        required=True,
        help="Baudrate of the CAN bus",
    )
    parser.add_argument(
        "-c",
        "--channel",
        dest="channel",
        default="/dev/ttyUSB0",
        help="Channel for USB CAN bus analyzer, ex: /dev/ttyUSB0 or COM10",
    )

    # for simplicity, we parse the data as floats. if type isnt supplied,
    # argparse handled inputs as strings. We later can cast the floats to int if necessary
    parser.add_argument(
        "-d",
        "--data",
        dest="data",
        type=float,
        nargs="+",
        required=True,
        help="Tuple containing the data to be published",
    )

    parser.add_argument(
        "-f",
        "--freq",
        dest="freq",
        default=1.0,
        type=float,
        help="Frequency at which data should be published, ex: 1.0",
    )


def send_msg(id, data: bytes, channel: str, freq: float, baudrate: int):
    with can.Bus(interface="seeedstudio", channel=channel, bitrate=baudrate) as bus:
        msg = can.Message(arbitration_id=id, data=data, is_extended_id=True)

        while True:
            try:
                bus.send(msg)
                print(f"Sent: {data} \t {bus.channel_info}")
            except can.CanError:
                print("Message NOT sent")

            time.sleep(1.0 / freq)


def convert_input(topic_str: str, data: tuple):
    """Extract msg ID as base10 integer and prepare data bytes"""

    # load the tree from filesystem
    ids, topics_list, topics_dict = helpers.flatten_tree()

    # select the specified topic according to user input
    if topic_str not in topics_dict:
        raise ValueError("Specified topic " + topic_str + " not in tree")

    topic: dict = topics_dict[topic_str]
    fields: dict = topic["data"]

    id: int = helpers.conv_hex_str(topic["id"])

    # make sure user supplied expected amount of data
    user_data = list(data)  # cast tuple to list
    if len(fields) != len(user_data):
        raise ValueError(
            f"supplied data length mismatch, expected {len(fields)} fields, got {len(user_data)}"
        )

    # combine user input tuple with topic data types
    # we need to relate the input data to the final data type. User input is
    # guaranteed to be float and sometimes needs to be made int

    # ('data_u32', 3.14159) -> 3: int
    # ('data_fp', 3.14159) -> 3.14159: float
    cast_targets: List[str] = [fields[f]["type"] for f in fields]

    for index, target in enumerate(cast_targets):
        if target != "data_fp":
            user_data[index] = int(user_data[index])

    # convert data to bits
    data = pack("<" + helpers.gen_format_str(topic["data"]), *user_data)
    return (id, data)


def main() -> None:
    # read args from CLI
    parser = argparse.ArgumentParser(description="Publish messages to topic")
    create_base_argument_parser(parser)
    args, unknown_args = parser.parse_known_args()

    # convert user data into format for sending msg
    try:
        id, data = convert_input(args.topic_str, args.data)
        send_msg(id, data, args.channel, args.freq, args.baudrate)

    except ValueError as e:
        print("ERR: Invalid input, could not publish to the topic:")
        print(e)


if __name__ == "__main__":
    print("Message Publishing Utility\n")
    main()
    print("\nDone")
