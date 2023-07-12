import struct
from datetime import datetime as dt
from typing import Union, Tuple, Dict

from can import SizedRotatingLogger, Bus, Message

from db.db_service import DbService

########################################################################################################################
# Configuration Parameters
########################################################################################################################

interface = "pcan"  # Type of CAN Analyzer Device
channel = "PCAN_USBBUS1"  # Channel of CAN Analyzer Device
bitrate = 500000  # Bitrate of device
file_size = 100000000  # Maximum size of a log file´in bytes

########################################################################################################################

# Create File Name
dt_string = dt.isoformat(dt.now())  # Get current timestamp
file_name = dt_string[:-7] + ".log"  # Cut-off subseconds and add file extension
file_name = file_name.replace(":", "_")  # Create valid filename
file_name = "logs/" + file_name  # Create the file in the right folder

# Bus instance
bus = Bus(channel=channel, interface=interface, bitrate=bitrate)


# Parses CAN messages and stores them in the database
class DatabaseLogger:
    db: DbService

    def __init__(self):
        self.data_structs: Dict[Union[int, Tuple[int, ...]], Union[struct.Struct, Tuple, None]] = {}
        self.db = DbService()

        with open("type_lookup.txt", encoding="utf-8") as f:
            structs = f.readlines()

        for s in structs:
            tmp: list[str] = s.rstrip("\n").split(":")
            key, data_format = int(tmp[0], base=16), tmp[1]
            self.data_structs[key] = struct.Struct(data_format)

    def on_message_received(self, msg: Message) -> None:
        key = msg.arbitration_id
        data_unpacked: Tuple = self.data_structs[key].unpack(msg.data)
        self.db.add_entry(key, data_unpacked, msg.timestamp)

    def stop(self) -> None:
        pass


########################################################################################################################
# Uncomment the type of logger you want
########################################################################################################################
logger = DatabaseLogger() # Stores messages in the database
# logger = SizedRotatingLogger(base_filename=file_name, max_bytes=file_size)    # Stores messages to a .log file
########################################################################################################################

print("Started Logger")

try:
    while True:
        msg = bus.recv(1)
        if msg is not None:
            logger.on_message_received(msg)

except KeyboardInterrupt:
    pass
finally:
    bus.shutdown()
    logger.stop()

print("Logger terminated")