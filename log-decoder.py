"""
decode data from a log file and read the information therein
"""
from multiprocessing import Lock
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer
from typing import Dict, List, Tuple, Union

import logging
import time
import os
import itertools


from pathlib import Path


class Watcher:
    def __init__(self, directory, handler=FileSystemEventHandler()):
        self.observer: Observer() = Observer()
        self.handler: FileSystemEventHandler() = handler
        self.directory: str = directory

    def run(self):
        self.observer.schedule(
            self.handler, self.directory, recursive=True)
        self.observer.start()

        print("CAN-Monitor running in {}\n".format(self.directory))

        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()

        print("CAN-Monitor gracefully terminated\n")


class LogEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.old_line_number: int = 0
        self.curr_file_name: str = ""
        self.lock: Lock = Lock()

    def on_modified(self, event: FileSystemEvent):
        # fire only on modified files, not directories
        if not event.is_directory:
            with self.lock:  # prevent concurrency issues with reading files

                # target file changes when log files roll over / new log started
                if event.src_path != self.curr_file_name:
                    self.old_line_number = 0
                    self.curr_file_name = event.src_path

                with open(event.src_path, 'r', encoding="utf-8") as f:
                    # only analyze the newly added lines in the file
                    # for loop goes from old line num till end of file
                    for line in itertools.islice(f, self.old_line_number, None):
                        # skip empty lines
                        temp = line.strip()
                        if not temp:
                            continue

                        self._process_line(line.rstrip("\n"))
                        self.old_line_number += 1

    def _process_line(self, line: str) -> None:
        timestamp_string, channel_string, frame, rx_or_tx = line.split(sep=" ")

        timestamp = float(timestamp_string[1:-1])
        can_id, data = frame.split("#", maxsplit=1)

    def _decode_data(data: str):
        data_structs: Dict[
            Union[int, Tuple[int, ...]], Union[struct.Struct, Tuple, None]
        ] = {}

        with open(parsed_args.decode[0], encoding="utf-8") as f:
            structs = f.readlines()

        for s in structs:
            tmp = s.rstrip("\n").split(":")


if __name__ == "__main__":
    # set the current working directory of script to resolve relative file path
    script_cwd: str = os.path.realpath(os.path.dirname(__file__))

    w: Watcher = Watcher(script_cwd + "/logs/", LogEventHandler())
    w.run()
