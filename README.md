# Audax Tracker Bot

This is a Telegram bot for tracking audax bicycle rides.

Audax is a [non-competitive cycling sport](https://en.wikipedia.org/wiki/Audax_(cycling)) where participants need to complete the route, checking in at controls within certain time constraints.

This bot helps "spectators" to track progress of their favourite participants during an event.  The bot uses an external data source to get data when participants check in at controls, and forwards notifications to its subscribers.

## Setup

Clone this repository.  Create a virtual Python environment with Python version 3.11.  (Other versions may work too but that is not tested.) Install `requirements.txt` in the virtual environment.

Follow the [official documentation](https://core.telegram.org/bots#how-do-i-create-a-bot) to register your bot with BotFather.

Now you need to configure your instance of the bot.  Follow these steps to complete this process:
1. Open the command terminal and activate the virtual environment that you created above
2. Run `python setup.py` and provide the essential configuration parameters: API token of your bot and the URL of your data endpoint when requested.  The script will render `src/settings.yaml` that is necessary for the bot to run.
3. Run `python src/bot.py`.  The command should start the bot and run indefinitely.  Find the bot in your Telegram client and talk to it in private.  Initiate the conversation by clicking the Start button in the direct message chat.  The bot will respond with a welcome message, and in the terminal where it is running you will see a log message: _Welcoming user {username} (chat ID {chat_id}), is this the admin?_ where `username` should be your Telegram username.  Copy the chat ID, open `src/settings.yaml` and paste that number as the new value of the `DEVELOPER_CHAT_ID` parameter.
4. Stop the bot by pressing `Ctrl+C` in the terminal, then start it again and send the `/start` command to the bot from your Telegram client.  This time you should see another log message in the terminal where the bot is running: _Welcoming the admin user {username} (chat ID {chat_id})_, and also the bot should show the administrator's menu in response to the `/admin` command.

Now the bot is ready to work.  It can be launched directly by running `python src/bot.py` in a command terminal, or it can be installed as a Linux system service.  The recommended way is first testing the bot in direct mode, tuning the configuration, and then installing it as the system service.  To change the configuration, edit `settings.yaml` (the exact location depends on the mode), then restart the bot.

## Running the bot in direct mode

The bot runs in direct mode if the `AUDAX_TRACKER_SERVICE_MODE` environment variable is not set or not equal to "1".

To launch the bot, activate the Python virtual environment and run `python bot.py` in a command terminal.  To stop it gracefully, press `Ctrl+C`.

In direct mode, the bot assumes that its configuration file and persistent state file are located in the same directory where its entry point script is located, which is the `src` subdirectory of this repository.

## Running the bot as a Linux system service

The bot can be registered as a Linux service daemon in a system that runs systemd.  The bot runs in service mode if the `AUDAX_TRACKER_SERVICE_MODE` environment variable is set and is equal to "1", which is provided by the systemd unit configuration.

You will need superuser privileges to proceed.

First configure the bot as explained above, then continue from here.

Run `sudo make install` to install the systemd unit.  The script will copy the bot program files to `/usr/local/lib/audax-tracker`, create the virtual Python environment there, register the systemd unit named `audax-tracker`, and copy `src/settings.yaml` to `/usr/local/etc/audax-tracker/settings.yaml`.  The persistent state **will not** be copied.

In service mode, the bot loads its configuration from `/usr/local/etc/audax-tracker/settings.yaml`, and stores its persistent state in `/var/local/audax-tracker/state.json`.

Start the service by running `sudo sustemctl start audax-tracker`, stop it by running `sudo sustemctl stop audax-tracker`.

## Troubleshooting and error handling

The bot writes log messages to `stdout` and `stderr`.  In service mode these are redirected to `/var/log/audax-tracker.log`.

Should any non-fatal errors occur in the bot, it will send error messages to its administrator user via private Telegram messages.
