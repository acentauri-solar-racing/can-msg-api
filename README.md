# CAN Message API

Repository tasked with interfacing between the CAN network data and external applications.

## Installation

Install python3 and pip. Then you can install the following modules required in this project's scripts with the following command:
```sh
python3 -m pip install -r requirements.txt
pip install
```


## How It Works

Our subsystem's modules generate data about a certain topic, i.e. BMS charge controller status, solar panel deck temperatures etc. This repo defines these topics and assigns the associated fields with concrete data types that can be followed throughout all user applications.

The file `msg-tree.yaml` contains a global lookup table with all topics and should hopefully prevent mismatches with ID's and datatypes across projects.

Each CAN bus message contains 8 bytes. The underlying datastructure that converts between the byte array and C types (uint32_t, float, etc.) is the following union:

```C
typedef union _group_64 {
 float data_fp[2];
 unsigned char data_u8[8];
 char data_8[8];
 unsigned int data_u16[4];
 int data_16[4];
 unsigned long data_u32[2];
 long data_32[2];
} group_64;
```

A union allows for the same section of memory to be represented by different data types. Your code might put some floats in the union. Afterwards the union's data_u8 member, the same float bits, is then sent through the CAN bus. Each topic's messages have 8 bytes worth of data inside, you are free to mix and match types of differing sizes to fill up a message. For example, you can allocate the 64 bits or 8 bytes with a float (32 bits), two chars (2x8 = 16 bits) and a uint16_t (16 bits).

### Use in STM32 Projects

The acentauri project template contains a script that downloads the latest version of the global lookup table and generates code based on it. With the code you can subscribe and publish to the topics.

If your project needs a specific data source that isn't yet in the tree, feel free to extend it and tell others that they need to reseed their project's lookup tables.

### CAN Bus monitoring

Next to subscribing and publishing to topics from our modules, externally recording and monitoring the state of the CAN bus is another necessity. The following system allows for logging data, playing it back at a later time and decoding data for external use / permanent storage.

![Overview](./docs/overview.png)

The CAN bus data is logged on an SD card in raw hex format (backup) and can also be retrieved in real-time with a USB-CAN analyzer. In racing operations, the telemetry module wirelessly relays the CAN bus data and outputs it on the receiving end to the same wirebound USB-CAN analyzer in the support vehicles.

Python-can is a library providing scripts for the USB-CAN analyzer. This allows us to log the real-time data into a logfile for posterity and playback later on. The playback script is also already provided by python-can.

The message data is decoded by a monitoring script `can-monitor.py` either in real-time or after a race day. It outputs CSV files with the decoded data, which can be used directly in the dashboard application (pandas likes CSV) or for strategy decisions.

### Links

- [https://python-can.readthedocs.io/en/stable/listeners.html](https://python-can.readthedocs.io/en/stable/listeners.html)
- [https://python-can.readthedocs.io/en/stable/scripts.html#can-logger](https://python-can.readthedocs.io/en/stable/scripts.html#can-logger)