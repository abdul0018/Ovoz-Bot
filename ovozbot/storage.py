"""SQLite: foydalanuvchi sozlamalari va transkripsiyalar (bot qayta ishga tushganda ham tugmalar ishlaydi)."""
import secrets
import sqlite3
import time
from pathlib import Path

from .models import Transcript

TRANSCRIPT_TTL_DAYS = 30


class Storage:
    def __init__(self, path: Path, default_gender: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.default_gender = default_gender
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                gender  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transcripts (
                token   TEXT PRIMARY KEY,
                user_id INTEGER,
                created INTEGER NOT NULL,
                data    TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS transcripts_created ON transcripts(created);
            """
        )
        self.prune()

    # --- foydalanuvchi sozlamalari ---

    def gender(self, user_id: int) -> str:
        row = self.db.execute("SELECT gender FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else self.default_gender

    def set_gender(self, user_id: int, gender: str) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO users(user_id, gender) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET gender = excluded.gender",
                (user_id, gender),
            )

    # --- transkripsiyalar ---

    def save_transcript(self, user_id: int, transcript: Transcript) -> str:
        token = secrets.token_urlsafe(8)
        with self.db:
            self.db.execute(
                "INSERT INTO transcripts(token, user_id, created, data) VALUES (?, ?, ?, ?)",
                (token, user_id, int(time.time()), transcript.model_dump_json()),
            )
        return token

    def get_transcript(self, token: str) -> Transcript | None:
        row = self.db.execute("SELECT data FROM transcripts WHERE token = ?", (token,)).fetchone()
        return Transcript.model_validate_json(row[0]) if row else None

    def update_transcript(self, token: str, transcript: Transcript) -> None:
        with self.db:
            self.db.execute(
                "UPDATE transcripts SET data = ? WHERE token = ?",
                (transcript.model_dump_json(), token),
            )

    def prune(self) -> None:
        cutoff = int(time.time()) - TRANSCRIPT_TTL_DAYS * 86400
        with self.db:
            self.db.execute("DELETE FROM transcripts WHERE created < ?", (cutoff,))
