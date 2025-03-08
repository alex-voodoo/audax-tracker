"""
Database stuff
"""
import datetime
import os
import sqlite3
from pathlib import Path

from common.log import get_file_logger, LogTime

db_connection: sqlite3.Connection

db_logger = get_file_logger("db", "db.log")

DB_FILENAME = "tracking.db"


def apply_migrations(migrations_directory: Path) -> None:
    """Apply migrations prepared at the given path

    Enumerates all files with .txt extension at the given path, and tries to execute each one as a sequence of SQL
    statements, going through files in alphabetical order.

    Every file should contain one or more SQL statements separated with semicolon.
    """

    if not migrations_directory.exists() or not migrations_directory.is_dir():
        print("Directory {d} does not exist, not applying any migrations".format(d=migrations_directory))
        return

    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS \"migrations\" ("
              "\"name\" TEXT UNIQUE,"
              "PRIMARY KEY(\"name\")"
              ")")

    migration_filenames = sorted(filename for filename in os.listdir(migrations_directory) if filename.endswith(".txt"))
    for migration_filename in migration_filenames:
        skip = False
        for _ in c.execute("SELECT name FROM migrations WHERE name=?", (migration_filename,)):
            print("Migration {filename} is already applied, skipping".format(filename=migration_filename))
            skip = True

        if skip:
            continue

        with open(migrations_directory / migration_filename) as inp:
            print("Applying migration {filename}".format(filename=migration_filename))

            migration = inp.read().split(";")
            for sql in migration:
                print(sql)
                c.execute(sql)

            c.execute("INSERT INTO migrations(name) VALUES(?)", (migration_filename,))

    conn.commit()
    conn.close()


def connect() -> None:
    """Initialise the DB connection"""

    global db_connection
    db_connection = sqlite3.connect(DB_FILENAME)


def disconnect() -> None:
    """Terminate the DB connection"""

    db_connection.close()


def is_fetching() -> bool:
    """Return whether the current state is fetching"""

    with LogTime("SELECT is_fetching FROM state", db_logger):
        c = db_connection.cursor()

        for record in c.execute("SELECT is_fetching FROM state"):
            return record[0] != 0

        raise "DB corrupt: no state record"


def set_is_fetching(is_fetching: bool) -> None:
    """Sets the fetching state"""

    with LogTime("UPDATE state(is_fetching)", db_logger):
        c = db_connection.cursor()

        c.execute("UPDATE state SET is_fetching={}".format(1 if is_fetching else 0))

        db_connection.commit()


def last_successful_fetch() -> datetime.datetime:
    """Return whether the current state is fetching"""

    with LogTime("SELECT last_successful_fetch FROM state", db_logger):
        c = db_connection.cursor()

        for record in c.execute("SELECT last_successful_fetch FROM state"):
            return datetime.datetime.fromisoformat(record[0]) if record[0] is not None else None

        raise "DB corrupt: no state record"
