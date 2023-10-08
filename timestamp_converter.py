# This file is intended to correct the offset of timestamps of a logfile
import argparse
import datetime
import os
import tkinter
from tkinter import filedialog


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""
    parser.add_argument(
        "-t",
        "--timedelta",
        help=r"time shift, format hh:mm:ss",
    )
    parser.add_argument(
        "-a",
        "--add",
        help=r"add the timedelta (default)",
        action="store_true"
    ),
    parser.add_argument(
        "-s",
        "--subtract",
        help=r"subtract the timedelta",
        action="store_true"
    ),
    parser.add_argument(
        "-f",
        "--file",
        help=r"the file that has to be corrected",
    )

def correct_timestamps(file: str, timedelta: datetime.timedelta) -> str:
    # Create new file with corrected timestamps

    with(open(file, "r", encoding="utf-8")) as f:

        out_lines = []
        print("Reading file...")

        for line in f:
            # skip empty lines
            temp = line.strip()
            if not temp:
                continue

            # Split up line and extract timestamp
            timestamp_str, channel_string, frame, rx_or_tx = line.split(" ")
            timestamp = float(timestamp_str[1:-1])

            # Correct timestamp
            timestamp = (datetime.datetime.fromtimestamp(timestamp) + timedelta).timestamp()

            # Merge corrected row together
            timestamp_str = "(" + "{:.3f}".format(timestamp) + ")"
            out_lines.append(timestamp_str + " " + channel_string + " " + frame + " " + rx_or_tx)

        print("done")

        # Open dialog to save file
        tkinter.Tk().withdraw()
        out_file = filedialog.asksaveasfilename(initialdir=os.getcwd(), title="Save file", filetypes=(("Log File", ".log"),("Any File", ".*")))

        # Save file
        with(open(out_file, "w", encoding="utf-8")) as out:
            out.writelines(out_lines)

    return out_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage database connection")
    _create_base_argument_parser(parser)
    results, unknown_args = parser.parse_known_args()

    if(results.add and results.subtract):
        print("Please do not use the -a and the -s flag simultaneously")

    # Read the input timedelta
    timestamp: datetime.datetime = datetime.datetime.strptime(results.timedelta, "%H:%M:%S")

    # Create timedelta object depending on whether the timedelta should be added or subtracted
    if(results.subtract):
        timedelta = -datetime.timedelta(hours=timestamp.hour, minutes=timestamp.minute, seconds=timestamp.second)
    else:
        timedelta = datetime.timedelta(hours=timestamp.hour, minutes=timestamp.minute, seconds=timestamp.second)

    # If no file specified, open the file dialog
    if results.file is None:
        tkinter.Tk().withdraw()
        results.file = filedialog.askopenfilename(initialdir=os.getcwd(), title="Open file", filetypes=(("Log File", ".log"),("Any File", ".*")))

    # Open the file and create a copy with corrected timestamps
    filename = correct_timestamps(results.file, timedelta)

    if filename != "":
        print('Saved file under {}'.format(filename))
    else:
        print('File was not saved')



