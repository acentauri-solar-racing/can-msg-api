import os
from datetime import datetime as dt

# File Size
f_size = 32768

# Get Port
port = input("Enter COM Port:")

# Get current timestamp for the file name
dt_string = dt.isoformat(dt.now())
file_name = dt_string[:-7] + ".log"         # Cut-off subseconds and add file extension
file_name = file_name.replace(":", "_")     # Create valid filename

cmd_string = "python -m can.logger -i seeedstudio -b 500000 -s %s -c %s -f logs/%s" % (f_size, port, file_name)

# start logger
os.popen(cmd_string)

print ("Logger running in %s. Press CTR + C to stop it" % (file_name))