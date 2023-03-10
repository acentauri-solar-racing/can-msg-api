import argparse

from db.db_service import DbService


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

    parser.add_argument(
        "-r",
        "--refresh",
        help=r"Drop DB tables and reinstantiate",
        action="store_true",
    )


if __name__ == "__main__":
    # read args from CLI
    parser = argparse.ArgumentParser(description="Manage database connection")
    _create_base_argument_parser(parser)
    results, unknown_args = parser.parse_known_args()

    if results.refresh:
        db: DbService = DbService()
        db.refresh()
