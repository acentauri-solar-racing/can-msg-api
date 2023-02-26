"""Read environment variables and construct the connection string for MySQL DB"""
import os
import argparse


from models import Base, User
from log_decoder import Watcher

from dotenv import dotenv_values

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

    parser.add_argument(
        "-r",
        "--refresh",
        help=r"Drop DB tables and reinstantiate",
        action="store_true",
    )


class DbService:
    script_cwd: str = os.path.realpath(os.path.dirname(__file__))
    session_entries: int = 0

    def __init__(self):
        self.engine: Engine = create_engine(self.conn_string())
        self.session: Session = self.create_session()

    def conn_string(self) -> str:
        env = dotenv_values(self.script_cwd + "/.env")

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

    def add_entry(self, entry: object) -> None:
        self.session.add(entry)
        self.session_entries += 1

        # prevent overloading of DB by writing to DB only when collected 20 entries
        if session_entries > 20:
            self.commit()
            self.session_entries = 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage database connection")
    _create_base_argument_parser(parser)
    results, unknown_args = parser.parse_known_args()

    service = DbService()

    if results.refresh:
        service.refresh()



if __name__ == "__main__":
    main()