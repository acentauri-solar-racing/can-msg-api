# Log CAN messages

This file is intended as a guideline to log CAN data. There are two options: Directly writing into the main database and
writing into a logfile.

## Hardware setup
1. Connect your CAN analyzer device via USB with the computer.
2. Open the file `can_logger.py` and specify the details about your CAN analyzer device in the top of the file. If you
are using a PCAN analyzer, you don't have to change anything. For more information, visit:
[https://python-can.readthedocs.io/en/stable/interfaces.html](https://python-can.readthedocs.io/en/stable/interfaces.html)

## Sofware setup
### Logging into database
For this, the database has to be set up. For further information, please refer to the corresponding manual.

1. Type the following command into the command line (you can also leave the `-d` away):

```sh
python can_logger.py -d
```

As soon as `Logger started` pops up in the terminal, the logger is running and writing all messages to the database. The
logger runs indefinitely, press any key to stop it.

### Logging into logfiles
1. If you do not want to set up the database and just want to log the data into separate files, you can do so by entering
the following command into the command line:

```sh
python can_logger.py -f
```

The program creates a file named by the current timestamp in the folder `/logs`. The logger runs indefinitely, press any
key to stop it.