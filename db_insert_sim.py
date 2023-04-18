# purpose of this file is to dump a bunch of fake data in the database for developing the dashboard
import numpy as np
import time

from db.db_service import DbService
from db.models import *
from utils import helpers
from typing import Tuple


def noise(mean: float, stddev) -> float:
    return float(np.random.normal(mean, stddev, 1))


def gen_mppt_pow(db_serv: DbService(), num_entries: int):
    timestamp: float = time.time()
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


if __name__ == "__main__":
    print("Continuously inserting fake data")
    db_serv: DbService = DbService()

    while True:
        gen_mppt_pow(db_serv, 2)
        time.sleep(0.25)

    print("done")
