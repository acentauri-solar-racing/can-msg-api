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
        vin1: float = noise(-12., 0.5) * 1000  # unit mV
        iin1: float = noise(1., 0.1) * 1000  # unit mV
        vout1: float = noise(-12., 0.5) * 1000  # unit mV
        iout1: float = noise(1., 0.1) * 1000  # unit mV
        vin2: float = noise(-12., 0.5) * 1000  # unit mV
        iin2: float = noise(1., 0.1) * 1000  # unit mV
        vout2: float = noise(-12., 0.5) * 1000  # unit mV
        iout2: float = noise(1., 0.1) * 1000  # unit mV
        vin3: float = noise(-12., 0.5) * 1000  # unit mV
        iin3: float = noise(1., 0.1) * 1000  # unit mV
        vout3: float = noise(-12., 0.5) * 1000  # unit mV
        iout3: float = noise(1., 0.1) * 1000  # unit mV

        db_serv.add_entry(512, (vin1, iin1, vout1, iout1),
                          timestamp + i)  # MpptPowerMeas0
        db_serv.add_entry(528, (vin2, iin2, vout2, iout2),
                          timestamp + i)  # MpptPowerMeas1
        db_serv.add_entry(544, (vin3, iin3, vout3, iout3),
                          timestamp + i)  # MpptPowerMeas2


def gen_mppt_stat(db_serv: DbService(), num_entries: int):
    mode: int = 0
    fault: int = 0
    enabled: int = 1
    ambient_temp: int = int(noise(32, 5))
    heatsink_temp: int = int(noise(35, 5))

    db_serv.add_entry(513, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp+300)  # MpptStatus0
    db_serv.add_entry(529, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp+300)  # MpptStatus0v
    db_serv.add_entry(545, (mode, fault, enabled, ambient_temp, heatsink_temp),
                      timestamp+300)  # MpptStatus0


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
        soc_percent: float = noise(130., 5)

        db_serv.add_entry(
            1780, (soc_ah, soc_percent), timestamp + i)


def gen_bms_vi(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackVoltageCurrent
        battery_voltage: float = noise(120000., 5000)
        battery_current: float = noise(-500., 40)

        db_serv.add_entry(
            1786, (battery_voltage, battery_current), timestamp + i)


def gen_bms_soc(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        soc_ah: float = noise(420., 5)
        soc_percent: float = noise(155., 5)

        db_serv.add_entry(
            1780, (soc_ah, soc_percent), timestamp + i)


def gen_icu_heartbeat(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        speed: float = noise(80., 1)
        states: float = noise(100., 5)

        db_serv.add_entry(
            336, (speed, states), timestamp + i+300)
        

def gen_icu_error(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        id: float = 11
        message: float = 0

        db_serv.add_entry(
            272, (id, message), timestamp + i)
        
def gen_vcu_error(db_serv: DbService(), num_entries: int):
    for i in range(num_entries):
        # BmsPackSoc
        id: float = 12
        message: float = 3

        db_serv.add_entry(
            273, (id, message), timestamp + i+1)

def main() -> None:
    print("Seeding fake data")
    db_serv: DbService = DbService()

    gen_mppt_pow(db_serv, 100)
    gen_mppt_stat(db_serv, 100)
    gen_bms_cmu(db_serv, 100)
    gen_bms_vi(db_serv, 100)
    gen_bms_soc(db_serv, 100)
    gen_bms_pack(db_serv, 100)
    gen_icu_heartbeat(db_serv, 100)
    gen_icu_error(db_serv, 100)
    gen_vcu_error(db_serv, 100)
    print("done")

if __name__ == "__main__":
    main()
