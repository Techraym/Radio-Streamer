#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

import edge_tts
from mutagen.id3 import ID3, TIT2, TPE1
from mutagen.mp3 import MP3

from common import load_config

log = logging.getLogger("ai")

def _clean(text: str, max_words: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip().strip('"')
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(",;:-") + "."
    return text

def fallback_line(track) -> str:
    artist = (track["artist"] or "").strip()
    title = (track["title"] or "").strip()
    if artist and title:
        return f"Je luistert naar NRG Radio. Hier is {artist} met {title}."
    if title:
        return f"NRG Radio gaat verder met {title}."
    return "NRG Radio gaat verder met de volgende plaat."

def ollama_line(track, config) -> str:
    ai = config["ai"]
    artist = (track["artist"] or "onbekende artiest").strip()
    title = (track["title"] or Path(track["path"]).stem).strip()
    album = (track["album"] or "").strip()
    genre = (track["genre"] or "").strip()
    year = track["year"] or ""

    prompt = (
        "Je bent de Nederlandse radiopresentator van NRG Radio. "
        "Schrijf één korte, natuurlijke aankondiging voor het nummer dat direct hierna draait. "
        "Geen opsomming, geen hashtags, geen aanhalingstekens, geen verzonnen feiten. "
        "Noem artiest en titel. Maximaal "
        f"{ai.get('max_words', 42)} woorden.\n"
        f"Artiest: {artist}\nTitel: {title}\nAlbum: {album}\nGenre: {genre}\nJaar: {year}"
    )
    payload = json.dumps({
        "model": ai.get("model", "llama3.2:1b"),
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        ai.get("ollama_url", "http://127.0.0.1:11434").rstrip("/") + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=float(ai.get("timeout_seconds", 18))) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _clean(data.get("response", ""), int(ai.get("max_words", 42)))

async def _tts(text: str, out: Path, ai):
    communicator = edge_tts.Communicate(
        text,
        voice=ai.get("voice", "nl-NL-MaartenNeural"),
        rate=ai.get("rate", "+0%"),
        pitch=ai.get("pitch", "+0Hz"),
        volume=ai.get("volume", "+0%"),
    )
    await communicator.save(str(out))

def tag_announcement(path: Path, title: str):
    try:
        audio = MP3(path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass
        audio.tags.delall("TPE1")
        audio.tags.delall("TIT2")
        audio.tags.add(TPE1(encoding=3, text=["NRG Radio"]))
        audio.tags.add(TIT2(encoding=3, text=[title]))
        audio.save()
    except Exception as exc:
        log.warning("Kon TTS metadata niet zetten: %s", exc)

def generate_announcement(track) -> Path | None:
    config = load_config()
    ai = config.get("ai", {})
    if not ai.get("enabled", True):
        return None

    try:
        text = ollama_line(track, config)
        if not text:
            text = fallback_line(track)
    except Exception as exc:
        log.warning("Ollama niet beschikbaar, fallback gebruikt: %s", exc)
        text = fallback_line(track)

    out_dir = Path(config["station"]["generated_dir"]) / "announcements"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"announcement_{int(time.time()*1000)}.mp3"

    try:
        asyncio.run(_tts(text, out, ai))
        tag_announcement(out, "Presentatie")
        cleanup(out_dir)
        return out
    except Exception as exc:
        log.error("TTS genereren mislukt: %s", exc)
        try:
            out.unlink(missing_ok=True)
        except Exception:
            pass
        return None

def cleanup(directory: Path, keep=40):
    files = sorted(directory.glob("announcement_*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
