"""
Internationalisation
"""

import gettext
import pathlib

from telegram import User

from . import settings

_DOMAIN = "bot"

_last_used_lang = None
_last_used_trans = None


def _get_locale_directory() -> pathlib.Path:
    """Get absolute path to the locale directory"""

    return pathlib.Path(__file__).parent.parent / "locales"


def default() -> gettext.GNUTranslations:
    """Get the default translator"""

    return gettext.translation(domain=_DOMAIN, localedir=_get_locale_directory(), languages=[settings.DEFAULT_LANGUAGE])


def for_lang(language_code: str) -> gettext.GNUTranslations:
    """Get the translator for `language_code` if it exists, otherwise the default one"""

    return gettext.translation(domain=_DOMAIN, localedir=_get_locale_directory(), languages=[
        language_code if language_code in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE])


def trans(user: User) -> gettext.GNUTranslations:
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
        _last_used_trans = gettext.translation(domain=_DOMAIN, localedir=_get_locale_directory(), languages=[user_lang])

    return _last_used_trans
