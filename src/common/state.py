"""
Persistent state
"""

import datetime
import gettext
import json
import logging
import pathlib
from collections.abc import Iterator

from telegram import User

from . import settings

_STATE_FILENAME = "/var/local/audax-tracker/state.json" if settings.SERVICE_MODE else pathlib.Path(
    __file__).parent.parent / "state.json"

# Keys used in the state object
(_CHECKIN_TIME, _CONTROL, _CONTROLS, _EVENT, _FEED_STATUS, _FINISH, _IS_FETCHING, _LANG, _LAST_KNOWN_STATUS,
 _LAST_SUCCESSFUL_FETCH, _NAME, _NUMBERS, _PARTICIPANTS, _START, _SUBSCRIPTIONS) = (
    "checkin_time", "control", "controls", "event", "feed_status", "finish", "is_fetching", "lang", "last_known_status",
    "last_successful_fetch", "name", "numbers", "participants", "start", "subscriptions")

# If set, called back when participants are removed from the state
_on_participant_removed = None


class Control:
    """Read-only convenience wrapper that describes a control"""

    _DISTANCE = "distance"
    _FINISH = "finish"
    _NAME = "name"

    def __init__(self, control_id: str):
        data = _state[_CONTROLS][control_id]

        self._name = data[self._NAME]

        self.distance = data[self._DISTANCE]
        self.finish = data[self._FINISH]

    def name(self, trans: gettext.GNUTranslations):
        return self._name[trans.info()["language"]]


class Event:
    """Read-only convenience wrapper that describes the event"""

    def __init__(self):
        data = _state[_EVENT]

        self.start = datetime.datetime.fromisoformat(data[_START]) if _START in data else None
        self.finish = datetime.datetime.fromisoformat(data[_FINISH]) if _FINISH in data else None
        self._name = data[_NAME] if _NAME in data else None

        self.valid = self.start is not None and self.finish is not None and self._name is not None

    def name(self, trans: gettext.GNUTranslations):
        return self._name[trans.info()["language"]] if self._name is not None else ""


class Participant:
    """Read-only convenience wrapper that describes a participant"""

    def __init__(self, frame_plate_number: str, other_data=None):
        data = other_data if other_data else _state[_PARTICIPANTS][frame_plate_number]

        self.frame_plate_number = frame_plate_number
        self.name = data[_NAME]

        last_known_status = data[_LAST_KNOWN_STATUS] if _LAST_KNOWN_STATUS in data else {}

        self.last_known_control_id = last_known_status[_CONTROL] if _CONTROL in last_known_status else None
        self.last_known_checkin_time = last_known_status[_CHECKIN_TIME] if _CHECKIN_TIME in last_known_status else None

    @property
    def label(self) -> str:
        return f"{self.frame_plate_number} {self.name}"


class Subscription:
    """Read-only convenience wrapper that describes a subscription"""

    def __init__(self, tg_id: str):
        data = _state[_SUBSCRIPTIONS][tg_id]

        self.tg_id = tg_id
        self.lang = data[_LANG]
        self.numbers = sorted(data[_NUMBERS], key=lambda n: int(n))


# State object.  Loaded once from the file, then used in-memory, saved to the file when changed.
_state = {}


def _save() -> None:
    if _state is not None:
        with open(_STATE_FILENAME, "w", encoding="utf8") as json_file:
            json.dump(_state, json_file, ensure_ascii=False)


def _maybe_load() -> None:
    global _state

    if _state:
        return

    try:
        with open(_STATE_FILENAME, "r") as json_file:
            _state = json.load(json_file)
    except FileNotFoundError:
        # First run, no problem, creating an empty state.
        _state = {_PARTICIPANTS: {}, _CONTROLS: {}, _SUBSCRIPTIONS: {},
                  _FEED_STATUS: {_IS_FETCHING: False, _LAST_SUCCESSFUL_FETCH: None}}


def is_fetching() -> bool:
    """Return whether the current state is fetching"""

    _maybe_load()
    return _state[_FEED_STATUS][_IS_FETCHING]


def set_is_fetching(new_value: bool) -> None:
    """Set the fetching state"""

    global _state
    _state[_FEED_STATUS][_IS_FETCHING] = new_value
    _save()


def last_successful_fetch() -> str:
    """Return the last successful fetch, if it was stored, or None otherwise"""

    _maybe_load()
    return _state[_FEED_STATUS][_LAST_SUCCESSFUL_FETCH]


def set_last_successful_fetch(new_value: str) -> None:
    """Set the last successful fetch"""

    global _state

    _state[_FEED_STATUS][_LAST_SUCCESSFUL_FETCH] = new_value
    _save()


