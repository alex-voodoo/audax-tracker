"""
Persistent state
"""

import datetime
import json
import logging
import pathlib

from telegram import User

from . import settings

_STATE_FILENAME = "/var/local/audax-tracker/state.json" if settings.SERVICE_MODE else pathlib.Path(
    __file__).parent.parent / "state.json"

# Keys used in the state object
(_CHECKIN_TIME, _CONTROL, _CONTROLS, _EVENT, _FEED_STATUS, _FINISH, _IS_FETCHING, _LANG, _LAST_KNOWN_STATUS,
 _LAST_SUCCESSFUL_FETCH, _NAME, _NUMBERS, _PARTICIPANTS, _START, _SUBSCRIPTIONS) = (
    "checkin_time", "control", "controls", "event", "feed_status", "finish", "is_fetching", "lang", "last_known_status",
    "last_successful_fetch", "name", "numbers", "participants", "start", "subscriptions")


class Participant:
    """Read-only convenience wrapper that describes a participant"""

    def __init__(self, frame_plate_number: str):
        data = _state[_PARTICIPANTS][frame_plate_number]

        self.frame_plate_number = frame_plate_number
        self.name = data[_NAME]

        last_known_status = data[_LAST_KNOWN_STATUS] if _LAST_KNOWN_STATUS in data else {}

        self.last_known_control_id = last_known_status[_CONTROL] if _CONTROL in last_known_status else None
        self.last_known_checkin_time = last_known_status[_CHECKIN_TIME] if _CHECKIN_TIME in last_known_status else None

    @property
    def label(self) -> str:
        return f"{self.frame_plate_number} {self.name}"


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


def event_name(lang: str) -> str:
    _maybe_load()
    if _EVENT not in _state or lang not in _state[_EVENT][_NAME]:
        return ""
    return _state[_EVENT][_NAME][lang]


def event_start() -> datetime.datetime:
    _maybe_load()
    return datetime.datetime.fromisoformat(_state[_EVENT][_START]) if _EVENT in _state else None


def event_finish() -> datetime.datetime:
    _maybe_load()
    return datetime.datetime.fromisoformat(_state[_EVENT][_FINISH]) if _EVENT in _state else None


def controls() -> dict:
    _maybe_load()
    return _state[_CONTROLS]


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

    # TODO: Handle removing participants that had subscribers.  Probably the subscribers should be notified.

    _save()


def participant(frame_plate_number: str) -> Participant:
    if frame_plate_number not in _state[_PARTICIPANTS]:
        return None

    return Participant(frame_plate_number)


def subscriptions() -> dict:
    _maybe_load()
    return _state[_SUBSCRIPTIONS]


def add_subscription(user: User, frame_plate_number: str) -> None:
    global _state

    tg_id = str(user.id)
    if tg_id not in _state[_SUBSCRIPTIONS]:
        _state[_SUBSCRIPTIONS][tg_id] = {_LANG: "", _NUMBERS: []}
    _state[_SUBSCRIPTIONS][tg_id][
        _LANG] = user.language_code if user.language_code in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        _state[_SUBSCRIPTIONS][tg_id][_NUMBERS].append(frame_plate_number)
    _save()


def remove_subscription(tg_id: str, frame_plate_number: str) -> None:
    global _state

    if tg_id not in _state[_SUBSCRIPTIONS]:
        return
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        return
    _state[_SUBSCRIPTIONS][tg_id][_NUMBERS].remove(frame_plate_number)
    if not _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]:
        del _state[_SUBSCRIPTIONS][tg_id]
    _save()


def has_subscription(tg_id: str, frame_plate_number: str) -> bool:
    return tg_id in _state[_SUBSCRIPTIONS] and frame_plate_number in _state[_SUBSCRIPTIONS][tg_id][_NUMBERS]


def has_participant(frame_plate_number: str) -> bool:
    return frame_plate_number in _state[_PARTICIPANTS]


def maybe_set_participant_last_known_status(frame_plate_number: str, control_id: str, checkin_time: str):
    """Set last known status of the participant iff there is no newer status already"""

    global _state

    p = participant(frame_plate_number)
    if (p.last_known_control_id and p.last_known_control_id != control_id and
            p.last_known_checkin_time and checkin_time < p.last_known_checkin_time):
        logging.info(f"Ignoring checkin of participant {frame_plate_number} at control {control_id} at {checkin_time} "
                     f"because they have checked in at control {p.last_known_control_id} "
                     f"at {p.last_known_checkin_time} (more recently)")
        return

    logging.info(f"New last known checkin time for participant {frame_plate_number} is {p.last_known_checkin_time}")

    global _state
    _state[_PARTICIPANTS][frame_plate_number][_LAST_KNOWN_STATUS][_CONTROL] = control_id
    _state[_PARTICIPANTS][frame_plate_number][_LAST_KNOWN_STATUS][_CHECKIN_TIME] = checkin_time

    _save()
