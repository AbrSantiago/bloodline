"""Where finished games are stored (for the ranking).

* ``CsvStore``: a local CSV file. Default for development. On Streamlit
  Community Cloud the disk is wiped when the app restarts, so use it only
  for testing there.
* ``GSheetsStore``: a Google Sheet, shared by every player. Used in
  production.
"""

from __future__ import annotations

import csv
import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path

from .. import settings

FIELDS = [
    "timestamp",
    "nick",
    "seed",
    "outcome",
    "risk",
    "p_perfect",
    "tests_used",
    "founders",
    "lang",
    "version",
]


class ResultStore(ABC):
    @abstractmethod
    def save(self, record: dict) -> None: ...

    @abstractmethod
    def load(self) -> list[dict]: ...


class CsvStore(ResultStore):
    _lock = threading.Lock()

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, record: dict) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            new = not self.path.exists()
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                if new:
                    writer.writeheader()
                writer.writerow(record)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


class GSheetsStore(ResultStore):
    """Appends one row per game to a worksheet of a Google Sheet.

    The sheet must be shared (as Editor) with the service account e-mail.
    """

    def __init__(self, spreadsheet_id: str, worksheet: str, service_account_info: dict):
        import gspread

        client = gspread.service_account_from_dict(service_account_info)
        book = client.open_by_key(spreadsheet_id)
        try:
            self.ws = book.worksheet(worksheet)
        except gspread.WorksheetNotFound:
            self.ws = book.add_worksheet(worksheet, rows=1000, cols=len(FIELDS))
        if self.ws.row_values(1) != FIELDS:
            self.ws.update([FIELDS], "A1")

    def save(self, record: dict) -> None:
        self.ws.append_row([record.get(k, "") for k in FIELDS], value_input_option="RAW")

    def load(self) -> list[dict]:
        return self.ws.get_all_records(expected_headers=FIELDS)


def _service_account_info() -> dict:
    raw = settings.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        return json.loads(raw)
    path = settings.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    raise RuntimeError("Google credentials missing: set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE")


def get_store() -> ResultStore:
    kind = settings.get("BLOODLINE_STORAGE").lower()
    if kind == "gsheets":
        return GSheetsStore(
            settings.get("GSHEETS_RESULTS_SPREADSHEET_ID"),
            settings.get("GSHEETS_RESULTS_WORKSHEET"),
            _service_account_info(),
        )
    return CsvStore(settings.get("BLOODLINE_CSV_PATH"))
