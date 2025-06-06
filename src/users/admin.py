"""
Administrator's interface
"""

import logging

from common import format, i18n, remote, settings, state
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

_COMMAND_ADMIN, _COMMAND_RELOAD_CONFIGURATION, _COMMAND_START_FETCHING, _COMMAND_STOP_FETCHING = (
    "admin", "admin-reload-configuration", "admin-start-fetching", "admin-stop-fetching")


def _keyboard() -> InlineKeyboardMarkup:
    """Create the administrator's keyboard"""

    trans = i18n.default()

    button_reload_configuration = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_RELOAD_CONFIGURATION"),
                                                       callback_data=_COMMAND_RELOAD_CONFIGURATION)
    if remote.is_fetching():
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_STOP_FETCHING"),
                                                      callback_data=_COMMAND_STOP_FETCHING)
    else:
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_START_FETCHING"),
                                                      callback_data=_COMMAND_START_FETCHING)

    return InlineKeyboardMarkup(((button_reload_configuration,), (button_toggle_fetching,)), )


def _general_status(result_message: str = None) -> str:
    """Format general status of the system"""

    trans = i18n.default()

    def format_stats() -> str:
        controls = trans.ngettext("PIECE_CONTROLS_S {count}", "PIECE_CONTROLS_P {count}", state.control_count()).format(
            count=state.control_count())
        participants = trans.ngettext("PIECE_PARTICIPANTS_S {count}", "PIECE_PARTICIPANTS_P {count}",
                                      state.participant_count()).format(count=state.participant_count())

        return trans.gettext("PIECE_ADMIN_STATS {controls} {participants}").format(controls=controls,
                                                                                   participants=participants)

    message = []
    event = state.Event()
    if not event.valid:
        message.append(trans.gettext("MESSAGE_ADMIN_START_STATUS_UNKNOWN"))
    else:
        message.append("<strong>{event_name}</strong>".format(event_name=event.name(trans)))
        message.append(format_stats())
        message.append(format.event_status(trans))

    if result_message:
        message.append("<em>{message}</em>".format(message=result_message))

    return "\n\n".join(message)


async def _handle_command_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the administrator's entry point message with the keyboard"""

    user = update.effective_message.from_user

    if user.id != settings.DEVELOPER_CHAT_ID:
        logging.info("User {username} tried to invoke the admin UI".format(username=user.username))
        return

    await context.bot.send_message(chat_id=user.id, text=_general_status(), reply_markup=_keyboard())


def _is_admin_query(data) -> bool:
    """Return whether `data` is one of administrator's sub-commands triggered by keyboard buttons"""

    return data in (_COMMAND_RELOAD_CONFIGURATION, _COMMAND_START_FETCHING, _COMMAND_STOP_FETCHING)


async def _handle_query_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle a button press"""

    query = update.callback_query
    user = query.from_user

    if user.id != settings.DEVELOPER_CHAT_ID:
        logging.error(f"User {user.id} (username '{user.username}') is not listed as administrator!")
        return

    await query.answer()

    trans = i18n.default()

    if query.data == _COMMAND_RELOAD_CONFIGURATION:
        await query.edit_message_text(_general_status(trans.gettext("MESSAGE_ADMIN_RELOADING_CONFIGURATION")),
                                      reply_markup=_keyboard())
        if await remote.reload_configuration():
            await query.edit_message_text(_general_status(trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOAD_SUCCESS")),
                                          reply_markup=_keyboard())
        else:
            await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOAD_ERROR"),
                                          reply_markup=_keyboard())
    elif query.data == _COMMAND_START_FETCHING:
        remote.start_fetching(context.application)
        await query.edit_message_text(_general_status(trans.gettext("MESSAGE_ADMIN_FETCHING_STARTED")),
                                      reply_markup=_keyboard())
    elif query.data == _COMMAND_STOP_FETCHING:
        remote.stop_fetching()
        await query.edit_message_text(_general_status(trans.gettext("MESSAGE_ADMIN_FETCHING_STOPPED")),
                                      reply_markup=_keyboard())
    else:
        raise RuntimeError("Unknown sub-command: {c}".format(c=query.data))


def init(application: Application) -> None:
    """Do what is necessary for the administrator's interface at the initial step (before starting the polling)"""

    application.add_handler(CommandHandler(_COMMAND_ADMIN, _handle_command_admin))
    application.add_handler(CallbackQueryHandler(_handle_query_admin, pattern=_is_admin_query))
