# Changelog

## 1.2.0
- Website/API-service op poort 8042.
- `/api/now-playing`, `/api/history`, `/api/status` en `/health`.
- Albumhoes-API leest uitsluitend embedded MP3 ID3/APIC artwork.
- Lokale cover-cache; muziekopslag blijft read-only.
- Now-playing state vanuit de radioqueue.
- CORS voor raysnijder.nl.
- Nieuwe `nrg-radio-api.service`.
- Smoke-test voor storage, Python, Liquidsoap, scan, trackselectie, FFmpeg, Ollama en API.
- Healthcheck uitgebreid met API-controle.
- Scanner maakt `/mnt/music` nooit zelf aan en schrijft niet naar de muziekbron.

## 1.1.0
- Complete radio-engine.
- Proxmox/Debian headless architectuur.
- Read-only `/mnt/music`.
- SQLite catalogus en geschiedenis.
- 8 uur artiest-repeat / 72 uur track-repeat.
- Dagdeelafhankelijke selectie.
- Ollama AI-presentator en Edge TTS.
- Liquidsoap naar Caster.fm 96 kbps.
