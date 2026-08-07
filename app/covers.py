#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple

from mutagen.id3 import ID3, APIC

from common import load_config


def fallback_svg(title: str = "NRG Radio") -> bytes:
    safe = (title or "NRG Radio").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#ff6a3d"/><stop offset="1" stop-color="#5c6cff"/></linearGradient></defs>'
        '<rect width="800" height="800" rx="400" fill="url(#g)"/>'
        '<circle cx="400" cy="400" r="250" fill="#000" opacity=".18"/>'
        '<circle cx="400" cy="400" r="55" fill="white" opacity=".9"/>'
        f'<text x="400" y="660" text-anchor="middle" font-family="Arial,sans-serif" font-size="54" '
        f'font-weight="700" fill="white">{safe[:22]}</text></svg>'
    ).encode("utf-8")


def extract_id3_cover(path: str) -> Optional[Tuple[bytes, str]]:
    """Read embedded album artwork from an MP3 ID3 APIC frame.

    The source file is opened read-only. No tag or artwork is ever written back.
    """
    p = Path(path)
    if not p.is_file() or p.suffix.lower() != ".mp3":
        return None
    try:
        tags = ID3(p)
    except Exception:
        return None
    pictures = [frame for frame in tags.values() if isinstance(frame, APIC) and frame.data]
    if not pictures:
        return None
    front = next((frame for frame in pictures if getattr(frame, "type", None) == 3), pictures[0])
    return bytes(front.data), front.mime or "image/jpeg"


def cached_cover(track_id: int, path: str, title: str = "") -> Tuple[bytes, str, bool]:
    config = load_config()
    cache_dir = Path(config.get("api", {}).get("cover_cache_dir", "/var/lib/nrg-radio/cover-cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not path:
        return fallback_svg(title or "NRG Radio"), "image/svg+xml", True
    p = Path(path)
    try:
        stamp = f"{p.stat().st_mtime_ns}:{p.stat().st_size}"
    except OSError:
        stamp = "missing"
    key = hashlib.sha1(f"{track_id}:{path}:{stamp}".encode("utf-8")).hexdigest()
    meta = cache_dir / f"{key}.mime"
    blob = cache_dir / f"{key}.bin"
    if blob.is_file() and meta.is_file():
        return blob.read_bytes(), meta.read_text(encoding="utf-8").strip(), False
    found = extract_id3_cover(path)
    if found:
        data, mime = found
        try:
            blob.write_bytes(data)
            meta.write_text(mime, encoding="utf-8")
        except OSError:
            pass
        return data, mime, False
    return fallback_svg(title or "NRG Radio"), "image/svg+xml", True
