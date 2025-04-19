"""
Admin stuff
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from . import i18n, remote, settings, state


ADMIN_RELOAD_CONFIGURATION, ADMIN_STOP_FETCHING, ADMIN_START_FETCHING = (
    "admin-reload-configuration", "admin-stop-fetching", "admin-start-fetching")


def get_admin_keyboard() -> InlineKeyboardMarkup:
    trans = i18n.default()

    button_reload_participants = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_RELOAD_PARTICIPANTS"),
                                                      callback_data=ADMIN_RELOAD_CONFIGURATION)
    if remote.is_fetching():
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_STOP_FETCHING"),
                                                      callback_data=ADMIN_STOP_FETCHING)
    else:
        button_toggle_fetching = InlineKeyboardButton(trans.gettext("BUTTON_ADMIN_START_FETCHING"),
                                                      callback_data=ADMIN_START_FETCHING)

    return InlineKeyboardMarkup(((button_reload_participants,), (button_toggle_fetching,)), )


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
        if await remote.reload_configuration():
            await query.edit_message_text(
                trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOADED {control_count} {participant_count}").format(
                    control_count=len(state.controls()), participant_count=len(state.participants())),
                reply_markup=get_admin_keyboard())
        else:
            await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_CONFIGURATION_RELOAD_ERROR"),
                                          reply_markup=get_admin_keyboard())
    elif query.data == ADMIN_STOP_FETCHING:
        remote.stop_fetching()
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_FETCHING_STOPPED"),
                                      reply_markup=get_admin_keyboard())
    elif query.data == ADMIN_START_FETCHING:
        remote.start_fetching(context.application)
        await query.edit_message_text(trans.gettext("MESSAGE_ADMIN_FETCHING_STARTED"),
                                      reply_markup=get_admin_keyboard())
