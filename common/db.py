"""
Database stuff
"""

import os
import sqlite3
from pathlib import Path

from common.log import get_file_logger

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
