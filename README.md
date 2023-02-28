# CAN Message API

Repository tasked with interfacing between the CAN network data and external applications.

Our subsystem's modules generate data about a certain topic, i.e. BMS charge controller status, solar panel deck temperatures etc. This repo defines these topics and defines methods to handle data.


![Overview](docs/overview.png)


## Installation

### Virtualenv

This step isn't required, yet is highly recommended. It isolates the installation of this project from the global python installation and prevents version mismatches.

Install `virtualenv` from  [https://pypi.org/project/virtualenv/](https://pypi.org/project/virtualenv/)

```sh
pipx install virtualenv
```

Then source the configuration in the active shell. This will allow the programs in the virtualenv to be used without the source directory prepended.

```sh
source .venv/bin/activate
```

### Python Modules
Install python3 and pip. Then you can install the following modules required in this project's scripts with the following command:

```sh
pip install -r requirements.txt
```

### CAN Analyzer Drivers

The Seeedstudio CAN USB analyzer requires some drivers that you can download online. Note that on linux, you actually have the drivers preinstalled and don't need to do anything, contrary to what is suggested in Seeedstudios documentation.

## Configuration

### Environment Variables

Make a copy of the file `db/.env.example` and rename the copy to `db/.env`. This file is local and contains configuration strings for your machine that shouldn't be shared in version control.

Then edit the `db/.env` file with the passwords and paths for your machine.

### Source Tree to Disk

The scripts require you to have an accurate representation of the CAN message tree in the file tree. These files are not in version control to prevent synchronization conflicts. Hence you are required to generate local files using the following commands:

```sh
python source_tree.py
```

## Usage

### Log CAN bus data

In the terminal, run the file `can-logger.sh`. It will create rotating log files capped at 50Mb in the `/logs` folder. Once a file reaches 50Mb, a new file with a different name is created.

```sh
./can-logger.sh
```

These log files can be saved and played back with the python-can playback at a later point in time.

### Decode CAN bus data

The script `log_decoder.py` watches for modifications to files in the `/logs` folder and reads the newly inserted lines to log files. New lines might appear because the real-time logging script is active or files from the SD-card logger are moved into the logs folder.



## Links

- [https://python-can.readthedocs.io/en/stable/listeners.html](https://python-can.readthedocs.io/en/stable/listeners.html)
- [https://python-can.readthedocs.io/en/stable/scripts.html#can-logger](https://python-can.readthedocs.io/en/stable/scripts.html#can-logger)