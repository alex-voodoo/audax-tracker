"""
String helper functions for formatting pieces of messages
"""

import datetime
from zoneinfo import ZoneInfo

from common import settings, state


def datetime_remainder(trans, delta: datetime.timedelta) -> str:
    hours = int(delta.seconds / 3600)
    minutes = int(delta.seconds % 3600 / 60)
    days_str = trans.ngettext("PIECE_DAYS_S {days}", "PIECE_DAYS_P {days}", delta.days).format(days=delta.days)
    hours_str = trans.ngettext("PIECE_HOURS_S {hours}", "PIECE_HOURS_P {hours}", hours).format(hours=hours)
    minutes_str = trans.ngettext("PIECE_MINUTES_S {minutes}", "PIECE_MINUTES_P {minutes}", minutes).format(
        minutes=minutes)

    return "{d}, {h}, {m}".format(d=days_str, h=hours_str, m=minutes_str)


def event_status(trans) -> str:
    now = datetime.datetime.now().astimezone(ZoneInfo(settings.TIME_ZONE))
    if now < state.event_start():
        return trans.gettext("PIECE_ADMIN_START_STATUS_BEFORE_START {remainder}").format(
            remainder=datetime_remainder(trans, state.event_start() - now))
    elif now < state.event_finish():
        return trans.gettext("PIECE_ADMIN_START_STATUS_IN_AIR {remainder}").format(
            remainder=datetime_remainder(trans, state.event_finish() - now))
    else:
        return trans.gettext("PIECE_ADMIN_START_STATUS_FINISHED")
