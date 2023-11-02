# This file contains the layout for the data visualisation used in 'overview' and 'analyzer'

from db.load_data import *
from frontend import Table
from frontend.Table import DataRow


def get_nearest_index(df: DataFrame, current_idx: int, target_timestamp: float) -> int:
    ### returns the index of the given dataframe with the nearest timestamp to the target timestamp. This function
    # assumes that the entries in the dataframe are ordered by timestamp (newest to oldest)###
    idx_max = len(df.index)
    current_timestamp = df['timestamp'].values[current_idx]

    # Move to next timestamp, if it is closer
    while current_timestamp > target_timestamp and current_idx < idx_max - 1:

        new_timestamp = df['timestamp'].values[current_idx + 1]

        if abs(new_timestamp - target_timestamp) < (current_timestamp - target_timestamp):
            current_idx += 1
            current_timestamp = new_timestamp
        else:
            break

    return current_idx


def getMinMaxMeanLast(df: Union[DataFrame, None], col: str, numberFormat: str) -> Tuple[str, str, str, str]:
    # Returns the minimum, maximum, mean and last entry of a given column in a Pandas.DataFrame as a string
    if df is None or df.empty:
        return 'No Data', 'No Data', 'No Data', 'No Data'
    else:
        return (('{:' + numberFormat + '}').format(df[col].min()),
                ('{:' + numberFormat + '}').format(df[col].max()),
                ('{:' + numberFormat + '}').format(df[col].mean()),
                ('{:' + numberFormat + '}').format(df[col][0]))


