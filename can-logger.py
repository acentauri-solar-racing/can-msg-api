import os
from datetime import datetime as dt
from typing import Any

from can import SizedRotatingLogger, Bus
from can.typechecking import StringPathLike

########################################################################################################################
# Configuration Parameters
########################################################################################################################

interface = "pcan"  # Type of CAN Analyzer Device
channel = "PCAN_USBBUS1"  # Channel of CAN Analyzer Device
file_size = 100000000  # Maximum size of a log file´in bytes

########################################################################################################################

# Create File Name
dt_string = dt.isoformat(dt.now())  # Get current timestamp
file_name = dt_string[:-7] + ".log"  # Cut-off subseconds and add file extension
file_name = file_name.replace(":", "_")  # Create valid filename
file_name = "logs/" + file_name  # Create the file in the right folder

# Bus instance
bus = Bus(channel=channel, interface=interface)

class CustomLogger(SizedRotatingLogger):
    def __init__(self, base_filename: StringPathLike, **kwargs: Any):
        super().__init__(base_filename, **kwargs)

    # TODO: Implement custom enter function
    def __enter__(self):
        super().__enter__()

    # TODO: Implement custom exit function
    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(self, exc_type, exc_val, exc_tb)


# Logger instance
logger = CustomLogger(
    base_filename=file_name,
    max_bytes=file_size, )

print("Starting Logger")

try:
    while True:
        msg = bus.recv(1)
        if msg is not None:
            logger(msg)
except KeyboardInterrupt:
    pass
finally:
    bus.shutdown()
    logger.stop()

print("Logger terminated")