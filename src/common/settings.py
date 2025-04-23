"""
Effective configuration of the bot

Merges the default settings defined in `/common/defaults.py` with the settings defined by the user in `settings.yaml`
"""

import pathlib

import yaml
# noinspection PyUnresolvedReferences
from common.defaults import *

_SETTINGS_FILENAME = "/usr/local/etc/audax-tracker/settings.yaml" if SERVICE_MODE else pathlib.Path(
    __file__).parent.parent / "settings.yaml"

_user_settings = yaml.safe_load(open(_SETTINGS_FILENAME))

BOT_TOKEN = _user_settings["BOT_TOKEN"]
DEVELOPER_CHAT_ID = _user_settings["DEVELOPER_CHAT_ID"]
REMOTE_ENDPOINT_URL = _user_settings["REMOTE_ENDPOINT_URL"]
REMOTE_ENDPOINT_AUTH_TOKEN = _user_settings["REMOTE_ENDPOINT_AUTH_TOKEN"]

if "DEFAULT_LANGUAGE" in _user_settings:
    DEFAULT_LANGUAGE = _user_settings["DEFAULT_LANGUAGE"]
if "SUPPORTED_LANGUAGES" in _user_settings:
    SUPPORTED_LANGUAGES = _user_settings["SUPPORTED_LANGUAGES"]
if "TIME_ZONE" in _user_settings:
    TIME_ZONE = _user_settings["TIME_ZONE"]

if "FETCHING_INTERVAL_MINUTES" in _user_settings:
    FETCHING_INTERVAL_MINUTES = _user_settings["FETCHING_INTERVAL_MINUTES"]


def source_path() -> str:
    """Return path to the file from which the settings were loaded"""

    return _SETTINGS_FILENAME
