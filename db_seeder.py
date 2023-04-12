# purpose of this file is to dump a bunch of fake data in the database for developing the dashboard
import numpy as np
import time

from db.db_service import DbService
from db.models import *
from utils import helpers
from typing import Tuple

timestamp: float = time.time()


def noise(mean: float, stddev) -> float:
    return float(np.random.normal(mean, stddev, 1))


def gen_mppt_pow(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        vin: float = noise(12., 0.5) * 1000  # unit mV
        iin: float = noise(1., 0.1) * 1000  # unit mV
        vout: float = noise(12., 0.5) * 1000  # unit mV
        iout: float = noise(1., 0.1) * 1000  # unit mV

        db_serv.add_entry(512, (vin, iin, vout, iout),
                          timestamp + i)  # MpptPowerMeas0
        db_serv.add_entry(528, (vin, iin, vout, iout),
                          timestamp + i)  # MpptPowerMeas1
        db_serv.add_entry(544, (vin, iin, vout, iout),
                          timestamp + i)  # MpptPowerMeas2


def gen_mppt_stat(db_serv: DbService(), num_entries: int):
    mode: int = 0
    fault: int = 0
    enabled: int = 1
    ambient_temp: int = int(noise(32, 5))
    heatsink_temp: int = int(noise(35, 5))

    db_serv.add_entry(513, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp)  # MpptStatus0
    db_serv.add_entry(529, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp)  # MpptStatus0v
    db_serv.add_entry(545, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp)  # MpptStatus0


def gen_bms_cmu(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsCmu1Stat
        serial_num: int = 42069
        pcb_temp: int = noise(42., 5) * 10
        cell_temp: int = noise(42., 5) * 10

        db_serv.add_entry(
            1537, (serial_num, pcb_temp, cell_temp), timestamp + i)

        #BmsCmu1Cells1 & BmsCmu1Cells2
        cell_0_volt: int = noise(3.7, 0.1) * 1000
        cell_1_volt: int = noise(3.7, 0.1) * 1000
        cell_2_volt: int = noise(3.7, 0.1) * 1000
        cell_3_volt: int = noise(3.7, 0.1) * 1000
        db_serv.add_entry(1538, (cell_0_volt, cell_1_volt,
                          cell_2_volt, cell_3_volt), timestamp + i)
        db_serv.add_entry(1539, (cell_0_volt, cell_1_volt,
                          cell_2_volt, cell_3_volt), timestamp + i)


def gen_bms_pack(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        soc_ah: float = noise(30, 5)
        soc_percent: float = noise(42., 5)

        db_serv.add_entry(
            1780, (soc_ah, soc_percent), timestamp + i)


def gen_bms_vi(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackVoltageCurrent
        battery_voltage: float = noise(120., 35)
        battery_current: float = noise(1., 0.2)

        db_serv.add_entry(
            1786, (battery_voltage, battery_current), timestamp + i)


def gen_bms_soc(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        soc_ah: float = noise(420., 5)
        soc_percent: float = noise(69., 5)

        db_serv.add_entry(
            1780, (soc_ah, soc_percent), timestamp + i)


if __name__ == "__main__":
    print("Seeding fake data")
    db_serv: DbService = DbService()

    gen_mppt_pow(db_serv, 100)
    gen_mppt_stat(db_serv, 100)
    gen_bms_cmu(db_serv, 100)
    gen_bms_vi(db_serv, 100)
    gen_bms_soc(db_serv, 100)
    gen_bms_pack(db_serv, 100)
    print("done")
