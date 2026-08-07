#!/usr/bin/env python3
from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

from common import db_connect, ensure_schema, load_config

def _minutes(hhmm: str) -> int:
    h, m = (int(x) for x in hhmm.split(":"))
    return h * 60 + m

def current_daypart(config):
    now = datetime.now()
    cur = now.hour * 60 + now.minute
    for dp in config["music"].get("dayparts", []):
        start = _minutes(dp["start"])
        end = _minutes(dp["end"])
        if start < end:
            match = start <= cur < end
        else:
            match = cur >= start or cur < end
        if match:
            return dp
    return {"name": "default", "genres": []}

def excluded_genre(genre: str, config) -> bool:
    g = (genre or "").lower()
    return any(x.lower() in g for x in config["music"].get("excluded_genres", []))

def pick_track():
    config = load_config()
    conn = db_connect(config)
    ensure_schema(conn)

    artist_hours = int(config["music"].get("artist_repeat_hours", 8))
    track_hours = int(config["music"].get("track_repeat_hours", 72))

    rows = conn.execute(
        """
        SELECT t.*
        FROM tracks t
        WHERE t.enabled=1
          AND NOT EXISTS (
              SELECT 1 FROM play_history h
              WHERE h.track_id=t.id
                AND h.played_at >= datetime('now', ?)
          )
          AND (
              trim(t.artist)=''
              OR NOT EXISTS (
                  SELECT 1
                  FROM play_history h2
                  JOIN tracks t2 ON t2.id=h2.track_id
                  WHERE lower(trim(t2.artist))=lower(trim(t.artist))
                    AND h2.played_at >= datetime('now', ?)
              )
          )
        """,
        (f"-{track_hours} hours", f"-{artist_hours} hours"),
    ).fetchall()

    if not rows:
        rows = conn.execute(
            """
            SELECT t.*
            FROM tracks t
            WHERE t.enabled=1
              AND NOT EXISTS (
                  SELECT 1 FROM play_history h
                  WHERE h.track_id=t.id
                    AND h.played_at >= datetime('now', ?)
              )
            """,
            (f"-{track_hours} hours",),
        ).fetchall()

    if not rows:
        rows = conn.execute("SELECT * FROM tracks WHERE enabled=1").fetchall()

    rows = [r for r in rows if Path(r["path"]).is_file() and not excluded_genre(r["genre"], config)]
    if not rows:
        return None

    dp = current_daypart(config)
    preferred = [g.lower() for g in dp.get("genres", [])]

    weighted = []
    for row in rows:
        genre = (row["genre"] or "").lower()
        weight = 4 if preferred and any(g in genre for g in preferred) else 1
        weighted.extend([row] * weight)

    return random.choice(weighted)

def mark_played(track_id: int):
    config = load_config()
    conn = db_connect(config)
    ensure_schema(conn)
    conn.execute("INSERT INTO play_history(track_id) VALUES(?)", (track_id,))
    conn.commit()
