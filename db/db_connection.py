"""Read environment variables and construct the connection string for MySQL DB"""
import os

from dotenv import dotenv_values
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

script_cwd: str = os.path.realpath(os.path.dirname(__file__))


def conn_string() -> str:
    env = dotenv_values(script_cwd + "/.env")

    return "mysql+pymysql://%s:%s@%s/%s" % (
        env['DB_USER'],
        env['DB_PASSWORD'],
        env['DB_HOST'],
        env['DB_NAME'],
    )


Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}"


engine = create_engine(conn_string())
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

entry = User(name="joe mama")
session.add(entry)
session.commit()

result = session.query(User).all()
print(result)
