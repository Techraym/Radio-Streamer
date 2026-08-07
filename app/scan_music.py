#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
from pathlib import Path

from mutagen import File as MutagenFile

from common import db_connect, ensure_schema, load_config, setup_logging

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".mp4", ".ogg", ".opus", ".wav", ".aac"}

log = logging.getLogger("scan")

def first_tag(audio, names, default=""):
    for name in names:
        try:
            value = audio.tags.get(name) if audio and audio.tags else None
        except Exception:
            value = None
        if value:
            if isinstance(value, (list, tuple)):
                value = value[0]
            text = str(value).strip()
            if text:
                return text
    return default

def parse_year(text):
    if not text:
        return None
    digits = "".join(ch for ch in str(text) if ch.isdigit())
    if len(digits) >= 4:
        try:
            return int(digits[:4])
        except ValueError:
            return None
    return None

def read_metadata(path: Path):
    artist = ""
    title = path.stem
    album = ""
    genre = ""
    year = None
    duration = None

    try:
        audio = MutagenFile(path, easy=True)
        if audio:
            artist = first_tag(audio, ["artist", "©ART"], "")
            title = first_tag(audio, ["title", "©nam"], path.stem)
            album = first_tag(audio, ["album", "©alb"], "")
            genre = first_tag(audio, ["genre", "©gen"], "")
            year = parse_year(first_tag(audio, ["date", "year", "©day"], ""))
            if getattr(audio, "info", None):
                duration = float(getattr(audio.info, "length", 0) or 0)
    except Exception as exc:
        log.warning("Metadata fout voor %s: %s", path, exc)

    return artist.strip(), title.strip(), album.strip(), genre.strip(), year, duration

def main():
    setup_logging()
    config = load_config()
    music_dir = Path(config["station"]["music_dir"])
    if not music_dir.exists():
        raise SystemExit(f"Muziekmap bestaat niet: {music_dir}")

    conn = db_connect(config)
    ensure_schema(conn)

    found = 0
    for path in music_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
            continue
        found += 1
        stat = path.stat()
        artist, title, album, genre, year, duration = read_metadata(path)
        conn.execute(
            """
            INSERT INTO tracks(path, artist, title, album, genre, year, duration, mtime, enabled, last_seen)
            VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(path) DO UPDATE SET
                artist=excluded.artist,
                title=excluded.title,
                album=excluded.album,
                genre=excluded.genre,
                year=excluded.year,
                duration=excluded.duration,
                mtime=excluded.mtime,
                enabled=1,
                last_seen=CURRENT_TIMESTAMP
            """,
            (str(path), artist, title, album, genre, year, duration, stat.st_mtime),
        )

    rows = conn.execute("SELECT id,path FROM tracks WHERE enabled=1").fetchall()
    disabled = 0
    for row in rows:
        if not os.path.isfile(row["path"]):
            conn.execute("UPDATE tracks SET enabled=0 WHERE id=?", (row["id"],))
            disabled += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM tracks WHERE enabled=1").fetchone()[0]
    log.info("Scan klaar: %d gevonden, %d actief, %d uitgeschakeld", found, total, disabled)

if __name__ == "__main__":
    main()
