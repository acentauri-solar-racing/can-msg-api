"""Read environment variables and construct the connection string for MySQL DB"""
import os
import pandas as pd

# import all DDL classes
from db.models import *

from dotenv import dotenv_values

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from pandas import DataFrame


class DbService:
    session_entries: int = 0
    rate_limit: bool = False

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

    def add_entry(self, can_id: int, unpacked_data: tuple, timestamp: float) -> None:
        model = ddl_models[can_id]
        entry: model = model(unpacked_data, timestamp)

        self.session.add(entry)

        if self.rate_limit:
            self.session_entries += 1

        # prevent overloading of DB by writing to DB only when collected 20 entries
        if self.rate_limit and self.session_entries > 20:
            self.session.commit()
            self.session_entries = 0
        else:
            self.session.commit()

    def query(self, orm_model, num_entries: int) -> DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql_query(
                sql=self.session.query(orm_model).statement,
                con=conn,
            )
