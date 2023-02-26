

import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey, Column, Integer, Double


class Temperature(Base):
    __tablename__ = "Temperature_Measurements"

    id = Column("id", Integer, primary_key=True)
    temp1 = Column("Temp1", Double)
    temp2 = Column("Temp2", Double)
    temp3 = Column("Temp3", Double)

    def __init__(self, id, temp1, temp2, temp3):
        self.id = id
        self.temp1 = temp1
        self.temp2 = temp2
        self.temp3 = temp3

    def __repr__(self):
        return f"({self.id}), ({self.temp1}, {self.temp2}, {self.temp3})"
