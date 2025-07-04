"""
Calls to the remote endpoint
"""

import logging

import requests
from telegram.error import Forbidden
from telegram.ext import ContextTypes, Application

from . import format, i18n, settings, state


_periodic_fetching_job = None


def is_fetching() -> bool:
    return _periodic_fetching_job is not None


async def reload_configuration() -> bool:
    try:
        request = {"token": settings.REMOTE_ENDPOINT_AUTH_TOKEN, "method": "get-configuration"}
        logging.info("Sending request: {}".format(request))
        response_raw = requests.post(settings.REMOTE_ENDPOINT_URL, json=request)
        if response_raw.status_code != 200:
            logging.info("Got HTTP error response: {c} {r}".format(c=response_raw.status_code, r=response_raw.reason))
            return False

        response = response_raw.json()
        if not response["success"]:
            logging.info("Got API error response: {}".format(response["error_message"]))
            return False

        logging.info(response)

        state.set_event(response["event"])
        state.set_controls(response["controls"])
        state.set_participants(response["participants"])

        return True

    except Exception as e:
        logging.error(e)
        return False


async def periodic_fetch_data_and_notify_subscribers(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        request = {"token": settings.REMOTE_ENDPOINT_AUTH_TOKEN, "method": "get-tracking-updates",
                   "since": state.last_successful_fetch()}
        response_raw = requests.post(settings.REMOTE_ENDPOINT_URL, json=request)
        if response_raw.status_code != 200:
            logging.info("Got HTTP error response: {c} {r}".format(c=response_raw.status_code, r=response_raw.reason))
            return

        response = response_raw.json()
        if not response["success"]:
            logging.info("Got API error response: {}".format(response["error_message"]))
            return

        logging.info(response)

        logging.info("Got data response from the remote endpoint, preparing updates for the subscribers.")
        packages = {}
        for update in response["updates"]:
            for subscription in state.subscriptions():
                if update["frame_plate_number"] in subscription.numbers:
                    if subscription.tg_id not in packages:
                        packages[subscription.tg_id] = []
                    packages[subscription.tg_id].append(update)

        for tg_id, updates in packages.items():
            checkins = []
            trans = i18n.for_lang(state.Subscription(tg_id).lang)
            for update in sorted(updates, key=lambda u: int(u['frame_plate_number'])):
                frame_plate_number = update["frame_plate_number"]
                control_id = str(update["control"])
                checkin_time = update["checkin_time"]
                if state.maybe_set_participant_last_known_status(frame_plate_number, control_id, checkin_time):
                    checkins.append(format.participant_status(trans, state.Participant(frame_plate_number)))

            try:
                await context.bot.send_message(chat_id=tg_id,
                                               text=trans.gettext("MESSAGE_CHECKIN_UPDATE {entries}").format(
                                                                  entries="\n".join(checkins)))
            except Forbidden as e:
                logging.error(f"Got Forbidden when sending an update to user {tg_id}!  Removing their subscription.")
                state.remove_subscriber(tg_id)

        state.set_last_successful_fetch(response["next_since"])

    except Exception:
        await context.bot.send_message(chat_id=settings.DEVELOPER_CHAT_ID,
                                       text=i18n.default().gettext("MESSAGE_ADMIN_FETCHING_STOPPED_AFTER_FAILURE"))

        stop_fetching()
        raise


def start_fetching(application: Application) -> None:
    global _periodic_fetching_job

    if _periodic_fetching_job:
        logging.error("Called start_fetching() but already fetching!")
        return

    _periodic_fetching_job = application.job_queue.run_repeating(periodic_fetch_data_and_notify_subscribers,
                                                                 interval=60 * settings.FETCHING_INTERVAL_MINUTES,
                                                                 first=10)

    state.set_is_fetching(True)


def stop_fetching() -> None:
    global _periodic_fetching_job

    if not _periodic_fetching_job:
        logging.error("Called stop_fetching() but not fetching!")
        return

    _periodic_fetching_job.schedule_removal()
    _periodic_fetching_job = None

    state.set_is_fetching(False)
