"""
Database stuff
"""
import json

_STATE_FILENAME = "state.json"

# State object.  Loaded once from the file, then used in-memory, saved to the file when changed.
_state = {}

# Keys used in the state object
_PARTICIPANTS, _CONTROLS, _SUBSCRIPTIONS, _FEED_STATUS, _IS_FETCHING, _LAST_SUCCESSFUL_FETCH = (
    "participants", "controls", "subscriptions", "feed_status", "is_fetching", "last_successful_fetch")


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
        _state = {_PARTICIPANTS: [], _CONTROLS: {}, _SUBSCRIPTIONS: {},
                  _FEED_STATUS: {_IS_FETCHING: False, _LAST_SUCCESSFUL_FETCH: None}}


def is_fetching() -> bool:
    """Return whether the current state is fetching"""

    _maybe_load()
    return _state[_FEED_STATUS][_IS_FETCHING]


def set_is_fetching(new_value: bool) -> None:
    """Sets the fetching state"""

    global _state
    _state[_FEED_STATUS][_IS_FETCHING] = new_value
    _save()


def last_successful_fetch() -> str:
    """Return the last successful fetch, if it was stored, or None otherwise"""

    _maybe_load()
    return _state[_FEED_STATUS][_LAST_SUCCESSFUL_FETCH]


def set_last_successful_fetch(new_value: str) -> None:
    """Sets the last successful fetch"""

    global _state
    _state[_FEED_STATUS][_LAST_SUCCESSFUL_FETCH] = new_value
    _save()


def controls() -> dict:
    _maybe_load()
    return _state[_CONTROLS]


def set_controls(new_value: list) -> None:
    global _state
    _state[_CONTROLS] = new_value
    _save()


def participants() -> list:
    _maybe_load()
    return _state[_PARTICIPANTS]


def set_participants(new_value: list) -> None:
    global _state
    _state[_PARTICIPANTS] = new_value
    _save()


def subscriptions() -> dict:
    _maybe_load()
    return _state[_SUBSCRIPTIONS]


def add_subscription(tg_id: str, frame_plate_number: str) -> None:
    global _state
    if tg_id not in _state[_SUBSCRIPTIONS]:
        _state[_SUBSCRIPTIONS][tg_id] = []
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id]:
        _state[_SUBSCRIPTIONS][tg_id].append(frame_plate_number)
    _save()


def remove_subscription(tg_id: str, frame_plate_number: str) -> None:
    global _state
    if tg_id not in _state[_SUBSCRIPTIONS]:
        return
    if frame_plate_number not in _state[_SUBSCRIPTIONS][tg_id]:
        return
    _state[_SUBSCRIPTIONS][tg_id].remove(frame_plate_number)
    if not _state[_SUBSCRIPTIONS][tg_id]:
        del _state[_SUBSCRIPTIONS][tg_id]
    _save()


def has_subscription(tg_id: str, frame_plate_number: str) -> bool:
    return tg_id in _state[_SUBSCRIPTIONS] and frame_plate_number in _state[_SUBSCRIPTIONS][tg_id]


def has_participant(frame_plate_number: str) -> bool:
    return frame_plate_number in _state[_PARTICIPANTS]
