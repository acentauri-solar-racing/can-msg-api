import datetime
from typing import Union
from pandas import DataFrame
import pandas as pd
from db.db_service import DbService


class Row:
    title: str = ''
    min: str = ''
    max: str = ''
    mean: str = ''
    last: str = ''

    # Returns a table row in the format that dash expects
    def refresh(self, timespan_displayed: int) -> {}:
        return {'': self.title,
                timespan_displayed.__str__() + '\' Min': self.min,
                timespan_displayed.__str__() + '\' Max': self.max,
                timespan_displayed.__str__() + '\' Mean': self.mean,
                timespan_displayed.__str__() + '\' Last': self.last}


class DataRow(Row):
    df_name: str
    df_col: str  # Column name in the dataframe
    numberFormat: str  # number format of the displayed values
    selected: bool  # indicates whether a row was selected

    def __init__(self, title: str, df_name: str, df_col: str, numberFormat: str = '3.1f', selected: bool = False):
        self.title = title
        self.df_name = df_name
        self.df_col = df_col
        self.numberFormat = numberFormat
        self.selected = selected

    def refresh(self, timespan_displayed: int) -> {}:
        print("Unexpected: function 'refresh' of 'DataRow' is not implemented by the user")
        return {}


class TableDataFrame:
    df: Union[DataFrame, None] = None
    max_timespan: datetime.timedelta  # Maximum time between the first and the last entry. This is only checked when using the append_from_db function

    def _refresh(self) -> Union[DataFrame, None]:
        return None

    def refresh(self) -> None:
        # This function should be called for processing the Data in the DataFrame without loading from the database.
        # Example use case: Calculate new entries for battery power. For this, the dataframes for battery current and
        # battery voltage are needed, but no access to the database is involved.
        new_df = self._refresh()
        if new_df is not None:
            self.df = new_df

    def _load_from_db(db_service: DbService, start_time: datetime.datetime, end_time: datetime.datetime) -> Union[
        DataFrame, None]:
        print("Unexpected: function '_load_from_db' of 'TableDataFrame' is not implemented by the user")
        return None

    def load_from_db(self, db_service: DbService, start_time: datetime.datetime, end_time: datetime.datetime) -> None:
        self.df = self._load_from_db(db_service, start_time, end_time)

    def _append_from_db(db_service: DbService, n_entries: int) -> Union[DataFrame, None]:
        print("Unexpected: function '_append_from_db' of 'TableDataFrame' is not implemented by the user")
        return None

    def append_from_db(self, db_service: DbService, n_entries: int) -> None:
        new_entries = self._append_from_db(db_service, n_entries)

        if new_entries is not None:
            if self.df is None or self.df.empty:
                self.df = new_entries
            else:
                last_timestamp_old = self.df['timestamp_dt'][0]
                last_timestamp_new = new_entries['timestamp_dt'][0]

                # Only append new timestamps
                new_entries = new_entries.loc[new_entries['timestamp_dt'] > last_timestamp_old]

                # Delete entries that are older than the max timespan
                self.df = self.df.loc[self.df['timestamp_dt'] + self.max_timespan > last_timestamp_new]
                self.df = pd.concat([new_entries, self.df], ignore_index=True)  # Add the latest values to the dataframe

    def __init__(self, max_timespan = datetime.timedelta(minutes=5), refresh=(lambda: None), load_from_db=(lambda db_service, start_time, end_time: None),
                 append_from_db=(lambda db_service, n_entries: None)):
        super().__init__()
        self.max_timespan = max_timespan
        self._refresh = refresh
        self._load_from_db = load_from_db
        self._append_from_db = append_from_db
