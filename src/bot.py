"""
This is the main script that contains the entry point of the bot.  Execute this file to run the bot.

See README.md for details.
"""

import io
import json
import logging
import traceback
import uuid

import httpx
from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, filters,
                          MessageHandler)

from common import admin, i18n, remote, settings, state

# Commands, sequences, and responses
COMMAND_ADD, COMMAND_ADMIN, COMMAND_HELP, COMMAND_REMOVE, COMMAND_START, COMMAND_STATUS = (
    "add", "admin", "help", "remove", "start", "status")
ADMIN_RELOAD_CONFIGURATION, ADMIN_START_FETCHING, ADMIN_STOP_FETCHING = (
    "admin-reload-configuration", "admin-start-fetching", "admin-stop-fetching")
TYPING_FRAME_PLATE_NUMBER = 1

# Configure logging
# Set higher logging level for httpx to avoid all GET and POST requests being logged.
# noinspection SpellCheckingInspection
logging.basicConfig(format="[%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d] %(message)s",
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def handle_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and show them the selection of options"""

    message = update.effective_message
    user = message.from_user

    if settings.DEVELOPER_CHAT_ID == 0:
        logging.info("Welcoming user {username} (chat ID {chat_id}), is this the admin?".format(username=user.username,
                                                                                                chat_id=user.id))
    elif user.id == settings.DEVELOPER_CHAT_ID:
        logging.info(
            "Welcoming the admin user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))
    else:
        logging.info("Welcoming user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))

    await message.reply_text(i18n.trans(user).gettext("MESSAGE_START"))


async def handle_command_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation to add a participant to the user's list"""

    await context.bot.send_message(chat_id=update.effective_user.id, text=i18n.trans(update.effective_user).gettext(
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE"), parse_mode=ParseMode.HTML)

    context.user_data["action"] = COMMAND_ADD

    return TYPING_FRAME_PLATE_NUMBER


async def handle_command_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation to remove a participant from the user's list"""

    await context.bot.send_message(chat_id=update.effective_user.id, text=i18n.trans(update.effective_user).gettext(
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_UNSUBSCRIBE"), parse_mode=ParseMode.HTML)

    context.user_data["action"] = COMMAND_REMOVE

    return TYPING_FRAME_PLATE_NUMBER


async def handle_command_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Render the current status of the user's subscription list and send it to the user"""

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


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer"""

    exception = context.error

    if isinstance(exception, httpx.RemoteProtocolError):
        # Connection errors happen regularly, and they are caused by reasons external to the bot, so it makes no
        # sense notifying the developer about them.  Log an error and bail out.
        logging.error(exception)
        return

    trans = i18n.default()

    error_uuid = uuid.uuid4()

    # Log the error before we do anything else, so we can see it even if something breaks.
    logging.error(f"Exception while handling an update (error UUID {error_uuid}):", exc_info=exception)

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
        logging.error("Unknown action {}".format(context.user_data["action"]))

    context.user_data.clear()
    return ConversationHandler.END


async def abort_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Clean up the intermediate state of the conversation if it went off the rails"""

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
    """Entry point"""

    logging.info("The bot starts in {} mode".format("service" if settings.SERVICE_MODE else "direct"))

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

    application.add_handler(CommandHandler(COMMAND_ADMIN, admin.handle_command_admin))
    application.add_handler(CallbackQueryHandler(admin.handle_query_admin, pattern=admin.is_admin_query))

    application.add_error_handler(handle_error)

    if state.is_fetching():
        logging.info("Last state is: fetching, starting")
        remote.start_fetching(application)
    else:
        logging.info("Last state is: not fetching, staying idle")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
