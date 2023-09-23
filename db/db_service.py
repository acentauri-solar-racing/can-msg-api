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


class DbService:

    def __init__(self):
        self.engine: Engine = create_engine(self.conn_string())
        self.session: Session = self.create_session()

    def conn_string(self) -> str:
        env = dotenv_values("db/.env")

        return "mysql+pymysql://%s:%s@%s/%s" % (
            env["DB_USER"],
            env["DB_PASSWORD"],
            env["DB_HOST"],
            env["DB_NAME"],
        )

    def create_session(self) -> Session:
        Base.metadata.create_all(bind=self.engine)

        Session = sessionmaker(bind=self.engine)
        return Session()

    def refresh(self) -> None:
        Base.metadata.reflect(bind=self.engine)
        Base.metadata.drop_all(bind=self.engine)

        Base.metadata.create_all(bind=self.engine)

        self.session.commit()

    def add_entry(self, can_id: int, unpacked_data: tuple, timestamp: float, commit_session: bool = True) -> None:
        model = ddl_models[can_id]
        entry: model = model(unpacked_data, timestamp)

        self.session.add(entry)

        # commit can also be done manually by calling the function "commit_session()", see below
        if commit_session:
            self.session.commit()

    def commit_session(self):
        self.session.commit()

    def query_latest(self, orm_model, num_entries: int) -> DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(
                sql=self.session.query(orm_model).order_by(
                    orm_model.timestamp.desc()).limit(num_entries).statement,
                con=conn,
            )

    def latest(self, orm_model):
        with self.engine.connect() as conn:
            return self.session.query(orm_model).order_by(
                orm_model.timestamp.desc()).first()

    def query(self, orm_model: declarative_base, start_time : datetime.datetime, end_time : datetime.datetime):

        results = self.session.query(orm_model).filter(
            and_(
                orm_model.timestamp >= start_time,
                orm_model.timestamp <= end_time
            )
        ).all()

        print("loaded the following lines")
        # Process the results
        for row in results:
        # Access the columns of the selected rows
            print(row.id, row.timestamp, row.column1, row.column2)  # Replace column1 and column2 with actual column names

        # Close the session when done
        self.session.close()