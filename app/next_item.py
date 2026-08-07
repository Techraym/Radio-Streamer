#!/usr/bin/env python3
from __future__ import annotations

import logging
import random

from ai_presenter import generate_announcement
from common import db_connect, ensure_schema, load_config, setup_logging
from music_selector import mark_played, pick_track

log = logging.getLogger("next")

def pop_queue(conn):
    row = conn.execute("SELECT * FROM queue ORDER BY id LIMIT 1").fetchone()
    if not row:
        return None
    conn.execute("DELETE FROM queue WHERE id=?", (row["id"],))
    conn.commit()
    return row

def queue_item(conn, kind, path, track_id=None):
    conn.execute(
        "INSERT INTO queue(kind,path,track_id) VALUES(?,?,?)",
        (kind, str(path), track_id),
    )
    conn.commit()

def main():
    setup_logging()
    config = load_config()
    conn = db_connect(config)
    ensure_schema(conn)

    queued = pop_queue(conn)
    if queued:
        if queued["kind"] == "music" and queued["track_id"]:
            mark_played(int(queued["track_id"]))
        print(queued["path"])
        return 0

    track = pick_track()
    if not track:
        log.error("Geen afspeelbare muziek gevonden. Controleer /mnt/music en voer scan_music.py uit.")
        return 2

    ai = config.get("ai", {})
    announce = bool(ai.get("enabled", True)) and random.random() < float(ai.get("announcement_probability", 0.35))

    if announce:
        announcement = generate_announcement(track)
        if announcement:
            queue_item(conn, "music", track["path"], int(track["id"]))
            print(str(announcement))
            return 0

    mark_played(int(track["id"]))
    print(track["path"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
