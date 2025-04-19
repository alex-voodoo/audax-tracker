"""
This is the main script that contains the entry point of the bot.  Execute this file to run the bot.

See README.md for details.
"""
import datetime
import io
import json
import logging
import traceback
import uuid
from zoneinfo import ZoneInfo

import httpx
import requests
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, filters,
                          MessageHandler)

from common import i18n, settings, state

# Commands, sequences, and responses
COMMAND_START, COMMAND_HELP, COMMAND_ADD, COMMAND_REMOVE, COMMAND_STATUS, COMMAND_ADMIN = (
    "start", "help", "add", "remove", "status", "admin")
ADMIN_RELOAD_CONFIGURATION, ADMIN_STOP_FETCHING, ADMIN_START_FETCHING = (
    "admin-reload-configuration", "admin-stop-fetching", "admin-start-fetching")
TYPING_FRAME_PLATE_NUMBER = 1

# Configure logging
# Set higher logging level for httpx to avoid all GET and POST requests being logged.
# noinspection SpellCheckingInspection
logging.basicConfig(format="[%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d] %(message)s",
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

periodic_fetching_job = None


def get_admin_keyboard() -> InlineKeyboardMarkup:
    global periodic_fetching_job

    trans = i18n.default()

    button_reload_participants = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_RELOAD_PARTICIPANTS"),
                                                      callback_data=ADMIN_RELOAD_CONFIGURATION)
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
    return data in (ADMIN_RELOAD_CONFIGURATION, ADMIN_START_FETCHING, ADMIN_STOP_FETCHING)


async def handle_query_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user

    if user.id != settings.DEVELOPER_CHAT_ID:
        logging.error("User {username} is not listed as administrator!".format(username=user.username))
        return

    await query.answer()

    trans = i18n.default()

    if query.data == ADMIN_RELOAD_CONFIGURATION:
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_RELOADING_CONFIGURATION"),
                                      reply_markup=get_admin_keyboard())
        if await reload_configuration():
            await query.edit_message_text(
                trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOADED {control_count} {participant_count}").format(
                    control_count=len(state.controls()), participant_count=len(state.participants())),
                reply_markup=get_admin_keyboard())
        else:
            await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOAD_ERROR"),
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

    trans = i18n.default()

    error_uuid = uuid.uuid4()

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(f"Exception while handling an update (error UUID {error_uuid}):", exc_info=exception)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)

    error_message = trans.gettext("ERROR_REPORT_BODY {error_uuid} {traceback} {update} {chat_data} {user_data}").format(
        chat_data=str(context.chat_data), error_uuid=error_uuid,
        traceback="".join(traceback.format_exception(None, exception, exception.__traceback__)),
        update=json.dumps(update_str, indent=2, ensure_ascii=False), user_data=str(context.user_data))

    # Finally, send the message
    await context.bot.send_document(chat_id=settings.DEVELOPER_CHAT_ID,
                                    caption=trans.gettext("ERROR_REPORT_CAPTION {error_uuid}").format(
                                        error_uuid=error_uuid), document=io.BytesIO(bytes(error_message, "utf-8")),
                                    filename=f"audax-tracker-error-{error_uuid}.txt", parse_mode=ParseMode.HTML)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            i18n.trans(update.effective_message.from_user).gettext("MESSAGE_DM_INTERNAL_ERROR {error_uuid}").format(
                error_uuid=error_uuid), parse_mode=ParseMode.HTML)


