"""
Public interface (functions available to every user)
"""
import datetime
import logging

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from common import format, i18n, settings, state

# Commands, sequences, and responses
COMMAND_ADD, COMMAND_HELP, COMMAND_REMOVE, COMMAND_START, COMMAND_STATUS = "add", "help", "remove", "start", "status"
TYPING_FRAME_PLATE_NUMBER = 1


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
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE"))

    context.user_data["action"] = COMMAND_ADD

    return TYPING_FRAME_PLATE_NUMBER


async def handle_command_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation to remove a participant from the user's list"""

    await context.bot.send_message(chat_id=update.effective_user.id, text=i18n.trans(update.effective_user).gettext(
        "MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_UNSUBSCRIBE"))

    context.user_data["action"] = COMMAND_REMOVE

    return TYPING_FRAME_PLATE_NUMBER


async def handle_command_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Render the current status of the user's subscription list and send it to the user"""

    user = update.effective_user
    trans = i18n.trans(user)
    lang = trans.info()["language"]
    tg_id = str(user.id)

    message = []
    if state.event_name(lang) and state.event_start() and state.event_finish():
        message.append("<strong>{event_name}</strong>".format(event_name=state.event_name(lang)))
        message.append(format.event_status(trans))
        message.append("")

    def format_checkin_time(checkin_str: str):
        checkin_time = datetime.datetime.fromisoformat(checkin_str)
        return trans.gettext("CHECKIN_DATE_AND_TIME {month} {day} {hour} {minute}").format(day=checkin_time.day,
                                                                                           hour=checkin_time.hour,
                                                                                           minute=checkin_time.minute,
                                                                                           month=format.datetime_month(
                                                                                               trans,
                                                                                               checkin_time.month))

    def format_control_name(control_id):
        return state.controls()[control_id]["name"][lang] if control_id else ""

    def format_last_known_status(participant: state.Participant):
        if not participant.last_known_control_id:
            return trans.gettext("LAST_KNOWN_STATUS_UNKNOWN {participant_name} {frame_plate_number}").format(
                participant_name=participant.name,
                frame_plate_number=participant.frame_plate_number)

        if state.controls()[participant.last_known_control_id]["finish"]:
            return trans.gettext("LAST_KNOWN_STATUS_FINISH {participant_name} {frame_plate_number} "
                                 "{result_time}").format(
                participant_name=participant.name,
                frame_plate_number=participant.frame_plate_number,
                result_time=format.result_time(participant.last_known_checkin_time))

        if participant.last_known_checkin_time:
            return trans.gettext("LAST_KNOWN_STATUS_OK {participant_name} {frame_plate_number} {checkin_time} "
                                 "{control_name} {distance}").format(
                control_name=format_control_name(participant.last_known_control_id),
                checkin_time=format_checkin_time(participant.last_known_checkin_time),
                distance=state.controls()[participant.last_known_control_id]["distance"],
                participant_name=participant.name,
                frame_plate_number=participant.frame_plate_number)

        return trans.gettext("LAST_KNOWN_STATUS_ABANDONED {participant_name} {frame_plate_number} "
                             "{control_name} {distance}").format(
            control_name=format_control_name(participant.last_known_control_id),
            distance=state.controls()[participant.last_known_control_id]["distance"],
            participant_name=participant.name,
            frame_plate_number=participant.frame_plate_number)

    if tg_id not in state.subscriptions():
        message.append(trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_EMPTY"))
    else:
        message.append(trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_LIST_HEADER"))
        for p in state.subscriptions()[tg_id]["numbers"]:
            message.append(format_last_known_status(state.participant(p)))
    await context.bot.send_message(chat_id=user.id, text="\n".join(message))


async def received_frame_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the received frame plate number and end one of conversations where it was requested"""

    user = update.effective_user
    frame_plate_number = update.message.text

    if not state.has_participant(frame_plate_number):
        await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_NO_SUCH_PARTICIPANT"))
    elif context.user_data["action"] == COMMAND_ADD:
        if state.has_subscription(str(user.id), frame_plate_number):
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_ALREADY_SUBSCRIBED"))
        else:
            state.add_subscription(user, update.message.text)
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext(
                "MESSAGE_SUBSCRIPTION_ADDED {frame_plate_number} {full_name}").format(
                frame_plate_number=frame_plate_number, full_name=state.participant(frame_plate_number).name))
    elif context.user_data["action"] == COMMAND_REMOVE:
        if not state.has_subscription(str(user.id), frame_plate_number):
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_NOT_SUBSCRIBED"))
        else:
            state.remove_subscription(str(user.id), update.message.text)
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext(
                "MESSAGE_SUBSCRIPTION_REMOVED {frame_plate_number} {full_name}").format(
                frame_plate_number=frame_plate_number, full_name=state.participant(frame_plate_number).name))
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


def init(application: Application) -> None:
    """Do what is necessary for the subscriber's interface at the initial step (before starting the polling)"""

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


async def post_init(application: Application) -> None:
    """Do what is necessary for the subscriber's interface at the post-initial step (after starting the polling)"""

    trans = i18n.default()

    await application.bot.set_my_commands(
        [BotCommand(command=COMMAND_ADD, description=trans.gettext("COMMAND_DESCRIPTION_ADD")),
         BotCommand(command=COMMAND_REMOVE, description=trans.gettext("COMMAND_DESCRIPTION_REMOVE")),
         BotCommand(command=COMMAND_STATUS, description=trans.gettext("COMMAND_DESCRIPTION_STATUS"))])
