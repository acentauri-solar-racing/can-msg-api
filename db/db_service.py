"""Read environment variables and construct the connection string for MySQL DB"""
import datetime
import os
import pandas as pd

# import all DDL classes
from db.models import *

from dotenv import dotenv_values

from sqlalchemy import create_engine, Engine
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

    def query(self, orm_model, num_entries: int) -> DataFrame:
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

    def queryTime(self, start : datetime.datetime, end : datetime.datetime):
        start = start
        end = end.timestamp()

        print(start)