# CAN Message API

Repository tasked with interfacing between the CAN network data and external applications.

Our subsystem's modules generate data about a certain topic, i.e. BMS charge controller status, solar panel deck temperatures etc. This repo defines these topics and defines methods to handle data.


![Overview](docs/overview.png)




## Installation

### Python and Utils (Windows only)

Install Python 3.x and [Git Bash for Windows](https://gitforwindows.org). Then you can use the commonly used Linux commands (ls, cd, etc.) on your Windows machine.

### SQL / MariaDB (optional)

This step is optional. If you want to store car data, setting up an SQL database is very much recommended. Please refer to `setup_database.md` for more details.

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

The CAN USB analyzers require some drivers that you can download online. 
#### PCAN
The PCAN driver can be found here:
- [https://www.peak-system.com/PCAN-USB.199.0.html](https://www.peak-system.com/PCAN-USB.199.0.html)

#### Seedstudio
##### Linux

The official seedstudio drivers have errors in them, preventing compilation. Install these drivers instead:

- [https://github.com/juliagoda/CH341SER](https://github.com/juliagoda/CH341SER)

##### Windows
For Windows, use the official github repository.
- [https://github.com/SeeedDocument/USB-CAN-Analyzer](https://github.com/SeeedDocument/USB-CAN-Analyzer)


## Configuration

### Source Tree to Disk

## Usage

Before running these commands, make sure your local filetree has the necessary message tree description. This can be generated using the following command:

```sh
python source_tree.py
```

For details regarding the scripts, refer to [Python CAN docs](https://python-can.readthedocs.io/en/master/scripts.html) or read the manpages.

### Logging

Car data CAN be logged directly into the database or alternatively into a logfile. For more information, please refer
to the file `can_logger.md`.

### Playback

```sh
python -m can.player -v -i pcan -b 500000 -c PCAN_USBBUS1 logs/LOGFILE_HERE
```

### View (terminal)

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

### Dashboard

There exists a dashboard application for plotting performance data of the car, such as speed, battery output power etc.
The dashboard has a live mode that is intended to monitor the solar racing car while driving. In addition, there's an
analyzer application that allows to plot performance data in a given time interval for subsequent analysis.

The dashboard application needs the database to be running.

```sh
python dashboard.py
```

#### Publish

If you want to send your device a certain message over CAN, you can use the `pub` utility.

```sh
python pub.py -t /stwheel/stwheel_heartbeat -c PCAN_USBBUS1 -b 500000 --data 0 0 0
```

#### Decode

A decoder program takes logfiles and inserts their data into the database. This is useful for analyzing the data in
hindsight. For straight-forward usage, type the following command into the terminal.

```sh
python log_decoder.py
```

However, there are multiple option for the decoder including a live decoder. For more information on the decoder, please
refer to `log_decoder.md`.

### Manage DB

If you want to delete all entries in the database, just execute the following command

```sh
python db_utils.py --refresh
```

## Links

- [https://python-can.readthedocs.io/en/stable/listeners.html](https://python-can.readthedocs.io/en/stable/listeners.html)
- [https://python-can.readthedocs.io/en/stable/scripts.html#can-logger](https://python-can.readthedocs.io/en/stable/scripts.html#can-logger)