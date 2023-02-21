"""
decode data from a log file and read the information therein
"""

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time
import os

from pathlib import Path

# set the current working directory of script to resolve relative file path
script_cwd: str = os.path.realpath(os.path.dirname(__file__))


class Watcher:
    def __init__(self, directory=".", handler=FileSystemEventHandler()):
        self.observer = Observer()
        self.handler = handler
        self.directory = directory

    def run(self):
        self.observer.schedule(
            self.handler, self.directory, recursive=True)
        self.observer.start()
        print("\nWatcher Running in {}/\n".format(self.directory))
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()
        print("\nWatcher Terminated\n")


class MyHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        print(event)  # Your code here


if __name__ == "__main__":
    w = Watcher(".", MyHandler())
    w.run()
