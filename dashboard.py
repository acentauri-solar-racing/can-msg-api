from db.models import *
from db.db_service import DbService

from pandas import DataFrame


def main():
    db: DbService = DbService()
    df: DataFrame = db.query(MpptPowerMeas2, 10)
    print(df)


if __name__ == "__main__":
    print(":::::: Starting Dashboard:::::::\n")
    main()
    print("\nDone")