def set_event(new_value: dict) -> None:
    global _state

    _state[_EVENT] = new_value
    _save()


def control_count() -> int:
    _maybe_load()
    return len(_state[_CONTROLS])


def set_controls(new_value: list) -> None:
    global _state

    _state[_CONTROLS] = new_value
    _save()


def participant_count() -> int:
    _maybe_load()
    return len(_state[_PARTICIPANTS])


def set_participants(new_value: dict) -> None:
    global _state

    old_participants = _state[_PARTICIPANTS] if _PARTICIPANTS in _state else {}

    def get_last_known_status(n: str) -> dict:
        if n not in old_participants or _LAST_KNOWN_STATUS not in old_participants[n]:
            return {}
        return old_participants[n][_LAST_KNOWN_STATUS]

    _state[_PARTICIPANTS] = {}
    for frame_plate_number, name in new_value.items():
        _state[_PARTICIPANTS][frame_plate_number] = {
            _NAME: name,
            _LAST_KNOWN_STATUS: get_last_known_status(frame_plate_number)
        }

    removed_participants = {k: Participant(k, v) for k, v in old_participants.items() if k not in _state[_PARTICIPANTS]}
    if not removed_participants:
        logging.info("No participants were removed")
    else:
        logging.info(f"Removed participants: {removed_participants}")

        packages = {}
        for subscription in subscriptions():
            for k, v in removed_participants.items():
                if k in subscription.numbers:
                    if subscription.tg_id not in packages:
                        packages[subscription.tg_id] = []
                    packages[subscription.tg_id].append(v)

                    remove_subscription(subscription.tg_id, k)

        if _on_participant_removed:
            _on_participant_removed(packages)

    _save()


def subscriptions() -> Iterator:
    _maybe_load()

    for tg_id in _state[_SUBSCRIPTIONS]:
        yield Subscription(tg_id)


def add_subscription(user: User, frame_plate_number: str) -> None:
    global _state

    tg_id = str(user.id)
    if tg_id not in _state[_SUBSCRIPTIONS]:
        _state[_SUBSCRIPTIONS][tg_id] = {_LANG: "", _NUMBERS: []}
    _state[_SUBSCRIPTIONS][tg_id][
        _LANG] = user.language_code if user.language_code in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        _state[_SUBSCRIPTIONS][tg_id][_NUMBERS].append(frame_plate_number)

    logging.info(f"Subscribed Telegram user {tg_id} at participant {frame_plate_number}")
    _save()


def remove_subscription(tg_id: str, frame_plate_number: str) -> None:
    global _state

    if tg_id not in _state[_SUBSCRIPTIONS]:
        return
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        return
    _state[_SUBSCRIPTIONS][tg_id][_NUMBERS].remove(frame_plate_number)
    logging.info(f"Unsubscribed Telegram user {tg_id} from participant {frame_plate_number}")

    if not _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        del _state[_SUBSCRIPTIONS][tg_id]
        logging.info(f"Telegram user {tg_id} has no more subscriptions; removed them completely")

    _save()


def has_subscriber(tg_id: str) -> bool:
    return tg_id in _state[_SUBSCRIPTIONS]


def has_subscription(tg_id: str, frame_plate_number: str) -> bool:
    return tg_id in _state[_SUBSCRIPTIONS] and frame_plate_number in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]


def has_participant(frame_plate_number: str) -> bool:
    return frame_plate_number in _state[_PARTICIPANTS]


def maybe_set_participant_last_known_status(frame_plate_number: str, control_id: str, checkin_time: str) -> bool:
    """Set last known status of the participant iff there is no newer status already

    Returns whether the state was changed.
    """

    global _state

    p = Participant(frame_plate_number)
    if (p.last_known_control_id and p.last_known_control_id != control_id and
            p.last_known_checkin_time and checkin_time is not None and checkin_time < p.last_known_checkin_time):
        logging.info(f"Ignoring checkin of participant {frame_plate_number} at control {control_id} at {checkin_time} "
                     f"because they have checked in at control {p.last_known_control_id} "
                     f"at {p.last_known_checkin_time} (more recently)")
        return False

    global _state
    _state[_PARTICIPANTS][frame_plate_number][_LAST_KNOWN_STATUS][_CONTROL] = control_id
    _state[_PARTICIPANTS][frame_plate_number][_LAST_KNOWN_STATUS][_CHECKIN_TIME] = checkin_time

    logging.info(f"New last known checkin time for participant {frame_plate_number} is {checkin_time}")

    _save()

    return True


def set_on_participant_removed(handler) -> None:
    global _on_participant_removed

    _on_participant_removed = handler
