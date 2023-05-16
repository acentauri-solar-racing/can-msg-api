from db.models import *
from db.db_service import DbService
from pandas import DataFrame
import pandas as pd
from typing import Tuple


#for speed calculation
def load_icu_heartbeat(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_icu_heartbeat(
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
def load_mppt_power(db_serv: DbService, n_entries) -> Tuple[DataFrame]:
    return (preprocess_mppt_power(
        db_serv.query(MpptPowerMeas0, n_entries),
    ),
        preprocess_mppt_power(
        db_serv.query(MpptPowerMeas1, n_entries)
    ),
        preprocess_mppt_power(
        db_serv.query(MpptPowerMeas2, n_entries)
    ))

# for power calculations
def load_bms_power(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_bms_power(
        db_serv.query(BmsPackVoltageCurrent, n_entries),
    )

# for state of charge graph
def load_bms_soc(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_generic(
        db_serv.query(BmsPackSoc, n_entries),
    )
    
# for cell graph
def load_cmu_data(db_serv: DbService(), n_entries):
    (df1, df2) = preprocess_cmu(
        db_serv.query(BmsCmu1Cells1, n_entries),
        db_serv.query(BmsCmu1Cells2, n_entries)
    )
    return (db_serv.latest(BmsCmu1Stat), df1, df2)


def preprocess_generic(df: DataFrame) -> DataFrame:
    """prepare data frame for heartbeat tracking"""
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df

def preprocess_icu_heartbeat(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_mppt_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages since given in mV. Only relevant quantities are adjusted!
    df['v_out'] *= 1e-3
    df['i_out'] *= 1e-3
    df['v_in'] *= 1e-3
    df['i_in'] *= 1e-3

    # P = UI
    df['p_out'] = df['v_out'] * df['i_out']
    df['p_in'] = df['v_in'] * df['i_in']

    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_bms_power(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale voltages since given in mV
    df['battery_voltage'] *= 1e-3
    df['battery_current'] *= 1e-3

    # P = UI
    df['p_out'] = df['battery_voltage'] * df['battery_current']

    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_cmu(df1: DataFrame, df2: DataFrame) -> Tuple[DataFrame,DataFrame]:
    # convert from mV to V
    df1['cell_0_volt'] *= 1e-3
    df1['cell_1_volt'] *= 1e-3
    df1['cell_2_volt'] *= 1e-3
    df1['cell_3_volt'] *= 1e-3

    df2['cell_4_volt'] *= 1e-3
    df2['cell_5_volt'] *= 1e-3
    df2['cell_6_volt'] *= 1e-3
    df2['cell_7_volt'] *= 1e-3

    # parse timestamps
    df1['timestamp_dt'] = pd.to_datetime(
        df1['timestamp'], unit='s', origin="unix", utc=True)
    df2['timestamp_dt'] = pd.to_datetime(
        df2['timestamp'], unit='s', origin="unix", utc=True)
    return (df1, df2)