class DataSection:
    max_time_offset: datetime.timedelta  # Maximum time offset between two measurements that are added together
    timespan_loaded: datetime.timedelta  # (maximum) Time between the first and last displayed entry.
    table_data = {}
    table_layout = []

    def __init__(self, timespan_loaded: datetime.timedelta, max_time_offset: datetime.timedelta):
        self.timespan_loaded = timespan_loaded
        self.max_time_offset = max_time_offset

        self.table_data = {
            'df_speed': Table.TableDataFrame(append_from_db=append_speed_data, load_from_db=load_speed_data),
            'df_motorPow': Table.TableDataFrame(refresh=refresh_motorPow),
            'df_mpptPow': Table.TableDataFrame(),
            'df_mpptPow0': Table.TableDataFrame(append_from_db=append_mppt_power0_data,
                                                load_from_db=load_mppt_power0_data),
            'df_mpptPow1': Table.TableDataFrame(append_from_db=append_mppt_power1_data,
                                                load_from_db=load_mppt_power1_data),
            'df_mpptPow2': Table.TableDataFrame(append_from_db=append_mppt_power2_data,
                                                load_from_db=load_mppt_power2_data),
            'df_mpptPow3': Table.TableDataFrame(append_from_db=append_mppt_power3_data,
                                                load_from_db=load_mppt_power3_data),
            'df_mpptStat0': Table.TableDataFrame(append_from_db=append_mppt_status0_data,
                                                 load_from_db=load_mppt_status0_data),
            'df_mpptStat1': Table.TableDataFrame(append_from_db=append_mppt_status1_data,
                                                 load_from_db=load_mppt_status1_data),
            'df_mpptStat2': Table.TableDataFrame(append_from_db=append_mppt_status2_data,
                                                 load_from_db=load_mppt_status2_data),
            'df_mpptStat3': Table.TableDataFrame(append_from_db=append_mppt_status3_data,
                                                 load_from_db=load_mppt_status3_data),
            'df_bat_pack': Table.TableDataFrame(append_from_db=append_bms_pack_data, load_from_db=load_bms_pack_data),
            'df_soc': Table.TableDataFrame(append_from_db=append_bms_soc_data, load_from_db=load_bms_soc_data),
            'df_cellVolt': Table.TableDataFrame(append_from_db=append_bms_cell_voltage_data,
                                                load_from_db=load_bms_cell_voltage_data),
            'df_cellTemp': Table.TableDataFrame(append_from_db=append_bms_cell_temp_data,
                                                load_from_db=load_bms_cell_temp_data)}

        self.table_layout = [
            Table.DataRow(title='Speed [km/h]', df_name='df_speed', df_col='speed', numberFormat='3.1f'),
            Table.DataRow(title='Motor Output Power [W]', df_name='df_motorPow', df_col='p_out',
                          numberFormat='3.1f'),
            Table.Row(),
            Table.DataRow(title='PV Output Power [W]', df_name='df_mpptPow', df_col='p_out',
                          numberFormat='3.1f'),
            Table.DataRow(title='PV String 0 Output Power [W]', df_name='df_mpptPow0', df_col='p_out',
                          numberFormat='3.1f'),
            Table.DataRow(title='PV String 1 Output Power [W]', df_name='df_mpptPow1', df_col='p_out',
                          numberFormat='3.1f'),
            Table.DataRow(title='PV String 2 Output Power [W]', df_name='df_mpptPow2', df_col='p_out',
                          numberFormat='3.1f'),
            Table.DataRow(title='PV String 3 Output Power [W]', df_name='df_mpptPow3', df_col='p_out',
                          numberFormat='3.1f'),
            Table.Row(),
            Table.DataRow(title='Battery Output Power [W]', df_name='df_bat_pack', df_col='battery_power',
                          numberFormat='3.1f'),
            Table.DataRow(title='Battery SOC [%]', df_name='df_soc', df_col='soc_percent',
                          numberFormat='3.1f'),
            Table.DataRow(title='Battery Voltage [V]', df_name='df_bat_pack', df_col='battery_voltage',
                          numberFormat='3.1f'),
            Table.DataRow(title='Battery Output Current [mA]', df_name='df_bat_pack', df_col='battery_current',
                          numberFormat='3.1f'),
            Table.DataRow(title='Battery Minimum Cell Voltage [mV]', df_name='df_cellVolt',
                          df_col='min_cell_voltage', numberFormat='3.1f'),
            Table.DataRow(title='Battery Maximum Cell Voltage [mV]', df_name='df_cellVolt',
                          df_col='max_cell_voltage', numberFormat='3.1f'),
            Table.Row(),
            Table.DataRow(title='Battery Minimum Cell Temperature [°C]', df_name='df_cellTemp',
                          df_col='min_cell_temp', numberFormat='3.1f'),
            Table.DataRow(title='Battery Maximum Cell Temperature [°C]', df_name='df_cellTemp',
                          df_col='max_cell_temp', numberFormat='3.1f'),
            Table.DataRow(title='MPPT String 0 Ambient Temperature [°C]', df_name='df_mpptStat0',
                          df_col='ambient_temp'),
            Table.DataRow(title='MPPT String 1 Ambient Temperature [°C]', df_name='df_mpptStat1',
                          df_col='ambient_temp'),
            Table.DataRow(title='MPPT String 2 Ambient Temperature [°C]', df_name='df_mpptStat2',
                          df_col='ambient_temp'),
            Table.DataRow(title='MPPT String 3 Ambient Temperature [°C]', df_name='df_mpptStat3',
                          df_col='ambient_temp'),
            Table.DataRow(title='MPPT String 0 Heatsink Temperature [°C]', df_name='df_mpptStat0',
                          df_col='heatsink_temp'),
            Table.DataRow(title='MPPT String 1 Heatsink Temperature [°C]', df_name='df_mpptStat1',
                          df_col='heatsink_temp'),
            Table.DataRow(title='MPPT String 2 Heatsink Temperature [°C]', df_name='df_mpptStat2',
                          df_col='heatsink_temp'),
            Table.DataRow(title='MPPT String 3 Heatsink Temperature [°C]', df_name='df_mpptStat3',
                          df_col='heatsink_temp')]

    def refresh(self, db_serv: DbService, timestamp_start: datetime.datetime, timestamp_end: datetime.datetime, loading_interval: int):
        ### Load new data into dataframes and update the view correspondingly ###

        # Load data that just can be pulled from the database
        for key in self.table_data:
            self.table_data[key].load_from_db(db_serv, timestamp_start, timestamp_end, loading_interval)

        # Load data that depends on other data. The order of those calls is important!
        self.table_data['df_mpptPow'].df = self.__get_mpptPow()  # Depends on individual mppt powers
        self.table_data[
            'df_motorPow'].df = self.__get_motorPow()  # Depends on total mppt power and battery output power

        # Refresh the table layout
        self.__refresh_layout()

    def refresh_append(self, db_serv: DbService, n_entries: int):
        ### Append the latest data to dataframe and update the view correspondingly ###

        # Load data that just can be pulled from the database
        for key in self.table_data:
            self.table_data[key].append_from_db(db_serv, n_entries, self.timespan_loaded)

        # Load data that depends on other data. The order of those calls is important!
        self.table_data['df_mpptPow'].df = self.__get_mpptPow()  # Depends on individual mppt powers
        self.table_data[
            'df_motorPow'].df = self.__get_motorPow()  # Depends on total mppt power and battery output power

        # Refresh the table layout
        self.__refresh_layout()

    def __get_motorPow(self) -> Union[DataFrame, None]:
        ### Calculate the total motor output power, based on the output power of battery and pv.
        # This function needs the elements to be chronologically ordered with the most recent entry at index 0 ###

        df_batPower = self.table_data['df_bat_pack'].df
        df_mpptPow = self.table_data['df_mpptPow'].df

        if df_batPower is None or df_batPower.empty or df_mpptPow is None or df_mpptPow.empty:
            print("Couldn't load motor output power")
            return self.table_data['df_motorPow'].df

        df_motorPow = pd.DataFrame(columns=['timestamp', 'p_out'])
        df_motorPow['timestamp'] = df_batPower['timestamp']

        bat_index = mppt_index = 0

        for i in range(len(df_motorPow.index)):
            timestamp = df_motorPow['timestamp'][i]

            # get index of the nearest timestamp to the one in the output dataframe
            bat_index = get_nearest_index(df_batPower, bat_index, timestamp)
            mppt_index = get_nearest_index(df_mpptPow, mppt_index, timestamp)

            timestamp_bat = df_batPower['timestamp'][bat_index]
            timestamp_mppt = df_mpptPow['timestamp'][mppt_index]

            # Calculate motor power if timestamps are close enough together
            if abs(timestamp - timestamp_bat) < self.max_time_offset.total_seconds() and abs(
                    timestamp - timestamp_mppt) < self.max_time_offset.total_seconds():
                df_motorPow.at[i, 'p_out'] = df_batPower['battery_power'][bat_index] + df_mpptPow['p_out'][mppt_index]

        return preprocess_generic(df_motorPow)


    def __get_mpptPow(self) -> Union[DataFrame, None]:
        ### Calculate the total power of the MPPTs, based on the individual measurements of the MPPTs
        # This function needs the elements to be chronologically ordered with the most recent entry at index 0 ###

        df_mppt0 = self.table_data['df_mpptPow0'].df
        df_mppt1 = self.table_data['df_mpptPow1'].df
        df_mppt2 = self.table_data['df_mpptPow2'].df
        df_mppt3 = self.table_data['df_mpptPow3'].df

        if df_mppt0 is None or df_mppt0.empty or df_mppt1 is None or df_mppt1.empty or df_mppt2 is None or df_mppt2.empty or df_mppt3 is None or df_mppt3.empty:
            print("Couldn't load total power of MPPTs")
            return self.table_data['df_mpptPow'].df

        df_mpptPow = pd.DataFrame(columns=['timestamp', 'p_out'])
        df_mpptPow['timestamp'] = df_mppt0['timestamp']

        mppt0_index = mppt1_index = mppt2_index = mppt3_index = 0

        for i in range(len(df_mpptPow.index)):
            timestamp = df_mpptPow['timestamp'].values[i]

            # get index of the nearest timestamp to the one in the output dataframe
            mppt0_index = get_nearest_index(df_mppt0, mppt0_index, timestamp)
            mppt1_index = get_nearest_index(df_mppt1, mppt1_index, timestamp)
            mppt2_index = get_nearest_index(df_mppt2, mppt2_index, timestamp)
            mppt3_index = get_nearest_index(df_mppt3, mppt3_index, timestamp)

            timestamp_mppt0 = df_mppt0['timestamp'].values[mppt0_index]
            timestamp_mppt1 = df_mppt1['timestamp'].values[mppt1_index]
            timestamp_mppt2 = df_mppt2['timestamp'].values[mppt2_index]
            timestamp_mppt3 = df_mppt3['timestamp'].values[mppt3_index]

            # Calculate Power, if timestamps are close enough together
            if abs(timestamp_mppt0 - timestamp) < self.max_time_offset.total_seconds() and abs(
                    timestamp_mppt1 - timestamp) < self.max_time_offset.total_seconds() and abs(
                timestamp_mppt2 - timestamp) < self.max_time_offset.total_seconds() and abs(
                timestamp_mppt3 - timestamp) < self.max_time_offset.total_seconds():
                df_mpptPow.at[i, 'p_out'] = df_mppt0['p_out'].values[mppt0_index] + df_mppt1['p_out'].values[
                    mppt1_index] + \
                                            df_mppt2['p_out'].values[mppt2_index] + df_mppt3['p_out'].values[
                                                mppt3_index]

        return preprocess_generic(df_mpptPow)

    def __refresh_layout(self):
        ### Update the table layout upon possible changes in the underlying data ###
        for row in self.table_layout:
            if type(row) is DataRow:
                row.timespan = self.timespan_loaded
                row.min, row.max, row.mean, row.last = getMinMaxMeanLast(self.table_data[row.df_name].df, row.df_col,
                                                                         row.numberFormat)
