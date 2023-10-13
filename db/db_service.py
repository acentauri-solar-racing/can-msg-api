"""Read environment variables and construct the connection string for MySQL DB"""
import datetime
import os
import pandas as pd

# import all DDL classes
from db.models import *

from dotenv import dotenv_values

from sqlalchemy import create_engine, Engine, text, and_
from sqlalchemy.orm import sessionmaker, Session
from pandas import DataFrame

import tkinter as tk
from tkinter import filedialog


class DbService:
    """ Class to handle all DB related operations """
    def __init__(self, out_of_folder:bool=False):
        self.engine: Engine = create_engine(self.conn_string(out_of_folder=out_of_folder))
        self.session: Session = self.create_session()

    def conn_string(self, out_of_folder:bool=False) -> str:
        """ Read the environment variables and construct the connection string for MySQL DB"""
        # Special case for Strategy when running on a different folder
        if out_of_folder:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.lift()  # Bring the window to the front
            root.attributes('-topmost', True)  # Keep the window on top of all others

            # Get the directory of the current script
            current_directory = os.path.dirname(os.path.abspath(__file__))

            chosen_file = filedialog.askopenfilename(title='Select the env file', 
                                                    filetypes=[("ENV files", "*.env")], 
                                                    initialdir=current_directory)

            if chosen_file:
                env = dotenv_values(chosen_file)
                print(f"Data read from {chosen_file}.")
            else:
                print("No directory chosen. Data not read.")

        # Normal case
        else:
            env = dotenv_values("db/.env")

        return "mysql+pymysql://%s:%s@%s/%s" % (
            env["DB_USER"],
            env["DB_PASSWORD"],
            env["DB_HOST"],
            env["DB_NAME"],
        )

    def create_session(self) -> Session:
        """ Create a session to the DB"""
        Base.metadata.create_all(bind=self.engine)

        Session = sessionmaker(bind=self.engine)
        return Session()

    def refresh(self) -> None:
        """ Refresh the DB by dropping all tables and creating them again"""
        Base.metadata.reflect(bind=self.engine)
        Base.metadata.drop_all(bind=self.engine)

        Base.metadata.create_all(bind=self.engine)

        self.session.commit()

    def add_entry(self, can_id: int, unpacked_data: tuple, timestamp: float, commit_session: bool = True) -> None:
        """ Add an entry to the DB

            Inputs:
                can_id (int): The CAN ID of the message
                unpacked_data (tuple): The unpacked data of the message
                timestamp (float): The timestamp of the message
                commit_session (bool): Whether to commit the session or not (default: True)"""
        
        model = ddl_models[can_id]
        entry: model = model(unpacked_data, timestamp)

        self.session.add(entry)

        # commit can also be done manually by calling the function "commit_session()", see below
        if commit_session:
            self.session.commit()

    def commit_session(self):
        """ Commit the session to the DB"""
        self.session.commit()

    def query_latest(self, orm_model: declarative_base, num_entries: int) -> DataFrame:
        """ Query the latest entries from the DB

            Inputs:
                orm_model (declarative_base): The ORM model to be queried
                num_entries (int): The number of entries to be queried

            Returns:
                DataFrame: The queried entries"""
        
        with self.engine.connect() as conn:
            return pd.read_sql_query(
                sql=self.session.query(orm_model).order_by(
                    orm_model.timestamp.desc()).limit(num_entries).statement,
                con=conn,
            )

    def latest(self, orm_model: declarative_base):
        """ Query the latest entry from the DB

            Inputs:
                orm_model (declarative_base): The ORM model to be queried

            Returns:
                DataFrame: The queried entry"""
        
        with self.engine.connect() as conn:
            return self.session.query(orm_model).order_by(
                orm_model.timestamp.desc()).first()

    def query(self, orm_model: declarative_base, start_time: datetime.datetime, end_time: datetime.datetime):
        """ Query the entries from the DB between two timestamps

            Inputs:
                orm_model (declarative_base): The ORM model to be queried
                start_time (datetime.datetime): The start timestamp
                end_time (datetime.datetime): The end timestamp

            Returns:
                DataFrame: The queried entries"""
        
        with self.engine.connect() as conn:
            return pd.read_sql_query(sql=self.session.query(orm_model)
                                     .filter(and_(orm_model.timestamp >= start_time.timestamp(),
                                                  orm_model.timestamp <= end_time.timestamp()))
                                     .order_by(orm_model.timestamp.desc()).statement,
                                     con=conn)
