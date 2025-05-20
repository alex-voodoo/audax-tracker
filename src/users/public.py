"""
Public interface (functions available to every user)
"""

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from common import format, i18n, settings, state

# Commands, sequences, and responses
COMMAND_ADD, COMMAND_HELP, COMMAND_REMOVE, COMMAND_START, COMMAND_STATUS = "add", "help", "remove", "start", "status"
TYPING_FRAME_PLATE_NUMBER = 1


async def handle_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and show them the selection of options"""

    user = update.effective_user
    trans = i18n.trans(user)

    if settings.DEVELOPER_CHAT_ID == 0:
        logging.info("Welcoming user {username} (chat ID {chat_id}), is this the admin?".format(username=user.username,
                                                                                                chat_id=user.id))
    elif user.id == settings.DEVELOPER_CHAT_ID:
        logging.info(
            "Welcoming the admin user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))
    else:
        logging.info("Welcoming user {username} (chat ID {chat_id})".format(username=user.username, chat_id=user.id))

    message = [trans.gettext("MESSAGE_START {max_subscription_count}").format(
        max_subscription_count=settings.MAX_SUBSCRIPTION_COUNT)]

    if settings.EVENT_PARTICIPANT_LIST_URL:
        message.append("")
        message.append(trans.gettext("MESSAGE_START_PARTICIPANTS_LIST {url}").format(
            url=settings.EVENT_PARTICIPANT_LIST_URL))

    await update.effective_message.reply_text("\n".join(message))


async def handle_command_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation to add a participant to the user's list"""

    user_id = update.effective_user.id
    trans = i18n.trans(update.effective_user)

    if len(state.Subscription(str(user_id)).numbers) >= settings.MAX_SUBSCRIPTION_COUNT:
        await context.bot.send_message(chat_id=user_id, text=trans.gettext("MESSAGE_MAX_SUBSCRIPTION_COUNT_REACHED"))
        return ConversationHandler.END

    await context.bot.send_message(chat_id=user_id, text=trans.gettext("MESSAGE_TYPE_FRAME_PLATE_NUMBER_TO_SUBSCRIBE"))

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
    tg_id = str(user.id)

    message = []
    event = state.Event()
    if event.valid:
        message.append("<strong>{event_name}</strong>".format(event_name=event.name(trans)))
        message.append(format.event_status(trans))
        message.append("")

    if not state.has_subscriber(tg_id):
        message.append(trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_EMPTY"))
    else:
        message.append(trans.gettext("MESSAGE_STATUS_SUBSCRIPTION_LIST_HEADER"))
        for frame_plate_number in state.Subscription(tg_id).numbers:
            message.append(format.participant_status(trans, state.Participant(frame_plate_number)))
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
                "MESSAGE_SUBSCRIPTION_ADDED {participant_label}").format(
                participant_label=state.Participant(frame_plate_number).label))
    elif context.user_data["action"] == COMMAND_REMOVE:
        if not state.has_subscription(str(user.id), frame_plate_number):
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_NOT_SUBSCRIBED"))
        else:
            state.remove_subscription(str(user.id), update.message.text)
            await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext(
                "MESSAGE_SUBSCRIPTION_REMOVED {participant_label}").format(
                participant_label=state.Participant(frame_plate_number).label))
    else:
        logging.error(f"Unknown action '{context.user_data['action']}'!")

    context.user_data.clear()
    return ConversationHandler.END


async def abort_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Clean up the intermediate state of the conversation if it went off the rails"""

    user = update.effective_user
    context.user_data.clear()
    await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_ABORT"))

    return ConversationHandler.END


async def handle_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle everything that was not caught by other handlers"""

    user = update.effective_user

    await context.bot.send_message(chat_id=user.id, text=i18n.trans(user).gettext("MESSAGE_UNRECOGNISED_INPUT"))


def on_participants_removed(updates) -> None:
    """Notify subscribers about their subscriptions that were removed"""

    # TODO: implement this
    pass


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
    application.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND), handle_random_input))

    state.set_on_participants_removed(on_participants_removed)


async def post_init(application: Application) -> None:
    """Do what is necessary for the subscriber's interface at the post-initial step (after starting the polling)"""

    for lang in settings.SUPPORTED_LANGUAGES:
        trans = i18n.for_lang(lang)

        await application.bot.set_my_commands(
            [BotCommand(command=COMMAND_ADD, description=trans.gettext("COMMAND_DESCRIPTION_ADD")),
             BotCommand(command=COMMAND_REMOVE, description=trans.gettext("COMMAND_DESCRIPTION_REMOVE")),
             BotCommand(command=COMMAND_STATUS, description=trans.gettext("COMMAND_DESCRIPTION_STATUS")),
             BotCommand(command=COMMAND_HELP, description=trans.gettext("COMMAND_DESCRIPTION_HELP"))],
            language_code=lang)
