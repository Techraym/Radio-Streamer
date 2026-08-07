#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

CONFIG_PATH = os.environ.get("NRG_CONFIG", "/etc/nrg-radio/config.json")


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def db_connect(config: dict[str, Any] | None = None) -> sqlite3.Connection:
    config = config or load_config()
    db = Path(config["station"]["database"])
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            artist TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            album TEXT NOT NULL DEFAULT '',
            genre TEXT NOT NULL DEFAULT '',
            year INTEGER,
            duration REAL,
            mtime REAL NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
        CREATE INDEX IF NOT EXISTS idx_tracks_enabled ON tracks(enabled);
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_history_track_time ON play_history(track_id, played_at);
        CREATE TABLE IF NOT EXISTS radio_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            track_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(radio_state)").fetchall()}
    if "updated_at" not in columns:
        conn.execute("ALTER TABLE radio_state ADD COLUMN updated_at TEXT")
        conn.execute("UPDATE radio_state SET updated_at=CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    conn.commit()


def set_state(conn: sqlite3.Connection, key: str, value: Any) -> None:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    conn.execute("""
        INSERT INTO radio_state(key, value, updated_at)
        VALUES(?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
    """, (key, value))
    conn.commit()


def get_state(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM radio_state WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return row["value"]
