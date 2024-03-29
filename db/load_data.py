import datetime

from db.models import *
from db.db_service import DbService
from pandas import DataFrame
import pandas as pd
from typing import Tuple, Union

### Errors #############################################################################################################
def append_error_data(db_serv: DbService, orm_model: any, n_entries: int) -> DataFrame:
    return preprocess_generic(db_serv.query_latest(orm_model, n_entries))



### General Car State  #################################################################################################
def refresh_motorPow() -> Union[DataFrame, None]:
    return None

def append_speed_data(db_serv: DbService, n_entries: int) -> Union[DataFrame, None]:
    return preprocess_speed(
        db_serv.query_latest(IcuHeartbeat, n_entries)
    )

def load_speed_data(db_serv: DbService, start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int):
    return preprocess_speed(db_serv.query(IcuHeartbeat,start_time,end_time, loading_interval))

def append_driverResponse(db_serv: DbService, n_entries: int) -> Union[DataFrame, None]:
    return preprocess_driverResponse(db_serv.query_latest(StwheelHeartbeat,n_entries))

### MPPTs ##############################################################################################################

def refresh_mpptPow() -> Union[DataFrame, None]:
    return None

def load_mppt_status_data_latest(db_serv: DbService) -> Union[Tuple[DataFrame, DataFrame, DataFrame, DataFrame], None]:
    return (
        preprocess_generic(db_serv.latest(MpptStatus0)),
        preprocess_generic(db_serv.latest(MpptStatus1)),
        preprocess_generic(db_serv.latest(MpptStatus2)),
        preprocess_generic(db_serv.latest(MpptStatus3))
    )

def append_mppt_status0_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query_latest(MpptStatus0, n_entries))

def append_mppt_status1_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query_latest(MpptStatus1, n_entries))

def append_mppt_status2_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query_latest(MpptStatus2, n_entries))

def append_mppt_status3_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query_latest(MpptStatus3, n_entries))

def load_mppt_status0_data(db_serv: DbService, start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query(MpptStatus0, start_time,end_time, loading_interval))

def load_mppt_status1_data(db_serv: DbService, start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query(MpptStatus1, start_time,end_time, loading_interval))

def load_mppt_status2_data(db_serv: DbService, start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query(MpptStatus2, start_time,end_time, loading_interval))

def load_mppt_status3_data(db_serv: DbService, start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_generic(db_serv.query(MpptStatus3, start_time,end_time, loading_interval))

def append_mppt_power0_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query_latest(MpptPowerMeas0, n_entries))

def load_mppt_power0_data(db_serv: DbService,  start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query(MpptPowerMeas0, start_time,end_time, loading_interval))

def append_mppt_power1_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query_latest(MpptPowerMeas1, n_entries))

def load_mppt_power1_data(db_serv: DbService,  start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query(MpptPowerMeas1, start_time,end_time, loading_interval))

def append_mppt_power2_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query_latest(MpptPowerMeas2, n_entries))

def load_mppt_power2_data(db_serv: DbService,  start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query(MpptPowerMeas2, start_time,end_time, loading_interval))

def append_mppt_power3_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query_latest(MpptPowerMeas3, n_entries))

def load_mppt_power3_data(db_serv: DbService,  start_time : datetime.datetime, end_time : datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_mppt_power(db_serv.query(MpptPowerMeas3, start_time,end_time, loading_interval))



### BMS ################################################################################################################
def append_bms_pack_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_bms_pack_data(
        db_serv.query_latest(BmsPackVoltageCurrent, n_entries),
    )

def load_bms_pack_data(db_serv: DbService, start_time :datetime.datetime, end_time: datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_bms_pack_data(
        db_serv.query(BmsPackVoltageCurrent, start_time, end_time, loading_interval),
    )

def append_bms_cell_voltage_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_generic(
        db_serv.query_latest((BmsMinMaxCellVoltage), n_entries)
    )

def load_bms_cell_voltage_data(db_serv: DbService, start_time :datetime.datetime, end_time: datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_generic(
        db_serv.query(BmsMinMaxCellVoltage, start_time, end_time, loading_interval),
    )

def append_bms_cell_temp_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_bms_cell_temp(
        db_serv.query_latest(BmsMinMaxCellTemp, n_entries)
    )

def load_bms_cell_temp_data(db_serv: DbService, start_time :datetime.datetime, end_time: datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_bms_cell_temp(
        db_serv.query(BmsMinMaxCellTemp, start_time, end_time, loading_interval),
    )

def append_bms_soc_data(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_bms_soc_data(
        db_serv.query_latest(BmsPackSoc, n_entries),
    )

def load_bms_soc_data(db_serv: DbService, start_time :datetime.datetime, end_time: datetime.datetime, loading_interval: int) -> Union[DataFrame, None]:
    return preprocess_bms_soc_data(
        db_serv.query(BmsPackSoc, start_time, end_time, loading_interval),
    )



### Preprocessing ######################################################################################################

def preprocess_generic(df: DataFrame) -> DataFrame:

    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)

    return df

def preprocess_speed(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6

    return preprocess_generic(df)


def preprocess_driverResponse(df: DataFrame) -> DataFrame:

    # Button encoding must be kept up-to-date
    df['button_yes'] = df['buttons_status'] & (1 << 4) > 1
    df['button_no'] = df['buttons_status'] & (1 << 5) > 1
    df['button_unclear'] = df['buttons_status'] & (1 << 6) > 1

    return preprocess_generic(df)

def preprocess_mppt_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages and currents according to communication protocol!
    df['v_out'] *= 1e-2 # [V]
    df['i_out'] *= 0.5 # [mA]
    df['v_in'] *= 1e-2 # [V]
    df['i_in'] *= 0.5 # [mA]

    # P = UI
    df['p_out'] = df['v_out'] * df['i_out'] * 1e-3
    df['p_in'] = df['v_in'] * df['i_in'] * 1e-3

    return preprocess_generic(df)

def preprocess_bms_cell_temp(df: DataFrame) -> DataFrame:
    df['max_cell_temp'] *= 0.1 # [°C]
    df['min_cell_temp'] *= 0.1 # [°C]

    return preprocess_generic(df)

def preprocess_bms_pack_data(df: DataFrame) -> DataFrame:

    """prepare data frame for plotting"""
    df['battery_voltage'] *= 1e-3    # Rescale
    df['battery_current'] *= -1

    # P = UI (current is given in mV -> multiply with 1e-3 to get W)
    df['battery_power'] = df['battery_voltage'] * df['battery_current'] * 1e-3

    return preprocess_generic(df)

def preprocess_bms_soc_data(df: DataFrame) -> DataFrame:

    df['soc_percent'] = df['soc_percent'] * 100  # Correct scaling

    return preprocess_generic(df)