#!/usr/bin/env python3
from __future__ import annotations

import logging
import random
from pathlib import Path

from ai_presenter import generate_announcement
from common import db_connect, ensure_schema, load_config, setup_logging
from music_selector import mark_played, pick_track
from state import set_now_playing

log = logging.getLogger("next")


def pop_queue(conn):
    row = conn.execute("SELECT * FROM queue ORDER BY id LIMIT 1").fetchone()
    if not row:
        return None
    conn.execute("DELETE FROM queue WHERE id=?", (row["id"],))
    conn.commit()
    return row


def queue_item(conn, kind, path, track_id=None):
    conn.execute("INSERT INTO queue(kind,path,track_id) VALUES(?,?,?)", (kind, str(path), track_id))
    conn.commit()


def track_by_id(conn, track_id):
    if not track_id:
        return None
    return conn.execute("SELECT * FROM tracks WHERE id=?", (int(track_id),)).fetchone()


def emit(kind, path, track_id=None, track=None):
    try:
        set_now_playing(kind, path, track_id, track)
    except Exception as exc:
        log.warning("Kon now-playing status niet bijwerken: %s", exc)
    print(path)


def main():
    setup_logging()
    config = load_config()
    conn = db_connect(config)
    ensure_schema(conn)
    for _ in range(20):
        queued = pop_queue(conn)
        if not queued:
            break
        if not Path(queued["path"]).is_file():
            log.warning("Queue-item bestaat niet meer: %s", queued["path"])
            continue
        track = track_by_id(conn, queued["track_id"])
        if queued["kind"] == "music" and queued["track_id"]:
            mark_played(int(queued["track_id"]))
        emit(queued["kind"], queued["path"], queued["track_id"], track)
        return 0
    track = pick_track()
    if not track:
        log.error("Geen afspeelbare muziek gevonden. Controleer /mnt/music en voer scan_music.py uit.")
        return 2
    ai = config.get("ai", {})
    announce = bool(ai.get("enabled", True)) and random.random() < float(ai.get("announcement_probability", 0.35))
    if announce:
        announcement = generate_announcement(track)
        if announcement and Path(announcement).is_file():
            queue_item(conn, "music", track["path"], int(track["id"]))
            emit("announcement", str(announcement))
            return 0
    mark_played(int(track["id"]))
    emit("music", track["path"], int(track["id"]), track)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
