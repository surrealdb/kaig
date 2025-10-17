from .db import init_db


def main() -> None:
    import sys

    file = sys.argv[1]

    db = init_db(True)
