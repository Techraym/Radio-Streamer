#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import db_connect, ensure_schema, load_config, set_state


def set_now_playing(kind: str, path: str, track_id: int | None = None, track: Any = None):
    config = load_config()
    conn = db_connect(config)
    ensure_schema(conn)
    payload = {"kind": kind, "path": path, "track_id": track_id, "started_at": datetime.now(timezone.utc).isoformat()}
    if track is not None:
        payload.update({
            "artist": track["artist"] or "",
            "title": track["title"] or Path(track["path"]).stem,
            "album": track["album"] or "",
            "genre": track["genre"] or "",
            "year": track["year"],
            "duration": track["duration"],
        })
    elif kind == "announcement":
        payload.update({"artist": "NRG Radio", "title": "Presentatie", "album": "", "genre": "Radio", "year": None, "duration": None})
    set_state(conn, "now_playing", payload)
