# CAN Message API

Repository tasked with interfacing between the CAN network data and external applications.

Our subsystem's modules generate data about a certain topic, i.e. BMS charge controller status, solar panel deck temperatures etc. This repo defines these topics and defines methods to handle data.


![Overview](docs/overview.png)




## Installation

### Python and Utils (Windows only)

Install Python 3.x and [Git Bash for Windows](https://gitforwindows.org). Then you can use the commonly used Linux commands (ls, cd, etc.) on your Windows machine.

### SQL / MariaDB (optional)

This step is optional. Maybe you just want to view the values being logged on the CAN bus, but not save them. If you don't want to save decoded values from the CAN bus in a database, just skip this step.

 For this I recommend XAMPP as an all-in-one tool to manage SQL databases.

### Virtualenv

This step isn't required, yet is highly recommended. It isolates the installation of this project from the global python installation and prevents version mismatches.

```sh
pip install virtualenv
```

Then source the configuration in the active shell. This will allow the programs in the virtualenv to be used without the source directory prepended.

```sh
python -m venv .venv
```

#### Linux
```sh
source .venv/bin/activate
```

#### Windows

```sh
source .venv/Scripts/activate
```

You should now see a `(.venv)` string in your CLI prompt, indicating that you are in the virtual environment.

### Python Modules
Then you can install the following modules required in this project's scripts with the following command:

```sh
pip install -r requirements.txt
```

#### Windows (required)

Windows users still need to install the following python module for compatibility with linux:

```sh
pip install windows-curses
```

### CAN Analyzer Drivers

The Seeedstudio CAN USB analyzer requires some drivers that you can download online.

#### Linux

The official seedstudio drivers have errors in them, preventing compilation. Install these drivers instead:

- [https://github.com/juliagoda/CH341SER](https://github.com/juliagoda/CH341SER)

#### Windows

- [https://github.com/SeeedDocument/USB-CAN-Analyzer](https://github.com/SeeedDocument/USB-CAN-Analyzer)


## Configuration

### SQL DB Environment Variables

Make a copy of the file `db/.env.example` and rename the copy to `db/.env`. This file is local and contains configuration strings for your machine that shouldn't be shared in version control.

Then edit the `db/.env` file with the passwords and paths for your machine.

### Source Tree to Disk

The scripts require you to have an accurate representation of the CAN message tree in the file tree. These files are not in version control to prevent synchronization conflicts. Hence you are required to generate local files using the following commands:

```sh
python source_tree.py
```

## Usage

Before running these commands, make sure your local filetree has the necessary message tree description. This can be generated using the following command:

```sh
python source_tree.py
```

For details regarding the scripts, refer to [Python CAN docs](https://python-can.readthedocs.io/en/master/scripts.html) or read the manpages.

### Logging

In the terminal, run the file `can-logger.sh`. It will create rotating log files capped at 50Mb in the `/logs` folder. Once a file reaches 50Mb, a new file with a different name is created.

```sh
# example for Linux
./can-logger.sh -c /dev/ttyUSB0 -b 500000
```

These log files can be saved and played back with the python-can playback at a later point in time.

### Playback

```sh
python -m can.player -v -i pcan -b 500000 -c PCAN_USBBUS1 logs/LOGFILE_HERE
```

### View

Automatically parses values in CAN bus and shows them in CAN viewer.

```sh
python -m can.viewer -v -i pcan -b 500000 -c PCAN_USBBUS1 -d type_lookup.txt
```

```
Shortcuts:
        +---------+-------------------------------+
        |   Key   |       Description             |
        +---------+-------------------------------+
        | ESQ/q   | Exit the viewer               |
        | c       | Clear the stored frames       |
        | s       | Sort the stored frames        |
        | h       | Toggle highlight byte changes |
        | SPACE   | Pause the viewer              |
        | UP/DOWN | Scroll the viewer             |
        +---------+-------------------------------+
```

#### Publish

If you want to send your device a certain message over CAN, you can use the `pub` utility.

```sh
python pub.py -t /stwheel/stwheel_heartbeat -c /dev/ttyUSB0 -b 500000 --data 0 0 0
```

#### Decode

The script `log_decoder.py` watches for modifications to files in the `/logs` folder and reads the newly inserted lines to log files. This decoder can run in real-time as log-files are being written, or also after recording data. New lines might appear because the real-time logging script is active or files from the SD-card logger are moved into the logs folder.

```sh
python log_decoder.py
```

### Manage DB

If you want to delete all entries in the database, just execute the following command

```sh
python db_utils.py --refresh
```

## Links

- [https://python-can.readthedocs.io/en/stable/listeners.html](https://python-can.readthedocs.io/en/stable/listeners.html)
- [https://python-can.readthedocs.io/en/stable/scripts.html#can-logger](https://python-can.readthedocs.io/en/stable/scripts.html#can-logger)