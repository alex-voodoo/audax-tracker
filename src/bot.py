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
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, Defaults

from common import i18n, remote, settings, state
from users import admin, public


# Configure logging
# Set higher logging level for httpx to avoid all GET and POST requests being logged.
# noinspection SpellCheckingInspection
logging.basicConfig(format="[%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d] %(message)s",
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


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
                                    filename=f"audax-tracker-error-{error_uuid}.txt")

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            i18n.trans(update.effective_message.from_user).gettext("MESSAGE_DM_INTERNAL_ERROR {error_uuid}").format(
                error_uuid=error_uuid))


async def post_init(application: Application) -> None:
    await public.post_init(application)


def main() -> None:
    """Entry point"""

    logging.info("The bot starts in {m} mode".format(m="service" if settings.SERVICE_MODE else "direct"))
    logging.info(f"Settings are loaded from {settings.source_path()}")
    logging.info(f"Remote endpoint URL: {settings.REMOTE_ENDPOINT_URL}, "
                 f"data is queried every {settings.FETCHING_INTERVAL_MINUTES} minutes")

    application = (Application.builder()
                   .token(settings.BOT_TOKEN)
                   .defaults(Defaults(parse_mode=ParseMode.HTML))
                   .post_init(post_init)
                   .build())

    admin.init(application)
    public.init(application)

    application.add_error_handler(handle_error)

    if state.is_fetching():
        logging.info("Last state is: fetching, starting")
        remote.start_fetching(application)
    else:
        logging.info("Last state is: not fetching, staying idle")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
