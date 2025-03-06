#!./venv/bin/python

"""
This is the main script that contains the entry point of the bot.  Execute this file to run the bot.

See README.md for details.
"""

import html
import json
import logging
import traceback

import httpx
from telegram import BotCommand,  Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

import settings
from common import db, i18n

# Commands, sequences, and responses
COMMAND_START, COMMAND_ADD, COMMAND_REMOVE, COMMAND_STATUS = "start", "add", "remove", "status"

# Configure logging
# Set higher logging level for httpx to avoid all GET and POST requests being logged.
# noinspection SpellCheckingInspection
logging.basicConfig(format="[%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d] %(message)s",
                    level=logging.INFO, filename="bot.log")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def handle_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and show them the selection of options"""

    message = update.effective_message
    user = message.from_user

    if settings.DEVELOPER_CHAT_ID == 0:
        logger.info("Welcoming user {username} (chat ID {chat_id}), is this the admin?".format(username=user.username,
                                                                                               chat_id=user.id))
    elif user.id == settings.DEVELOPER_CHAT_ID:
        logger.info("Welcoming the admin user {username} (chat ID {chat_id})".format(username=user.username,
                                                                                     chat_id=user.id))
    else:
        logger.info("Welcoming user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))

    await message.reply_text(i18n.trans(user).gettext("MESSAGE_START"))


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer"""

    if not isinstance(update, Update):
        logger.error("Unexpected type of update: {}".format(type(update)))
        return

    user = update.effective_message.from_user

    exception = context.error

    if isinstance(exception, httpx.RemoteProtocolError):
        # Connection errors happen regularly, and they are caused by reasons external to the bot, so it makes no
        # sense notifying the developer about them.  Log an error and bail out.
        logger.error(exception)
        return

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=exception)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_string = "".join(traceback.format_exception(None, exception, exception.__traceback__))

    # Build the message with some markup and additional information about what happened.
    # TODO: add logic to deal with messages longer than 4096 characters (Telegram has that limit).
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    error_message = (f"<pre>{html.escape(tb_string)}</pre>"
                     f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
                     f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
                     f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n")

    # Finally, send the message
    await context.bot.send_message(chat_id=settings.DEVELOPER_CHAT_ID, text=error_message, parse_mode=ParseMode.HTML)

    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
    else:
        logger.error("Unexpected state of the update: {}".format(update_str))
        return

    await message.reply_text(i18n.trans(user).gettext("MESSAGE_DM_INTERNAL_ERROR"))


async def post_init(application: Application) -> None:
    bot = application.bot

    trans = i18n.default()

    await bot.set_my_commands(
        [BotCommand(command=COMMAND_ADD, description=trans.gettext("COMMAND_DESCRIPTION_ADD")),
         BotCommand(command=COMMAND_REMOVE, description=trans.gettext("COMMAND_DESCRIPTION_REMOVE")),
         BotCommand(command=COMMAND_STATUS, description=trans.gettext("COMMAND_DESCRIPTION_STATUS"))])


def main() -> None:
    """Run the bot"""

    db.connect()

    application = Application.builder().token(settings.BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler(COMMAND_START, handle_command_start))

    application.add_error_handler(handle_error)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    db.disconnect()


if __name__ == "__main__":
    main()
