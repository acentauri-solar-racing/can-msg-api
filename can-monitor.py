"""
decode data from a log file and read the information therein
"""
from multiprocessing import Lock
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import logging
import time
import os

from pathlib import Path


class Watcher:

    def __init__(self, directory, handler=FileSystemEventHandler()):
        self.observer = Observer()
        self.handler = handler
        self.directory = directory

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
        self.line_number = -1
        self.lock = Lock()

    def on_modified(self, event):
        # fire only on modified files, not directories
        if not event.is_directory:

            # prevent concurrency issues with reading files
            with self.lock:
                with open(event.src_path, 'r', encoding="utf-8") as f:
                    count = 0
                    for line in f:
                        if count > self.line_number:
                            self._process_line(line)
                            self.line_number = count

                        count += 1

    # Insert the values into MySql database
    def _process_line(self, line):
        print(line)


if __name__ == "__main__":
    # set the current working directory of script to resolve relative file path
    script_cwd: str = os.path.realpath(os.path.dirname(__file__))

    w = Watcher(script_cwd + "/logs/", LogEventHandler())
    w.run()
