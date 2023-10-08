"""
decode data from a log file and read the information therein
"""
import argparse
import itertools
import binascii
import os
import struct
import time
import math
import tkinter
from tkinter import filedialog

from utils import helpers
from db.db_service import DbService

from typing import Dict, Tuple, Union

from multiprocessing import Lock
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""
    parser.add_argument(
        "-f",
        "--file",
        help=r"Decode logfile specified by path",
    )
    parser.add_argument(
        "-l",
        "--live",
        help=r"Start live logfile decoder",
        action="store_true",
    )


class Watcher:
    """This class is responsible for triggering the LogEventHandler processes
    indefinitely. It only monitors the specified directory.
    """
    def __init__(self, directory, handler=FileSystemEventHandler()):
        self.observer: Observer() = Observer()
        self.handler: FileSystemEventHandler() = handler
        self.directory: str = directory

    def run(self):
        """This starts the monitoring process of self.directory. Any file
        changes (e.g. creation, modification) will trigger the LogEventHandler.
        This function runs until the program is terminated.
        """
        self.observer.schedule(self.handler, self.directory, recursive=True)
        self.observer.start()

        print("CAN-Monitor running in {}\n".format(self.directory))

        try:
            while True:
                time.sleep(1)
        except:
            ##program is stopped (i.e. runs forever)
            self.observer.stop()
        self.observer.join()

        print("CAN-Monitor gracefully terminated\n")


class LogParser:
    db: DbService = DbService()
    def __init__(self):
        self.lock: Lock = Lock()

        self.data_structs: Dict[
            Union[int, Tuple[int, ...]], Union[struct.Struct, Tuple, None]
        ] = {}

        # read and process file listing can message data formats
        # data_structs is a dictionary keyed with can_ids to struct objects
        # configured per message to unpack the bits to data
        with open("type_lookup.txt", encoding="utf-8") as f:
            structs = f.readlines()

        for s in structs:
            tmp = s.rstrip("\n").split(":")

            # The ID is given as a hex value, the format needs no conversion
            key, fmt = int(tmp[0], base=16), tmp[1]

            # create struct object that interprets bits with given format
            self.data_structs[key] = struct.Struct(fmt)

    def _process_line(self, line: str) -> None:
        try:
            timestamp_string, channel_string, frame, rx_or_tx = line.split(sep=" ")
            timestamp = float(timestamp_string[1:-1])
        except:
            print("line stripping failed, invalid log line: \r\n" + str(line))
            return

        try:
            can_id, data = frame.split("#", maxsplit=1)
            key = helpers.conv_hex_str(can_id)
        except:
            print("couldn't extract log data for msg with id: " + str(hex(key)))
            print("possibly unknown ID")
            return

        try:
            unpacked_data: Tuple = self.data_structs[key].unpack(binascii.unhexlify(data))

            # https://en.wikipedia.org/wiki/2,147,483,647
            if any(map(lambda x: math.isnan(x) or x is None or x > 0x7FFFFFFF, unpacked_data)):
                raise ValueError("Invalid data input")

            # Do not commit session after adding a single entry for performance reasons
            self.db.add_entry(key, unpacked_data, timestamp, commit_session=False)
        except ValueError:
            print("\r\ndata contains nan or None or is too large for INT")
            print("id: " + str(hex(key)))
            print("data: " + str(unpacked_data))
            print("timestamp: " + str(timestamp) + "\r\n")
        except:
            print("\r\nfailed inserting msg to DB w/ id: " + str(hex(key)))
            print("data: " + str(unpacked_data))
            print("timestamp: " + str(timestamp) + "\r\n")


class LogFileParser(LogParser):
    def __init__(self):
        super().__init__()

    def parse_file(self, path):
        with self.lock:  # prevent concurrency issues with reading files
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                n_lines = len(lines)
                print("parsing {} entries from logfile with path {}".format(n_lines, path))
                ctr = 0
                for line in lines:
                    ctr += 1

                    # Print current state
                    if ctr % math.ceil(int(n_lines/100)) == 0:
                        print("Loading from logfile: {:3.0%}".format(ctr/n_lines))

                    # skip empty lines
                    temp = line.strip()
                    if not temp:
                        continue

                    # Add entry to database session. Does not commit database session!
                    self._process_line(line.rstrip("\n"))

                    # Commit database session regularly
                    if(ctr % 100000 == 0):
                        print("Committing to database, may take a moment...")
                        self.db.commit_session()

        print("Committing to database, may take a moment...")
        self.db.commit_session()
        print("done")



class LogEventHandler(FileSystemEventHandler, LogParser):

    def __init__(self):
        super().__init__()
        self.old_line_number: int = 0
        self.curr_file_name: str = ""

    def on_modified(self, event: FileSystemEvent):
        """This function gets triggered automatically once the Watcher is
        running and a modification in the monitored directory or
        subdirectory is detected. It will only respond to modified files,
        decodes the newly modified lines and adds them to the SQL database.

        Args:
            event (FileSystemEvent): Event triggered by the Watcher class.
        """
        if not event.is_directory:
            with self.lock:  # prevent concurrency issues with reading files

                # target file changes when log files roll over / new log started
                if event.src_path != self.curr_file_name:
                    print("opened file: " + str(event.src_path))
                    self.old_line_number = 0
                    self.curr_file_name = event.src_path

                with open(event.src_path, "r", encoding="utf-8") as f:
                    # only analyze the newly added lines in the file
                    # for loop goes from old line num till end of file
                    for line in itertools.islice(f, self.old_line_number, None):
                        if (self.old_line_number % 500 == 0):
                            print("reading line nr " + str(self.old_line_number))

                        # skip empty lines
                        temp = line.strip()
                        if not temp:
                            continue

                        # Add line to database session and commit directly afterwards
                        self._process_line(line.rstrip("\n"))
                        self.db.commit_session()
                        self.old_line_number += 1


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Manage database connection")
    _create_base_argument_parser(arg_parser)
    results, unknown_args = arg_parser.parse_known_args()

    if results.file is not None:
        parser = LogFileParser()
        parser.parse_file(results.file)
    elif results.live:
        w: Watcher = Watcher("logs/", LogEventHandler())
        w.run()
    else:
        tkinter.Tk().withdraw()
        paths = filedialog.askopenfilenames(initialdir=os.getcwd(), title="Select log files", filetypes=(("Log File", ".log"),("Any File", ".*")))
        if paths != "":
            parser = LogFileParser()
            for path in paths:
                parser.parse_file(path)
