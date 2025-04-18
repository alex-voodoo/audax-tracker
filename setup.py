"""
Renders the bot settings file

This script requests mandatory configuration data and renders `src/settings.yaml` with it.
"""

import os
import pathlib


def main() -> None:
    os.chdir(pathlib.Path(__file__).parent / "src")

    if os.path.exists("settings.yaml"):
        print("ERROR: already set up!  Please remove src/settings.yaml before running this script.")
        return

    # Create settings.yaml
    bot_token = input("Please enter the API token of your bot: ")
    remote_endpoint_url = input("Please enter the URL of your remote endpoint that the bot will fetch data from: ")
    remote_endpoint_token = input("Please enter the authentication token that the remote endpoint will recognise: ")

    with open("settings-template.yaml", "r") as template:
        template_lines = template.read()
        template_lines = template_lines.split("# %TEMPLATE%\n")[-1].format(bot_token=bot_token.replace("\"", "\\\""),
                                                                           remote_endpoint_token=remote_endpoint_token,
                                                                           remote_endpoint_url=remote_endpoint_url)
        with open("settings.yaml", "w") as config:
            config.write(template_lines)
    print("Created src/settings.yaml that defines configuration of the bot")

    print("The first step of your setup is complete.  Refer to README.md for more information.")


if __name__ == "__main__":
    main()
