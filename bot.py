#!./venv/bin/python

"""
This is the main script that contains the entry point of the bot.  Execute this file to run the bot.

See README.md for details.
"""

import html
import json
import logging
import traceback
import datetime

import httpx
import requests
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

import settings
from common import db, i18n

# Commands, sequences, and responses
COMMAND_START, COMMAND_HELP, COMMAND_ADD, COMMAND_REMOVE, COMMAND_STATUS, COMMAND_ADMIN = (
    "start", "help", "add", "remove", "status", "admin")
ADMIN_RELOAD_PARTICIPANTS, ADMIN_STOP_FETCHING, ADMIN_START_FETCHING = (
    "admin-load-participants", "admin-stop-fetching", "admin-start-fetching")

# Configure logging
# Set higher logging level for httpx to avoid all GET and POST requests being logged.
# noinspection SpellCheckingInspection
logging.basicConfig(format="[%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d] %(message)s",
                    level=logging.INFO, filename="bot.log")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

periodic_fetching_job = None
last_successful_fetch = None


def get_admin_keyboard() -> InlineKeyboardMarkup:
    global periodic_fetching_job

    trans = i18n.default()

    button_reload_participants = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_RELOAD_PARTICIPANTS"),
                                                      callback_data=ADMIN_RELOAD_PARTICIPANTS)
    if periodic_fetching_job:
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_STOP_FETCHING"),
                                                      callback_data=ADMIN_STOP_FETCHING)
    else:
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_START_FETCHING"),
                                                      callback_data=ADMIN_START_FETCHING)

    return InlineKeyboardMarkup(((button_reload_participants,), (button_toggle_fetching,)), )


async def handle_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and show them the selection of options"""

    message = update.effective_message
    user = message.from_user

    if settings.DEVELOPER_CHAT_ID == 0:
        logger.info("Welcoming user {username} (chat ID {chat_id}), is this the admin?".format(username=user.username,
                                                                                               chat_id=user.id))
    elif user.id == settings.DEVELOPER_CHAT_ID:
        logger.info(
            "Welcoming the admin user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))
    else:
        logger.info("Welcoming user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))

    await message.reply_text(i18n.trans(user).gettext("MESSAGE_START"))


async def handle_command_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the admin menu"""

    message = update.effective_message
    user = message.from_user

    if user.id != settings.DEVELOPER_CHAT_ID:
        logging.info("User {username} tried to invoke the admin UI".format(username=user.username))
        return

    trans = i18n.default()

    await context.bot.send_message(chat_id=user.id, text=trans.gettext("MESSAGE_ADMIN_START"),
                                   reply_markup=get_admin_keyboard())


def is_admin_query(data) -> bool:
    return data in (ADMIN_RELOAD_PARTICIPANTS, ADMIN_START_FETCHING, ADMIN_STOP_FETCHING)


async def handle_query_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user

    if user.id != settings.DEVELOPER_CHAT_ID:
        logging.error("User {username} is not listed as administrator!".format(username=user.username))
        return

    await query.answer()

    trans = i18n.default()

    if query.data == ADMIN_RELOAD_PARTICIPANTS:
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_RELOADING_PARTICIPANTS"),
                                      reply_markup=get_admin_keyboard())
    elif query.data == ADMIN_STOP_FETCHING:
        stop_fetching()
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_FETCHING_STOPPED"),
                                      reply_markup=get_admin_keyboard())
    elif query.data == ADMIN_START_FETCHING:
        start_fetching(context.application)
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_FETCHING_STARTED"),
                                      reply_markup=get_admin_keyboard())


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer"""

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

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            i18n.trans(update.effective_message.from_user).gettext("MESSAGE_DM_INTERNAL_ERROR"))


async def periodic_fetch_data_and_notify_subscribers(context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_successful_fetch

    try:
        if not last_successful_fetch:
            last_successful_fetch = db.last_successful_fetch()
        request = {
            "token": settings.FETCH_TOKEN,
            "since": last_successful_fetch.isoformat() if last_successful_fetch else None
        }
        logger.info("Sending request: {}".format(request))
        response = requests.post(settings.REMOTE_ENDPOINT_URL, json=request)
        logger.info("Got response: {}".format(response))
    except Exception as e:
        stop_fetching()
        logger.error(e)
        await context.bot.send_message(chat_id=settings.DEVELOPER_CHAT_ID,
                                       text="{} raised when trying to fetch data, stopped fetching.".format(
                                           html.escape(str(type(e)))), parse_mode=ParseMode.HTML)


def start_fetching(application: Application) -> None:
    global periodic_fetching_job

    if periodic_fetching_job:
        logger.error("Called start_fetching() but already fetching!")
        return

    periodic_fetching_job = application.job_queue.run_repeating(periodic_fetch_data_and_notify_subscribers,
                                                                interval=60 * settings.FETCHING_INTERVAL_MINUTES,
                                                                first=10)

    db.set_is_fetching(True)


def stop_fetching() -> None:
    global periodic_fetching_job

    if not periodic_fetching_job:
        logger.error("Called stop_fetching() but not fetching!")
        return

    periodic_fetching_job.schedule_removal()
    periodic_fetching_job = None

    db.set_is_fetching(False)


async def post_init(application: Application) -> None:
    trans = i18n.default()

    await application.bot.set_my_commands(
        [BotCommand(command=COMMAND_ADD, description=trans.gettext("COMMAND_DESCRIPTION_ADD")),
         BotCommand(command=COMMAND_REMOVE, description=trans.gettext("COMMAND_DESCRIPTION_REMOVE")),
         BotCommand(command=COMMAND_STATUS, description=trans.gettext("COMMAND_DESCRIPTION_STATUS"))])


def main() -> None:
    """Run the bot"""

    db.connect()

    application = Application.builder().token(settings.BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler(COMMAND_START, handle_command_start))
    application.add_handler(CommandHandler(COMMAND_HELP, handle_command_start))
    application.add_handler(CommandHandler(COMMAND_ADMIN, handle_command_admin))
    application.add_handler(CallbackQueryHandler(handle_query_admin, pattern=is_admin_query))

    application.add_error_handler(handle_error)

    if db.is_fetching():
        logger.info("Last state is: fetching, starting")
        start_fetching(application)
    else:
        logger.info("Last state is: not fetching, staying idle")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

    db.disconnect()


if __name__ == "__main__":
    main()
