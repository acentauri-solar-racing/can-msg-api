# Decode Logfiles

This file is intended as a guideline to decode log files from the car and insert the decoded data into the main sql
database.

## Structure of logfiles

The logfiles are named after the timestamp they are created, e.g. `09031656` corresponds to September 3, at 16.56.
The content of the files looks something like this:

```
(1693760165.223) vcan0 505#C80000000000 R
(1693760165.247) vcan0 100#000000000000 R
(1693760165.266) vcan0 6F7#0000000000000000 R
...
````

## Decode the data

0. optionally, you can delete all data that has been previously been in the database by running the following command.
   Attention! This will erase all data from the database!

```sh
python db_utils.py -r
```

### Via GUI

1. Type the following command into the command line:

```sh
python log_decoder.py
```

2. A file explorer should pop up. Chose all the logfiles you wish to decode. The files will be parsed and added to the
   database.

### Via Command Line

1. Alternatively, you can directly specify the path to the logfile by using the -f option:

```sh
python log_decoder.py -f <path_to_logfile>
```

### Live decoding

NOTE: This option is kept for legacy reasons and not recommended for logging car data into the database. If you want to
do so, please use the database option the logging script directly.

The decoder watches for modifications to files in the `/logs` folder. It automatically parses the newly inserted lines
and adds them to the database. 

1. For usage, type the following command into the terminal:

```sh
python log_decoder.py -l 
```
