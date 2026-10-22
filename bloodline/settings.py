"""Runtime settings and secrets.

Values are read, in order, from:
1. environment variables (a local ``.env`` file is loaded automatically);
2. Streamlit secrets (``.streamlit/secrets.toml`` locally, or the
   "Secrets" box of Streamlit Community Cloud).

See ``.env.example`` for every available key.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # optional in production
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass

DEFAULTS = {
    "BLOODLINE_STORAGE": "csv",  # "csv" or "gsheets"
    "BLOODLINE_CSV_PATH": ".data/results.csv",
    "BLOODLINE_PUBLIC_URL": "http://localhost:8501",
    "BLOODLINE_REPO_URL": "https://github.com/AbrSantiago/bloodline",
    "GSHEETS_RESULTS_SPREADSHEET_ID": "",
    "GSHEETS_RESULTS_WORKSHEET": "results",
    "GOOGLE_SERVICE_ACCOUNT_JSON": "",
    "GOOGLE_SERVICE_ACCOUNT_FILE": "",
}


def _from_streamlit_secrets(key: str) -> str | None:
    try:
        import streamlit as st

        value = st.secrets.get(key)
    except Exception:  # no secrets file, or not running under Streamlit
        return None
    if value is None:
        return None
    if isinstance(value, dict):  # a TOML table, e.g. the service account
        import json

        return json.dumps(dict(value))
    return str(value)


def get(key: str, default: str | None = None) -> str:
    value = os.environ.get(key)
    if not value:
        value = _from_streamlit_secrets(key)
    if not value:
        value = default if default is not None else DEFAULTS.get(key, "")
    return value
