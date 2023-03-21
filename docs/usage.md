# Usage Guide

Here is a short list of commands for logging data. These commands need to be adapted for the necessary COM ports in Win10.

```sh
# CAN Viewer command
python3 -m can.viewer -i seeedstudio -b 500000 -c /dev/ttyCH341USB0

# Log file generation command
# baudrate: 250'000, max logfile size: 50 Mb -> rollover
python3 -m can.logger -i seeedstudio -b 500000 -s 52428800 -c /dev/ttyCH341USB0 -f bus_data_dump.log
```