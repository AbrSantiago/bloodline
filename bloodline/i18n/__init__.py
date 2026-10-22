"""Tiny translation helper: every UI string lives in ``<lang>.json``."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = "es"
_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def strings(lang: str) -> dict[str, str]:
    with open(_DIR / f"{lang}.json", encoding="utf-8") as f:
        return json.load(f)


def translate(lang: str, key: str, **params) -> str:
    """Return the string for ``key`` in ``lang`` (falls back to Spanish,
    then to the key itself) formatted with ``params``."""
    text = strings(lang).get(key) or strings(DEFAULT_LANGUAGE).get(key) or key
    return text.format(**params) if params else text
