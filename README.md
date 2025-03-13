# Audax Tracker Bot

This is a Telegram bot for tracking audax bicycle rides.

Audax is a [non-competitive cycling sport](https://en.wikipedia.org/wiki/Audax_(cycling)) where participants need to complete the route, checking in at controls within certain time constraints.

This bot helps "spectators" to track progress of their favourite participants during an event.  The bot uses an external data source to get data when participants check in at controls, and forwards notifications to its subscribers.

## Setup and usage

Clone this repository.  Create a virtual Python environment with Python version 3.11.  (Other versions may work too but that is not tested.) Install `requirements.txt` in the virtual environment.

Follow the [official documentation](https://core.telegram.org/bots#how-do-i-create-a-bot) to register your bot with BotFather.

Now you need to configure your instance of the bot.  Follow these steps to complete this process:
1. Open the command terminal and activate the virtual environment that you created above
2. Run `python setup.py` and provide the essential configuration parameters: API token of your bot and the URL of your data endpoint when requested.  The script will render `settings.py` that is necessary for the bot to run.
3. Run `python bot.py`.  The command should start the bot and run indefinitely.  Find your bot in Telegram and talk to it in private.  Initiate the conversation by clicking the Start button in the direct message chat.  The bot will respond with a welcome message.  Stop the bot by pressing `Ctrl+C` in the terminal.
4. In the directory where you have your bot, find `bot.log`, open it, and find a log message: `"Welcoming user {username} (chat ID {chat_id}), is this the admin?"` where `username` should be your Telegram username.  Copy the chat ID, open `settings.py` and paste that number as the new value of the `DEVELOPER_CHAT_ID` parameter.

Now the bot is ready to work.  You can start it by running `python bot.py` in a command terminal or adding it to some system auto-run.  The script will run indefinitely, unless something severe causes it to crash.  Should any non-fatal error occur in the bot, it will send error messages to you via private Telegram message.

## Configuration

To tune your bot, read and edit `settings.py`.  Uncomment settings that you want to alter and put your values.

Do not forget to restart the bot after you have changed the settings!

## Updating

To get the newest version of the bot, stop it, update your working copy by running `git pull`, then update Python packages by running `pip install -r requirements.txt`.
