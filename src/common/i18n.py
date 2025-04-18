"""
Internationalisation utilities
"""

import gettext

from telegram import User

from . import settings

_last_used_lang = None
_last_used_trans = None


def default():
    """Get the default translator"""

    return gettext.translation("bot", localedir="locales", languages=[settings.DEFAULT_LANGUAGE])


def for_lang(language_code: str):
    """Get the translator for `language_code` if it exists"""

    return gettext.translation("bot", localedir="locales", languages=[
        language_code if language_code in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE])


def trans(user: User):
    """Get a translator for the given user

    Respects the language-related settings.  Caches the translator and only loads another one if the language changes.
    """

    if user.language_code not in settings.SUPPORTED_LANGUAGES:
        user_lang = settings.DEFAULT_LANGUAGE
    else:
        user_lang = user.language_code

    global _last_used_lang, _last_used_trans
    if _last_used_lang != user_lang:
        _last_used_lang = user_lang
        _last_used_trans = gettext.translation("bot", localedir="locales", languages=[user_lang])

    return _last_used_trans
