#!./venv/bin/python

"""
Sets up a new instance of the bot

This script renders `settings.py` based on `common/defaults.py` and the Telegram API
key provided by the user at the run time.

TODO implement updating the settings.py with updated defaults
"""

import os.path


def main() -> None:
    if os.path.exists("settings.py"):
        print("ERROR: already set up!  Please remove settings.py before running this script.")
        return

    # Create settings.py
    bot_token = input("Please enter the API token of your bot: ")
    remote_endpoint_url = input("Please enter the URL of your remote endpoint that the bot will fetch data from: ")
    remote_endpoint_token = input("Please enter the authentication token that the remote endpoint will recognise: ")

    with open(__file__, "r") as this_file:
        secret_lines = this_file.read()
        secret_lines = secret_lines.split("# %TEMPLATE%\n")[-1].format(bot_token=bot_token.replace("\"", "\\\""),
                                                                       remote_endpoint_token=remote_endpoint_token,
                                                                       remote_endpoint_url=remote_endpoint_url)
        with open("settings.py", "w") as secret:
            secret.write(secret_lines)
    print("- Created settings.py: bot configuration")

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
# URL of the remote endpoint that the data is fetched from
REMOTE_ENDPOINT_URL = "{remote_endpoint_url}"
# Fetch token
REMOTE_ENDPOINT_AUTH_TOKEN = "{remote_endpoint_token}"
