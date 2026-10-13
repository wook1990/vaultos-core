"""Korean / English output.

The language is chosen once per process, in this order:
VAULTOS_LANG, then `lang:` in ~/.config/vaultos/config, then the system locale.
Anything that is not Korean falls back to English.

    from vaultos_core.i18n import t
    print(t("볼트를 찾지 못했습니다", "Vault not found"))
"""

import locale
import os

LANGS = ("ko", "en")
_lang = None


def _from_config():
    path = os.path.join(os.path.expanduser("~"), ".config", "vaultos", "config")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("lang:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _detect():
    for value in (os.environ.get("VAULTOS_LANG"), _from_config()):
        if value:
            return "ko" if value.lower().startswith("ko") else "en"
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        if os.environ.get(var, "").lower().startswith("ko"):
            return "ko"
    try:
        loc = locale.getlocale()[0] or ""
    except ValueError:
        loc = ""
    return "ko" if loc.lower().startswith("ko") else "en"


def lang():
    global _lang
    if _lang is None:
        _lang = _detect()
    return _lang


def set_lang(value):
    """Force a language (tests, `vaultos --lang`)."""
    global _lang
    _lang = "ko" if (value or "").lower().startswith("ko") else "en"


def t(ko, en):
    return ko if lang() == "ko" else en
