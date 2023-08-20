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
                '{:d}\' Min'.format(timespan_displayed): self.min,
                '{:d}\' Max'.format(timespan_displayed): self.max,
                '{:d}\' Mean'.format(timespan_displayed): self.mean,
                'Last'.format(timespan_displayed): self.last}


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

    def _refresh(self) -> Union[DataFrame, None]:
        return None

    def refresh(self) -> None:
        new_df = self._refresh()
        if new_df is not None:
            self.df = new_df

    def _load_from_db(self, db_service: DbService, n_entries: int) -> Union[DataFrame, None]:
        print("Unexpected: function '_load_from_db' of 'TableDataFrame' is not implemented by the user")
        return None

    def load_from_db(self, db_service: DbService):
        new_row = self._load_from_db(db_service, 1)
        if self.df is not None or new_row is not None:
            self.df = pd.concat([new_row, self.df], ignore_index=True)  # Add newest value to the dataframe

    def __init__(self, refresh: (lambda: Union[None, DataFrame]) = (lambda: None),
                 load_from_db: (lambda db_service, n_entries: Union[None, DataFrame]) = (
                 lambda db_service, n_entries: None)):
        super().__init__()
        self._load_from_db = load_from_db
        self._refresh = refresh
