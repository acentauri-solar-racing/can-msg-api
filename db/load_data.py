from db.models import *
from db.db_service import DbService
from pandas import DataFrame
import pandas as pd
from typing import Tuple, Union


#for speed calculation
def load_speed(db_serv: DbService, n_entries) -> Union[DataFrame, None]:
    return preprocess_speed(
        db_serv.query(IcuHeartbeat, n_entries)
    )

#for activity calculation
def load_heartbeat(db_serv: DbService, orm_model: any) -> DataFrame:
    return preprocess_generic(db_serv.query(orm_model, 1))

#for error log
def load_errors(db_serv: DbService, orm_model: any, n_entries: int) -> DataFrame:
    return preprocess_generic(db_serv.query(orm_model, n_entries))

# for mppt status
def load_mppt_status_data(db_serv: DbService) -> Tuple[MpptStatus0, MpptStatus1, MpptStatus2]:
    return (
        db_serv.latest(MpptStatus0),
        db_serv.latest(MpptStatus1),
        db_serv.latest(MpptStatus2)
    )

# for power calculations and mppt graph
def load_mppt_power(db_serv: DbService, n_entries) -> Union[Tuple[DataFrame,DataFrame,DataFrame,DataFrame,DataFrame], None]:

    df_mppt0 = preprocess_mppt_power(db_serv.query(MpptPowerMeas0, n_entries))
    df_mppt1 = preprocess_mppt_power(db_serv.query(MpptPowerMeas1, n_entries))
    df_mppt2 = preprocess_mppt_power(db_serv.query(MpptPowerMeas2, n_entries))
    df_mppt3 = preprocess_mppt_power(db_serv.query(MpptPowerMeas3, n_entries))

    df_pv = DataFrame()
    df_pv['p_out'] = df_mppt0['p_out'] + df_mppt1['p_out'] + df_mppt2['p_out'] + df_mppt3['p_out']

    return (df_pv,df_mppt0,df_mppt1,df_mppt2,df_mppt3)


# for power calculations
def load_bms_pack_data(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_bms_pack_data(
        db_serv.query(BmsPackVoltageCurrent, n_entries),
    )

def load_bms_cell_voltage(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_generic(
        db_serv.query((BmsMinMaxCellVoltage), n_entries)
    )

def load_bms_cell_temp(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_generic(
        db_serv.query((BmsMinMaxCellTemp), n_entries)
    )

# for state of charge graph
def load_bms_soc(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_generic(
        db_serv.query(BmsPackSoc, n_entries),
    )


def preprocess_generic(df: DataFrame) -> DataFrame:

    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)

    return df

def preprocess_speed(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6

    return preprocess_generic(df)


def preprocess_mppt_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages since given in mV. Only relevant quantities are adjusted!
    df['v_out'] *= 1e-3
    # df['i_out'] *= 1e-3
    df['v_in'] *= 1e-3
    # df['i_in'] *= 1e-3

    # P = UI
    df['p_out'] = df['v_out'] * df['i_out'] * 1e-3
    df['p_in'] = df['v_in'] * df['i_in'] * 1e-3

    return preprocess_generic(df)


def preprocess_bms_pack_data(df: DataFrame) -> DataFrame:

    """prepare data frame for plotting"""
    df['battery_voltage'] *= 1e-3    # Rescale
    df['battery_current'] *= -1

    # P = UI (current is given in mV -> multiply with 1e-3 to get W)
    df['battery_power'] = df['battery_voltage'] * df['battery_current'] * 1e-3

    return preprocess_generic(df)


def refresh_motorPow() -> Union[DataFrame, None]:
    return None

def refresh_mpptPow() -> Union[DataFrame, None]:
    return None