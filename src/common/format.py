"""
String helper functions for formatting pieces of messages
"""

import datetime
from zoneinfo import ZoneInfo

from common import settings, state


def datetime_remainder(trans, delta: datetime.timedelta) -> str:
    """Format time delta as days, hours and minutes"""

    hours = int(delta.seconds / 3600)
    minutes = int(delta.seconds % 3600 / 60)
    days_str = trans.ngettext("PIECE_DAYS_S {days}", "PIECE_DAYS_P {days}", delta.days).format(days=delta.days)
    hours_str = trans.ngettext("PIECE_HOURS_S {hours}", "PIECE_HOURS_P {hours}", hours).format(hours=hours)
    minutes_str = trans.ngettext("PIECE_MINUTES_S {minutes}", "PIECE_MINUTES_P {minutes}", minutes).format(
        minutes=minutes)

    return "{d}, {h}, {m}".format(d=days_str, h=hours_str, m=minutes_str)


def event_status(trans) -> str:
    """Format current status of the event"""

    now = datetime.datetime.now().astimezone(ZoneInfo(settings.TIME_ZONE))
    if now < state.event_start():
        return trans.gettext("PIECE_ADMIN_START_STATUS_BEFORE_START {remainder}").format(
            remainder=datetime_remainder(trans, state.event_start() - now))
    elif now < state.event_finish():
        return trans.gettext("PIECE_ADMIN_START_STATUS_IN_AIR {remainder}").format(
            remainder=datetime_remainder(trans, state.event_finish() - now))
    else:
        return trans.gettext("PIECE_ADMIN_START_STATUS_FINISHED")


def month_name(trans, month_index: int) -> str:
    """Return name of the month"""

    if month_index == 1:
        return trans.gettext("PIECE_DATETIME_JAN")
    elif month_index == 2:
        return trans.gettext("PIECE_DATETIME_FEB")
    elif month_index == 3:
        return trans.gettext("PIECE_DATETIME_MAR")
    elif month_index == 4:
        return trans.gettext("PIECE_DATETIME_APR")
    elif month_index == 5:
        return trans.gettext("PIECE_DATETIME_MAY")
    elif month_index == 6:
        return trans.gettext("PIECE_DATETIME_JUN")
    elif month_index == 7:
        return trans.gettext("PIECE_DATETIME_JUL")
    elif month_index == 8:
        return trans.gettext("PIECE_DATETIME_AUG")
    elif month_index == 9:
        return trans.gettext("PIECE_DATETIME_SEP")
    elif month_index == 10:
        return trans.gettext("PIECE_DATETIME_OCT")
    elif month_index == 11:
        return trans.gettext("PIECE_DATETIME_NOV")
    elif month_index == 12:
        return trans.gettext("PIECE_DATETIME_DEC")
    else:
        raise RuntimeError("Wrong month number: ".format(month_index))


def control_name(trans, control_id: str):
    return state.controls()[control_id]["name"][trans.info()["language"]] if control_id else ""


def checkin_day_and_time(trans, timestamp: str) -> str:
    """Format a datetime object in checkin format, which is month, day, hour and minute"""

    checkin_time = datetime.datetime.fromisoformat(timestamp)
    return trans.gettext("CHECKIN_DATE_AND_TIME {month} {day} {hour} {minute}").format(day=checkin_time.day,
                                                                                       hour=checkin_time.hour,
                                                                                       minute=checkin_time.minute,
                                                                                       month=month_name(
                                                                                           trans,
                                                                                           checkin_time.month))


def result_time(timestamp: str) -> str:
    """Calculate difference with event start and format result as hours and minutes"""

    delta = datetime.datetime.fromisoformat(timestamp) - state.event_start()
    hours = int(delta.seconds / 3600)
    minutes = int(delta.seconds % 3600 / 60)
    return f"{hours}:{minutes:02d}"


def participant_status(trans, participant: state.Participant) -> str:
    """Format current status of the participant"""

    if not participant.last_known_control_id:
        return trans.gettext("LAST_KNOWN_STATUS_UNKNOWN {participant_label}").format(
            participant_label=participant.label)

    if state.controls()[participant.last_known_control_id]["finish"]:
        return trans.gettext("LAST_KNOWN_STATUS_FINISH {participant_label} {result_time}").format(
            participant_label=participant.label,
            result_time=result_time(participant.last_known_checkin_time))

    if participant.last_known_checkin_time:
        return trans.gettext(
            "LAST_KNOWN_STATUS_OK {participant_label} {checkin_time} {control_name} {distance}").format(
                control_name=control_name(trans, participant.last_known_control_id),
                checkin_time=checkin_day_and_time(trans, participant.last_known_checkin_time),
                distance=state.controls()[participant.last_known_control_id]["distance"],
                participant_label=participant.label)

    return trans.gettext("LAST_KNOWN_STATUS_ABANDONED {participant_label} {control_name} {distance}").format(
        control_name=control_name(trans, participant.last_known_control_id),
        distance=state.controls()[participant.last_known_control_id]["distance"],
        participant_label=participant.label)
