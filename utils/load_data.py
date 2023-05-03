from db.models import *
from db.db_service import DbService
from pandas import DataFrame
import pandas as pd
from typing import Tuple


def load_icu_heartbeat(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_icu_heartbeat(
        db_serv.query(IcuHeartbeat, n_entries)
    )


def load_bms_heartbeat(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_bms_heartbeat(
        db_serv.query(BmsHeartbeat, n_entries)
    )


def load_stwheel_heartbeat(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_stwheel_heartbeat(
        db_serv.query(StwheelHeartbeat, n_entries)
    )


def load_vcu_heartbeat(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_vcu_heartbeat(
        db_serv.query(StwheelHeartbeat, n_entries)
    )


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


def load_bms_power(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_bms_power(
        db_serv.query(BmsPackVoltageCurrent, n_entries),
    )


def load_bms_soc(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_bms_soc(
        db_serv.query(BmsPackSoc, n_entries),
    )


def load_mppt_status0(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_mppt_status(
        db_serv.query(BmsPackSoc, n_entries),
    )


def load_mppt_status1(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_mppt_status(
        db_serv.query(BmsPackSoc, n_entries),
    )


def load_mppt_status2(db_serv: DbService, n_entries) -> DataFrame:
    return preprocess_mppt_status(
        db_serv.query(BmsPackSoc, n_entries),
    )


def preprocess_icu_heartbeat(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # rescale to km/h
    df['speed'] *= 3.6
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_bms_heartbeat(df: DataFrame) -> DataFrame:
    """prepare data frame"""
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_vcu_heartbeat(df: DataFrame) -> DataFrame:
    """prepare data frame"""
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


def preprocess_bms_soc(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_mppt_status(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df


def preprocess_stwheel_heartbeat(df: DataFrame) -> DataFrame:
    """prepare data frame for plotting"""
    # parse timestamp
    df['timestamp_dt'] = pd.to_datetime(
        df['timestamp'], unit='s', origin="unix", utc=True)
    return df
