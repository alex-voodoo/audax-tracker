"""
Database stuff
"""

import os
import sqlite3
from pathlib import Path

from common.log import get_file_logger

db_connection: sqlite3.Connection

db_logger = get_file_logger("db", "db.log")


def apply_migrations(migrations_directory: Path) -> None:
    conn = sqlite3.connect("people.db")
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
    db_connection = sqlite3.connect(".db")


def disconnect() -> None:
    """Terminate the DB connection"""

    db_connection.close()
