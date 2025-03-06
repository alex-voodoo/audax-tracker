#!./venv/bin/python

"""
Sets up a new instance of the bot

This script creates a new empty database and renders `settings.py` based on `common/defaults.py` and the Telegram API
key provided by the user at the run time.

TODO implement updating the settings.py with updated defaults
"""

import os.path
import pathlib

from common import db


def main() -> None:
    if os.path.exists("settings.py") or os.path.exists(db.DB_FILENAME):
        print("ERROR: local files already exist!  "
              "Please remove settings.py and {db_filename} before running this script.".format(
            db_filename=db.DB_FILENAME))
        return

    # Create settings.py
    bot_token = input("Please enter the API token of your bot: ")

    with open(__file__, "r") as this_file:
        secret_lines = this_file.read()
        secret_lines = secret_lines.split("# %TEMPLATE%\n")[-1].format(bot_token=bot_token.replace("\"", "\\\""))
        with open("settings.py", "w") as secret:
            secret.write(secret_lines)
    print("- Created settings.py: bot configuration")

    # Create people.db
    db.connect()
    db.disconnect()

    print("- Created people.db: the empty database")

    db.apply_migrations(pathlib.Path(__file__).parent / "migrations")

    print("The first step of your setup is complete.  Refer to README.md for more information.")


if __name__ == "__main__":
    main()

# Below is the template for the settings.py.
# %TEMPLATE%
"""
Custom configuration of the bot.

This is where you keep all your secrets, and also here you can override the default settings.
"""

# noinspection PyUnresolvedReferences
from common.defaults import *

# ----------------------------------------------------------------------------------------------------------------------
# Mandatory settings
#
# Token of the bot, obtained from BotFather
BOT_TOKEN = "{bot_token}"
# ID of the chat with the developer
DEVELOPER_CHAT_ID = 0
