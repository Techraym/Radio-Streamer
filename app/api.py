#!/usr/bin/env python3
from __future__ import annotations

import socket

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from common import db_connect, ensure_schema, get_state, load_config
from covers import cached_cover

config = load_config()
app = FastAPI(title="NRG Radio API", version="1.2.0")
origins = config.get("api", {}).get("allowed_origins", [])
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])


def conn():
    c = db_connect(config)
    ensure_schema(c)
    return c


def caster_reachable():
    stream = config.get("stream", {})
    host = stream.get("caster_host")
    port = int(stream.get("caster_port", 0) or 0)
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


@app.get("/health")
def health():
    c = conn()
    music_count = c.execute("SELECT COUNT(*) FROM tracks WHERE enabled=1").fetchone()[0]
    return {"ok": True, "version": "1.2.0", "music_tracks": music_count, "music_mount": config["station"]["music_dir"]}


@app.get("/api/status")
def status():
    c = conn()
    music_count = c.execute("SELECT COUNT(*) FROM tracks WHERE enabled=1").fetchone()[0]
    last_play = c.execute("SELECT MAX(played_at) AS t FROM play_history").fetchone()["t"]
    return {"station": config["station"]["name"], "version": "1.2.0", "music_tracks": music_count, "last_played_at": last_play, "caster_reachable": caster_reachable(), "bitrate_kbps": config.get("stream", {}).get("bitrate_kbps", 96), "public_stream_url": config.get("stream", {}).get("public_url", "")}


@app.get("/api/now-playing")
def now_playing():
    c = conn()
    current = get_state(c, "now_playing", None)
    if not current:
        return {"station": config["station"]["name"], "playing": False, "kind": None, "artist": "", "title": "", "album": "", "track_id": None, "cover_url": "/api/cover/current"}
    current = dict(current)
    current["station"] = config["station"]["name"]
    current["playing"] = True
    current["cover_url"] = "/api/cover/current"
    current.pop("path", None)
    return current


@app.get("/api/history")
def history(limit: int = Query(default=20, ge=1, le=100)):
    c = conn()
    rows = c.execute("""
        SELECT h.played_at, t.id AS track_id, t.artist, t.title, t.album,
               t.genre, t.year, t.duration
        FROM play_history h
        JOIN tracks t ON t.id=h.track_id
        ORDER BY h.id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [{"played_at": r["played_at"], "track_id": r["track_id"], "artist": r["artist"], "title": r["title"], "album": r["album"], "genre": r["genre"], "year": r["year"], "duration": r["duration"], "cover_url": f"/api/cover/{r['track_id']}"} for r in rows]


def get_track(track_id: int):
    c = conn()
    row = c.execute("SELECT * FROM tracks WHERE id=? AND enabled=1", (track_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Track niet gevonden")
    return row


@app.get("/api/cover/current")
def cover_current():
    c = conn()
    current = get_state(c, "now_playing", None)
    if not current or not current.get("track_id"):
        data, mime, _ = cached_cover(0, "", "NRG Radio")
        return Response(content=data, media_type=mime, headers={"Cache-Control": "no-cache"})
    return cover_track(int(current["track_id"]))


@app.get("/api/cover/{track_id}")
def cover_track(track_id: int):
    row = get_track(track_id)
    data, mime, fallback = cached_cover(int(row["id"]), row["path"], row["album"] or row["title"] or "NRG Radio")
    cache = "public, max-age=86400" if not fallback else "public, max-age=3600"
    return Response(content=data, media_type=mime, headers={"Cache-Control": cache})
