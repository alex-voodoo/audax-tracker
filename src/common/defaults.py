"""
Default configuration of the bot

DO NOT EDIT THIS FILE to configure your instance of the bot, instead edit `settings.yaml`.  Please refer to `README.md`
for more details.
"""
import os

# Working mode.
SERVICE_MODE = os.getenv("AUDAX_TRACKER_SERVICE_MODE") == "1"

# ----------------------------------------------------------------------------------------------------------------------
# Internationalisation
#
# Language to fall back to if there is no translation to the user's language. Default is "en".
DEFAULT_LANGUAGE = "en"
# Supported languages.  Must be a subset of languages that present in the `locales` directory.  Default is a tuple that
# contains all available languages.
SUPPORTED_LANGUAGES = ("en", "ru")
# Time zone in which the event is held, and in which all dates and times are presented.  Default is "UTC".
TIME_ZONE = "UTC"

# ----------------------------------------------------------------------------------------------------------------------
# Data fetching
#
# Fetching interval in minutes.  Default is 5.
FETCHING_INTERVAL_MINUTES = 5

# ----------------------------------------------------------------------------------------------------------------------
# Other settings
#
# Telegram limits the maximum size of messages.  To not surpass it, the bot limits number of subscriptions for a single
# user.  Default is 20.
MAX_SUBSCRIPTION_COUNT = 20