async def periodic_fetch_data_and_notify_subscribers(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        request = {"token": settings.REMOTE_ENDPOINT_AUTH_TOKEN, "method": "get-tracking-updates",
                   "since": state.last_successful_fetch()}
        response_raw = requests.post(settings.REMOTE_ENDPOINT_URL, json=request)
        if response_raw.status_code != 200:
            logger.info("Got HTTP error response: {c} {r}".format(c=response_raw.status_code, r=response_raw.reason))
            return

        response = response_raw.json()
        if not response["success"]:
            logger.info("Got API error response: {}".format(response["error_message"]))
            return

        logger.info("Got data response from the remote endpoint, preparing updates for the subscribers.")
        packages = {}
        for update in response["updates"]:
            for tg_id, subscription in state.subscriptions().items():
                if update["frame_plate_number"] in subscription["numbers"]:
                    if tg_id not in packages:
                        packages[tg_id] = []
                    packages[tg_id].append(update)

        def convert(tr, t) -> str:
            if not t:
                return tr.gettext("DNF")
            return datetime.datetime.fromisoformat(t).astimezone(ZoneInfo(settings.TIME_ZONE)).strftime("%d %B %H:%M")

        for tg_id, updates in packages.items():
            checkins = []
            lang = state.subscriptions()[tg_id]["lang"]
            trans = i18n.for_lang(lang)
            for update in sorted(updates, key=lambda u: int(u["frame_plate_number"])):
                control = state.controls()[str(update["control"])]
                checkins.append(trans.gettext(
                    "MESSAGE_UPDATE_ENTRY {control_name} {distance} {frame_plate_number} {full_name} {time}").format(
                    control_name=control["name"][lang], distance=control["distance"],
                    frame_plate_number=update["frame_plate_number"],
                    full_name=state.participants()[update["frame_plate_number"]],
                    time=convert(trans, update["checkin_time"])))

            await context.bot.send_message(chat_id=tg_id, text=trans.gettext("MESSAGE_CHECKIN_UPDATE {entries}").format(
                entries="\n".join(checkins)), parse_mode=ParseMode.HTML)

        state.set_last_successful_fetch(response["next_since"])

    except Exception as e:
        stop_fetching()
        raise


def start_fetching(application: Application) -> None:
    global periodic_fetching_job

    if periodic_fetching_job:
        logger.error("Called start_fetching() but already fetching!")
        return

    periodic_fetching_job = application.job_queue.run_repeating(periodic_fetch_data_and_notify_subscribers,
                                                                interval=60 * settings.FETCHING_INTERVAL_MINUTES,
                                                                first=10)

    state.set_is_fetching(True)


def stop_fetching() -> None:
    global periodic_fetching_job

    if not periodic_fetching_job:
        logger.error("Called stop_fetching() but not fetching!")
        return

    periodic_fetching_job.schedule_removal()
    periodic_fetching_job = None

    state.set_is_fetching(False)


async def reload_configuration() -> bool:
    try:
        request = {"token": settings.REMOTE_ENDPOINT_AUTH_TOKEN, "method": "get-configuration"}
        logger.info("Sending request: {}".format(request))
        response_raw = requests.post(settings.REMOTE_ENDPOINT_URL, json=request)
        if response_raw.status_code != 200:
            logger.info("Got HTTP error response: {c} {r}".format(c=response_raw.status_code, r=response_raw.reason))
            return False

        response = response_raw.json()
        if not response["success"]:
            logger.info("Got API error response: {}".format(response["error_message"]))
            return False

        logger.info(response)

        state.set_controls(response["controls"])
        state.set_participants(response["participants"])

        return True

    except Exception as e:
        logger.error(e)
        return False


async def handle_command_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(chat_id=update.effective_user.id, text=i18n.trans(update.effective_user).gettext(
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE"), parse_mode=ParseMode.HTML)

    context.user_data["action"] = COMMAND_ADD

    return TYPING_FRAME_PLATE_NUMBER


async def handle_command_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(chat_id=update.effective_user.id, text=i18n.trans(update.effective_user).gettext(
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_UNSUBSCRIBE"), parse_mode=ParseMode.HTML)

    context.user_data["action"] = COMMAND_REMOVE

    return TYPING_FRAME_PLATE_NUMBER


async def received_frame_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the received frame plate number and end one of conversations where it was requested"""

    user = update.effective_user
    frame_plate_number = update.message.text

    if not state.has_participant(frame_plate_number):
        await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_NO_SUCH_PARTICIPANT"),
                                       parse_mode=ParseMode.HTML)
    elif context.user_data["action"] == COMMAND_ADD:
        if state.has_subscription(str(user.id), frame_plate_number):
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_ALREADY_SUBSCRIBED"),
                                           parse_mode=ParseMode.HTML)
        else:
            state.add_subscription(user, update.message.text)
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext(
                "MESSAGE_SUBSCRIPTION_ADDED {frame_plate_number} {full_name}").format(
                frame_plate_number=frame_plate_number, full_name=state.participants()[frame_plate_number]),
                                           parse_mode=ParseMode.HTML)
    elif context.user_data["action"] == COMMAND_REMOVE:
        if not state.has_subscription(str(user.id), frame_plate_number):
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_NOT_SUBSCRIBED"),
                                           parse_mode=ParseMode.HTML)
        else:
            state.remove_subscription(str(user.id), update.message.text)
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext(
                "MESSAGE_SUBSCRIPTION_REMOVED {frame_plate_number} {full_name}").format(
                frame_plate_number=frame_plate_number, full_name=state.participants()[frame_plate_number]),
                                           parse_mode=ParseMode.HTML)
    else:
        logger.error("Unknown action {}".format(context.user_data["action"]))

    context.user_data.clear()
    return ConversationHandler.END


async def handle_command_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    trans = i18n.trans(user)
    tg_id = str(user.id)

    if tg_id not in state.subscriptions():
        await context.bot.send_message(chat_id=user.id, text=trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_EMPTY"),
                                       parse_mode=ParseMode.HTML)
    else:
        items = [trans.gettext("MESSAGE_STATUS_ITEM {frame_plate_number} {full_name}").format(frame_plate_number=p,
                                                                                              full_name=
                                                                                              state.participants()[p])
                 for p in state.subscriptions()[tg_id]["numbers"]]
        await context.bot.send_message(chat_id=user.id,
                                       text=trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_LIST {items}").format(
                                           items="\n".join(items)), parse_mode=ParseMode.HTML)


async def abort_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data.clear()
    await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_ABORT"))

    return ConversationHandler.END


async def post_init(application: Application) -> None:
    trans = i18n.default()

    await application.bot.set_my_commands(
        [BotCommand(command=COMMAND_ADD, description=trans.gettext("COMMAND_DESCRIPTION_ADD")),
         BotCommand(command=COMMAND_REMOVE, description=trans.gettext("COMMAND_DESCRIPTION_REMOVE")),
         BotCommand(command=COMMAND_STATUS, description=trans.gettext("COMMAND_DESCRIPTION_STATUS"))])


def main() -> None:
    """Run the bot"""

    logger.info("The bot starts in {} mode".format("service" if settings.SERVICE_MODE else "direct"))

    application = Application.builder().token(settings.BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler(COMMAND_START, handle_command_start))
    application.add_handler(CommandHandler(COMMAND_HELP, handle_command_start))

    application.add_handler(ConversationHandler(entry_points=[CommandHandler(COMMAND_ADD, handle_command_add)], states={
        TYPING_FRAME_PLATE_NUMBER: [MessageHandler(filters.TEXT & (~ filters.COMMAND), received_frame_plate_number)]},
                                                fallbacks=[MessageHandler(filters.ALL, abort_conversation)]))
    application.add_handler(ConversationHandler(entry_points=[CommandHandler(COMMAND_REMOVE, handle_command_remove)],
                                                states={TYPING_FRAME_PLATE_NUMBER: [
                                                    MessageHandler(filters.TEXT & (~ filters.COMMAND),
                                                                   received_frame_plate_number)]},
                                                fallbacks=[MessageHandler(filters.ALL, abort_conversation)]))
    application.add_handler(CommandHandler(COMMAND_STATUS, handle_command_status))

    application.add_handler(CommandHandler(COMMAND_ADMIN, handle_command_admin))
    application.add_handler(CallbackQueryHandler(handle_query_admin, pattern=is_admin_query))

    application.add_error_handler(handle_error)

    if state.is_fetching():
        logger.info("Last state is: fetching, starting")
        start_fetching(application)
    else:
        logger.info("Last state is: not fetching, staying idle")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
